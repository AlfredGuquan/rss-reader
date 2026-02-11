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
import { useInitOAuth } from '@/hooks/queries/use-email-accounts';
import { useUIStore } from '@/stores/ui-store';

interface ConnectEmailDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

export function ConnectEmailDialog({ open, onOpenChange }: ConnectEmailDialogProps) {
  const [label, setLabel] = useState('Newsletters');
  const initOAuth = useInitOAuth();
  const setShortcutsEnabled = useUIStore((s) => s.setShortcutsEnabled);

  const handleConnect = async () => {
    const result = await initOAuth.mutateAsync();
    localStorage.setItem('gmail_oauth_label', label);
    window.location.href = result.auth_url;
  };

  const handleOpenChange = (nextOpen: boolean) => {
    setShortcutsEnabled(!nextOpen);
    if (!nextOpen) {
      setLabel('Newsletters');
      initOAuth.reset();
    }
    onOpenChange(nextOpen);
  };

  return (
    <Dialog open={open} onOpenChange={handleOpenChange}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>Connect Gmail</DialogTitle>
        </DialogHeader>
        <div className="space-y-4">
          <p className="text-sm text-muted-foreground">
            Sign in with Google to import newsletters from your Gmail account.
          </p>
          <div className="space-y-2">
            <label htmlFor="gmail-label" className="text-sm font-medium">
              Gmail Label
            </label>
            <Input
              id="gmail-label"
              placeholder="Newsletters"
              value={label}
              onChange={(e) => setLabel(e.target.value)}
              disabled={initOAuth.isPending}
            />
            <p className="text-xs text-muted-foreground">
              Emails with this Gmail label will be synced as newsletters.
            </p>
          </div>
          {initOAuth.isError && (
            <p className="text-sm text-destructive">{initOAuth.error.message}</p>
          )}
        </div>
        <DialogFooter>
          <Button
            onClick={handleConnect}
            disabled={initOAuth.isPending}
          >
            {initOAuth.isPending ? 'Connecting...' : 'Sign in with Google'}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
