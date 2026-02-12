# Session State: 2026-02-11T10:45

## Active Task
批量研究市面 RSS 阅读器的共性/优劣，基于研究结果为项目 7 个待解决问题产出技术实现计划

## Current Phase
Plan: `plans/01~06-*.md` (6 份独立计划)
Phase: 2 of 3 (研究完成、计划完成、实施未开始)
Status: Awaiting Implementation

## Completed This Session

### Round 1: 市场调研（Agent Team: rss-reader-research）
- [x] Reddit 研究员：搜索 r/rss, r/selfhosted, r/apple 等社区 50+ 帖子 500+ 评论，产出 `research-reddit.md`
- [x] Web 研究员：搜索 Zapier, VPN Tier Lists, Lighthouse 等 15+ 来源的评测文章，产出 `research-web.md`
- [x] HN 研究员：搜索 Hacker News 数十个热门帖按 points 排序分析，产出 `research-hn.md`
- [x] 综合分析四个维度：用户评价、RSS 解决的问题、功能-问题映射、功能缺失时的体验

### Round 2: 技术方案研究（Agent Team: rss-feature-research）
- [x] 全文抓取增强 → `plans/01-fulltext-enhancement.md`
- [x] OPML 导入导出 → `plans/02-opml-import-export.md`
- [x] AI 摘要 + 智能排序 → `plans/03-ai-summary-and-sorting.md`
- [x] 非 RSS 源订阅 → `plans/04-non-rss-sources.md`
- [x] 话题聚类与去重 → `plans/05-topic-clustering.md`
- [x] 键盘快捷键 → `plans/06-keyboard-shortcuts.md`
- [ ] **Phase 3: 组建开发团队实施** ← Next

## Key Context

### 项目结构
- Backend: `/Users/alfred.gu/Desktop/1-Inbox/RSS 阅读器/backend/` — FastAPI + SQLAlchemy async + SQLite + uv
- Frontend: `/Users/alfred.gu/Desktop/1-Inbox/RSS 阅读器/frontend/` — React + bun + shadcn/ui + Tailwind v4
- Glob tool 不支持中文路径，用 Bash ls 或 Read 配完整路径

### 已有实现（git log 确认）
- full-text fetch（trafilatura，基础版）
- FTS5 全文搜索
- feed auto-discovery
- newsletter IMAP（Gmail OAuth）
- group drag-and-drop sorting
- 基础键盘快捷键（j/k/s/m/v/r，原生 keydown）
- 基础 OPML 导入（opml_service.py + ImportOpmlDialog）

### 研究报告（市场调研原始数据）
- `research-reddit.md`: Reddit 用户对 15+ 阅读器的评价、痛点、切换路径
- `research-web.md`: 专业评测综合，含定价/AI/平台覆盖对比表，生态趋势分析
- `research-hn.md`: HN 技术社区视角，自建偏好、RSS vs 算法争论、协议讨论

### 待解决问题清单
- `待解决问题.md`: 用户确认的 7 个待开发功能

### 6 份实现计划（每份含具体文件修改清单）
- `plans/01-fulltext-enhancement.md`: 四层级联提取（自定义规则 → trafilatura → readability-lxml → 原始 RSS）。新依赖 readability-lxml, beautifulsoup4, lxml
- `plans/02-opml-import-export.md`: 增强导入为预览→确认两阶段 + 新增导出端点。零新依赖（标准库 xml.etree）
- `plans/03-ai-summary-and-sorting.md`: LiteLLM BYOK 架构，批量摘要生成（APScheduler），混合评分排序，自然语言过滤规则。新依赖 litellm, cryptography。Gemini Flash 月成本约 $3.9
- `plans/04-non-rss-sources.md`: Reddit/YouTube 原生 RSS + Twitter 依赖 RSSHub。YouTube Shorts 过滤需 YouTube Data API v3。Feed 模型新增 source_platform/source_identifier/filter_rules。零新后端依赖
- `plans/05-topic-clustering.md`: 三阶段——SimHash 去重（零依赖）→ TF-IDF 聚类（scikit-learn）→ Embedding 语义（sqlite-vec，可选）。阶段一解决 80% 重复
- `plans/06-keyboard-shortcuts.md`: react-hotkeys-hook 升级，4 scope 共 20 快捷键，`?` 帮助面板。新依赖 react-hotkeys-hook

## Next Steps

### Phase 3: 实施开发

建议实施优先级（投入产出比排序）：

1. OPML 导入导出（最简单，零依赖，降低用户迁移门槛）
2. 键盘快捷键（已有基础实现，升级工作量小）
3. 全文抓取增强（核心阅读体验提升）
4. 非 RSS 源订阅 - Reddit/YouTube 阶段（原生 RSS，零新依赖）
5. 话题聚类阶段一 - SimHash 去重（零依赖，解决 80% 重复）
6. AI 摘要和智能排序（最复杂但差异化最大）
7. 非 RSS 源订阅 - Twitter 阶段（需 RSSHub）
8. 话题聚类阶段二/三（TF-IDF / Embedding）

### 开发团队建议
- 每个功能按计划文件中的步骤拆分 task
- 后端和前端可并行开发（API 先行，前端跟进）
- 每个功能完成后跑 regression test

## Blockers / Questions
- 全文抓取：当前 trafilatura 实现的具体覆盖率和失败场景未量化，计划中建议先增强再评估是否需要 CSS 选择器规则
- AI 摘要：用户尚未确认偏好的 LLM 提供商（Gemini Flash 推荐但需 API key）
- Twitter 订阅：依赖自部署 RSSHub 实例，用户是否已有或愿意部署待确认
- YouTube Shorts 过滤：需要 YouTube Data API key，免费额度 10,000 units/天是否够用取决于订阅频道数量

## Agent Team Pattern Notes
- spawn prompt 中必须提供完整代码上下文（agent 无前序记忆）
- 前端 agent 不擅长交互式 CLI 工具（shadcn init 等手动处理）
- 绝对不要让 agent 删除数据库做迁移测试——用 alembic upgrade head
