import { useRef, useEffect } from 'react';
import { useVirtualizer } from '@tanstack/react-virtual';
import { EntryCard } from '@/components/entries/EntryCard';
import { useUIStore } from '@/stores/ui-store';
import type { Entry } from '@/types';

interface EntryListViewProps {
  entries: Entry[];
}

export function EntryListView({ entries }: EntryListViewProps) {
  const parentRef = useRef<HTMLDivElement>(null);
  const selectedEntryId = useUIStore((s) => s.selectedEntryId);

  const virtualizer = useVirtualizer({
    count: entries.length,
    getScrollElement: () => parentRef.current,
    estimateSize: () => 88,
    overscan: 5,
  });

  useEffect(() => {
    if (!selectedEntryId) return;
    const idx = entries.findIndex((e) => e.id === selectedEntryId);
    if (idx >= 0) virtualizer.scrollToIndex(idx, { align: 'auto' });
  }, [selectedEntryId, entries, virtualizer]);

  return (
    <div ref={parentRef} className="h-full overflow-auto">
      <div
        className="relative w-full p-2"
        style={{ height: `${virtualizer.getTotalSize()}px` }}
      >
        {virtualizer.getVirtualItems().map((virtualRow) => (
          <div
            key={virtualRow.key}
            data-index={virtualRow.index}
            ref={virtualizer.measureElement}
            className="absolute left-0 top-0 w-full px-2"
            style={{
              transform: `translateY(${virtualRow.start}px)`,
            }}
          >
            <EntryCard entry={entries[virtualRow.index]} />
          </div>
        ))}
      </div>
    </div>
  );
}
