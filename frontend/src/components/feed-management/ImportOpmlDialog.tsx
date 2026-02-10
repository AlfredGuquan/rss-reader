import { useState, useRef } from 'react';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { useImportOpml } from '@/hooks/queries/use-feeds';
import { useUIStore } from '@/stores/ui-store';

interface ImportOpmlDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

export function ImportOpmlDialog({ open, onOpenChange }: ImportOpmlDialogProps) {
  const setShortcutsEnabled = useUIStore((s) => s.setShortcutsEnabled);
  const fileRef = useRef<HTMLInputElement>(null);
  const [result, setResult] = useState<{
    added: number;
    skipped: number;
    failed: number;
  } | null>(null);
  const importOpml = useImportOpml();

  const handleImport = async () => {
    const file = fileRef.current?.files?.[0];
    if (!file) return;
    const response = await importOpml.mutateAsync(file);
    setResult(response);
  };

  const handleClose = () => {
    setShortcutsEnabled(true);
    setResult(null);
    importOpml.reset();
    if (fileRef.current) {
      fileRef.current.value = '';
    }
    onOpenChange(false);
  };

  return (
    <Dialog open={open} onOpenChange={(val) => { setShortcutsEnabled(!val); if (!val) handleClose(); else onOpenChange(val); }}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>Import OPML</DialogTitle>
        </DialogHeader>
        {result ? (
          <div className="space-y-2 text-sm">
            <p>Import complete:</p>
            <p>Added: {result.added} feeds</p>
            <p>Skipped (duplicates): {result.skipped}</p>
            {result.failed > 0 && (
              <p className="text-destructive">Failed: {result.failed}</p>
            )}
          </div>
        ) : (
          <div className="space-y-2">
            <input
              ref={fileRef}
              type="file"
              accept=".opml,.xml"
              className="text-sm"
            />
            {importOpml.isError && (
              <p className="text-sm text-destructive">
                {importOpml.error.message}
              </p>
            )}
          </div>
        )}
        <DialogFooter>
          {result ? (
            <Button onClick={handleClose}>Done</Button>
          ) : (
            <>
              <Button variant="outline" onClick={handleClose} disabled={importOpml.isPending}>
                Cancel
              </Button>
              <Button onClick={handleImport} disabled={importOpml.isPending}>
                {importOpml.isPending ? 'Importing...' : 'Import'}
              </Button>
            </>
          )}
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
