import { useState } from 'react';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { useAddFeed } from '@/hooks/queries/use-feeds';
import { useUIStore } from '@/stores/ui-store';
import { discoverFeeds, type DiscoveredFeed } from '@/api/feeds';
import { Loader2, Rss } from 'lucide-react';

interface AddFeedDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

export function AddFeedDialog({ open, onOpenChange }: AddFeedDialogProps) {
  const setShortcutsEnabled = useUIStore((s) => s.setShortcutsEnabled);
  const [url, setUrl] = useState('');
  const [discoveredFeeds, setDiscoveredFeeds] = useState<DiscoveredFeed[]>([]);
  const [isDiscovering, setIsDiscovering] = useState(false);
  const [discoveryError, setDiscoveryError] = useState<string | null>(null);
  const addFeed = useAddFeed();

  function reset() {
    setUrl('');
    setDiscoveredFeeds([]);
    setIsDiscovering(false);
    setDiscoveryError(null);
    addFeed.reset();
  }

  function looksLikeFeedUrl(testUrl: string): boolean {
    const lower = testUrl.toLowerCase();
    return /\.(xml|rss|atom)(\?|$)/.test(lower)
      || lower.includes('/feed')
      || lower.includes('/rss')
      || lower.includes('/atom');
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    const trimmedUrl = url.trim();
    if (!trimmedUrl) return;

    if (looksLikeFeedUrl(trimmedUrl)) {
      subscribeFeed(trimmedUrl);
      return;
    }

    setIsDiscovering(true);
    setDiscoveryError(null);
    try {
      const result = await discoverFeeds(trimmedUrl);
      if (result.feeds.length === 0) {
        subscribeFeed(trimmedUrl);
      } else if (result.feeds.length === 1) {
        subscribeFeed(result.feeds[0].url);
      } else {
        setDiscoveredFeeds(result.feeds);
      }
    } catch {
      subscribeFeed(trimmedUrl);
    } finally {
      setIsDiscovering(false);
    }
  }

  function subscribeFeed(feedUrl: string) {
    addFeed.mutate(
      { url: feedUrl },
      {
        onSuccess: () => {
          reset();
          onOpenChange(false);
        },
      }
    );
  }

  function handleOpenChange(val: boolean) {
    setShortcutsEnabled(!val);
    if (!val) reset();
    onOpenChange(val);
  }

  const isPending = addFeed.isPending || isDiscovering;

  return (
    <Dialog open={open} onOpenChange={handleOpenChange}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>Add Feed</DialogTitle>
        </DialogHeader>

        {discoveredFeeds.length > 0 ? (
          <div className="space-y-3">
            <p className="text-sm text-muted-foreground">
              Found {discoveredFeeds.length} feeds. Select one to subscribe:
            </p>
            <div className="max-h-60 space-y-1 overflow-y-auto">
              {discoveredFeeds.map((feed) => (
                <button
                  key={feed.url}
                  type="button"
                  className="flex w-full items-center gap-2 rounded-md px-3 py-2 text-left text-sm transition-colors hover:bg-accent"
                  onClick={() => subscribeFeed(feed.url)}
                  disabled={addFeed.isPending}
                >
                  <Rss className="size-4 shrink-0 text-muted-foreground" />
                  <div className="min-w-0 flex-1">
                    <p className="truncate font-medium">{feed.title}</p>
                    <p className="truncate text-xs text-muted-foreground">{feed.url}</p>
                  </div>
                </button>
              ))}
            </div>
            {addFeed.isError && (
              <p className="text-sm text-destructive">{addFeed.error.message}</p>
            )}
            <DialogFooter>
              <Button
                variant="outline"
                onClick={() => setDiscoveredFeeds([])}
                disabled={addFeed.isPending}
              >
                Back
              </Button>
            </DialogFooter>
          </div>
        ) : (
          <form onSubmit={handleSubmit}>
            <div className="py-4">
              <Input
                placeholder="https://example.com or feed URL"
                value={url}
                onChange={(e) => setUrl(e.target.value)}
                disabled={isPending}
                autoFocus
              />
              {addFeed.isError && (
                <p className="mt-2 text-sm text-destructive">
                  {addFeed.error.message}
                </p>
              )}
              {discoveryError && (
                <p className="mt-2 text-sm text-destructive">{discoveryError}</p>
              )}
            </div>
            <DialogFooter>
              <Button
                type="button"
                variant="outline"
                onClick={() => handleOpenChange(false)}
                disabled={isPending}
              >
                Cancel
              </Button>
              <Button type="submit" disabled={!url.trim() || isPending}>
                {isDiscovering ? (
                  <>
                    <Loader2 className="size-4 animate-spin" />
                    Discovering...
                  </>
                ) : addFeed.isPending ? (
                  'Adding...'
                ) : (
                  'Add'
                )}
              </Button>
            </DialogFooter>
          </form>
        )}
      </DialogContent>
    </Dialog>
  );
}
