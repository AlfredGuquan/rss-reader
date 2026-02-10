import { useEffect, useRef } from 'react';
import { useUIStore } from '@/stores/ui-store';
import { useEntry, useMarkRead, useToggleStar, useMarkUnread } from '@/hooks/queries/use-entries';
import { ArticleToolbar } from '@/components/reading/ArticleToolbar';
import { ArticleView } from '@/components/reading/ArticleView';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Skeleton } from '@/components/ui/skeleton';

export function ReadingPane() {
  const selectedEntryId = useUIStore((s) => s.selectedEntryId);
  const { data: entry, isLoading } = useEntry(selectedEntryId);
  const markRead = useMarkRead();
  const markUnread = useMarkUnread();
  const toggleStar = useToggleStar();
  const lastMarkedId = useRef<string | null>(null);

  // Auto-mark-read when selecting a new entry
  useEffect(() => {
    if (entry && !entry.is_read && entry.id !== lastMarkedId.current) {
      lastMarkedId.current = entry.id;
      markRead.mutate(entry.id);
    }
  }, [entry]);

  if (!selectedEntryId) {
    return (
      <div className="flex h-full items-center justify-center">
        <p className="text-sm text-muted-foreground">Select an article to read.</p>
      </div>
    );
  }

  if (isLoading || !entry) {
    return (
      <div className="flex h-full flex-col">
        <div className="border-b px-4 py-2">
          <Skeleton className="h-8 w-32" />
        </div>
        <div className="space-y-4 p-6">
          <Skeleton className="h-8 w-3/4" />
          <Skeleton className="h-4 w-1/2" />
          <Skeleton className="h-40 w-full" />
        </div>
      </div>
    );
  }

  return (
    <div className="flex h-full flex-col">
      <ArticleToolbar
        entry={entry}
        onToggleStar={() => toggleStar.mutate({ entryId: entry.id, starred: !entry.is_starred })}
        onToggleRead={() => (entry.is_read ? markUnread.mutate(entry.id) : markRead.mutate(entry.id))}
      />
      <ScrollArea className="flex-1">
        <ArticleView entry={entry} />
      </ScrollArea>
    </div>
  );
}
