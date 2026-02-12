import { useState, useEffect } from 'react';
import { ChevronRight } from 'lucide-react';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Switch } from '@/components/ui/switch';
import { useUpdateFeed } from '@/hooks/queries/use-feeds';
import { useGroups } from '@/hooks/queries/use-groups';
import { useUIStore } from '@/stores/ui-store';
import { cn } from '@/lib/utils';
import type { Feed } from '@/types';

interface EditFeedDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  feed: Feed | null;
}

export function EditFeedDialog({ open, onOpenChange, feed }: EditFeedDialogProps) {
  const [title, setTitle] = useState('');
  const [groupId, setGroupId] = useState<string>('');
  const [paused, setPaused] = useState(false);
  const [cssSelector, setCssSelector] = useState('');
  const [cssRemove, setCssRemove] = useState('');
  const [extractionMode, setExtractionMode] = useState<'default' | 'precision' | 'recall'>('default');
  const [showAdvanced, setShowAdvanced] = useState(false);
  const updateFeed = useUpdateFeed();
  const { data: groups } = useGroups();
  const setShortcutsEnabled = useUIStore((s) => s.setShortcutsEnabled);

  useEffect(() => {
    if (open && feed) {
      setTitle(feed.title);
      setGroupId(feed.group_id ?? '');
      setPaused(feed.status === 'paused');
      const config = feed.fulltext_config;
      setCssSelector(config?.css_selector ?? '');
      setCssRemove(config?.css_remove ?? '');
      setExtractionMode(config?.extraction_mode ?? 'default');
      setShowAdvanced(
        !!config?.css_selector ||
        !!config?.css_remove ||
        (!!config?.extraction_mode && config.extraction_mode !== 'default')
      );
    }
  }, [open, feed]);

  const handleSubmit = async () => {
    if (!feed || !title.trim()) return;

    let fulltextConfig: Feed['fulltext_config'] = null;
    if (cssSelector || cssRemove || extractionMode !== 'default') {
      const config: Record<string, string> = {};
      if (cssSelector) config.css_selector = cssSelector;
      if (cssRemove) config.css_remove = cssRemove;
      if (extractionMode !== 'default') config.extraction_mode = extractionMode;
      fulltextConfig = config;
    }

    await updateFeed.mutateAsync({
      feedId: feed.id,
      data: {
        title: title.trim(),
        group_id: groupId || null,
        status: paused ? 'paused' : 'active',
        fulltext_config: fulltextConfig,
      },
    });
    onOpenChange(false);
  };

  const handleOpenChange = (nextOpen: boolean) => {
    setShortcutsEnabled(!nextOpen);
    if (!nextOpen) {
      setTitle('');
      setGroupId('');
      setPaused(false);
      setCssSelector('');
      setCssRemove('');
      setExtractionMode('default');
      setShowAdvanced(false);
      updateFeed.reset();
    }
    onOpenChange(nextOpen);
  };

  return (
    <Dialog open={open} onOpenChange={handleOpenChange}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>Edit Feed</DialogTitle>
        </DialogHeader>
        <div className="space-y-4">
          <div className="space-y-2">
            <label htmlFor="feed-title" className="text-sm font-medium">
              Title
            </label>
            <Input
              id="feed-title"
              placeholder="Feed title"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleSubmit()}
              disabled={updateFeed.isPending}
              autoFocus
            />
          </div>
          <div className="space-y-2">
            <label htmlFor="feed-group" className="text-sm font-medium">
              Group
            </label>
            <select
              id="feed-group"
              value={groupId}
              onChange={(e) => setGroupId(e.target.value)}
              disabled={updateFeed.isPending}
              className="border-input bg-background flex h-9 w-full rounded-md border px-3 py-1 text-sm shadow-xs transition-colors focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring"
            >
              <option value="">No group</option>
              {groups?.map((group) => (
                <option key={group.id} value={group.id}>
                  {group.name}
                </option>
              ))}
            </select>
          </div>
          <div className="flex items-center justify-between">
            <label htmlFor="feed-paused" className="text-sm font-medium">
              Pause feed
            </label>
            <Switch
              id="feed-paused"
              checked={paused}
              onCheckedChange={setPaused}
              disabled={updateFeed.isPending}
            />
          </div>
          <div className="space-y-2">
            <button
              type="button"
              onClick={() => setShowAdvanced(!showAdvanced)}
              className="flex items-center gap-1 text-sm font-medium text-muted-foreground hover:text-foreground transition-colors"
            >
              <ChevronRight className={cn('size-4 transition-transform', showAdvanced && 'rotate-90')} />
              Full-text Extraction
            </button>
            {showAdvanced && (
              <div className="space-y-3 pl-5">
                <div className="space-y-1">
                  <label className="text-xs text-muted-foreground">CSS Selector</label>
                  <Input
                    placeholder="article.content, .post-body"
                    value={cssSelector}
                    onChange={(e) => setCssSelector(e.target.value)}
                    disabled={updateFeed.isPending}
                    className="h-8 text-xs"
                  />
                </div>
                <div className="space-y-1">
                  <label className="text-xs text-muted-foreground">Exclude Selectors</label>
                  <Input
                    placeholder=".ads, .sidebar, .related"
                    value={cssRemove}
                    onChange={(e) => setCssRemove(e.target.value)}
                    disabled={updateFeed.isPending}
                    className="h-8 text-xs"
                  />
                </div>
                <div className="space-y-1">
                  <label className="text-xs text-muted-foreground">Extraction Mode</label>
                  <select
                    value={extractionMode}
                    onChange={(e) => setExtractionMode(e.target.value as 'default' | 'precision' | 'recall')}
                    disabled={updateFeed.isPending}
                    className="border-input bg-background flex h-8 w-full rounded-md border px-2 text-xs shadow-xs transition-colors focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring"
                  >
                    <option value="default">Default</option>
                    <option value="precision">Precision (less noise)</option>
                    <option value="recall">Recall (more content)</option>
                  </select>
                </div>
              </div>
            )}
          </div>
          {updateFeed.isError && (
            <p className="text-sm text-destructive">{updateFeed.error.message}</p>
          )}
        </div>
        <DialogFooter>
          <Button variant="outline" onClick={() => handleOpenChange(false)} disabled={updateFeed.isPending}>
            Cancel
          </Button>
          <Button onClick={handleSubmit} disabled={!title.trim() || updateFeed.isPending}>
            {updateFeed.isPending ? 'Saving...' : 'Save'}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
