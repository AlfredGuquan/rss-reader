import dayjs from 'dayjs';
import relativeTime from 'dayjs/plugin/relativeTime';
import { ArticleContent } from './ArticleContent';
import { Badge } from '@/components/ui/badge';
import type { Entry } from '@/types';

dayjs.extend(relativeTime);

interface ArticleViewProps {
  entry: Entry;
}

export function ArticleView({ entry }: ArticleViewProps) {
  const displayContent = entry.content || entry.summary || '';

  return (
    <article className="px-6 py-4">
      <h1 className="text-xl font-bold leading-tight">{entry.title}</h1>
      <div className="mt-2 flex items-center gap-2 text-sm text-muted-foreground">
        {entry.feed_title && <span>{entry.feed_title}</span>}
        {entry.author && (
          <>
            <span>·</span>
            <span>{entry.author}</span>
          </>
        )}
        <span>·</span>
        <time>{dayjs(entry.published_at).format('YYYY-MM-DD HH:mm')}</time>
        {!entry.content && entry.summary && (
          <Badge variant="outline" className="ml-2 text-xs">
            Summary only
          </Badge>
        )}
      </div>
      <div className="mt-6">
        <ArticleContent content={displayContent} />
      </div>
      <div className="mt-8 border-t pt-4">
        <a
          href={entry.url}
          target="_blank"
          rel="noopener noreferrer"
          className="text-sm text-blue-600 hover:underline dark:text-blue-400"
        >
          Read original article →
        </a>
      </div>
    </article>
  );
}
