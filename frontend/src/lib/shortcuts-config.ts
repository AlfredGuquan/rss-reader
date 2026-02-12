export interface ShortcutDef {
  keys: string | string[];
  label: string;
  description: string;
  scope: 'global' | 'entry-list' | 'entry-action' | 'sidebar';
}

export const SHORTCUTS: Record<string, ShortcutDef> = {
  // Global
  HELP: { keys: 'shift+/', label: '?', description: '显示快捷键帮助', scope: 'global' },
  SEARCH: { keys: '/', label: '/', description: '搜索', scope: 'global' },
  ESCAPE: { keys: 'Escape', label: 'Esc', description: '关闭/取消', scope: 'global' },
  REFRESH: { keys: 'r', label: 'r', description: '刷新当前 Feed', scope: 'global' },
  MARK_ALL_READ: { keys: 'shift+a', label: 'Shift+A', description: '全部标记已读', scope: 'global' },

  // Entry list navigation
  NEXT_ENTRY: { keys: ['j', 'ArrowDown'], label: 'j / ↓', description: '下一篇文章', scope: 'entry-list' },
  PREV_ENTRY: { keys: ['k', 'ArrowUp'], label: 'k / ↑', description: '上一篇文章', scope: 'entry-list' },
  OPEN_ENTRY: { keys: ['Enter', 'o'], label: 'Enter / o', description: '打开文章', scope: 'entry-list' },
  FIRST_ENTRY: { keys: 'g', label: 'g g', description: '跳到第一篇', scope: 'entry-list' },
  LAST_ENTRY: { keys: 'shift+g', label: 'Shift+G', description: '跳到最后一篇', scope: 'entry-list' },
  NEXT_UNREAD: { keys: 'n', label: 'n', description: '下一篇未读', scope: 'entry-list' },
  PREV_UNREAD: { keys: 'p', label: 'p', description: '上一篇未读', scope: 'entry-list' },

  // Entry actions
  TOGGLE_STAR: { keys: 's', label: 's', description: '收藏/取消收藏', scope: 'entry-action' },
  TOGGLE_READ: { keys: 'm', label: 'm', description: '标记已读/未读', scope: 'entry-action' },
  OPEN_ORIGINAL: { keys: 'v', label: 'v', description: '打开原文', scope: 'entry-action' },
  FETCH_CONTENT: { keys: 'd', label: 'd', description: '抓取全文', scope: 'entry-action' },

  // Sidebar
  NEXT_FEED: { keys: 'shift+j', label: 'Shift+J', description: '下一个 Feed', scope: 'sidebar' },
  PREV_FEED: { keys: 'shift+k', label: 'Shift+K', description: '上一个 Feed', scope: 'sidebar' },
  FILTER_ALL: { keys: '1', label: '1', description: '显示全部', scope: 'sidebar' },
  FILTER_UNREAD: { keys: '2', label: '2', description: '显示未读', scope: 'sidebar' },
  FILTER_STARRED: { keys: '3', label: '3', description: '显示收藏', scope: 'sidebar' },
};

export const SCOPE_LABELS: Record<string, string> = {
  global: '全局',
  'entry-list': '文章导航',
  'entry-action': '文章操作',
  sidebar: '侧边栏',
};
