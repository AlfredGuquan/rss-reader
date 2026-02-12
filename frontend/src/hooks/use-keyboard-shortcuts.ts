import { useHotkeys } from 'react-hotkeys-hook';
import { useUIStore } from '@/stores/ui-store';
import { useQueryClient } from '@tanstack/react-query';
import type { Entry, PaginatedResponse } from '@/types';

interface ShortcutActions {
  toggleStar: () => void;
  toggleRead: () => void;
  refreshFeed: () => void;
  openOriginal: () => void;
  fetchContent?: () => void;
  markAllRead?: () => void;
  openEntry?: () => void;
}

function isEnabled() {
  return useUIStore.getState().shortcutsEnabled;
}

function navigateEntry(direction: 'next' | 'prev') {
  const state = useUIStore.getState();
  const idx = state.entryIds.indexOf(state.selectedEntryId || '');
  const targetId = direction === 'next'
    ? state.entryIds[idx + 1]
    : state.entryIds[idx - 1];
  if (targetId) state.setSelectedEntry(targetId);
}

function getEntriesFromCache(queryClient: ReturnType<typeof useQueryClient>): Entry[] {
  const queries = queryClient.getQueriesData<PaginatedResponse<Entry>>({ queryKey: ['entries'] });
  for (const [, data] of queries) {
    if (data?.items?.length) return data.items;
  }
  return [];
}

export function useKeyboardShortcuts(actions: ShortcutActions) {
  const queryClient = useQueryClient();

  const commonOptions = { preventDefault: true, enabled: isEnabled } as const;

  // --- Global ---
  useHotkeys('shift+/', () => {
    useUIStore.getState().setHelpDialogOpen(true);
  }, { ...commonOptions, scopes: ['global'] });

  useHotkeys('/', (e) => {
    e.preventDefault();
    const searchInput = document.querySelector('[data-search-input]') as HTMLInputElement;
    searchInput?.focus();
  }, { ...commonOptions, scopes: ['global'] });

  useHotkeys('Escape', () => {
    const state = useUIStore.getState();
    if (state.helpDialogOpen) { state.setHelpDialogOpen(false); return; }
    if (document.activeElement?.hasAttribute('data-search-input')) {
      (document.activeElement as HTMLElement).blur();
      state.setSearchQuery('');
      return;
    }
    if (state.selectedEntryId) { state.setSelectedEntry(null); return; }
  }, { ...commonOptions, scopes: ['global'], enableOnFormTags: ['INPUT'] });

  useHotkeys('r', (e) => {
    e.preventDefault();
    actions.refreshFeed();
  }, { ...commonOptions, scopes: ['global'] });

  useHotkeys('shift+a', () => {
    actions.markAllRead?.();
  }, { ...commonOptions, scopes: ['global'] });

  // --- Entry list navigation ---
  useHotkeys('j, ArrowDown', () => {
    navigateEntry('next');
  }, { ...commonOptions, scopes: ['entry-list'] });

  useHotkeys('k, ArrowUp', () => {
    navigateEntry('prev');
  }, { ...commonOptions, scopes: ['entry-list'] });

  useHotkeys('Enter, o', () => {
    actions.openEntry?.();
  }, { ...commonOptions, scopes: ['entry-list'] });

  useHotkeys('g', () => {
    const state = useUIStore.getState();
    const firstId = state.entryIds[0];
    if (firstId) state.setSelectedEntry(firstId);
  }, { ...commonOptions, scopes: ['entry-list'] });

  useHotkeys('shift+g', () => {
    const state = useUIStore.getState();
    const lastId = state.entryIds[state.entryIds.length - 1];
    if (lastId) state.setSelectedEntry(lastId);
  }, { ...commonOptions, scopes: ['entry-list'] });

  useHotkeys('n', () => {
    const state = useUIStore.getState();
    const entries = getEntriesFromCache(queryClient);
    const currentIdx = state.entryIds.indexOf(state.selectedEntryId || '');
    for (let i = currentIdx + 1; i < entries.length; i++) {
      if (!entries[i].is_read) {
        state.setSelectedEntry(entries[i].id);
        return;
      }
    }
  }, { ...commonOptions, scopes: ['entry-list'] });

  useHotkeys('p', () => {
    const state = useUIStore.getState();
    const entries = getEntriesFromCache(queryClient);
    const currentIdx = state.entryIds.indexOf(state.selectedEntryId || '');
    for (let i = currentIdx - 1; i >= 0; i--) {
      if (!entries[i].is_read) {
        state.setSelectedEntry(entries[i].id);
        return;
      }
    }
  }, { ...commonOptions, scopes: ['entry-list'] });

  // --- Entry actions ---
  useHotkeys('s', () => {
    actions.toggleStar();
  }, { ...commonOptions, scopes: ['entry-action'] });

  useHotkeys('m', () => {
    actions.toggleRead();
  }, { ...commonOptions, scopes: ['entry-action'] });

  useHotkeys('v', () => {
    actions.openOriginal();
  }, { ...commonOptions, scopes: ['entry-action'] });

  useHotkeys('d', () => {
    actions.fetchContent?.();
  }, { ...commonOptions, scopes: ['entry-action'] });

  // --- Sidebar ---
  useHotkeys('1', () => {
    useUIStore.getState().setEntryFilter('all');
  }, { ...commonOptions, scopes: ['sidebar'] });

  useHotkeys('2', () => {
    useUIStore.getState().setEntryFilter('unread');
  }, { ...commonOptions, scopes: ['sidebar'] });

  useHotkeys('3', () => {
    useUIStore.getState().setEntryFilter('starred');
  }, { ...commonOptions, scopes: ['sidebar'] });
}
