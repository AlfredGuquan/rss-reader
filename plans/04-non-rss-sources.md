# 非 RSS 源订阅实现计划

## 现有架构分析

项目已有 `feed_type` 字段（Feed 模型第 30 行），当前值为 `"rss"` 和 `"newsletter"`。Newsletter 的集成模式提供了一个好的参考：每个 sender 创建一个 Feed 记录，entries 按正常流程存入 Entry 表，`feed_type` 用于区分抓取逻辑。抓取服务 `fetch_service.py` 目前只处理标准 RSS/Atom feed，通过 `feedparser` 解析。

新的非 RSS 源可以复用这套 Feed + Entry 模型，通过 `feed_type` 字段路由到不同的抓取逻辑。

## 各平台接入方式对比

### Reddit

Reddit 原生支持 RSS，直接在 subreddit URL 后追加 `.rss` 即可获取 Atom feed。例如 `https://www.reddit.com/r/python/.rss` 或 `https://www.reddit.com/r/python/top/.rss?t=day`。多个 subreddit 可合并为一个 feed（`/r/a+b+c.rss`），用户页面也支持（`/user/username.rss`）。

主要限制在于 rate limiting：Reddit 根据 User-Agent 限流，默认 UA（如 Python/urllib）会被严格限制。需要设置格式化的 UA（`<platform>:<app_id>:<version> (by /u/<username>)`）。OAuth 认证后限额为 60 请求/分钟。

推荐方案：直接通过现有 `fetch_service` 抓取，只需在用户输入 Reddit URL 时自动转换为 `.rss` 后缀，并设置符合 Reddit 要求的 User-Agent。不需要 RSSHub 中间层，因为 Reddit 原生 RSS 足够好用。feed_type 可设为 `"reddit"` 以便 UI 显示特定图标，但技术上走标准 RSS 解析路径即可。

### YouTube

YouTube 提供原生 RSS feed，格式为 `https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}`。feed 使用 Atom 格式，包含 `yt:videoId`、`media:group`（含缩略图和描述）等元素，feedparser 可以正常解析。

主要限制：每个 feed 最多返回最近 15 条视频，且 feed 中不包含视频时长信息（duration），这对过滤 Shorts 构成挑战。

推荐方案：订阅本身走原生 RSS，用 feedparser 解析即可。对于 Shorts 过滤，需要额外调用 YouTube Data API v3 获取 `contentDetails.duration`（ISO 8601 格式如 `PT15M51S`），然后根据时长判断是否为 Shorts（3 分钟以下）。YouTube 频道 URL 到 channel_id 的转换需要在添加 feed 时处理（从频道页面 HTML 中提取或通过 API 查询）。

### Twitter/X

Twitter 是所有平台中最难的。自 2023 年 API 付费化和 Nitter 公共实例关闭后，没有免费且稳定的直接获取方式。

可用方案对比：

方案一是自部署 RSSHub，通过 TWITTER_AUTH_TOKEN 环境变量配置已登录账号的 cookie，RSSHub 使用 Twitter Web API 获取推文并转为 RSS。路由格式为 `/twitter/user/:username`。优点是成熟方案、社区活跃，缺点是需要维护一个 RSSHub 实例、Twitter cookie 可能过期需要定期更换。

方案二是自部署 Nitter，开源项目仍可自建，提供 RSS 端点 `/username/rss`。但项目维护不活跃，Twitter 反爬措施持续加强，稳定性堪忧。

方案三是 RSS Bridge（PHP），支持 200+ 平台包括 Twitter，但路由不如 RSSHub 丰富。

推荐方案：采用 RSSHub 作为 Twitter RSS 的中间代理层。用户需自部署 RSSHub 实例并配置 Twitter 认证信息。项目后端通过配置 RSSHub 实例地址来订阅 Twitter 用户。如果用户没有 RSSHub 实例，Twitter 订阅功能不可用，但其他平台不受影响。

## 推荐架构：混合方案

采用混合架构而非全面依赖 RSSHub。原因是 Reddit 和 YouTube 的原生 RSS 已经足够好，引入 RSSHub 作为中间层反而增加故障点和部署复杂度。

总体思路为三个层次：第一层是原生 RSS，用于 Reddit 和 YouTube 以及所有标准 RSS/Atom 源；第二层是 RSSHub 代理，仅用于 Twitter/X 等没有原生 RSS 的平台；第三层是后处理增强，比如 YouTube 的 Shorts 过滤通过 YouTube Data API 实现。

```
用户输入 URL
    |
    v
URL 识别器 (platform_detector)
    |
    +-- reddit.com/r/xxx  --> 转换为 .rss URL --> feedparser 标准解析
    +-- youtube.com/@xxx  --> 提取 channel_id --> 构建 XML feed URL --> feedparser 标准解析
    +-- twitter.com/xxx   --> 构建 RSSHub URL --> feedparser 标准解析
    +-- 其他              --> 走现有 RSS/Atom 发现 + 解析流程
```

## YouTube Shorts 过滤方案

YouTube RSS feed 不含视频时长信息，需要额外方案。

方案一（推荐）：在 Entry 模型增加 `extra_metadata` JSON 字段，抓取 YouTube feed 条目后，用 YouTube Data API v3 批量查询 `contentDetails.duration`。每次最多 50 个 video ID 一次查询，API 免费额度为 10,000 units/天，videos.list 每次消耗 1 unit，足够日常使用。解析 ISO 8601 duration 判断：小于 180 秒标记为 Shorts。在 Feed 设置中提供过滤选项："显示全部"、"仅长视频（> 3min）"、"仅 Shorts"。

方案二（备选）：不调 API，直接用 URL 特征判断。YouTube Shorts 的 URL 格式通常为 `youtube.com/shorts/VIDEO_ID`，但 RSS feed 中的 link 统一为 `youtube.com/watch?v=VIDEO_ID`，无法区分。因此 URL 特征方案不可靠。

方案三（轻量备选）：通过 yt-dlp 命令获取视频元数据。可以批量提取 duration，但需要安装额外系统依赖。

推荐方案一，通过 YouTube Data API 获取时长最可靠。需要用户配置 Google API Key（免费），与已有的 Gmail OAuth 体系一致。

## 数据模型变更

### Feed 模型扩展

```python
# Feed 模型新增字段
source_platform: Mapped[Optional[str]] = mapped_column(String, nullable=True)
# 值: "reddit", "youtube", "twitter", "generic"
# 用于 UI 展示平台图标和特定操作

source_identifier: Mapped[Optional[str]] = mapped_column(String, nullable=True)
# 平台特定标识: subreddit 名、channel_id、twitter username 等

filter_rules: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
# JSON: {"min_duration": 180, "exclude_shorts": true, "sort": "top", "time_filter": "day"}
```

`feed_type` 字段保持不变，仍然表示抓取方式（"rss" / "newsletter"）。新增 `source_platform` 表示内容来源平台，两个维度独立：一个 YouTube feed 的 feed_type 是 "rss"（通过 RSS 抓取）但 source_platform 是 "youtube"。

### Entry 模型扩展

```python
# Entry 模型新增字段
extra_metadata: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
# JSON: YouTube 视频可存 {"duration": 325, "is_short": false, "thumbnail": "..."}
# Reddit 帖子可存 {"score": 1234, "num_comments": 56, "subreddit": "python"}
```

### 配置扩展

在 `app/config.py` 的 Settings 中增加：

```python
rsshub_base_url: str = ""  # 自部署 RSSHub 实例地址，空则不启用 Twitter 订阅
youtube_api_key: str = ""  # YouTube Data API key，空则不启用 Shorts 过滤
reddit_user_agent: str = "RSS-Reader:v1.0 (by /u/rss-reader-app)"
```

## 前端 UI 设计

### 添加非 RSS 源的流程

当前 "Add Feed" 对话框只有一个 URL 输入框。改进方案为保留单一 URL 输入框，但增加平台自动识别。用户粘贴如下 URL 时自动识别：

对于 `https://www.reddit.com/r/python`，识别为 Reddit subreddit，显示 Reddit 图标和选项面板（排序方式: hot/new/top、时间范围: day/week/month/all、结果数量限制）。

对于 `https://www.youtube.com/@channel`，识别为 YouTube 频道，显示 YouTube 图标和选项面板（过滤 Shorts: 是/否、最小时长过滤）。

对于 `https://twitter.com/username` 或 `https://x.com/username`，识别为 Twitter，如果已配置 RSSHub 则显示 Twitter 图标，如果未配置则显示提示信息引导用户配置 RSSHub 地址。

对于其他 URL，走现有 RSS 发现流程。

### Feed 列表展示

每个 feed 项根据 `source_platform` 显示对应的平台图标（Reddit 外星人、YouTube 播放按钮、Twitter 小鸟），鼠标悬停时显示平台特定信息。YouTube feed 可在设置中切换 Shorts 过滤选项。

### 设置页面

新增 "非 RSS 源配置" 区域，包含 RSSHub 实例地址输入框（带连通性测试按钮）和 YouTube API Key 输入框。

## 实现步骤

### 第一阶段：Reddit 支持（最简单，原生 RSS）

后端工作：创建 `app/services/platform_detector.py` 实现 URL 识别逻辑，将 Reddit URL 转换为 `.rss` 格式。在 `feed_service.py` 的 `create_feed` 中集成平台检测。在 `fetch_service.py` 中针对 Reddit feed 设置合规 User-Agent。数据库 migration 增加 `source_platform`、`source_identifier`、`filter_rules` 字段。

前端工作：在 AddFeedDialog 中增加 URL 平台识别和对应选项面板。Feed 列表增加平台图标显示。

### 第二阶段：YouTube 支持（原生 RSS + API 增强）

后端工作：在 `platform_detector.py` 增加 YouTube URL 识别和 channel_id 提取逻辑。创建 `app/services/youtube_service.py` 封装 channel_id 解析（从频道页 HTML 提取或通过 API 查询）和 Shorts 过滤（调 YouTube Data API 获取 duration）。数据库 migration 增加 Entry 的 `extra_metadata` 字段。在 `fetch_service.py` 中，YouTube feed 抓取后触发 duration 元数据补充。

前端工作：YouTube feed 设置面板增加 Shorts 过滤开关。Entry 列表中 YouTube 条目显示视频时长。如果 `exclude_shorts` 启用，前端过滤掉 `is_short=true` 的条目（或后端查询时直接排除）。

### 第三阶段：Twitter/X 支持（需 RSSHub）

后端工作：在 Settings 和前端设置页增加 RSSHub 实例地址配置。`platform_detector.py` 增加 Twitter URL 识别，将 `twitter.com/username` 转为 `{rsshub_base_url}/twitter/user/username`。`create_feed` 中校验 RSSHub 可达性。

前端工作：设置页增加 RSSHub 配置区。AddFeedDialog 中 Twitter URL 检测到时，若未配置 RSSHub 则显示配置引导提示。

## 需要的新依赖

后端仅在启用 YouTube Shorts 过滤功能时需要 `google-api-python-client`（与已有的 Gmail OAuth 集成共享，pyproject.toml 中已有）。核心功能（Reddit、YouTube 基本订阅、Twitter via RSSHub）不需要任何新依赖，全部通过现有的 httpx + feedparser 处理。

前端不需要新增依赖。

## 风险和注意事项

Reddit rate limiting 是主要风险，需要严格控制抓取频率。建议 Reddit feed 默认 fetch_interval 设为 60 分钟（比普通 RSS 的 30 分钟更长）。

Twitter via RSSHub 的可靠性取决于 RSSHub 实例健康状况和 Twitter cookie 有效期。需要在 feed status 中清晰展示错误信息，帮助用户排查问题。

YouTube Data API 有每日免费额度（10,000 units），正常使用不会触及上限，但如果订阅了大量频道则需要注意。可以在后台任务中批量处理，每次 fetch 后统一查询该批次所有新视频的 duration。

YouTube channel_id 的获取需要处理多种 URL 格式：`/@handle`、`/channel/UC...`、`/c/customname`、`/user/username`。前两种可以直接从 URL 解析，后两种需要请求页面提取。
