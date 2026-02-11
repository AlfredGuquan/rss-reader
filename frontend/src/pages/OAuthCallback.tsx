import { useEffect } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { useOAuthCallback } from '@/hooks/queries/use-email-accounts';

export function OAuthCallback() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const oauthCallback = useOAuthCallback();

  useEffect(() => {
    const code = searchParams.get('code');
    if (code && !oauthCallback.isPending && !oauthCallback.isSuccess && !oauthCallback.isError) {
      const gmailLabel = localStorage.getItem('gmail_oauth_label') || 'Newsletters';
      localStorage.removeItem('gmail_oauth_label');

      oauthCallback.mutate(
        { code, gmail_label: gmailLabel },
        {
          onSuccess: () => {
            navigate('/', { replace: true });
          },
        }
      );
    }
  }, [searchParams]);

  if (oauthCallback.isPending) {
    return (
      <div className="flex h-screen items-center justify-center">
        <div className="text-center space-y-4">
          <div className="animate-spin h-8 w-8 border-4 border-primary border-t-transparent rounded-full mx-auto" />
          <p className="text-muted-foreground">Connecting Gmail account...</p>
        </div>
      </div>
    );
  }

  if (oauthCallback.isError) {
    return (
      <div className="flex h-screen items-center justify-center">
        <div className="text-center space-y-4">
          <p className="text-destructive">Connection failed: {oauthCallback.error.message}</p>
          <button
            className="text-sm text-primary underline"
            onClick={() => navigate('/', { replace: true })}
          >
            Back to home
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="flex h-screen items-center justify-center">
      <p className="text-muted-foreground">Processing...</p>
    </div>
  );
}
