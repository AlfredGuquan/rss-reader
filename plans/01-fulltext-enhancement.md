# 全文抓取增强方案

## 1. 当前实现分析

当前的全文抓取实现位于 `backend/app/services/content_service.py`，核心逻辑约 65 行代码，使用 trafilatura 库进行内容提取。

### 工作流程

整个流程分为两个阶段。第一阶段是 RSS feed 解析（`fetch_service.py`），从 RSS/Atom feed 中提取 entry 的 summary 和 content 字段（来自 feedparser），并将 `content_fetched` 设为 False。第二阶段是全文抓取（`content_service.py`），由 APScheduler 每 10 分钟触发 `fetch_content_batch`，每批处理 20 条 `content_fetched=False` 的 entry，使用 trafilatura 访问原始 URL 并提取正文 HTML，通过 `asyncio.Semaphore(5)` 控制并发。

用户也可以通过 `POST /api/entries/{entry_id}/fetch-content` 手动触发单篇文章的全文抓取。

### 当前实现的优点

trafilatura 是目前 Python 生态中 F1 分数最高的正文提取库（F1=0.958），显著优于 readability-lxml（0.922）和 newspaper4k（0.949）。代码结构清晰，使用了信号量控制并发，有异常处理和错误日志记录。`content_fetched` 标志位防止重复抓取。

### 当前实现的不足

第一，trafilatura 内置的 HTTP 下载器（`trafilatura.fetch_url`）不支持自定义 headers、代理、cookies，对反爬虫网站基本无能为力。第二，没有 per-feed 的自定义抓取规则（CSS 选择器或 XPath），对于某些网站 trafilatura 的自动提取效果不佳时无法手动介入。第三，抓取失败后直接将 `content_fetched` 标记为 True，没有重试机制，也没有区分"抓取失败"和"抓取成功但无内容"。第四，没有利用 trafilatura 的高级参数（`favor_recall`、`favor_precision`、`deduplicate`）。第五，使用 `asyncio.to_thread` 包裹同步调用，而 trafilatura 内部会自行发 HTTP 请求，无法复用项目已有的 httpx 异步客户端。第六，批处理大小硬编码为 20，没有配置化。

## 2. 推荐技术方案

采用分层提取策略（Cascade Extraction），按优先级尝试多种方法，直到成功提取内容。

### 2.1 分层提取架构

```
Layer 0: Per-feed CSS/XPath 自定义规则（优先级最高）
Layer 1: Trafilatura 提取（主力，已有）
Layer 2: readability-lxml 回退（当 trafilatura 结果为空或质量低）
Layer 3: 原始 RSS content 保留（兜底）
```

每一层尝试后，如果结果内容长度大于阈值（如 200 字符），就认为提取成功并停止。否则继续尝试下一层。

### 2.2 自定义 HTTP 下载

将 HTML 下载与内容提取解耦。用项目已有的 httpx AsyncClient（支持 socks 代理、自定义 headers、follow_redirects）统一负责下载，然后将 HTML 字符串传给各提取器处理。这样可以在 Feed 级别配置自定义 User-Agent、cookies、代理等参数。

### 2.3 Per-Feed 自定义规则

在 Feed 模型上增加一个 JSON 字段 `fulltext_config`，存储该 feed 的自定义抓取配置：

```json
{
  "css_selector": "article.post-content",
  "css_remove": ".ads, .sidebar, .related-posts",
  "xpath": "//div[@class='entry-content']",
  "user_agent": "Mozilla/5.0 ...",
  "headers": {"Cookie": "..."},
  "prefer_original_content": true,
  "extraction_mode": "precision"
}
```

当 `css_selector` 或 `xpath` 存在时，直接使用 BeautifulSoup/lxml 按规则提取，跳过 trafilatura。这是 FreshRSS 使用的成熟方案。

### 2.4 增强 Trafilatura 参数

根据 feed 特性（新闻类 vs 博客类 vs 论坛类）动态调整 trafilatura 参数：

对于新闻类 feed，使用 `favor_precision=True` 减少噪音；对于博客类 feed，使用 `favor_recall=True` 确保完整内容；统一启用 `include_links=True, include_images=True, output_format="html"` 保留富文本格式。

### 2.5 抓取失败与重试

区分三种状态：`not_fetched`（未抓取）、`fetched`（成功）、`failed`（失败但可重试）。失败的 entry 记录失败原因和重试次数，允许最多重试 3 次，重试间隔随失败次数指数递增。超过最大重试次数后标记为永久失败。

## 3. 具体实现步骤

### 步骤 1：数据模型变更

文件 `backend/app/models/feed.py`，在 Feed 模型中新增：

```python
fulltext_config: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
```

存储 JSON 格式的自定义抓取配置。

文件 `backend/app/models/entry.py`，在 Entry 模型中新增：

```python
content_fetch_status: Mapped[str] = mapped_column(
    String, default="pending", server_default="pending"
)
content_fetch_error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
content_fetch_retries: Mapped[int] = mapped_column(default=0, server_default="0")
extraction_method: Mapped[Optional[str]] = mapped_column(String, nullable=True)
```

`content_fetch_status` 取值为 "pending"、"success"、"failed"、"permanent_failure"。`extraction_method` 记录实际使用的提取层（"custom_css"、"trafilatura"、"readability"、"original"）。

需要同时编写 Alembic 迁移脚本处理新字段，以及将旧的 `content_fetched=True` 数据映射为 `content_fetch_status="success"` 或 `"permanent_failure"`。

### 步骤 2：重写 content_service.py

将 `content_service.py` 重构为分层提取架构：

```python
# backend/app/services/content_service.py

async def extract_with_custom_rules(html: str, config: dict) -> str | None:
    """Layer 0: CSS/XPath 自定义规则提取"""

async def extract_with_trafilatura(html: str, mode: str = "default") -> str | None:
    """Layer 1: Trafilatura 提取"""

async def extract_with_readability(html: str) -> str | None:
    """Layer 2: readability-lxml 回退"""

async def cascade_extract(html: str, feed_config: dict | None) -> tuple[str | None, str]:
    """按优先级尝试各提取层，返回 (content, method_name)"""

async def download_html(url: str, feed_config: dict | None) -> str | None:
    """使用 httpx 下载页面 HTML"""

async def fetch_content_for_entry(session: AsyncSession, entry: Entry, feed: Feed) -> bool:
    """单篇文章全文抓取入口"""
```

关键变化是下载和提取解耦：`download_html` 用 httpx 下载原始 HTML，`cascade_extract` 按层级提取正文，`fetch_content_for_entry` 协调整个流程并更新数据库状态。

### 步骤 3：更新 Schema 和 API

文件 `backend/app/schemas/feed.py`，`FeedUpdate` 中增加 `fulltext_config: Optional[dict] = None` 字段，`FeedResponse` 中增加对应的响应字段。

文件 `backend/app/schemas/entry.py`，`EntryResponse` 中将 `content_fetched: bool` 替换为（或补充）`content_fetch_status: str` 和 `extraction_method: Optional[str]`。

文件 `backend/app/routers/entries.py`，`fetch-content` 端点需要传入 feed 信息以获取自定义规则。

### 步骤 4：更新批处理逻辑

文件 `backend/app/tasks/jobs.py`，`fetch_content_batch` 需要 join Feed 表以获取 `fulltext_config`，筛选条件从 `content_fetched == False` 变为 `content_fetch_status.in_(["pending", "failed"])`，同时只重试 `retries < MAX_RETRIES` 的 entry。

### 步骤 5：前端配置界面

文件 `frontend/src/components/` 中增加 Feed 设置弹窗的全文抓取配置面板，允许用户：填写 CSS 选择器（正选 + 排除），填写自定义 User-Agent 和 Headers，选择提取模式（自动 / 精确 / 完整），测试抓取效果（调用 fetch-content 端点并预览结果）。

## 4. 需要的新依赖

在 `backend/pyproject.toml` 中新增：

```
"readability-lxml>=0.8.1"
"beautifulsoup4>=4.12.0"
"lxml>=5.0.0"
```

trafilatura 已经是现有依赖（`>=2.0.0`），无需变更。httpx 也已存在。beautifulsoup4 用于 CSS 选择器自定义规则的解析。readability-lxml 作为 Layer 2 回退提取器。lxml 是 readability-lxml 的底层依赖，通常会自动安装，但显式声明更稳妥。

## 5. 预期效果

通过分层提取策略，全文抓取的成功率预计从当前的 70-80% 提升到 90% 以上。对于 trafilatura 难以处理的网站（如反爬严重的新闻站点、结构特殊的博客平台），用户可以通过 CSS 选择器自定义规则实现精准提取。readability-lxml 回退层可以捕获 trafilatura 遗漏的内容（尤其是 recall 方面的优势）。重试机制避免了因临时网络问题导致的永久性内容缺失。`extraction_method` 字段让用户了解每篇文章是如何被提取的，便于调试和优化规则。

### 兼容性

所有变更向后兼容。旧数据通过迁移脚本自动映射到新状态字段。前端可以渐进式采用新的 API 字段，`content_fetched` 在过渡期仍然保留（作为 `content_fetch_status == "success"` 的语法糖）。

### 性能影响

新增 readability-lxml 回退仅在 trafilatura 失败时触发，不影响正常提取路径的性能。CSS/XPath 自定义规则是最快的提取路径（跳过 trafilatura 的复杂启发式算法），对已配置规则的 feed 反而会加速。HTTP 下载使用 httpx 异步客户端，比 trafilatura 内置的同步下载更高效。
