import {
  AlertDialog,
  AlertDialogContent,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogCancel,
  AlertDialogAction,
} from '@/components/ui/alert-dialog';
import { useDeleteGroup } from '@/hooks/queries/use-groups';
import { useUIStore } from '@/stores/ui-store';
import type { Group } from '@/types';

interface DeleteGroupDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  group: Group | null;
}

export function DeleteGroupDialog({ open, onOpenChange, group }: DeleteGroupDialogProps) {
  const deleteGroup = useDeleteGroup();
  const setShortcutsEnabled = useUIStore((s) => s.setShortcutsEnabled);

  const handleDelete = async () => {
    if (!group) return;
    await deleteGroup.mutateAsync(group.id);
    onOpenChange(false);
  };

  return (
    <AlertDialog open={open} onOpenChange={(val) => { setShortcutsEnabled(!val); onOpenChange(val); }}>
      <AlertDialogContent>
        <AlertDialogHeader>
          <AlertDialogTitle>Delete Group</AlertDialogTitle>
          <AlertDialogDescription>
            Are you sure you want to delete &quot;{group?.name}&quot;? Feeds in this group will
            become ungrouped. This action cannot be undone.
          </AlertDialogDescription>
        </AlertDialogHeader>
        <AlertDialogFooter>
          <AlertDialogCancel>Cancel</AlertDialogCancel>
          <AlertDialogAction variant="destructive" onClick={handleDelete}>
            {deleteGroup.isPending ? 'Deleting...' : 'Delete'}
          </AlertDialogAction>
        </AlertDialogFooter>
      </AlertDialogContent>
    </AlertDialog>
  );
}
