import { Inbox, CheckCircle, Star, Rss } from 'lucide-react';

type EmptyType = 'no-feed' | 'no-entries' | 'all-read' | 'no-starred';

interface EntryListEmptyProps {
  type: EmptyType;
}

const emptyConfig: Record<EmptyType, { icon: typeof Inbox; message: string }> = {
  'no-feed': { icon: Rss, message: 'Select a feed to view articles.' },
  'no-entries': { icon: Inbox, message: 'No articles yet. Try refreshing the feed.' },
  'all-read': { icon: CheckCircle, message: 'All caught up!' },
  'no-starred': { icon: Star, message: 'No starred articles.' },
};

export function EntryListEmpty({ type }: EntryListEmptyProps) {
  const config = emptyConfig[type];
  const Icon = config.icon;

  return (
    <div className="flex h-full flex-col items-center justify-center gap-3 p-6">
      <Icon className="size-8 text-muted-foreground/50" />
      <p className="text-sm text-muted-foreground">{config.message}</p>
    </div>
  );
}
