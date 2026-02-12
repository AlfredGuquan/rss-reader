# 键盘快捷键系统实现计划

## 现状分析

项目已有基础的键盘快捷键实现，位于 `frontend/src/hooks/use-keyboard-shortcuts.ts`。当前实现使用原生 `keydown` 事件监听，支持 6 个快捷键：j/k（上下导航）、s（收藏）、m（标记已读）、v（打开原文）、r（刷新）。UI store 中已有 `shortcutsEnabled` 开关和 `entryIds` 列表用于导航。

存在的主要问题包括：没有快捷键提示 UI（用户无法发现可用的快捷键）；没有全局 vs 上下文快捷键的区分架构；不支持组合键（如 Shift+A 全部标记已读）；不支持按键序列（如 g+u 跳转到未读页）；缺少搜索聚焦、侧边栏导航等常用操作的快捷键。

## 库选型：react-hotkeys-hook

### 推荐方案

使用 `react-hotkeys-hook`（当前 npm 周下载量约 170 万，GitHub 3400+ stars）替代当前的原生事件监听实现。

### 选型理由

react-hotkeys-hook 提供了 `useHotkeys` hook，天然契合项目的 React 函数组件架构。它内置了 scope 机制（通过 `HotkeysProvider` + `useHotkeysContext`），可以优雅地处理全局快捷键与上下文快捷键的切换，例如在 Dialog 打开时自动禁用文章导航快捷键。它自动处理了输入框内的快捷键屏蔽（`enableOnFormTags` 选项），避免在搜索框输入时触发快捷键。支持组合键（`shift+a`）和按键序列，API 简洁，与现有 zustand store 配合无额外适配成本。

相比之下，tinykeys（约 5 万周下载量）虽然体积更小（约 700B gzip），但它是框架无关的底层库，没有 React 集成，需要自行封装 hook 并实现 scope 管理、表单屏蔽等逻辑。mousetrap 已多年未维护，且使用已废弃的 `keyCode` API。项目当前的手动实现方式在快捷键数量少时可行，但扩展到 20+ 个快捷键后，scope 管理和冲突处理的复杂度会快速增长，不如直接使用成熟库。

### 安装

```bash
cd frontend && bun add react-hotkeys-hook
```

## 键位映射表设计

键位设计参考了 Miniflux、Feedly 和 Google Reader 这三个主流 RSS 阅读器的惯例，遵循 vim 风格导航（j/k），同时兼顾非 vim 用户的直觉（箭头键）。

### 全局快捷键（Global scope，始终生效）

| 按键 | 动作 | 说明 |
|------|------|------|
| `?` | 显示/关闭快捷键帮助面板 | 所有主流阅读器的标准约定 |
| `/` | 聚焦搜索框 | Miniflux、GitHub 等通用约定 |
| `Escape` | 关闭 Dialog / 取消搜索聚焦 / 清除选择 | 通用 |
| `r` | 刷新当前 Feed | 保持现有行为 |
| `Shift+A` | 全部标记已读 | Feedly 约定，Miniflux 用 A |

### 文章列表导航（Entry List scope）

| 按键 | 动作 | 说明 |
|------|------|------|
| `j` / `ArrowDown` | 选择下一篇文章 | vim 风格 + 箭头键兼容 |
| `k` / `ArrowUp` | 选择上一篇文章 | vim 风格 + 箭头键兼容 |
| `Enter` / `o` | 打开当前选中文章（在阅读面板显示） | Miniflux 约定 |
| `g g` | 跳转到列表第一篇 | vim 风格，Miniflux 约定 |
| `Shift+G` | 跳转到列表最后一篇 | vim 风格，Miniflux 约定 |
| `n` | 选择下一篇未读文章 | Feedly 约定，跳过已读 |
| `p` | 选择上一篇未读文章 | Feedly 约定，跳过已读 |

### 文章操作（Entry Action scope，需要有选中文章）

| 按键 | 动作 | 说明 |
|------|------|------|
| `s` | 切换收藏/取消收藏 | Miniflux 用 f，但 s=star 更直觉 |
| `m` | 切换已读/未读 | Miniflux、Feedly 共同约定 |
| `v` | 在新标签页打开原文 | Miniflux、Feedly 共同约定 |
| `d` | 抓取全文内容 | Miniflux 约定（fetch full text） |

### 侧边栏导航（Sidebar scope）

| 按键 | 动作 | 说明 |
|------|------|------|
| `Shift+J` | 下一个 Feed/分组 | Feedly 约定 |
| `Shift+K` | 上一个 Feed/分组 | Feedly 约定 |
| `1` | 切换过滤器为 "全部" | 快速切换视图 |
| `2` | 切换过滤器为 "未读" | 快速切换视图 |
| `3` | 切换过滤器为 "收藏" | 快速切换视图 |

### 设计原则

单字母快捷键（j/k/s/m/v/r）覆盖最高频操作，保持与现有实现的向后兼容。Shift 修饰键用于"更大范围"的同类操作（Shift+A = 全部标记已读 vs m = 单篇标记已读，Shift+J = 下一个 Feed vs j = 下一篇文章）。所有快捷键在输入框（搜索框、编辑框）获得焦点时自动失效。`/` 键是唯一的例外——它会主动将焦点移到搜索框，此时其他快捷键自然失效。

## 架构设计

### Scope 分层

```
HotkeysProvider
├── global scope  （始终激活）
│   ├── ?  → 帮助面板
│   ├── /  → 聚焦搜索
│   ├── Escape → 关闭/取消
│   ├── r → 刷新
│   └── Shift+A → 全部已读
│
├── entry-list scope （有 feed/group 选中时激活）
│   ├── j/k/ArrowDown/ArrowUp → 文章导航
│   ├── n/p → 未读文章导航
│   ├── g g / Shift+G → 首尾跳转
│   └── Enter/o → 打开文章
│
├── entry-action scope （有文章选中时激活）
│   ├── s → 收藏
│   ├── m → 已读
│   ├── v → 原文
│   └── d → 全文抓取
│
└── sidebar scope （始终激活，Shift 修饰避免冲突）
    ├── Shift+J/K → Feed 导航
    └── 1/2/3 → 过滤器切换
```

### 核心文件结构

```
frontend/src/
├── hooks/
│   └── use-keyboard-shortcuts.ts  （重写：拆分为多个 scope hook）
├── components/
│   └── keyboard/
│       ├── KeyboardShortcutsProvider.tsx  （HotkeysProvider 封装 + scope 管理）
│       └── KeyboardShortcutsHelp.tsx      （? 键触发的帮助面板）
├── stores/
│   └── ui-store.ts  （新增 helpDialogOpen 状态）
└── lib/
    └── shortcuts-config.ts  （快捷键配置常量，键位映射表集中管理）
```

## 集成方案

### 第一步：安装依赖并创建配置

在 `lib/shortcuts-config.ts` 中集中定义所有快捷键的 key、label（显示名称）、description（帮助文本）和 scope。这样快捷键帮助面板可以从同一配置自动生成，避免映射表和实际代码不同步。

```typescript
export const SHORTCUTS = {
  HELP: { keys: '?', label: '?', description: '显示快捷键帮助', scope: 'global' },
  SEARCH: { keys: '/', label: '/', description: '搜索', scope: 'global' },
  NEXT_ENTRY: { keys: ['j', 'ArrowDown'], label: 'j / ↓', description: '下一篇文章', scope: 'entry-list' },
  PREV_ENTRY: { keys: ['k', 'ArrowUp'], label: 'k / ↑', description: '上一篇文章', scope: 'entry-list' },
  // ...
} as const;
```

### 第二步：创建 Provider

在 `App.tsx` 中用 `HotkeysProvider` 包裹根组件，初始激活 `global` 和 `sidebar` scope。entry-list 和 entry-action scope 的激活/停用由 ui-store 中的 `selectedFeedId`、`selectedEntryId` 状态驱动。

```tsx
// App.tsx 修改
import { HotkeysProvider } from 'react-hotkeys-hook';

function App() {
  return (
    <ThemeProvider>
      <HotkeysProvider initiallyActiveScopes={['global', 'sidebar']}>
        <QueryClientProvider client={queryClient}>
          {/* ... */}
        </QueryClientProvider>
      </HotkeysProvider>
    </ThemeProvider>
  );
}
```

### 第三步：重写快捷键 hook

将现有的单一 `useKeyboardShortcuts` 拆分为按 scope 组织的多个 hook 调用，直接在对应的组件中使用 `useHotkeys`。全局快捷键放在 `AppLayout` 中，文章列表导航放在 `EntryList` 或 `EntryListView` 中，文章操作放在 `ReadingPane` 中。

`AppLayout` 中的核心代码示意：

```tsx
// 全局：帮助面板
useHotkeys('shift+/', () => setHelpOpen(prev => !prev), { scopes: ['global'] });

// 全局：搜索聚焦
useHotkeys('/', (e) => {
  e.preventDefault();
  searchInputRef.current?.focus();
}, { scopes: ['global'] });

// 文章导航
useHotkeys(['j', 'ArrowDown'], () => {
  const state = useUIStore.getState();
  const idx = state.entryIds.indexOf(state.selectedEntryId || '');
  const nextId = state.entryIds[idx + 1];
  if (nextId) state.setSelectedEntry(nextId);
}, { scopes: ['entry-list'] });
```

### 第四步：scope 激活管理

在 `AppLayout` 或一个专用的 `KeyboardScopeManager` 组件中，监听 UI store 的状态变化，通过 `useHotkeysContext()` 动态启用/禁用 scope：

```tsx
function KeyboardScopeManager() {
  const { enableScope, disableScope } = useHotkeysContext();
  const selectedFeedId = useUIStore(s => s.selectedFeedId);
  const selectedGroupId = useUIStore(s => s.selectedGroupId);
  const selectedEntryId = useUIStore(s => s.selectedEntryId);

  useEffect(() => {
    if (selectedFeedId || selectedGroupId) {
      enableScope('entry-list');
    } else {
      disableScope('entry-list');
    }
  }, [selectedFeedId, selectedGroupId]);

  useEffect(() => {
    if (selectedEntryId) {
      enableScope('entry-action');
    } else {
      disableScope('entry-action');
    }
  }, [selectedEntryId]);

  return null;
}
```

### 第五步：快捷键帮助面板

使用 shadcn/ui 的 `Dialog` 组件实现帮助面板。内容从 `SHORTCUTS` 配置自动生成，按 scope 分组展示。布局参考 GitHub 的快捷键帮助面板：左侧显示按键（用 `<kbd>` 标签样式），右侧显示描述。

```
┌─────────────────────────────────────┐
│         键盘快捷键                    │
├─────────────────────────────────────┤
│ 全局                                 │
│  ?          显示快捷键帮助            │
│  /          搜索                     │
│  r          刷新当前 Feed            │
│  Shift+A    全部标记已读              │
│  Esc        关闭/取消                │
│                                      │
│ 文章导航                              │
│  j / ↓      下一篇文章               │
│  k / ↑      上一篇文章               │
│  n          下一篇未读               │
│  ...                                 │
│                                      │
│ 文章操作                              │
│  s          收藏/取消收藏             │
│  m          标记已读/未读             │
│  v          打开原文                  │
│  ...                                 │
└─────────────────────────────────────┘
```

### 第六步：自动滚动选中项到可视区域

当前 `EntryListView` 使用 `@tanstack/react-virtual` 进行虚拟滚动。键盘导航切换 selectedEntryId 后，需要调用 virtualizer 的 `scrollToIndex` 方法将选中项滚动到视口内。在 `EntryListView` 中添加一个 effect，监听 selectedEntryId 变化，找到其在 entries 数组中的 index，调用 `virtualizer.scrollToIndex(idx, { align: 'auto' })`。

## 实现步骤（按顺序）

### 步骤 1：安装 react-hotkeys-hook

```bash
cd frontend && bun add react-hotkeys-hook
```

### 步骤 2：创建 `lib/shortcuts-config.ts`

定义全部快捷键的配置常量，包括 keys、label、description、scope。

### 步骤 3：修改 `App.tsx`

用 `HotkeysProvider` 包裹根组件，设置初始 scope。

### 步骤 4：创建 `components/keyboard/KeyboardShortcutsHelp.tsx`

实现帮助面板 Dialog，从 shortcuts-config 自动生成内容。

### 步骤 5：在 `stores/ui-store.ts` 添加状态

新增 `helpDialogOpen` 布尔值和 `setHelpDialogOpen` setter。

### 步骤 6：重写 `hooks/use-keyboard-shortcuts.ts`

将原有的单一 hook 拆分为多个基于 `useHotkeys` 的调用，按 scope 分组。保持现有 ShortcutActions 接口的向后兼容，AppLayout 的调用方式改动最小化。

### 步骤 7：在 `EntryListView.tsx` 添加自动滚动

监听 selectedEntryId 变化，调用 `virtualizer.scrollToIndex` 确保选中项可见。

### 步骤 8：创建 `KeyboardScopeManager` 组件

放在 AppLayout 中，监听 UI store 状态变化，动态管理 scope 激活。

### 步骤 9：添加搜索框 ref 和 `/` 键聚焦

在 Sidebar 组件中为搜索 Input 添加 ref，通过 `forwardRef` 或 zustand store 暴露给全局快捷键使用。

## 需要新增的依赖

| 依赖 | 版本 | 用途 |
|------|------|------|
| react-hotkeys-hook | ^4.x | 快捷键管理 |

无其他新依赖。帮助面板使用已有的 shadcn/ui Dialog 组件，kbd 样式用 Tailwind 直接实现。

## 浏览器快捷键冲突处理

需要特别注意避免与浏览器内置快捷键冲突。`/` 在 Firefox 中默认触发快速搜索，需要 `preventDefault`。`Ctrl+` 组合键全部避免使用（保留给浏览器：Ctrl+T/W/L/R 等）。所有快捷键仅使用单字母键或 Shift+字母键，不占用任何 Ctrl/Cmd 组合。`Escape` 的处理需要分层：Dialog 打开时优先关闭 Dialog，搜索框聚焦时退出搜索，否则清除文章选择。

`?` 键实际上是 `Shift+/`，在 react-hotkeys-hook 中需要注册为 `shift+/` 或直接使用 `?`（库会自动处理）。

## 后续扩展点

快捷键自定义（允许用户重映射按键）可以在未来通过将 shortcuts-config 存入 localStorage 来实现，但作为 MVP 不需要。vi 风格的 `:` 命令模式（输入命令如 `:mark-all-read`）可以作为高级功能在后续迭代中考虑。
