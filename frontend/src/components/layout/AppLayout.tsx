import {
  ResizableHandle,
  ResizablePanel,
  ResizablePanelGroup,
} from '@/components/ui/resizable';
import { Sidebar } from './Sidebar';
import { EntryList } from './EntryList';
import { ReadingPane } from './ReadingPane';
import { useKeyboardShortcuts } from '@/hooks/use-keyboard-shortcuts';
import { useUIStore } from '@/stores/ui-store';
import { useEntry, useMarkRead, useMarkUnread, useToggleStar, useRefreshFeed } from '@/hooks/queries/use-entries';

export function AppLayout() {
  const selectedEntryId = useUIStore((s) => s.selectedEntryId);
  const selectedFeedId = useUIStore((s) => s.selectedFeedId);
  const { data: entry } = useEntry(selectedEntryId);
  const markRead = useMarkRead();
  const markUnread = useMarkUnread();
  const toggleStar = useToggleStar();
  const refreshFeedMutation = useRefreshFeed();

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
  });

  return (
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
  );
}
