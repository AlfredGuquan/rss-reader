import { useState, useMemo, useCallback } from 'react';
import {
  DndContext,
  closestCenter,
  KeyboardSensor,
  PointerSensor,
  useSensor,
  useSensors,
  type DragEndEvent,
} from '@dnd-kit/core';
import {
  SortableContext,
  verticalListSortingStrategy,
  arrayMove,
} from '@dnd-kit/sortable';
import { ScrollArea } from '@/components/ui/scroll-area';
import { FeedItem } from '@/components/sidebar/FeedItem';
import { GroupItem } from '@/components/sidebar/GroupItem';
import { SidebarFooter } from '@/components/sidebar/SidebarFooter';
import { EditFeedDialog } from '@/components/feed-management/EditFeedDialog';
import { ThemeToggle } from '@/components/theme/ThemeToggle';
import { useFeeds } from '@/hooks/queries/use-feeds';
import { useGroups, useReorderGroups } from '@/hooks/queries/use-groups';
import { useUIStore } from '@/stores/ui-store';
import { Skeleton } from '@/components/ui/skeleton';
import { Separator } from '@/components/ui/separator';
import type { Feed } from '@/types';

export function Sidebar() {
  const { data: feeds, isLoading: feedsLoading } = useFeeds();
  const { data: groups, isLoading: groupsLoading } = useGroups();
  const selectedFeedId = useUIStore((s) => s.selectedFeedId);
  const setSelectedFeed = useUIStore((s) => s.setSelectedFeed);
  const reorderGroups = useReorderGroups();

  const [editingFeed, setEditingFeed] = useState<Feed | null>(null);

  const isLoading = feedsLoading || groupsLoading;

  const { groupedFeeds, ungroupedFeeds } = useMemo(() => {
    if (!feeds) return { groupedFeeds: new Map<string, Feed[]>(), ungroupedFeeds: [] };

    const grouped = new Map<string, Feed[]>();
    const ungrouped: Feed[] = [];

    for (const feed of feeds) {
      if (feed.group_id) {
        const existing = grouped.get(feed.group_id) ?? [];
        existing.push(feed);
        grouped.set(feed.group_id, existing);
      } else {
        ungrouped.push(feed);
      }
    }

    return { groupedFeeds: grouped, ungroupedFeeds: ungrouped };
  }, [feeds]);

  const sortedGroups = useMemo(() => {
    if (!groups) return [];
    return [...groups].sort((a, b) => a.sort_order - b.sort_order);
  }, [groups]);

  const groupIds = useMemo(() => sortedGroups.map((g) => g.id), [sortedGroups]);

  const sensors = useSensors(
    useSensor(PointerSensor, { activationConstraint: { distance: 5 } }),
    useSensor(KeyboardSensor)
  );

  const handleDragEnd = useCallback(
    (event: DragEndEvent) => {
      const { active, over } = event;
      if (!over || active.id === over.id) return;

      const oldIndex = groupIds.indexOf(String(active.id));
      const newIndex = groupIds.indexOf(String(over.id));
      if (oldIndex === -1 || newIndex === -1) return;

      const newOrder = arrayMove(groupIds, oldIndex, newIndex);
      reorderGroups.mutate(newOrder);
    },
    [groupIds, reorderGroups]
  );

  const hasContent = (groups && groups.length > 0) || (feeds && feeds.length > 0);

  return (
    <div className="flex h-full flex-col">
      <div className="flex items-center justify-between border-b px-4 py-3">
        <h1 className="text-sm font-semibold">Feeds</h1>
        <ThemeToggle />
      </div>
      <ScrollArea className="flex-1">
        <div className="p-2">
          {isLoading && (
            <div className="space-y-2 p-2">
              {Array.from({ length: 5 }).map((_, i) => (
                <Skeleton key={i} className="h-8 w-full" />
              ))}
            </div>
          )}

          {!isLoading && sortedGroups.length > 0 && (
            <DndContext
              sensors={sensors}
              collisionDetection={closestCenter}
              onDragEnd={handleDragEnd}
            >
              <SortableContext items={groupIds} strategy={verticalListSortingStrategy}>
                {sortedGroups.map((group) => (
                  <GroupItem
                    key={group.id}
                    group={group}
                    feeds={groupedFeeds.get(group.id) ?? []}
                    onEditFeed={setEditingFeed}
                  />
                ))}
              </SortableContext>
            </DndContext>
          )}

          {!isLoading && sortedGroups.length > 0 && ungroupedFeeds.length > 0 && (
            <Separator className="my-2" />
          )}

          {!isLoading && ungroupedFeeds.map((feed) => (
            <FeedItem
              key={feed.id}
              feed={feed}
              isSelected={feed.id === selectedFeedId}
              onSelect={() => setSelectedFeed(feed.id)}
              onEdit={() => setEditingFeed(feed)}
            />
          ))}

          {!isLoading && !hasContent && (
            <p className="p-4 text-center text-sm text-muted-foreground">
              No feeds yet. Add one below.
            </p>
          )}
        </div>
      </ScrollArea>
      <SidebarFooter />

      <EditFeedDialog
        open={editingFeed !== null}
        onOpenChange={(open) => { if (!open) setEditingFeed(null); }}
        feed={editingFeed}
      />
    </div>
  );
}
