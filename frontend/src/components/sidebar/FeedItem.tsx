import { MoreHorizontal, Pencil, Trash2, Rss, AlertTriangle, PauseCircle, PlayCircle, Mail, MessageSquare, Play } from 'lucide-react';
import {
  DropdownMenu,
  DropdownMenuTrigger,
  DropdownMenuContent,
  DropdownMenuItem,
} from '@/components/ui/dropdown-menu';
import type { Feed } from '@/types';
import { Badge } from '@/components/ui/badge';
import { cn } from '@/lib/utils';
import { useDeleteFeed, useUpdateFeed } from '@/hooks/queries/use-feeds';

interface FeedItemProps {
  feed: Feed;
  isSelected: boolean;
  onSelect: () => void;
  onEdit?: () => void;
}

export function FeedItem({ feed, isSelected, onSelect, onEdit }: FeedItemProps) {
  const deleteFeed = useDeleteFeed();
  const updateFeed = useUpdateFeed();

  function getFeedIcon(f: Feed) {
    if (f.source_platform === 'reddit') return MessageSquare;
    if (f.source_platform === 'youtube') return Play;
    if (f.feed_type === 'newsletter') return Mail;
    return Rss;
  }

  const FeedIcon = getFeedIcon(feed);

  return (
    <div className="group/feed flex items-center">
      <button
        onClick={onSelect}
        className={cn(
          'flex min-w-0 flex-1 items-center gap-2 rounded-md px-2 py-1.5 text-left text-sm transition-colors',
          'hover:bg-accent hover:text-accent-foreground',
          isSelected && 'bg-accent text-accent-foreground'
        )}
      >
        {feed.favicon_url ? (
          <img
            src={feed.favicon_url}
            alt=""
            className="h-4 w-4 shrink-0 rounded"
            onError={(e) => {
              e.currentTarget.style.display = 'none';
              e.currentTarget.nextElementSibling?.classList.remove('hidden');
            }}
          />
        ) : null}
        <FeedIcon className={cn('h-4 w-4 shrink-0 text-muted-foreground', feed.favicon_url && 'hidden')} />
        <span className={cn('min-w-0 flex-1 truncate', feed.status === 'paused' && 'opacity-60')}>{feed.title}</span>
        {feed.status === 'error' && (
          <span title={`Feed has errors (${feed.error_count} failures)`}><AlertTriangle className="size-3.5 shrink-0 text-orange-500" /></span>
        )}
        {feed.status === 'paused' && (
          <span title="Feed is paused"><PauseCircle className="size-3.5 shrink-0 text-muted-foreground" /></span>
        )}
        {feed.unread_count > 0 && (
          <Badge variant="secondary" className="ml-auto h-5 min-w-5 justify-center px-1 text-xs">
            {feed.unread_count}
          </Badge>
        )}
      </button>
      <DropdownMenu>
        <DropdownMenuTrigger asChild>
          <button className="shrink-0 rounded-md p-1 opacity-0 transition-opacity hover:bg-accent group-hover/feed:opacity-100">
            <MoreHorizontal className="size-3.5" />
          </button>
        </DropdownMenuTrigger>
        <DropdownMenuContent align="start" side="right">
          {onEdit && (
            <DropdownMenuItem onClick={onEdit}>
              <Pencil />
              Edit
            </DropdownMenuItem>
          )}
          <DropdownMenuItem
            onClick={() =>
              updateFeed.mutate({
                feedId: feed.id,
                data: { status: feed.status === 'paused' ? 'active' : 'paused' },
              })
            }
          >
            {feed.status === 'paused' ? <PlayCircle /> : <PauseCircle />}
            {feed.status === 'paused' ? 'Resume' : 'Pause'}
          </DropdownMenuItem>
          <DropdownMenuItem
            variant="destructive"
            onClick={() => deleteFeed.mutate(feed.id)}
          >
            <Trash2 />
            Delete
          </DropdownMenuItem>
        </DropdownMenuContent>
      </DropdownMenu>
    </div>
  );
}
