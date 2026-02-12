import { useEffect } from 'react';
import { useHotkeysContext } from 'react-hotkeys-hook';
import {
  ResizableHandle,
  ResizablePanel,
  ResizablePanelGroup,
} from '@/components/ui/resizable';
import { Sidebar } from './Sidebar';
import { EntryList } from './EntryList';
import { ReadingPane } from './ReadingPane';
import { KeyboardShortcutsHelp } from '@/components/keyboard/KeyboardShortcutsHelp';
import { useKeyboardShortcuts } from '@/hooks/use-keyboard-shortcuts';
import { useUIStore } from '@/stores/ui-store';
import { useEntry, useMarkRead, useMarkUnread, useToggleStar, useRefreshFeed, useMarkAllRead, useFetchContent } from '@/hooks/queries/use-entries';

function KeyboardScopeManager() {
  const { enableScope, disableScope } = useHotkeysContext();
  const selectedFeedId = useUIStore((s) => s.selectedFeedId);
  const selectedGroupId = useUIStore((s) => s.selectedGroupId);
  const selectedEntryId = useUIStore((s) => s.selectedEntryId);

  useEffect(() => {
    if (selectedFeedId || selectedGroupId) enableScope('entry-list');
    else disableScope('entry-list');
  }, [selectedFeedId, selectedGroupId, enableScope, disableScope]);

  useEffect(() => {
    if (selectedEntryId) enableScope('entry-action');
    else disableScope('entry-action');
  }, [selectedEntryId, enableScope, disableScope]);

  return null;
}

export function AppLayout() {
  const selectedEntryId = useUIStore((s) => s.selectedEntryId);
  const selectedFeedId = useUIStore((s) => s.selectedFeedId);
  const selectedGroupId = useUIStore((s) => s.selectedGroupId);
  const { data: entry } = useEntry(selectedEntryId);
  const markRead = useMarkRead();
  const markUnread = useMarkUnread();
  const toggleStar = useToggleStar();
  const refreshFeedMutation = useRefreshFeed();
  const markAllReadMutation = useMarkAllRead();
  const fetchContentMutation = useFetchContent();

  useKeyboardShortcuts({
    toggleStar: () => {
      if (entry) toggleStar.mutate({ entryId: entry.id, starred: !entry.is_starred });
    },
    toggleRead: () => {
      if (entry) {
        entry.is_read ? markUnread.mutate(entry.id) : markRead.mutate(entry.id);
      }
    },
    refreshFeed: () => {
      if (selectedFeedId) refreshFeedMutation.mutate(selectedFeedId);
    },
    openOriginal: () => {
      if (entry?.url) window.open(entry.url, '_blank');
    },
    fetchContent: () => {
      if (entry && !entry.content_fetched) fetchContentMutation.mutate(entry.id);
    },
    markAllRead: () => {
      const params: { feed_id?: string; group_id?: string } = {};
      if (selectedFeedId) params.feed_id = selectedFeedId;
      else if (selectedGroupId) params.group_id = selectedGroupId;
      if (params.feed_id || params.group_id) markAllReadMutation.mutate(params);
    },
    openEntry: () => {
      // If no entry selected, select the first one
      const state = useUIStore.getState();
      if (!state.selectedEntryId && state.entryIds.length > 0) {
        state.setSelectedEntry(state.entryIds[0]);
      }
    },
  });

  return (
    <>
      <KeyboardScopeManager />
      <KeyboardShortcutsHelp />
      <ResizablePanelGroup orientation="horizontal" className="h-screen w-screen">
        <ResizablePanel defaultSize="20%" minSize="15%" maxSize="30%">
          <Sidebar />
        </ResizablePanel>
        <ResizableHandle withHandle />
        <ResizablePanel defaultSize="30%" minSize="20%">
          <EntryList />
        </ResizablePanel>
        <ResizableHandle withHandle />
        <ResizablePanel defaultSize="50%" minSize="30%">
          <ReadingPane />
        </ResizablePanel>
      </ResizablePanelGroup>
    </>
  );
}
