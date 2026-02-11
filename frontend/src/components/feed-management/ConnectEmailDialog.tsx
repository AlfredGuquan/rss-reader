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
import { useConnectEmail, useTestConnection } from '@/hooks/queries/use-email-accounts';
import { useUIStore } from '@/stores/ui-store';

interface ConnectEmailDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

export function ConnectEmailDialog({ open, onOpenChange }: ConnectEmailDialogProps) {
  const [emailAddress, setEmailAddress] = useState('');
  const [appPassword, setAppPassword] = useState('');
  const [label, setLabel] = useState('Newsletters');
  const connectEmail = useConnectEmail();
  const testConnection = useTestConnection();
  const setShortcutsEnabled = useUIStore((s) => s.setShortcutsEnabled);

  const handleTest = () => {
    testConnection.mutate({
      email_address: emailAddress,
      app_password: appPassword,
    });
  };

  const handleConnect = async () => {
    if (!emailAddress || !appPassword) return;
    await connectEmail.mutateAsync({
      email_address: emailAddress,
      app_password: appPassword,
      label,
    });
    onOpenChange(false);
  };

  const handleOpenChange = (nextOpen: boolean) => {
    setShortcutsEnabled(!nextOpen);
    if (!nextOpen) {
      setEmailAddress('');
      setAppPassword('');
      setLabel('Newsletters');
      connectEmail.reset();
      testConnection.reset();
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
          <div className="space-y-2">
            <label htmlFor="email-address" className="text-sm font-medium">
              Gmail Address
            </label>
            <Input
              id="email-address"
              type="email"
              placeholder="you@gmail.com"
              value={emailAddress}
              onChange={(e) => setEmailAddress(e.target.value)}
              disabled={connectEmail.isPending}
              autoFocus
            />
          </div>
          <div className="space-y-2">
            <label htmlFor="app-password" className="text-sm font-medium">
              App Password
            </label>
            <Input
              id="app-password"
              type="password"
              placeholder="xxxx xxxx xxxx xxxx"
              value={appPassword}
              onChange={(e) => setAppPassword(e.target.value)}
              disabled={connectEmail.isPending}
            />
            <p className="text-xs text-muted-foreground">
              Generate an App Password at myaccount.google.com/apppasswords
            </p>
          </div>
          <div className="space-y-2">
            <label htmlFor="email-label" className="text-sm font-medium">
              Gmail Label
            </label>
            <Input
              id="email-label"
              placeholder="Newsletters"
              value={label}
              onChange={(e) => setLabel(e.target.value)}
              disabled={connectEmail.isPending}
            />
          </div>
          {testConnection.isSuccess && (
            <p className="text-sm text-green-600">
              {testConnection.data.success ? 'Connection successful!' : `Failed: ${testConnection.data.message}`}
            </p>
          )}
          {testConnection.isError && (
            <p className="text-sm text-destructive">{testConnection.error.message}</p>
          )}
          {connectEmail.isError && (
            <p className="text-sm text-destructive">{connectEmail.error.message}</p>
          )}
        </div>
        <DialogFooter>
          <Button
            variant="outline"
            onClick={handleTest}
            disabled={!emailAddress || !appPassword || testConnection.isPending}
          >
            {testConnection.isPending ? 'Testing...' : 'Test Connection'}
          </Button>
          <Button
            onClick={handleConnect}
            disabled={!emailAddress || !appPassword || connectEmail.isPending}
          >
            {connectEmail.isPending ? 'Connecting...' : 'Connect'}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
