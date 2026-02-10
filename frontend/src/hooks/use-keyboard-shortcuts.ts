import { useEffect, useRef } from 'react';
import { useUIStore } from '@/stores/ui-store';

interface ShortcutActions {
  toggleStar: () => void;
  toggleRead: () => void;
  refreshFeed: () => void;
  openOriginal: () => void;
}

export function useKeyboardShortcuts(actions: ShortcutActions) {
  const actionsRef = useRef(actions);
  actionsRef.current = actions;

  useEffect(() => {
    function handler(e: KeyboardEvent) {
      if (!useUIStore.getState().shortcutsEnabled) return;

      const target = e.target as HTMLElement;
      if (target.tagName === 'INPUT' || target.tagName === 'TEXTAREA' || target.tagName === 'SELECT' || target.isContentEditable) return;

      const state = useUIStore.getState();

      switch (e.key) {
        case 'j': {
          const idx = state.entryIds.indexOf(state.selectedEntryId || '');
          const nextId = state.entryIds[idx + 1];
          if (nextId) state.setSelectedEntry(nextId);
          break;
        }
        case 'k': {
          const idx = state.entryIds.indexOf(state.selectedEntryId || '');
          const prevId = state.entryIds[idx - 1];
          if (prevId) state.setSelectedEntry(prevId);
          break;
        }
        case 's':
          actionsRef.current.toggleStar();
          break;
        case 'm':
          actionsRef.current.toggleRead();
          break;
        case 'v':
          actionsRef.current.openOriginal();
          break;
        case 'r':
          e.preventDefault();
          actionsRef.current.refreshFeed();
          break;
      }
    }

    document.addEventListener('keydown', handler);
    return () => document.removeEventListener('keydown', handler);
  }, []);
}
