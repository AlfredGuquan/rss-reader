import { RefreshCw, CheckCheck, Layers } from 'lucide-react';
import { ToggleGroup, ToggleGroupItem } from '@/components/ui/toggle-group';
import { Button } from '@/components/ui/button';
import { useUIStore } from '@/stores/ui-store';
import { useRefreshFeed, useMarkAllRead } from '@/hooks/queries/use-entries';

export function EntryFilterBar() {
  const entryFilter = useUIStore((s) => s.entryFilter);
  const setEntryFilter = useUIStore((s) => s.setEntryFilter);
  const selectedFeedId = useUIStore((s) => s.selectedFeedId);
  const selectedGroupId = useUIStore((s) => s.selectedGroupId);
  const deduplicateEnabled = useUIStore((s) => s.deduplicateEnabled);
  const setDeduplicateEnabled = useUIStore((s) => s.setDeduplicateEnabled);
  const refreshFeed = useRefreshFeed();
  const markAllRead = useMarkAllRead();

  return (
    <div className="flex items-center gap-1">
      <ToggleGroup
        type="single"
        size="sm"
        variant="outline"
        value={entryFilter}
        onValueChange={(value) => {
          if (value) setEntryFilter(value as 'all' | 'unread' | 'starred');
        }}
      >
        <ToggleGroupItem value="all" className="text-xs px-2 h-7">
          All
        </ToggleGroupItem>
        <ToggleGroupItem value="unread" className="text-xs px-2 h-7">
          Unread
        </ToggleGroupItem>
        <ToggleGroupItem value="starred" className="text-xs px-2 h-7">
          Starred
        </ToggleGroupItem>
      </ToggleGroup>
      <Button
        variant={deduplicateEnabled ? 'secondary' : 'ghost'}
        size="icon-xs"
        title="Deduplicate articles"
        onClick={() => setDeduplicateEnabled(!deduplicateEnabled)}
      >
        <Layers />
      </Button>
      <Button
        variant="ghost"
        size="icon-xs"
        onClick={() => {
          if (selectedFeedId) refreshFeed.mutate(selectedFeedId);
        }}
        disabled={refreshFeed.isPending}
        title="Refresh feed"
      >
        <RefreshCw className={refreshFeed.isPending ? 'animate-spin' : ''} />
      </Button>
      <Button
        variant="ghost"
        size="icon-xs"
        title="Mark all as read"
        disabled={markAllRead.isPending || (!selectedFeedId && !selectedGroupId)}
        onClick={() => {
          const params: { feed_id?: string; group_id?: string } = {};
          if (selectedFeedId) params.feed_id = selectedFeedId;
          if (selectedGroupId) params.group_id = selectedGroupId;
          markAllRead.mutate(params);
        }}
      >
        <CheckCheck />
      </Button>
    </div>
  );
}
