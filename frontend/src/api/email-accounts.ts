import { apiClient } from './client';

export interface EmailAccount {
  id: string;
  email_address: string;
  gmail_label: string;
  is_active: boolean;
  last_synced_at: string | null;
  last_error: string | null;
  created_at: string;
  updated_at: string;
}

export interface OAuthInitResponse {
  auth_url: string;
}

export interface OAuthCallbackRequest {
  code: string;
  gmail_label?: string;
}

export function getEmailAccounts(): Promise<EmailAccount[]> {
  return apiClient.get<EmailAccount[]>('/email-accounts');
}

export function initOAuth(): Promise<OAuthInitResponse> {
  return apiClient.post<OAuthInitResponse>('/email-accounts/oauth/init');
}

export function handleOAuthCallback(data: OAuthCallbackRequest): Promise<EmailAccount> {
  return apiClient.post<EmailAccount>('/email-accounts/oauth/callback', data);
}

export function disconnectEmail(accountId: string): Promise<void> {
  return apiClient.delete<void>(`/email-accounts/${accountId}`);
}

export function syncEmail(accountId: string): Promise<{ new_entries: number }> {
  return apiClient.post<{ new_entries: number }>(`/email-accounts/${accountId}/sync`);
}
