import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { HotkeysProvider } from 'react-hotkeys-hook';
import { TooltipProvider } from '@/components/ui/tooltip';
import { ThemeProvider } from '@/components/theme/ThemeProvider';
import { AppLayout } from '@/components/layout/AppLayout';
import { OAuthCallback } from '@/pages/OAuthCallback';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 1000 * 60,
      retry: 1,
    },
  },
});

function App() {
  return (
    <ThemeProvider>
      <HotkeysProvider initiallyActiveScopes={['global', 'sidebar']}>
        <QueryClientProvider client={queryClient}>
          <TooltipProvider>
            <BrowserRouter>
              <Routes>
                <Route path="/oauth/callback" element={<OAuthCallback />} />
                <Route path="*" element={<AppLayout />} />
              </Routes>
            </BrowserRouter>
          </TooltipProvider>
        </QueryClientProvider>
      </HotkeysProvider>
    </ThemeProvider>
  );
}

export default App;
