# RSS 阅读器 Web 评测研究报告

## 研究概述

本报告基于 2025-2026 年间多篇权威评测文章和对比分析，涵盖 Zapier、VPN Tier Lists、Lighthouse、FeedSpot、IvyReader、BGR、SourceForge 等来源，系统整理了当前 RSS 阅读器生态的全貌。

---

## 一、RSS 生态演变

2013 年 Google Reader 停服是 RSS 历史的分水岭。Google Reader 以其简洁直觉的界面和强大功能积累了大量忠实用户，但 Google 认为 RSS 无法货币化，最终关闭了服务。此后社交媒体和算法推荐流逐渐取代了 RSS 在普通用户中的地位。然而到了 2025-2026 年，随着用户对算法推荐的疲倦、对隐私的重视以及信息过载的加剧，RSS 正在经历一轮复兴。越来越多的用户重新发现 RSS 的价值：无广告、无算法干预、完全由用户掌控信息来源。

值得注意的是，Google Reader 的技术遗产至今仍在发挥影响。Google Reader API 虽从未被官方文档化，但通过逆向工程的规范已被大多数现代 RSS 客户端广泛支持，成为事实上的同步标准之一。

---

## 二、主流 RSS 阅读器完整概览

### 2.1 云端托管型（Hosted SaaS）

#### Feedly
定位：面向大众和商业用户的行业标杆。

Feedly 是目前用户量最大的 RSS 阅读器，以清洁的杂志式界面和 AI 功能著称。其 AI 助手 Leo 可以根据用户设定的标准自动过滤、优先排序和摘要文章，支持识别产品发布、安全漏洞等特定内容类型。Leo 还能与 Slack、Trello、Zapier 等生产力工具集成，适合团队协作场景。

免费版限制 100 个订阅源。Pro 版 $6-8/月支持 1000 个源和搜索功能。Pro+ 版 $12/月增加 AI 摘要、内容去重、AI Feeds（定义主题扫描数百万源）、静音过滤器等高级功能。Enterprise 版 $18/月面向企业。

平台覆盖：Web、iOS、Android。

隐私方面存在争议：据评测指出，Feedly 会分析用户的阅读模式建立用户画像，隐私评分中等偏低。

#### Inoreader
定位：功能最全面的高级用户之选。

Inoreader 在核心 RSS 阅读的基础上提供了极其丰富的高级功能。免费版即支持 150 个源和搜索（Feedly 免费版不支持搜索），Pro 版支持高级过滤、自动化规则、完整文章存档、布尔逻辑搜索（支持日期范围）以及对 Reddit、Twitter、YouTube 频道、Facebook 页面、Bluesky 等非 RSS 源的订阅。2025 年新增了与 Notion 和 Obsidian 的集成。

Inoreader Intelligence（AI 功能）包含文章摘要和智能标签建议，属于 Pro 计划的一部分。

定价：免费版 150 源；Starter $5/月；Plus $7/月；Professional $10/月。

平台覆盖：Web、iOS、Android。在各类社区评测中，Inoreader 通常被推荐为面向大多数用户的首选。

#### NewsBlur
定位：开源透明、社交属性强的阅读器。

NewsBlur 由 Samuel Clay 创建，采用 freemium 模式，代码完全开源。其最具特色的功能是 Intelligence Trainer（智能训练器）：用户可以显式地对故事、作者、标签、出版商进行喜欢/不喜欢标记，系统据此学习用户偏好进行内容高亮或过滤。这种基于显式手动反馈（而非算法观察）的方式给用户更多控制感。

此外 NewsBlur 支持全文阅读、社交分享、评论功能，以及可以自部署的开源版本。

免费版限制 64 个订阅源。Premium $36/年支持 1000 个源。

平台覆盖：Web、iOS、Android。界面虽在 2022 年重新设计，但在三大主流阅读器中仍显得最为传统。

#### Feedbin
定位：注重隐私和简洁的付费精品。

Feedbin 没有免费版，以 $5/月或 $50/年的价格提供简洁优雅的阅读体验。其优势在于：可定制的主题和排版、全文抓取（对仅提供摘要的 feed 自动提取全文）、专用邮箱地址可直接订阅 Newsletter、99.9% 的高可用性，以及极少的数据收集。不参与广告合作，隐私评分较高。

平台覆盖：Web，支持多种第三方客户端通过 API 连接。

#### The Old Reader
定位：Google Reader 精神继承者。

The Old Reader 刻意保持了 Google Reader 的简洁界面风格，不追求花哨的 AI 功能，专注于 RSS 阅读的基本功能。支持 OPML 导入、文件夹管理、邮件分享、Facebook/X 分享和内部评论。

免费版支持 100 个源。Premium $3/月或 $25/年，增加全文搜索和最多 500 个订阅，1 年文章存储。局限性在于搜索功能有限，缺少过滤和自动化工具。

#### Spark News Reader
定位：隐私至上的免费阅读器。

Spark 以零知识架构（zero-knowledge）著称：无追踪像素、无指纹脚本、无分析工具，所有数据仅存储在本地。完全免费且不限制订阅源数量。支持离线阅读（文章本地下载）和干净的文章提取。在以隐私为评测维度的对比中通常名列前茅。

#### Readwise Reader
定位：融合 RSS 与 Read-it-later 的知识管理工具。

Readwise Reader 并非纯粹的 RSS 阅读器，而是将 RSS 订阅、文章保存、高亮标注、笔记导出整合到一个平台。支持 OPML 导入、与 Kindle/Goodreads/Libby/Apple Books/Medium/Twitter/Discord 等平台的高亮同步，以及向 Notion/Obsidian 导出。

$9.99/月。界面功能丰富但也因此被批评为过于复杂、视觉上有些拥挤。适合需要深度知识管理工作流的用户。

#### Folo (Follow)
定位：新一代 AI 驱动的开源 RSS 阅读器。

Folo 是 2025 年崛起的新项目，在 GitHub 上获得 36k+ star。以 AI 为核心特色，支持 AI 摘要（BYOK 自带 API Key）、AI 标签自动生成、AI 记忆功能、时间线汇总和每日 AI 摘要邮件。支持订阅列表分享和探索社区精选内容集。处理多种内容类型（文章、视频、图片、音频）。

采用 AGPL v3 开源许可。目前免费但暗示未来会推出付费层级。全新的入门引导流程被评价为流畅直觉。

---

### 2.2 自部署型（Self-Hosted）

#### FreshRSS
定位：功能最丰富、社区最活跃的自部署方案。

FreshRSS 被广泛认为是自部署 RSS 领域的标杆。支持 15+ 种语言，拥有丰富的扩展和主题生态，支持 WebSub、搜索、过滤、内置阅读器。安装方式灵活，支持裸机和 Docker 部署。默认使用 SQLite 数据库，可切换到 PostgreSQL 或 MySQL 以获得更好性能。支持多用户。

完全免费开源。适合需要高度定制化和完全数据控制的用户。

#### Miniflux
定位：极简主义、专注阅读的轻量方案。

Miniflux 以极简设计哲学著称，界面精简到只保留阅读所需的核心功能。后端仅支持 PostgreSQL，通过 Fever API 支持第三方客户端。移动端和桌面端体验一致，响应式设计。

完全免费开源（自部署），也提供 $15/年的托管版本（含 15 天试用）。适合追求极简、不需要过多功能的用户。

#### Tiny Tiny RSS (TT-RSS)
定位：历史悠久但原维护者已退出的自部署方案。

TT-RSS 曾是功能最全面的自部署 RSS 阅读器之一，拥有丰富的插件体系、主题、文章过滤/评分机制和多种分享方式。然而在 2025 年 10 月，长期维护者 Andrew Dolgov（Fox）宣布停止开发并于 11 月 1 日关闭了所有基础设施（tt-rss.org、论坛、代码仓库等）。

项目并未完全消亡：长期贡献者 supahgreg 在同日将代码 fork 到 github.com/tt-rss/tt-rss（GPLv3+），继续活跃维护。但未来发展方向存在不确定性。

---

### 2.3 原生桌面/移动客户端

#### NetNewsWire
定位：Apple 生态的免费开源标杆。

NetNewsWire 是一款免费、开源的 Mac/iOS 原生 RSS 阅读器，完全在设备本地存储数据，支持 iCloud 同步。不限制订阅源数量，无广告无追踪。支持 Safari 扩展集成和 AppleScript。被广泛认为是 Apple 平台上最好的免费 RSS 客户端，操作流畅响应迅速。

仅支持 Mac 和 iOS。

#### Reeder
定位：Apple 生态的精品付费客户端。

Reeder 是 Mac/iOS 上的高品质 RSS 客户端，以精美的设计、流畅的手势导航和优秀的排版著称。新版 Reeder 不仅是 RSS 阅读器，还整合了统一时间线，聚合 RSS、播客和社交媒体内容。

约 $10/年。提供比 NetNewsWire 更多的定制选项和更精致的视觉体验。

#### Newsboat
定位：终端用户的极客之选。

Newsboat 是一款基于文本终端的 RSS/Atom 阅读器，是已停止维护的 Newsbeuter 的活跃 fork。MIT 许可证。完全键盘驱动，默认快捷键模仿 vi。支持文章过滤、元 feed 聚合、播客、OPML 导入导出，以及与 The Old Reader、NewsBlur、FeedHQ 等服务的同步。内置 HTML 渲染器。

完全免费。仅支持 Unix-like 系统的终端环境。适合习惯命令行工作流的开发者和系统管理员。

#### Fluent Reader
定位：Windows/macOS 的免费桌面客户端。

开源免费，提供干净的界面、OPML 支持和现代化的无干扰设计。Windows 原生支持，macOS 有社区构建版本。

---

### 2.4 浏览器扩展

#### Feedbro
定位：功能最强大的浏览器内 RSS 阅读器。

Feedbro 是唯一仍在活跃维护的主要浏览器扩展型 RSS 阅读器（Smart-RSS 已于 2025 年 2 月停止维护）。支持 Chrome 和 Firefox。

核心特色是内置规则引擎（Rule Engine），可定义过滤、高亮、自动书签、标签、隐藏和正则表达式高亮规则。提供多种视图模式（全文、标题、报纸、杂志等），内置 Readability 风格的全文提取。支持 YouTube、Facebook、Twitter、Instagram、LinkedIn、Reddit 等平台的内置插件。集成 IFTTT、Discord、Slack。

完全免费。数据存储在本地浏览器中，浏览器活跃时才抓取 feed。

---

### 2.5 Read-it-Later 混合型

#### Matter
定位：以阅读体验为核心的 Read-it-later 应用。

Matter 自 2021 年上线以来以其优美的阅读体验和稳定的 iPhone/iPad 应用著称。支持 RSS 源和 Newsletter 导入，内置朗读功能（针对 iPhone 和 AirPods 优化）。

$80/年。适合追求优质阅读体验、不需要复杂功能的移动端用户。

#### Omnivore（已关闭）
Omnivore 是一款完全免费、开源的 Read-it-later 应用，曾广受好评。2024 年 10 月被 ElevenLabs 收购后宣布关闭服务，用户需在 2024 年 11 月 15 日前导出数据。团队转向开发 ElevenReader（专注 AI 语音朗读）。Omnivore 代码仍然开源可自部署，但托管服务已永久关闭。这一事件引发了社区对免费服务可持续性的广泛讨论。

---

## 三、核心功能对比

### 3.1 定价对比表

| 阅读器 | 免费版限制 | 入门付费 | 最高付费 | 免费搜索 |
|---------|----------|---------|---------|---------|
| Feedly | 100 源 | $6/月 (Pro) | $18/月 (Enterprise) | 否 |
| Inoreader | 150 源 | $5/月 (Starter) | $10/月 (Professional) | 是 |
| NewsBlur | 64 源 | $36/年 | $36/年 | 有限 |
| Feedbin | 无免费版 | $5/月 | $5/月 | 是 |
| The Old Reader | 100 源 | $3/月 | $3/月 | 付费 |
| Readwise Reader | 无免费版 | $9.99/月 | $9.99/月 | 是 |
| Spark | 无限制（免费） | - | - | 是 |
| Folo | 无限制（免费） | - | 未来计划 | 是 |
| NetNewsWire | 无限制（免费） | - | - | 是 |
| Reeder | - | ~$10/年 | ~$10/年 | 是 |
| FreshRSS | 无限制（自部署） | - | - | 是 |
| Miniflux | 无限制（自部署） | $15/年(托管) | $15/年(托管) | 是 |
| Feedbro | 无限制（免费） | - | - | 是 |
| Newsboat | 无限制（免费） | - | - | 是 |

### 3.2 AI 功能对比

Feedly 的 AI 功能最为成熟。Leo AI 助手可以过滤和优先排序内容、生成 2-3 句摘要、跨源去重、通过 AI Feeds 持续扫描数百万源发现特定主题内容，以及通过静音过滤器隐藏匹配特定关键词的内容。但这些高级 AI 功能集中在 Pro+ ($12/月) 及以上计划。

Inoreader Intelligence 提供文章摘要和智能标签建议，属于 Pro 计划。功能不如 Feedly 的 Leo 全面，但在自动化规则方面更加灵活强大。

NewsBlur 的 Intelligence Trainer 基于用户显式训练反馈学习偏好，更像传统机器学习而非生成式 AI，但在长期使用中效果很好。

Folo 是最新的 AI 原生 RSS 阅读器，支持 BYOK（自带 API Key）、AI 摘要、AI 标签、AI 记忆，且是开源的。代表了 RSS 阅读器 AI 功能的未来方向。

大多数 AI 功能都集中在付费层级，免费用户能获得的 AI 能力非常有限。

### 3.3 平台覆盖对比

| 阅读器 | Web | iOS | Android | Mac | Windows | Linux | 终端 |
|---------|-----|-----|---------|-----|---------|-------|------|
| Feedly | Yes | Yes | Yes | - | - | - | - |
| Inoreader | Yes | Yes | Yes | - | - | - | - |
| NewsBlur | Yes | Yes | Yes | - | - | - | - |
| Feedbin | Yes | 三方 | 三方 | - | - | - | - |
| The Old Reader | Yes | - | - | - | - | - | - |
| Readwise Reader | Yes | Yes | Yes | - | - | - | - |
| NetNewsWire | - | Yes | - | Yes | - | - | - |
| Reeder | - | Yes | - | Yes | - | - | - |
| FreshRSS | Yes | 三方 | 三方 | - | - | - | - |
| Miniflux | Yes | 三方 | 三方 | - | - | - | - |
| Feedbro | 扩展 | - | - | 扩展 | 扩展 | 扩展 | - |
| Newsboat | - | - | - | Yes | - | Yes | Yes |
| Fluent Reader | - | - | - | Yes | Yes | - | - |
| Folo | Yes | Yes | - | Yes | Yes | Yes | - |

### 3.4 独特卖点汇总

Feedly 的独特优势在于 Leo AI 助手和企业级团队协作功能。Inoreader 在自动化规则和非 RSS 源（社交媒体、Newsletter）集成方面无出其右。NewsBlur 的开源代码和基于显式反馈的 Intelligence Trainer 给用户最大的控制感和透明度。Feedbin 以隐私、可靠性和优雅的 Newsletter 集成取胜。

自部署方面，FreshRSS 的扩展生态和多语言支持使其成为最通用的选择，而 Miniflux 的极简哲学吸引着不想被功能淹没的用户。

原生客户端中，NetNewsWire 以免费开源和原生 Apple 体验立足，Reeder 则以设计品质和统一时间线的创新理念见长。

Folo 作为新一代选手，以 AI 原生和开源的组合切入市场，GitHub 上的高星数表明社区对这类产品有强烈需求。

---

## 四、选择建议

对于初入 RSS 世界的新用户，Feedly 的简洁界面和渐进式功能是最友好的起点。需要更多功能但不想付费的用户可以选择 Inoreader（150 源免费且支持搜索）。

对于高级用户和信息工作者，Inoreader 的自动化规则、跨源搜索和永久存档是最全面的工具箱。Feedly Pro+ 适合需要 AI 辅助信息筛选的场景。

隐私优先的用户应该关注 Spark（零追踪、完全免费）或自部署方案（FreshRSS/Miniflux）。

Apple 生态的用户在 NetNewsWire（免费）和 Reeder（付费）之间选择即可。开发者和终端用户 Newsboat 是不二之选。

想要结合 RSS 和知识管理工作流的用户，Readwise Reader 提供了最完整的高亮、标注和导出体系。

关注开源和 AI 趋势的用户可以尝试 Folo，它代表了 RSS 阅读器的下一代形态。

---

## 五、关键趋势观察

2025-2026 年 RSS 阅读器市场呈现几个明显趋势。

第一，AI 功能的全面渗透。从 Feedly 的 Leo 到 Folo 的 BYOK AI，几乎所有主流阅读器都在集成 AI 摘要、智能过滤和内容推荐。但大多数 AI 功能被锁定在付费层级，成为阅读器变现的核心手段。

第二，RSS 与其他内容形式的融合。现代 RSS 阅读器不再局限于传统 RSS/Atom feed，而是向 Newsletter（Feedbin、Inoreader）、社交媒体（Inoreader 支持 Reddit/Twitter/Bluesky）、播客（Reeder、Vivaldi）、YouTube（Feedbro、Vivaldi）等方向扩展。Readwise Reader 进一步模糊了 RSS 阅读器和 Read-it-later 应用的边界。

第三，隐私成为差异化维度。在 Feedly 和 Inoreader 被批评收集过多用户数据的背景下，Spark、Feedbin、自部署方案等以隐私为卖点的产品获得了越来越多的关注。

第四，开源和自部署的持续活跃。尽管 TT-RSS 原维护者退出，但社区 fork 迅速接手。FreshRSS、Miniflux、Folo 等开源项目依然活跃，反映了用户对数据主权的持续重视。Omnivore 的关闭事件也强化了社区对自部署方案的偏好。

第五，免费服务的可持续性问题。Omnivore 被收购后关闭、TT-RSS 原维护者退出，提醒用户免费服务并非永恒。选择有可持续商业模式的付费服务或自部署方案可能是更稳妥的长期选择。

---

## 来源

- [Zapier: The 3 best RSS reader apps in 2026](https://zapier.com/blog/best-rss-feed-reader-apps/)
- [VPN Tier Lists: Best RSS Feed Readers 2026 Complete Comparison Guide](https://vpntierlists.com/blog/best-rss-feed-readers-2025-complete-comparison-guide)
- [Lighthouse: A deep dive into the RSS feed reader landscape](https://lighthouseapp.io/blog/feed-reader-deep-dive)
- [IvyReader: Best RSS Readers in 2025](https://ivyreader.com/articles/best-rss-reader)
- [Miniloop: Best RSS Feed Readers in 2026](https://www.miniloop.ai/blog/best-rss-feed-readers-2026)
- [FeedSpot: 5 Best RSS Readers On The Web in 2026](https://www.feedspot.com/blog/best-rss-reader/)
- [SourceForge: Best RSS Readers of 2026](https://sourceforge.net/software/rss-readers/)
- [VPN Tier Lists: RSS Reader Showdown Feedly vs Inoreader vs NewsBlur vs Spark](https://vpntierlists.com/blog/rss-reader-showdown-feedly-vs-inoreader-vs-newsblur-vs-spark)
- [Inoreader: Inoreader vs Feedly Feature Comparison](https://www.inoreader.com/alternative-to-feedly)
- [Slant: Feedly vs Inoreader](https://www.slant.co/versus/1455/1461/~feedly_vs_inoreader)
- [Slant: Tiny Tiny RSS vs Miniflux](https://www.slant.co/versus/1452/18504/~tiny-tiny-rss_vs_miniflux)
- [GitHub: Folo (RSSNext)](https://github.com/RSSNext/Folo)
- [LinuxIAC: TT-RSS Shuts Down but the Project Lives On Under a New Fork](https://linuxiac.com/tt-rss-shuts-down-but-the-project-lives-on-under-a-new-fork/)
- [Omnivore: Details on Omnivore shutting down](https://blog.omnivore.app/p/details-on-omnivore-shutting-down)
- [Arekore: Is RSS Really Dead?](https://arekore.app/en/articles/rss-readers)
