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
import { useUpdateGroup } from '@/hooks/queries/use-groups';
import { useUIStore } from '@/stores/ui-store';
import type { Group } from '@/types';

interface RenameGroupDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  group: Group | null;
}

export function RenameGroupDialog({ open, onOpenChange, group }: RenameGroupDialogProps) {
  const [name, setName] = useState('');
  const updateGroup = useUpdateGroup();
  const setShortcutsEnabled = useUIStore((s) => s.setShortcutsEnabled);

  useEffect(() => {
    if (open && group) {
      setName(group.name);
    }
  }, [open, group]);

  const handleSubmit = async () => {
    if (!name.trim() || !group) return;
    await updateGroup.mutateAsync({ groupId: group.id, name: name.trim() });
    onOpenChange(false);
  };

  const handleOpenChange = (nextOpen: boolean) => {
    setShortcutsEnabled(!nextOpen);
    if (!nextOpen) {
      setName('');
      updateGroup.reset();
    }
    onOpenChange(nextOpen);
  };

  return (
    <Dialog open={open} onOpenChange={handleOpenChange}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>Rename Group</DialogTitle>
        </DialogHeader>
        <Input
          placeholder="Group name"
          value={name}
          onChange={(e) => setName(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && handleSubmit()}
          disabled={updateGroup.isPending}
          autoFocus
        />
        {updateGroup.isError && (
          <p className="text-sm text-destructive">{updateGroup.error.message}</p>
        )}
        <DialogFooter>
          <Button variant="outline" onClick={() => handleOpenChange(false)} disabled={updateGroup.isPending}>
            Cancel
          </Button>
          <Button onClick={handleSubmit} disabled={!name.trim() || updateGroup.isPending}>
            {updateGroup.isPending ? 'Saving...' : 'Save'}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
