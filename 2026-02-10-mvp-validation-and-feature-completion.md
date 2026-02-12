# 2026-02-10 MVP 验证与功能补全会话记录

## 会话目标

对 RSS 阅读器 MVP 进行端到端功能验证，确认所有功能正常工作，然后完成 SPEC 中明确要求但尚未实现的三个功能。

## 完成的工作

### Phase 1: MVP 端到端验证 (8/8 PASS)

通过 agent team 派出 e2e-tester 使用 Chrome MCP 浏览器自动化，逐项验证了 8 个 MVP 核心功能。全部通过，零 bug，零控制台错误。

验证清单：首次加载与三栏布局、Feed 管理（添加/刷新/编辑/删除）、分组管理（创建/展开折叠/重命名/未读数聚合）、文章阅读（内容显示/自动标已读/收藏/原文链接）、筛选（All/Unread/Starred）、键盘快捷键（j/k/s/m/v）、OPML 导入、标记全部已读。

### Phase 3: 三个新功能开发与验证 (3/3 PASS)

#### 功能 1: Feed paused 状态视觉区分

改动文件：`frontend/src/components/sidebar/FeedItem.tsx`

当 `feed.status === 'paused'` 时，feed 标题文字透明度降低（`opacity-60`），并在标题右侧显示 `PauseCircle` 图标（灰色）。与已有的 error 状态（橙色 AlertTriangle）保持一致的设计模式。

#### 功能 2: Feed 自动发现 UI 集成

改动文件：
- `frontend/src/api/feeds.ts` -- 新增 `discoverFeeds` 函数和 `DiscoveredFeed` 类型
- `frontend/src/components/feed-management/AddFeedDialog.tsx` -- 完全重写

用户输入网站 URL 时，先通过 `looksLikeFeedUrl` 判断是否为 RSS URL（检查 .xml/.rss/.atom 后缀或 /feed /rss /atom 路径）。如果不是，调用后端 `GET /api/feeds/discover?url=xxx` 发现 feed。发现多个 feed 时展示列表供选择，发现单个时直接订阅，发现零个时回退到直接订阅原 URL。

#### 功能 3: 分组拖拽排序

后端改动：
- `backend/app/schemas/group.py` -- 新增 `GroupReorder` schema（`group_ids: list[str]`）
- `backend/app/services/group_service.py` -- 新增 `reorder_groups` 函数，遍历 group_ids 按索引更新 sort_order
- `backend/app/routers/groups.py` -- 新增 `PUT /api/groups/reorder` 端点（注意放在 `/{group_id}` 之前避免路由冲突）

前端改动：
- `frontend/package.json` -- 新增 `@dnd-kit/core`、`@dnd-kit/sortable`、`@dnd-kit/utilities`
- `frontend/src/api/groups.ts` -- 新增 `reorderGroups` 函数
- `frontend/src/hooks/queries/use-groups.ts` -- 新增 `useReorderGroups` hook
- `frontend/src/components/layout/Sidebar.tsx` -- 用 `DndContext` + `SortableContext` 包裹分组列表，`PointerSensor(distance:5)` + `KeyboardSensor`
- `frontend/src/components/sidebar/GroupItem.tsx` -- 用 `useSortable` 使分组可拖拽，新增 GripVertical 拖拽手柄（hover 时显示）

## 发现与经验

### Chrome MCP 浏览器自动化

Chrome MCP 的 `left_click_drag` 与 dnd-kit 的 PointerSensor 存在兼容性限制，无法通过自动化直接完成拖拽交互。tester 通过直接调用 API 验证了完整流程作为替代。

### e2e-tester agent 模式

e2e-tester 作为 general-purpose subagent 使用 Chrome MCP 工具效果很好，能独立完成截图验证、console 检查、API 调用等完整测试流程。关键是在 spawn prompt 中提供完整的验证清单和报告格式要求。

### update_plan 域名声明

Chrome MCP 要求先调用 `update_plan` 声明域名才能导航，但有时新创建的 tab 无法立即调用 `update_plan`（返回 "No tab available"）。需要先 `navigate` 到目标 URL，然后再操作。

## 当前状态

Git commit: `e811765` -- "Add group drag-and-drop sorting, feed auto-discovery, and paused feed visual indicator"

12 个文件变更，350 行增加，108 行删除。

后端运行在 localhost:8000，前端运行在 localhost:5173。TypeScript 编译零错误，浏览器控制台零错误。

## SPEC 中尚未实现的功能（下一步）

以下功能在 SPEC.md 中定义但当前尚未实现，需要新实例继续：

1. **Feed pause/unpause API** -- 后端 `FeedUpdate` schema 只支持 title 和 group_id，不支持修改 status 字段。需要扩展 API 让用户可以通过 UI 暂停/恢复 feed。前端 EditFeedDialog 也需要添加暂停开关。

2. **后台自动刷新调度** -- `backend/app/tasks/jobs.py` 中有 `fetch_all_active_feeds` 函数，但需要集成 APScheduler 或类似调度器来自动定时抓取。

3. **全文抓取** -- Entry 模型有 `content_fetched` 字段，可能需要实现从原文 URL 抓取完整内容的功能。

4. **错误重试与退避** -- Feed 抓取失败时的指数退避策略。

5. **搜索功能** -- 如果 SPEC 中包含文章搜索，当前未实现。

建议下一个实例先 `cat SPEC.md` 对照当前代码状态，确认完整的待办清单。

## 关键文件索引

```
backend/
  app/main.py                          # FastAPI 入口
  app/routers/{feeds,entries,groups}.py # API 路由
  app/services/{feed,entry,group,fetch,discovery,opml}_service.py
  app/models/{feed,entry,user_entry_state,group}.py
  app/schemas/{feed,entry,group}.py

frontend/
  src/App.tsx                           # 根组件
  src/stores/ui-store.ts                # Zustand UI 状态
  src/api/{client,feeds,entries,groups}.ts
  src/hooks/queries/use-{feeds,entries,groups}.ts
  src/components/
    layout/{AppLayout,Sidebar,EntryList,ReadingPane}.tsx
    sidebar/{FeedItem,GroupItem,SidebarFooter}.tsx
    feed-management/{AddFeedDialog,EditFeedDialog,ImportOpmlDialog}.tsx
    group-management/{CreateGroupDialog,RenameGroupDialog,DeleteGroupDialog}.tsx
    entries/{EntryCard,EntryListView,EntryFilterBar,EntryListEmpty}.tsx
    reading/{ArticleToolbar,ArticleView,ArticleContent}.tsx
    theme/{ThemeProvider,ThemeToggle}.tsx
  src/hooks/use-keyboard-shortcuts.ts
  src/types/index.ts
```
