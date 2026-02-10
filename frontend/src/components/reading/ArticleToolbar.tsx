import { Star, Eye, EyeOff, ExternalLink } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Separator } from '@/components/ui/separator';
import { cn } from '@/lib/utils';
import type { Entry } from '@/types';

interface ArticleToolbarProps {
  entry: Entry;
  onToggleStar: () => void;
  onToggleRead: () => void;
}

export function ArticleToolbar({ entry, onToggleStar, onToggleRead }: ArticleToolbarProps) {
  return (
    <div className="flex items-center gap-1 border-b px-4 py-2">
      <Button variant="ghost" size="sm" onClick={onToggleStar} title={entry.is_starred ? 'Unstar' : 'Star'}>
        <Star className={cn('size-4', entry.is_starred && 'fill-yellow-400 text-yellow-400')} />
      </Button>
      <Button variant="ghost" size="sm" onClick={onToggleRead} title={entry.is_read ? 'Mark unread' : 'Mark read'}>
        {entry.is_read ? <EyeOff className="size-4" /> : <Eye className="size-4" />}
      </Button>
      <Separator orientation="vertical" className="mx-1 h-5" />
      <Button variant="ghost" size="sm" asChild>
        <a href={entry.url} target="_blank" rel="noopener noreferrer">
          <ExternalLink className="size-4" />
          <span className="ml-1">Original</span>
        </a>
      </Button>
    </div>
  );
}
