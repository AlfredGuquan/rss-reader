import { useState } from 'react';
import { ChevronRight, MoreHorizontal, Pencil, Trash2, GripVertical } from 'lucide-react';
import { useSortable } from '@dnd-kit/sortable';
import { CSS } from '@dnd-kit/utilities';
import {
  Collapsible,
  CollapsibleTrigger,
  CollapsibleContent,
} from '@/components/ui/collapsible';
import {
  DropdownMenu,
  DropdownMenuTrigger,
  DropdownMenuContent,
  DropdownMenuItem,
} from '@/components/ui/dropdown-menu';
import { cn } from '@/lib/utils';
import { Badge } from '@/components/ui/badge';
import { FeedItem } from './FeedItem';
import { RenameGroupDialog } from '@/components/group-management/RenameGroupDialog';
import { DeleteGroupDialog } from '@/components/group-management/DeleteGroupDialog';
import { useUIStore } from '@/stores/ui-store';
import type { Feed, Group } from '@/types';

interface GroupItemProps {
  group: Group;
  feeds: Feed[];
  onEditFeed: (feed: Feed) => void;
}

export function GroupItem({ group, feeds, onEditFeed }: GroupItemProps) {
  const expandedGroupIds = useUIStore((s) => s.expandedGroupIds);
  const toggleGroupExpanded = useUIStore((s) => s.toggleGroupExpanded);
  const selectedGroupId = useUIStore((s) => s.selectedGroupId);
  const selectedFeedId = useUIStore((s) => s.selectedFeedId);
  const setSelectedGroup = useUIStore((s) => s.setSelectedGroup);
  const setSelectedFeed = useUIStore((s) => s.setSelectedFeed);

  const [renameOpen, setRenameOpen] = useState(false);
  const [deleteOpen, setDeleteOpen] = useState(false);

  const {
    attributes,
    listeners,
    setNodeRef,
    transform,
    transition,
    isDragging,
  } = useSortable({ id: group.id });

  const style = {
    transform: CSS.Transform.toString(transform),
    transition,
  };

  const isExpanded = expandedGroupIds.has(group.id);
  const isGroupSelected = selectedGroupId === group.id && selectedFeedId === null;
  const totalUnread = feeds.reduce((sum, feed) => sum + feed.unread_count, 0);

  const handleGroupClick = () => {
    setSelectedGroup(group.id);
    if (!isExpanded) {
      toggleGroupExpanded(group.id);
    }
  };

  return (
    <>
      <div ref={setNodeRef} style={style} className={cn(isDragging && 'opacity-50')}>
        <Collapsible open={isExpanded} onOpenChange={() => toggleGroupExpanded(group.id)}>
          <div className="group/group flex items-center">
            <button
              className="shrink-0 cursor-grab rounded-md p-1 opacity-0 transition-opacity hover:bg-accent group-hover/group:opacity-100 active:cursor-grabbing"
              {...attributes}
              {...listeners}
            >
              <GripVertical className="size-3.5 text-muted-foreground" />
            </button>
            <CollapsibleTrigger asChild>
              <button
                className="shrink-0 rounded-md p-1 hover:bg-accent"
                onClick={(e) => {
                  e.stopPropagation();
                }}
              >
                <ChevronRight
                  className={cn(
                    'size-3.5 transition-transform',
                    isExpanded && 'rotate-90'
                  )}
                />
              </button>
            </CollapsibleTrigger>
            <button
              onClick={handleGroupClick}
              className={cn(
                'flex min-w-0 flex-1 items-center gap-1.5 rounded-md px-1.5 py-1.5 text-sm transition-colors',
                'hover:bg-accent hover:text-accent-foreground',
                isGroupSelected && 'bg-accent text-accent-foreground'
              )}
            >
              <span className="min-w-0 flex-1 truncate text-left font-medium">
                {group.name}
              </span>
              {totalUnread > 0 && (
                <Badge
                  variant="secondary"
                  className="h-5 min-w-5 justify-center px-1 text-xs"
                >
                  {totalUnread}
                </Badge>
              )}
            </button>
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <button className="shrink-0 rounded-md p-1 opacity-0 transition-opacity hover:bg-accent group-hover/group:opacity-100">
                  <MoreHorizontal className="size-3.5" />
                </button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="start" side="right">
                <DropdownMenuItem onClick={() => setRenameOpen(true)}>
                  <Pencil />
                  Rename
                </DropdownMenuItem>
                <DropdownMenuItem variant="destructive" onClick={() => setDeleteOpen(true)}>
                  <Trash2 />
                  Delete
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          </div>
          <CollapsibleContent>
            <div className="ml-3 border-l pl-1">
              {feeds.map((feed) => (
                <FeedItem
                  key={feed.id}
                  feed={feed}
                  isSelected={feed.id === selectedFeedId}
                  onSelect={() => setSelectedFeed(feed.id)}
                  onEdit={() => onEditFeed(feed)}
                />
              ))}
            </div>
          </CollapsibleContent>
        </Collapsible>
      </div>

      <RenameGroupDialog open={renameOpen} onOpenChange={setRenameOpen} group={group} />
      <DeleteGroupDialog open={deleteOpen} onOpenChange={setDeleteOpen} group={group} />
    </>
  );
}
