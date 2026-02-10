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
import { useCreateGroup } from '@/hooks/queries/use-groups';
import { useUIStore } from '@/stores/ui-store';

interface CreateGroupDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

export function CreateGroupDialog({ open, onOpenChange }: CreateGroupDialogProps) {
  const [name, setName] = useState('');
  const createGroup = useCreateGroup();
  const setShortcutsEnabled = useUIStore((s) => s.setShortcutsEnabled);

  const handleSubmit = async () => {
    if (!name.trim()) return;
    await createGroup.mutateAsync(name.trim());
    setName('');
    onOpenChange(false);
  };

  const handleOpenChange = (nextOpen: boolean) => {
    setShortcutsEnabled(!nextOpen);
    if (!nextOpen) {
      setName('');
      createGroup.reset();
    }
    onOpenChange(nextOpen);
  };

  return (
    <Dialog open={open} onOpenChange={handleOpenChange}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>Create Group</DialogTitle>
        </DialogHeader>
        <Input
          placeholder="Group name"
          value={name}
          onChange={(e) => setName(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && handleSubmit()}
          disabled={createGroup.isPending}
          autoFocus
        />
        {createGroup.isError && (
          <p className="text-sm text-destructive">{createGroup.error.message}</p>
        )}
        <DialogFooter>
          <Button variant="outline" onClick={() => handleOpenChange(false)} disabled={createGroup.isPending}>
            Cancel
          </Button>
          <Button onClick={handleSubmit} disabled={!name.trim() || createGroup.isPending}>
            {createGroup.isPending ? 'Creating...' : 'Create'}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
