import { create } from 'zustand';

type EntryFilter = 'all' | 'unread' | 'starred';

interface UIState {
  selectedFeedId: string | null;
  selectedGroupId: string | null;
  selectedEntryId: string | null;
  entryFilter: EntryFilter;
  expandedGroupIds: Set<string>;
  sidebarCollapsed: boolean;
  shortcutsEnabled: boolean;
  entryIds: string[];

  setSelectedFeed: (feedId: string | null) => void;
  setSelectedGroup: (groupId: string | null) => void;
  setSelectedEntry: (entryId: string | null) => void;
  setEntryFilter: (filter: EntryFilter) => void;
  toggleGroupExpanded: (groupId: string) => void;
  setSidebarCollapsed: (collapsed: boolean) => void;
  setShortcutsEnabled: (enabled: boolean) => void;
  setEntryIds: (ids: string[]) => void;
}

export const useUIStore = create<UIState>((set) => ({
  selectedFeedId: null,
  selectedGroupId: null,
  selectedEntryId: null,
  entryFilter: 'all',
  expandedGroupIds: new Set<string>(),
  sidebarCollapsed: false,
  shortcutsEnabled: true,
  entryIds: [],

  setSelectedFeed: (feedId) =>
    set({ selectedFeedId: feedId, selectedGroupId: null, selectedEntryId: null }),
  setSelectedGroup: (groupId) =>
    set({ selectedGroupId: groupId, selectedFeedId: null, selectedEntryId: null }),
  setSelectedEntry: (entryId) => set({ selectedEntryId: entryId }),
  setEntryFilter: (filter) => set({ entryFilter: filter }),
  toggleGroupExpanded: (groupId) =>
    set((state) => {
      const next = new Set(state.expandedGroupIds);
      if (next.has(groupId)) next.delete(groupId);
      else next.add(groupId);
      return { expandedGroupIds: next };
    }),
  setSidebarCollapsed: (collapsed) => set({ sidebarCollapsed: collapsed }),
  setShortcutsEnabled: (enabled) => set({ shortcutsEnabled: enabled }),
  setEntryIds: (ids) => set({ entryIds: ids }),
}));
