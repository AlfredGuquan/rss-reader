import { useEffect } from 'react';
import { useUIStore } from '@/stores/ui-store';
import { useEntries } from '@/hooks/queries/use-entries';
import { EntryFilterBar } from '@/components/entries/EntryFilterBar';
import { EntryListView } from '@/components/entries/EntryListView';
import { EntryListEmpty } from '@/components/entries/EntryListEmpty';
import { Skeleton } from '@/components/ui/skeleton';

export function EntryList() {
  const selectedFeedId = useUIStore((s) => s.selectedFeedId);
  const selectedGroupId = useUIStore((s) => s.selectedGroupId);
  const entryFilter = useUIStore((s) => s.entryFilter);

  const hasSelection = !!(selectedFeedId || selectedGroupId);

  const { data, isLoading } = useEntries({
    feed_id: selectedFeedId || undefined,
    group_id: selectedGroupId || undefined,
    status: entryFilter,
    per_page: 50,
  });

  // 同步文章 ID 到 store 以支持键盘导航
  useEffect(() => {
    const setEntryIds = useUIStore.getState().setEntryIds;
    if (data?.items) {
      setEntryIds(data.items.map((e) => e.id));
    } else {
      setEntryIds([]);
    }
  }, [data?.items]);

  return (
    <div className="flex h-full flex-col">
      <div className="border-b px-4 py-3">
        <div className="flex items-center justify-between">
          <h2 className="text-sm font-semibold">Articles</h2>
          {hasSelection && <EntryFilterBar />}
        </div>
      </div>
      <div className="flex-1 overflow-hidden">
        {!hasSelection ? (
          <EntryListEmpty type="no-feed" />
        ) : isLoading ? (
          <div className="space-y-3 p-4">
            {Array.from({ length: 5 }).map((_, i) => (
              <Skeleton key={i} className="h-20 w-full" />
            ))}
          </div>
        ) : !data?.items.length ? (
          <EntryListEmpty
            type={
              entryFilter === 'unread'
                ? 'all-read'
                : entryFilter === 'starred'
                  ? 'no-starred'
                  : 'no-entries'
            }
          />
        ) : (
          <EntryListView entries={data.items} />
        )}
      </div>
    </div>
  );
}
