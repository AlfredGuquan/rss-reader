import { useEffect } from 'react';
import { useUIStore } from '@/stores/ui-store';
import { useEntries, useSearchEntries } from '@/hooks/queries/use-entries';
import { EntryFilterBar } from '@/components/entries/EntryFilterBar';
import { EntryListView } from '@/components/entries/EntryListView';
import { EntryListEmpty } from '@/components/entries/EntryListEmpty';
import { Skeleton } from '@/components/ui/skeleton';

export function EntryList() {
  const selectedFeedId = useUIStore((s) => s.selectedFeedId);
  const selectedGroupId = useUIStore((s) => s.selectedGroupId);
  const entryFilter = useUIStore((s) => s.entryFilter);
  const searchQuery = useUIStore((s) => s.searchQuery);
  const deduplicateEnabled = useUIStore((s) => s.deduplicateEnabled);

  const isSearching = searchQuery.length > 0;
  const hasSelection = !!(selectedFeedId || selectedGroupId);

  const entriesQuery = useEntries({
    feed_id: selectedFeedId || undefined,
    group_id: selectedGroupId || undefined,
    status: entryFilter,
    per_page: 50,
    deduplicate: deduplicateEnabled || undefined,
  });

  const searchResults = useSearchEntries(searchQuery);

  const activeQuery = isSearching ? searchResults : entriesQuery;
  const data = activeQuery.data;
  const isLoading = activeQuery.isLoading;

  useEffect(() => {
    const setEntryIds = useUIStore.getState().setEntryIds;
    if (data?.items) {
      setEntryIds(data.items.map((e) => e.id));
    } else {
      setEntryIds([]);
    }
  }, [data?.items]);

  const showContent = isSearching || hasSelection;

  return (
    <div className="flex h-full flex-col">
      <div className="border-b px-4 py-3">
        <div className="flex items-center justify-between">
          <h2 className="text-sm font-semibold">
            {isSearching ? `Search: ${searchQuery}` : 'Articles'}
          </h2>
          {!isSearching && hasSelection && <EntryFilterBar />}
        </div>
      </div>
      <div className="flex-1 overflow-hidden">
        {!showContent ? (
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
              isSearching
                ? 'no-entries'
                : entryFilter === 'unread'
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
