# RSS Reader — 产品规格说明

## 概述

一个面向开发者的个人 RSS 阅读器 Web 应用，解决信息来源分散、内容质量参差不齐的问题。采用 Python 后端 + React 前端的前后端分离架构，MVP 聚焦标准 RSS 阅读体验，后期逐步引入 AI 深度参与内容筛选和分类。

项目同时作为学习项目，覆盖前后端分离架构、定时任务、网页解析、数据建模等完整技术链路。

### 目标用户

开发者本人（单用户使用，架构预留多用户扩展）。

### 关注领域

技术博客、开源项目、Hacker News 类资讯、AI 动态、内容创作与营销、产品相关。

## 技术架构

### 后端

- 框架: FastAPI (Python)
- 数据库: SQLite（MVP），后期可迁移至 PostgreSQL
- 定时任务: APScheduler 或 Celery Beat（管理 feed 定时拉取）
- RSS 解析: feedparser
- 全文抓取: trafilatura（主力）+ newspaper3k（备选降级）
- OPML 解析: 标准库 xml.etree.ElementTree
- ORM: SQLAlchemy + Alembic（数据库迁移）

### 前端

- 框架: React + TypeScript
- 构建工具: Vite
- UI: shadcn/ui + Tailwind CSS
- 状态管理: TanStack Query（服务端状态）+ zustand（客户端状态）
- 路由: React Router
- 包管理: bun

### 部署

- MVP: Docker Compose 本地部署（后端 + 前端 + SQLite 文件挂载）
- 后期: 前端部署 Vercel，后端部署 Fly.io/Railway，数据库迁移至 Turso 或 PostgreSQL

## 数据模型

### users 表

```
id: UUID (PK)
username: string (unique)
email: string (unique, nullable)
created_at: datetime
updated_at: datetime
```

MVP 阶段预置一个默认用户，不实现注册/登录 UI，但所有业务数据通过 user_id 关联，为后期多用户做准备。

### feeds 表

```
id: UUID (PK)
user_id: UUID (FK -> users)
url: string (feed URL)
title: string
site_url: string (网站首页 URL)
description: text (nullable)
favicon_url: string (nullable)
group_id: UUID (FK -> groups, nullable)
fetch_interval_minutes: int (default: 30)
last_fetched_at: datetime (nullable)
last_error: text (nullable)
error_count: int (default: 0)
status: enum (active, error, paused)
created_at: datetime
updated_at: datetime
```

### groups 表

```
id: UUID (PK)
user_id: UUID (FK -> users)
name: string
sort_order: int
created_at: datetime
```

### entries 表

```
id: UUID (PK)
feed_id: UUID (FK -> feeds)
guid: string (RSS item 的唯一标识)
title: string
url: string (原文链接)
author: string (nullable)
summary: text (RSS 自带的摘要)
content: text (全文抓取的内容，nullable)
content_fetched: boolean (default: false)
published_at: datetime
created_at: datetime
```

唯一约束: (feed_id, guid)，防止同一 feed 的文章重复入库。

### user_entry_states 表

```
id: UUID (PK)
user_id: UUID (FK -> users)
entry_id: UUID (FK -> entries)
is_read: boolean (default: false)
is_starred: boolean (default: false)
read_at: datetime (nullable)
starred_at: datetime (nullable)
```

将用户状态与文章内容分离，支持多用户场景下每人独立的已读/收藏状态。

## 核心功能（MVP）

### Feed 管理

添加 feed：输入 RSS URL，后端自动解析获取 feed 标题、描述、favicon。支持 RSS 2.0、Atom 两种格式。如果输入的是网站 URL 而非 feed URL，尝试自动发现页面中的 RSS link。

删除 feed：删除 feed 时同时删除其所有 entries 和关联的 user_entry_states。

编辑 feed：可修改 feed 的自定义标题和所属分组。

分组管理：创建、重命名、删除分组。支持拖拽调整分组排序。feed 可以不属于任何分组（显示在"未分组"区域）。

### OPML 导入

支持上传 .opml 文件，解析其中的 feed URL 和分组结构，批量创建 feeds 和 groups。导入时如果 feed URL 已存在则跳过。导入完成后显示成功/跳过/失败的统计。

### 文章拉取

定时后台拉取：默认每 30 分钟拉取一次所有 active 状态的 feeds。使用 feedparser 解析 feed 内容，根据 guid 去重，新文章存入 entries 表。

拉取时遵循 HTTP 缓存协议：使用 ETag 和 Last-Modified 头，避免无变化时重复下载和解析。

### 全文抓取

对于 RSS 只提供摘要的 feed，后台异步抓取原文全文。使用 trafilatura 提取正文内容，去除导航、广告等干扰元素。抓取成功后将 content 字段更新，content_fetched 标记为 true。

抓取失败（如反爬、付费墙）时不重试，保留 RSS 自带的 summary 作为降级内容。

### 异常处理

feed 拉取失败时静默重试，最多 3 次（指数退避）。连续失败超过 3 次后将 feed status 标记为 error，UI 上在该 feed 旁显示警告图标。用户可以手动重试或暂停 feed。error_count 在下次成功拉取时重置为 0。

### 阅读体验

三栏经典布局：左侧边栏显示分组和 feed 列表（带未读数），中间栏显示文章列表（标题、来源、时间、摘要前两行），右侧栏显示文章正文。

文章列表默认按发布时间倒序。支持筛选：全部 / 未读 / 已收藏。

点击文章自动标记为已读。收藏功能：点击星标收藏文章。

右侧阅读窗格显示优先级：全文抓取内容 > RSS 自带 content > RSS summary。底部始终显示"阅读原文"链接跳转到源网站。

文章正文渲染：安全地渲染 HTML 内容（sanitize 防 XSS），支持代码高亮（技术博客场景），图片懒加载。

### 键盘快捷键

j/k：上一篇/下一篇文章。s：收藏/取消收藏。m：标记已读/未读。v：在新标签页打开原文。r：刷新当前 feed。

## UI/UX 设计

### 布局规格

三栏布局比例约 1:1.5:2.5（可拖拽调整宽度）。左侧边栏最小宽度 200px，可折叠。中间文章列表最小宽度 300px。右侧阅读窗格自适应剩余宽度。

### 主题

支持 light/dark 两种主题，跟随系统设置，也可手动切换。默认 light 主题。

### 空状态

首次使用（无 feed）：引导用户添加第一个 feed 或导入 OPML。feed 无文章：显示"暂无文章"提示。全部已读：显示"全部已读"的轻松状态。

### 加载状态

文章列表切换时显示骨架屏。全文抓取中显示加载指示器，同时展示 RSS 自带摘要。feed 拉取中在对应 feed 旁显示旋转图标。

### 响应式

MVP 只需要适配桌面端（>1024px）。后期再考虑平板和移动端适配。

## API 设计

RESTful API，所有请求带 Content-Type: application/json。

### Feed 相关

```
GET    /api/feeds                    # 获取所有 feeds（含分组信息和未读数）
POST   /api/feeds                    # 添加 feed { url: string, group_id?: string }
PUT    /api/feeds/:id                # 更新 feed { title?: string, group_id?: string }
DELETE /api/feeds/:id                # 删除 feed
POST   /api/feeds/:id/refresh       # 手动刷新单个 feed
POST   /api/feeds/import-opml       # 导入 OPML 文件（multipart/form-data）
GET    /api/feeds/:id/discover       # 自动发现网站的 RSS feed URL
```

### 分组相关

```
GET    /api/groups                   # 获取所有分组
POST   /api/groups                   # 创建分组 { name: string }
PUT    /api/groups/:id               # 更新分组 { name?: string, sort_order?: int }
DELETE /api/groups/:id               # 删除分组（feeds 移至未分组）
```

### 文章相关

```
GET    /api/entries                  # 获取文章列表（支持分页、筛选）
       ?feed_id=xxx                  # 按 feed 筛选
       ?group_id=xxx                 # 按分组筛选
       ?status=unread|starred|all    # 按状态筛选
       ?page=1&per_page=50          # 分页
GET    /api/entries/:id              # 获取单篇文章详情（含全文）
PUT    /api/entries/:id/read         # 标记已读
PUT    /api/entries/:id/unread       # 标记未读
PUT    /api/entries/:id/star         # 收藏
PUT    /api/entries/:id/unstar       # 取消收藏
POST   /api/entries/mark-all-read    # 全部标记已读 { feed_id?: string, group_id?: string }
```

## 约束与非功能需求

### 性能

文章列表加载时间 < 200ms（本地部署下）。feed 拉取不阻塞用户操作（后台异步处理）。文章列表支持虚拟滚动（当 entries 超过 100 条时）。

### 安全

HTML 内容渲染前必须 sanitize（使用 DOMPurify），防止 XSS。后期上云时需增加认证中间件。全文抓取请求需设置合理的 User-Agent 和请求频率限制，避免被目标网站封禁。

### 可扩展性

数据模型支持多用户。定时任务框架支持后期增加 AI 处理管道（如文章入库后触发 AI 分类/评分）。前端组件化设计，方便后期切换布局模式或增加新视图。

## 后期迭代路线（不在 MVP 范围内）

### Phase 2: AI 深度集成

LLM 自动摘要：新文章入库后生成中文摘要。智能分类：根据文章内容自动打标签、分配分组。质量评分：基于内容深度、新颖性、与用户兴趣的匹配度进行 1-5 分评分。优先级排序：每天生成"今日必读"摘要，由 AI 从全天文章中筛选 top 10。

### Phase 3: 多源聚合

Newsletter 邮件解析：通过 IMAP 连接或 RSS-to-Email 转换服务聚合 Newsletter 内容。Twitter/X 集成：将关注列表的推文转化为 feed。

### Phase 4: 云部署与多端

用户认证（OAuth/密码登录）。PWA 支持移动端访问。OPML 导出。阅读进度跨设备同步。

## 决策记录

### DR-001: 产品形态选择 Web 应用
- 背景: 需要在 Web、桌面客户端、CLI、移动端中选择产品形态
- 选择: Web 应用（前后端分离）
- 理由: 学习项目需要覆盖完整技术链路，Web 开发生态最成熟，前后端分离架构学习价值高，部署后多设备可用
- 备选: CLI 工具（太轻量，学习面窄）、桌面客户端（Electron 过重）、移动端（开发周期长）

### DR-002: 技术栈选择 Python + React
- 背景: 需要确定前后端技术栈
- 选择: FastAPI (Python) + React + TypeScript
- 理由: Python 后端在后期接入 AI 功能时生态最自然（LLM SDK、数据处理库），React 社区资源丰富，TypeScript 提供类型安全
- 备选: Next.js 全栈（AI 接入不如 Python 方便）、Python 全栈 HTMX（交互体验有天花板）

### DR-003: 三栏经典布局
- 背景: 从四种布局方案中选择：三栏经典、卡片流、杂志风格、极简列表
- 选择: 三栏经典布局（类 Feedly/Reeder）
- 理由: 信息层级最清晰，适合重度 RSS 用户的高效阅读场景，是 RSS 阅读器的成熟范式
- 备选: 极简列表（信息密度高但视觉层次弱）、卡片流（浏览效率低）

### DR-004: MVP 先用 SQLite，预留迁移路径
- 背景: 需要选择数据存储方案
- 选择: SQLite + SQLAlchemy ORM
- 理由: 零配置、本地部署完美适配、单用户性能绰绰有余。使用 ORM 抽象数据库层，后期迁移到 PostgreSQL 只需改连接字符串
- 备选: PostgreSQL（MVP 阶段过重）

### DR-005: 数据模型预留多用户
- 背景: MVP 单用户使用，但需要考虑未来扩展
- 选择: 所有业务表关联 user_id，用户状态（已读/收藏）与文章内容分离
- 理由: 数据模型层面的扩展成本极低（只是多一个字段），但如果 MVP 不做，后期改造成本很高
- 备选: 无 user 概念的单用户设计（后期改造需要重构全部查询）

### DR-006: MVP 包含全文抓取
- 背景: 很多 RSS feed 只提供摘要，需要决定是否在 MVP 就做全文抓取
- 选择: MVP 就做，使用 trafilatura 库
- 理由: 全文抓取对阅读体验的提升是决定性的，没有全文的 RSS 阅读器体验大打折扣。trafilatura 库成熟度高，开发成本可控
- 备选: 仅用 RSS 自带内容 + "阅读原文"链接（体验差）

### DR-007: Newsletter 聚合延后
- 背景: 用户有多源聚合需求（RSS + Newsletter + Twitter）
- 选择: MVP 只做标准 RSS，Newsletter 和 Twitter 聚合作为后期迭代
- 理由: 邮件解析技术复杂度高（IMAP 连接管理、HTML 邮件解析、隐私处理），会显著拖慢 MVP 进度。先把 RSS 基础做扎实
- 备选: MVP 就做 IMAP 连接（风险太高）

### DR-008: 定时后台拉取
- 背景: feed 更新拉取策略有多种方案
- 选择: 后台定时拉取（默认 30 分钟间隔）
- 理由: 用户打开即可看到最新内容，体验最好。支持 HTTP 缓存头（ETag/Last-Modified）避免无效请求
- 备选: 打开时拉取（首次加载慢）

### DR-009: UI 框架选择 shadcn/ui + Tailwind
- 背景: 需要选择 React UI 组件库
- 选择: shadcn/ui + Tailwind CSS
- 理由: 组件代码直接复制到项目中可完全定制，不依赖 npm 包版本，三栏布局和列表组件支持好，学习价值高，社区活跃
- 备选: Ant Design（风格固定难定制）、纯 Tailwind 手写（开发慢）

### DR-010: 异常处理策略
- 背景: RSS feed 拉取会遇到各种异常（网络超时、格式错误、服务不可用）
- 选择: 静默重试 + 状态标记
- 理由: 不打断用户阅读流，通过 UI 上的视觉标记让用户感知异常但不被强制处理。连续 3 次失败标记为 error 状态，防止无限重试浪费资源
- 备选: 积极通知（对用户干扰大）
