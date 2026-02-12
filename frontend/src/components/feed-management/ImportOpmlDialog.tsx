import { useState, useRef } from 'react';
import { ChevronRight } from 'lucide-react';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import {
  Collapsible,
  CollapsibleTrigger,
  CollapsibleContent,
} from '@/components/ui/collapsible';
import { useImportOpml, usePreviewOpml } from '@/hooks/queries/use-feeds';
import { useUIStore } from '@/stores/ui-store';
import type { OpmlPreviewResult, OpmlPreviewFeed } from '@/api/feeds';

interface ImportOpmlDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

type DialogState = 'select' | 'preview' | 'result';

function groupFeedsByGroup(feeds: OpmlPreviewFeed[]): Map<string, OpmlPreviewFeed[]> {
  const grouped = new Map<string, OpmlPreviewFeed[]>();
  for (const feed of feeds) {
    const groupName = feed.group ?? 'Ungrouped';
    const existing = grouped.get(groupName);
    if (existing) {
      existing.push(feed);
    } else {
      grouped.set(groupName, [feed]);
    }
  }
  return grouped;
}

export function ImportOpmlDialog({ open, onOpenChange }: ImportOpmlDialogProps) {
  const setShortcutsEnabled = useUIStore((s) => s.setShortcutsEnabled);
  const fileRef = useRef<HTMLInputElement>(null);
  const [dialogState, setDialogState] = useState<DialogState>('select');
  const [previewData, setPreviewData] = useState<OpmlPreviewResult | null>(null);
  const [result, setResult] = useState<{
    added: number;
    skipped: number;
    failed: number;
  } | null>(null);

  const previewOpml = usePreviewOpml();
  const importOpml = useImportOpml();

  const handlePreview = async () => {
    const file = fileRef.current?.files?.[0];
    if (!file) return;
    const data = await previewOpml.mutateAsync(file);
    setPreviewData(data);
    setDialogState('preview');
  };

  const handleImport = async () => {
    const file = fileRef.current?.files?.[0];
    if (!file) return;
    const response = await importOpml.mutateAsync(file);
    setResult(response);
    setDialogState('result');
  };

  const handleClose = () => {
    setShortcutsEnabled(true);
    setDialogState('select');
    setPreviewData(null);
    setResult(null);
    previewOpml.reset();
    importOpml.reset();
    if (fileRef.current) {
      fileRef.current.value = '';
    }
    onOpenChange(false);
  };

  const handleBack = () => {
    setDialogState('select');
    setPreviewData(null);
    previewOpml.reset();
  };

  const groupedFeeds = previewData ? groupFeedsByGroup(previewData.feeds) : null;

  return (
    <Dialog open={open} onOpenChange={(val) => { setShortcutsEnabled(!val); if (!val) handleClose(); else onOpenChange(val); }}>
      <DialogContent className={dialogState === 'preview' ? 'sm:max-w-lg' : 'sm:max-w-md'}>
        <DialogHeader>
          <DialogTitle>Import OPML</DialogTitle>
        </DialogHeader>

        {dialogState === 'select' && (
          <div className="space-y-2">
            <input
              ref={fileRef}
              type="file"
              accept=".opml,.xml"
              className="text-sm"
            />
            {previewOpml.isError && (
              <p className="text-sm text-destructive">
                {previewOpml.error.message}
              </p>
            )}
          </div>
        )}

        {dialogState === 'preview' && previewData && (
          <div className="space-y-3">
            <p className="text-sm text-muted-foreground">
              {previewData.summary.new} new feeds, {previewData.summary.duplicate} duplicates
            </p>
            <div className="max-h-64 overflow-y-auto space-y-1">
              {groupedFeeds && Array.from(groupedFeeds.entries()).map(([groupName, feeds]) => (
                <FeedGroup key={groupName} groupName={groupName} feeds={feeds} />
              ))}
            </div>
            {importOpml.isError && (
              <p className="text-sm text-destructive">
                {importOpml.error.message}
              </p>
            )}
          </div>
        )}

        {dialogState === 'result' && result && (
          <div className="space-y-2 text-sm">
            <p>Import complete:</p>
            <p>Added: {result.added} feeds</p>
            <p>Skipped (duplicates): {result.skipped}</p>
            {result.failed > 0 && (
              <p className="text-destructive">Failed: {result.failed}</p>
            )}
          </div>
        )}

        <DialogFooter>
          {dialogState === 'select' && (
            <>
              <Button variant="outline" onClick={handleClose} disabled={previewOpml.isPending}>
                Cancel
              </Button>
              <Button onClick={handlePreview} disabled={previewOpml.isPending}>
                {previewOpml.isPending ? 'Loading...' : 'Next'}
              </Button>
            </>
          )}
          {dialogState === 'preview' && (
            <>
              <Button variant="outline" onClick={handleBack} disabled={importOpml.isPending}>
                Back
              </Button>
              <Button onClick={handleImport} disabled={importOpml.isPending || previewData?.summary.new === 0}>
                {importOpml.isPending ? 'Importing...' : `Import ${previewData?.summary.new ?? 0} new feeds`}
              </Button>
            </>
          )}
          {dialogState === 'result' && (
            <Button onClick={handleClose}>Done</Button>
          )}
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

function FeedGroup({ groupName, feeds }: { groupName: string; feeds: OpmlPreviewFeed[] }) {
  return (
    <Collapsible defaultOpen>
      <CollapsibleTrigger className="flex items-center gap-1 w-full text-sm font-medium py-1 hover:bg-accent rounded px-1 group">
        <ChevronRight className="h-3.5 w-3.5 transition-transform group-data-[state=open]:rotate-90" />
        <span>{groupName}</span>
        <span className="text-muted-foreground font-normal">({feeds.length})</span>
      </CollapsibleTrigger>
      <CollapsibleContent>
        <div className="ml-5 space-y-0.5">
          {feeds.map((feed) => (
            <div key={feed.url} className="flex items-center justify-between text-sm py-0.5">
              <span className="truncate mr-2">{feed.title || feed.url}</span>
              {feed.status === 'new' ? (
                <Badge className="bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400 shrink-0">
                  new
                </Badge>
              ) : (
                <Badge variant="secondary" className="shrink-0">
                  duplicate
                </Badge>
              )}
            </div>
          ))}
        </div>
      </CollapsibleContent>
    </Collapsible>
  );
}
