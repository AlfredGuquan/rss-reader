import { useState } from 'react';
import dayjs from 'dayjs';
import relativeTime from 'dayjs/plugin/relativeTime';
import { Star, Layers } from 'lucide-react';
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
  const [sourcesExpanded, setSourcesExpanded] = useState(false);

  const hasDuplicates = entry.duplicate_count > 0;

  return (
    <div>
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
            {hasDuplicates && (
              <>
                <span>·</span>
                <button
                  type="button"
                  className="inline-flex shrink-0 items-center gap-0.5 rounded-full bg-muted px-1.5 py-0.5 text-[10px] font-medium text-muted-foreground transition-colors hover:bg-muted-foreground/20"
                  onClick={(e) => {
                    e.stopPropagation();
                    setSourcesExpanded(!sourcesExpanded);
                  }}
                >
                  <Layers className="size-2.5" />
                  {entry.duplicate_count + 1} sources
                </button>
              </>
            )}
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

      {hasDuplicates && sourcesExpanded && entry.duplicate_sources && (
        <div className="ml-8 mr-3 mb-1 rounded-md border bg-muted/30 px-3 py-2">
          <p className="mb-1.5 text-[10px] font-medium uppercase tracking-wide text-muted-foreground">
            Also reported by
          </p>
          <div className="space-y-1">
            {entry.duplicate_sources.map((source, index) => (
              <div key={index} className="flex items-center gap-2 text-xs text-muted-foreground">
                {source.feed_favicon_url ? (
                  <img
                    src={source.feed_favicon_url}
                    alt=""
                    className="size-3.5 shrink-0 rounded-sm"
                  />
                ) : (
                  <span className="size-3.5 shrink-0 rounded-sm bg-muted" />
                )}
                <span className="truncate">{source.feed_title || 'Unknown'}</span>
                <span className="shrink-0 text-[10px]">
                  {dayjs(source.published_at).fromNow()}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
