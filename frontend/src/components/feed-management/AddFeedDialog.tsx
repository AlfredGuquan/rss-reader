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

interface AddFeedDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

export function AddFeedDialog({ open, onOpenChange }: AddFeedDialogProps) {
  const setShortcutsEnabled = useUIStore((s) => s.setShortcutsEnabled);
  const [url, setUrl] = useState('');
  const addFeed = useAddFeed();

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    const trimmedUrl = url.trim();
    if (!trimmedUrl) return;

    addFeed.mutate(
      { url: trimmedUrl },
      {
        onSuccess: () => {
          setUrl('');
          onOpenChange(false);
        },
      }
    );
  }

  return (
    <Dialog open={open} onOpenChange={(val) => { setShortcutsEnabled(!val); onOpenChange(val); }}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>Add Feed</DialogTitle>
        </DialogHeader>
        <form onSubmit={handleSubmit}>
          <div className="py-4">
            <Input
              placeholder="https://example.com/feed.xml"
              value={url}
              onChange={(e) => setUrl(e.target.value)}
              disabled={addFeed.isPending}
              autoFocus
            />
            {addFeed.isError && (
              <p className="mt-2 text-sm text-destructive">
                {addFeed.error.message}
              </p>
            )}
          </div>
          <DialogFooter>
            <Button
              type="button"
              variant="outline"
              onClick={() => onOpenChange(false)}
              disabled={addFeed.isPending}
            >
              Cancel
            </Button>
            <Button type="submit" disabled={!url.trim() || addFeed.isPending}>
              {addFeed.isPending ? 'Adding...' : 'Add'}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
