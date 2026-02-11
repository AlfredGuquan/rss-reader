import { useState, useEffect } from 'react';
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
  const updateFeed = useUpdateFeed();
  const { data: groups } = useGroups();
  const setShortcutsEnabled = useUIStore((s) => s.setShortcutsEnabled);

  useEffect(() => {
    if (open && feed) {
      setTitle(feed.title);
      setGroupId(feed.group_id ?? '');
      setPaused(feed.status === 'paused');
    }
  }, [open, feed]);

  const handleSubmit = async () => {
    if (!feed || !title.trim()) return;
    await updateFeed.mutateAsync({
      feedId: feed.id,
      data: {
        title: title.trim(),
        group_id: groupId || null,
        status: paused ? 'paused' : 'active',
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
