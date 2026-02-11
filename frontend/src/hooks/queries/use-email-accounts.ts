import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  getEmailAccounts,
  initOAuth,
  handleOAuthCallback,
  disconnectEmail,
  syncEmail,
} from '@/api/email-accounts';

export function useEmailAccounts() {
  return useQuery({
    queryKey: ['email-accounts'],
    queryFn: getEmailAccounts,
  });
}

export function useInitOAuth() {
  return useMutation({
    mutationFn: initOAuth,
  });
}

export function useOAuthCallback() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: handleOAuthCallback,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['email-accounts'] });
      queryClient.invalidateQueries({ queryKey: ['feeds'] });
    },
  });
}

export function useDisconnectEmail() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: disconnectEmail,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['email-accounts'] });
      queryClient.invalidateQueries({ queryKey: ['feeds'] });
    },
  });
}

export function useSyncEmail() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: syncEmail,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['entries'] });
      queryClient.invalidateQueries({ queryKey: ['feeds'] });
    },
  });
}
