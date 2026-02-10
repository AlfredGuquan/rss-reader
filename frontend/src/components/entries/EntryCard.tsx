import dayjs from 'dayjs';
import relativeTime from 'dayjs/plugin/relativeTime';
import { Star } from 'lucide-react';
import { cn } from '@/lib/utils';
import { useUIStore } from '@/stores/ui-store';
import type { Entry } from '@/types';

dayjs.extend(relativeTime);

function stripHtml(html: string): string {
  const doc = new DOMParser().parseFromString(html, 'text/html');
  return doc.body.textContent || '';
}

interface EntryCardProps {
  entry: Entry;
}

export function EntryCard({ entry }: EntryCardProps) {
  const selectedEntryId = useUIStore((s) => s.selectedEntryId);
  const setSelectedEntry = useUIStore((s) => s.setSelectedEntry);
  const isSelected = selectedEntryId === entry.id;

  return (
    <button
      type="button"
      className={cn(
        'flex w-full gap-3 rounded-md px-3 py-2.5 text-left transition-colors hover:bg-accent/50',
        isSelected && 'bg-accent',
      )}
      onClick={() => setSelectedEntry(entry.id)}
    >
      <div className="mt-2 flex shrink-0 items-start">
        {!entry.is_read ? (
          <span className="size-2 rounded-full bg-blue-500" />
        ) : (
          <span className="size-2" />
        )}
      </div>

      <div className="min-w-0 flex-1">
        <p className="line-clamp-2 text-sm font-medium leading-snug">
          {entry.title}
        </p>
        <div className="mt-1 flex items-center gap-1.5 text-xs text-muted-foreground">
          {entry.feed_title && (
            <>
              <span className="truncate">{entry.feed_title}</span>
              <span>·</span>
            </>
          )}
          <span className="shrink-0">{dayjs(entry.published_at).fromNow()}</span>
        </div>
        {entry.summary && (
          <p className="mt-1 line-clamp-2 text-xs text-muted-foreground">
            {stripHtml(entry.summary)}
          </p>
        )}
      </div>

      {entry.is_starred && (
        <div className="mt-1 shrink-0">
          <Star className="size-3.5 fill-yellow-400 text-yellow-400" />
        </div>
      )}
    </button>
  );
}
