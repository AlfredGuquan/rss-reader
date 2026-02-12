# AI 摘要、智能排序与 AI 过滤规则

## 现状分析

当前项目的 Entry 模型已有 `summary` 字段（存储 RSS feed 自带的摘要），但没有 AI 生成的摘要。文章排序采用简单的 `published_at DESC` 时间倒序，无智能排序。搜索基于 FTS5 全文检索，过滤仅支持 unread/starred/all 三种状态。后台通过 APScheduler 调度 feed 抓取和全文提取任务，已有批量处理基础设施。

技术栈关键约束：SQLite 数据库，单用户模式（default_user_id 硬编码），FastAPI + SQLAlchemy async 后端，React + Zustand 前端。


## 一、技术方案选型

### 1.1 LLM Provider 统一层：LiteLLM

推荐使用 LiteLLM 作为 LLM 调用的统一抽象层。LiteLLM 提供一个 OpenAI 兼容的 Python SDK，支持 100+ 模型提供商（OpenAI、Anthropic Claude、Google Gemini、DeepSeek、Ollama 本地模型等），通过 `litellm.acompletion()` 统一异步调用。这使得 BYOK 架构的实现极为简洁——只需切换 model 字符串和 api_key 即可。

选择 LiteLLM 而不是直接对接各家 SDK 的原因：一是避免为每个 provider 写适配代码，二是 LiteLLM 内置了 token 计数、cost tracking、fallback 和 retry 机制，三是用户日后切换 provider 无需改后端代码。

### 1.2 推荐模型组合

摘要生成和过滤规则不需要顶级推理能力，应优先选择性价比高的模型：

| 用途 | 推荐模型 | 备选 | 单价 (每 1M token) |
|------|----------|------|-------------------|
| 摘要生成 | Gemini 2.5 Flash | DeepSeek V3, GPT-4o Mini | Input $0.15, Output $0.60 |
| AI 过滤判定 | Gemini 2.5 Flash | DeepSeek V3 | 同上 |
| Embedding | text-embedding-3-small | 本地 all-MiniLM-L6-v2 | $0.02 / 1M tokens |
| 翻译（可选） | Gemini 2.5 Flash | DeepSeek V3 | 同上 |

Gemini 2.5 Flash 在成本和质量之间取得了极好的平衡。DeepSeek 更便宜（$0.14 input + $0.28 output / 1M tokens）但服务可用性不如 Google 稳定。如果用户有 Ollama 本地部署，则所有功能零成本。

### 1.3 成本估算

假设每天处理 200 篇文章，每篇平均 2000 tokens 内容，摘要输出约 150 tokens：

| 操作 | 每日 Token 消耗 | Gemini Flash 成本 | GPT-4o Mini 成本 |
|------|----------------|-------------------|------------------|
| 摘要生成 | 400K input + 30K output | ~$0.08 | ~$0.31 |
| AI 过滤（10条规则） | 200K input + 10K output | ~$0.04 | ~$0.13 |
| Embedding | 400K input | ~$0.01 | ~$0.01 |
| 月度总计 | - | ~$3.9 | ~$13.5 |

这个成本对个人用户完全可接受。通过批量处理和缓存可进一步降低。


## 二、BYOK 架构设计

### 2.1 数据模型

新增 `ai_settings` 表存储用户的 AI 配置：

```sql
CREATE TABLE ai_settings (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL REFERENCES users(id),
    provider TEXT NOT NULL DEFAULT 'openai',       -- openai/anthropic/gemini/deepseek/ollama/custom
    api_key TEXT,                                    -- 加密存储，Ollama 可为空
    api_base TEXT,                                   -- 自定义 endpoint (Ollama: http://localhost:11434)
    model_summary TEXT DEFAULT 'gemini/gemini-2.5-flash',  -- LiteLLM model string
    model_filter TEXT DEFAULT 'gemini/gemini-2.5-flash',
    model_embedding TEXT DEFAULT 'text-embedding-3-small',
    embedding_api_key TEXT,                          -- embedding 可用不同 provider
    embedding_api_base TEXT,
    auto_summarize BOOLEAN DEFAULT FALSE,            -- 新文章自动摘要
    auto_filter BOOLEAN DEFAULT FALSE,               -- 新文章自动应用过滤规则
    max_daily_calls INTEGER DEFAULT 500,             -- 每日调用限制
    daily_calls_used INTEGER DEFAULT 0,
    daily_reset_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### 2.2 API Key 安全

API key 在存入数据库前使用 Fernet 对称加密（`cryptography` 库）。加密密钥从环境变量 `RSS_ENCRYPTION_KEY` 读取，首次启动时自动生成并写入 `.env` 文件。这对单用户本地应用是足够安全的方案——密钥与数据库分离，即使 db 文件泄露也无法还原 API key。

### 2.3 LiteLLM 调用封装

后端创建 `app/services/ai_service.py` 作为所有 AI 调用的统一入口：

```python
import litellm
from app.services.encryption import decrypt_key

async def call_llm(settings: AISettings, prompt: str, system: str = "", max_tokens: int = 300) -> str:
    """统一的 LLM 调用，根据用户的 BYOK 配置路由到对应 provider."""
    api_key = decrypt_key(settings.api_key) if settings.api_key else None
    response = await litellm.acompletion(
        model=settings.model_summary,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": prompt},
        ],
        api_key=api_key,
        api_base=settings.api_base,
        max_tokens=max_tokens,
        temperature=0.3,
    )
    return response.choices[0].message.content
```

LiteLLM 的 model string 格式为 `provider/model-name`，如 `gemini/gemini-2.5-flash`、`anthropic/claude-3-haiku`、`ollama/llama3`、`deepseek/deepseek-chat`。用户在设置页面选择 provider 和 model，前端拼接成 LiteLLM model string 传给后端。


## 三、AI 摘要

### 3.1 数据模型变更

在 Entry 模型新增字段，将 AI 摘要与 RSS 原生摘要分开存储：

```sql
ALTER TABLE entries ADD COLUMN ai_summary TEXT;
ALTER TABLE entries ADD COLUMN ai_summary_generated_at TIMESTAMP;
```

保留原有 `summary` 字段（RSS feed 提供的原始摘要），新增 `ai_summary` 字段存储 AI 生成的摘要。这样用户可以同时看到原始摘要和 AI 摘要，也方便回退。

### 3.2 摘要生成流程

摘要生成有两个触发时机：

第一个是后台批量生成。当 `auto_summarize` 开启时，feed 抓取完成后，新增一个 APScheduler 任务，批量为尚未生成 AI 摘要的新文章调用 LLM。批量处理使用 `asyncio.Semaphore(3)` 控制并发，避免 API rate limit。每次最多处理 50 篇，通过 `ai_summary IS NULL AND created_at > datetime('now', '-24 hours')` 筛选。

第二个是用户手动触发。用户在阅读面板点击"生成 AI 摘要"按钮，单篇即时调用。这个场景延迟要求高，直接调用 LLM 返回 streaming response。

### 3.3 Prompt 设计

```
System: You are a concise article summarizer. Generate a 2-3 sentence summary in the same language as the article. Focus on the key insight or news value. Do not include phrases like "This article discusses" or "The author argues".

User: Summarize the following article:

Title: {title}
Content: {content[:3000]}
```

限制 content 到前 3000 字符（约 1000-1500 tokens），既包含文章核心信息，又控制成本。对于内容极短（< 200 字符）或无内容的文章，跳过摘要生成。

### 3.4 缓存策略

AI 摘要直接持久化到 `entries.ai_summary` 字段，无需额外缓存层。摘要一旦生成不会过期——文章内容不变，摘要也不需要更新。用户可手动点击"重新生成"来刷新。

### 3.5 前端展示

在 EntryCard 组件中，当 `ai_summary` 存在时优先显示 AI 摘要（前面加一个小的 AI 图标标识），否则回退到原始 `summary`。在文章详情阅读面板中，AI 摘要作为一个可折叠的卡片展示在文章正文之前，带有"AI 生成"标签。

```typescript
// EntryCard 中的摘要展示逻辑
const displaySummary = entry.ai_summary || entry.summary;
```


## 四、智能排序

### 4.1 方案选择：混合评分排序

不采用纯 embedding 相似度排序（需要用户 profile 向量，冷启动问题严重），而是采用混合评分系统，结合多个可解释的信号：

```
score = w1 * recency_score + w2 * engagement_score + w3 * source_priority + w4 * keyword_boost
```

各分量的计算方式：

`recency_score` 基于发布时间的衰减函数，最近 1 小时内 = 1.0，24 小时内线性衰减到 0.5，超过 3 天 = 0.1。这是默认权重最高的信号。

`engagement_score` 基于用户的阅读行为：来自用户经常阅读（is_read = True 比例高）的 feed 得分更高。计算为该 feed 近 30 天已读文章数 / 总文章数。这是一个隐式反馈信号，不需要用户手动配置。

`source_priority` 用户可以给 feed 设定优先级（高/中/低），映射为 1.0 / 0.6 / 0.3。默认为中。

`keyword_boost` 如果文章标题或摘要匹配用户定义的关注关键词，加分。这与 AI 过滤规则系统集成。

### 4.2 数据模型变更

Feed 模型新增 `priority` 字段：

```sql
ALTER TABLE feeds ADD COLUMN priority TEXT DEFAULT 'medium';  -- high/medium/low
```

新增 `user_interests` 表存储用户关注的关键词/话题（也供 AI 过滤使用）：

```sql
CREATE TABLE user_interests (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL REFERENCES users(id),
    keyword TEXT NOT NULL,
    weight REAL DEFAULT 1.0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### 4.3 排序实现

排序评分在查询时计算，不预存储。考虑到 SQLite 的计算能力有限，采用的策略是：在 Python 层面对查询结果做后排序。获取最近的文章（如最近 3 天的 unread），在 Python 中计算每篇文章的综合分数，排序后返回。

```python
async def list_entries_smart(db, user_id, page, per_page):
    # 1. 获取最近的文章（宽范围查询）
    entries = await fetch_recent_entries(db, user_id, days=3, limit=500)
    # 2. 获取 feed engagement 数据（缓存在内存中，每小时更新）
    engagement = await get_feed_engagement_scores(db, user_id)
    # 3. 获取用户兴趣关键词
    interests = await get_user_interests(db, user_id)
    # 4. 计算综合分数并排序
    scored = [(e, compute_score(e, engagement, interests)) for e in entries]
    scored.sort(key=lambda x: x[1], reverse=True)
    # 5. 分页返回
    return scored[offset:offset+per_page]
```

### 4.4 前端排序切换

在文章列表的 FilterBar 中添加排序选项：时间排序（默认，保持现有行为）和智能排序。后端 API 新增 `sort=smart` 参数。

### 4.5 Embedding 方案（可选增强，Phase 2）

如果需要更深层的语义相关度排序（如"与我最近阅读过的文章相似"），可以引入 embedding：

使用 sqlite-vec 扩展在 SQLite 中存储文章的 embedding 向量。每篇文章生成一个 384 维的 embedding（使用 text-embedding-3-small 或本地 all-MiniLM-L6-v2 模型）。当用户请求"相关文章"时，取最近阅读的 5 篇文章的 embedding 均值作为 query vector，用 sqlite-vec 的 KNN 搜索找到最相似的文章。

这个功能放在 Phase 2，因为 embedding 生成需要额外 API 成本或本地模型部署，且对初始版本来说混合评分排序已经足够好。


## 五、AI 过滤规则

### 5.1 设计理念

用户使用自然语言描述过滤意图，AI 判断每篇新文章是否匹配。这取代了传统的正则表达式或关键词匹配，大幅降低了规则创建门槛。

示例规则：
- "只保留关于 AI 和机器学习的深度技术文章，过滤掉产品发布和广告"
- "标记所有关于 Python 安全漏洞的文章为星标"
- "隐藏重复的新闻转载，只保留原创报道"

### 5.2 数据模型

```sql
CREATE TABLE ai_filter_rules (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL REFERENCES users(id),
    name TEXT NOT NULL,                    -- 规则名称
    description TEXT NOT NULL,             -- 自然语言描述
    action TEXT NOT NULL DEFAULT 'hide',   -- hide / star / mark_read / tag
    action_value TEXT,                     -- tag 名称等
    apply_to TEXT DEFAULT 'all',           -- all / feed:{feed_id} / group:{group_id}
    is_active BOOLEAN DEFAULT TRUE,
    priority INTEGER DEFAULT 0,           -- 优先级，高优先
    match_count INTEGER DEFAULT 0,        -- 已匹配文章数
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### 5.3 执行流程

AI 过滤在新文章入库后触发，采用批量判定模式以控制成本。核心思路是：将多条规则合并到一个 prompt 中，让 LLM 一次性判断一篇文章匹配哪些规则，而不是每条规则调用一次 API。

```
System: You are an article classification assistant. Given an article and a list of filter rules, determine which rules (if any) this article matches. Respond in JSON format.

User:
Article:
  Title: {title}
  Summary: {summary or content[:500]}

Rules:
1. [hide] "只保留AI技术深度文章，过滤产品广告"
2. [star] "关于Python安全漏洞的文章"
3. [mark_read] "重复的新闻转载"

Response format: {"matches": [{"rule_id": 1, "confidence": 0.9, "reason": "..."}]}
```

这样无论用户定义了多少条规则，每篇文章只需要一次 LLM 调用。对于每日 200 篇文章，这意味着只有 200 次调用而不是 200 x N 次。

### 5.4 批量处理优化

当新文章批量入库时（feed 抓取完成），将这些文章按 10 篇一组打包，连同所有活跃的过滤规则一起发给 LLM。prompt 会更长，但调用次数从 200 降到 20。

```python
async def apply_ai_filters_batch(db, user_id, entries: list[Entry]):
    rules = await get_active_rules(db, user_id)
    if not rules:
        return

    # 每 10 篇文章一组
    for chunk in chunked(entries, 10):
        prompt = build_filter_prompt(chunk, rules)
        result = await call_llm(settings, prompt, system=FILTER_SYSTEM_PROMPT, max_tokens=500)
        matches = parse_filter_result(result)
        await apply_filter_actions(db, user_id, matches)
```

### 5.5 Confidence 阈值

LLM 返回每个匹配的 confidence 分数。只有 confidence >= 0.7 的匹配才会执行 action。用户可以在规则设置中调整这个阈值。这避免了误判带来的用户体验问题——被错误隐藏的文章比漏掉的文章更让人恼火。

### 5.6 前端规则管理

提供一个 AI 过滤规则管理页面：规则列表展示每条规则的名称、描述、action、匹配统计。创建规则时只需输入自然语言描述和选择 action（隐藏 / 星标 / 标记已读）。提供"测试规则"功能，对最近 50 篇文章运行该规则预览匹配结果，帮助用户验证规则是否符合预期。


## 六、新增依赖

后端新增：
- `litellm` — LLM 统一调用层
- `cryptography` — API key 加密

可选（Phase 2）：
- `sqlite-vec` — SQLite 向量搜索扩展（pip install sqlite-vec）
- `sentence-transformers` — 本地 embedding 模型（如不想用 OpenAI embedding API）


## 七、实现步骤

### Phase 1：基础设施 + AI 摘要（优先级最高）

Step 1 — AI Settings 数据模型和 API。新增 `ai_settings` 表的 migration，创建 `app/models/ai_settings.py`、`app/schemas/ai_settings.py`、`app/routers/ai_settings.py`。实现 GET/PUT `/api/ai-settings` 接口，包含 API key 加密存储。

Step 2 — AI Service 核心层。创建 `app/services/ai_service.py`，封装 LiteLLM 调用逻辑，包括 retry、rate limiting、cost tracking。实现 `generate_summary(entry)` 和 `test_connection(settings)` 方法。

Step 3 — AI 摘要 API 和后台任务。新增 entries 表 `ai_summary` 和 `ai_summary_generated_at` 字段。实现 `POST /api/entries/{id}/ai-summary` 单篇生成接口。在 APScheduler 中添加批量摘要生成任务。

Step 4 — 前端 AI 设置页。新增 Settings 页面的 AI 配置 tab：provider 选择、API key 输入、model 选择、连接测试按钮。

Step 5 — 前端摘要展示。EntryCard 和阅读面板中展示 AI 摘要，添加"生成摘要"和"重新生成"按钮。

### Phase 2：智能排序 + AI 过滤规则

Step 6 — 智能排序后端。Feed 模型新增 `priority` 字段。实现 `list_entries_smart()` 排序算法。计算 feed engagement scores 的缓存服务。API 新增 `sort=smart` 参数。

Step 7 — 智能排序前端。FilterBar 添加排序切换（时间/智能）。Feed 设置中添加优先级选项。

Step 8 — AI 过滤规则后端。新增 `ai_filter_rules` 表和对应 CRUD API。实现 `apply_ai_filters_batch()` 批量过滤逻辑。集成到 feed 抓取后的处理流程。

Step 9 — AI 过滤规则前端。规则管理页面（列表、创建、编辑、删除）。规则测试功能（预览匹配结果）。文章列表中标记被规则匹配的文章（如 tag badge）。

### Phase 3（可选增强）

Step 10 — Embedding 向量搜索。集成 sqlite-vec 扩展。为文章生成 embedding 的后台任务。"相关文章"推荐功能。混合搜索（FTS5 + 向量语义搜索）。

Step 11 — AI 每日摘报。每日定时任务生成当日重要文章的汇总 digest。前端展示 AI daily brief 面板。

Step 12 — 更多 AI Actions（参考 Folo）。AI 翻译标题和正文。AI 自动打标签。AI 重写/格式化。


## 八、API 设计总览

```
# AI 设置
GET    /api/ai-settings                  — 获取 AI 配置
PUT    /api/ai-settings                  — 更新 AI 配置
POST   /api/ai-settings/test-connection  — 测试 LLM 连接

# AI 摘要
POST   /api/entries/{id}/ai-summary      — 生成单篇 AI 摘要
POST   /api/entries/ai-summary/batch     — 批量生成 AI 摘要

# AI 过滤规则
GET    /api/ai-filter-rules              — 列出所有规则
POST   /api/ai-filter-rules              — 创建规则
PUT    /api/ai-filter-rules/{id}         — 更新规则
DELETE /api/ai-filter-rules/{id}         — 删除规则
POST   /api/ai-filter-rules/{id}/test    — 测试规则（预览匹配）

# 智能排序（通过现有 entries API 扩展）
GET    /api/entries?sort=smart            — 智能排序的文章列表
```


## 九、关键设计决策说明

为什么选 LiteLLM 而不是直接调各家 SDK：LiteLLM 提供统一接口、内置 cost tracking 和 fallback，新增 provider 零代码改动。缺点是多了一层依赖，但考虑到 BYOK 需求，这是最优解。

为什么 AI 摘要存在 entries 表而不是单独的表：避免 JOIN 开销。摘要与文章是 1:1 关系，没有理由拆成独立表。Entry 模型已有 summary 字段先例。

为什么智能排序不用 embedding：冷启动问题（新用户没有阅读历史，embedding 无法计算偏好），embedding 生成有额外 API 成本，混合评分系统更透明可解释。embedding 作为 Phase 2 可选增强。

为什么 AI 过滤是批量判定而不是逐条：成本控制（200 篇文章 * 10 条规则 = 2000 次调用 vs 200 次甚至 20 次），且 LLM 在给定完整上下文时判断准确度更高。

参考了 Folo（36k stars 的开源 RSS Reader）的 AI action 系统设计，以及 SmartRSS 的 prompt workflow 方案。Folo 使用 Vercel AI SDK 处理 streaming、chat 和 tool calling，但它是 TypeScript 全栈。我们采用 Python 后端，LiteLLM 是对等的选择。
