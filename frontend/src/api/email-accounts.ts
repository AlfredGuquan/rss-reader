import { apiClient } from './client';

export interface EmailAccount {
  id: string;
  email_address: string;
  imap_host: string;
  imap_port: number;
  label: string;
  is_active: boolean;
  last_synced_at: string | null;
  last_error: string | null;
  created_at: string;
  updated_at: string;
}

export interface ConnectEmailRequest {
  email_address: string;
  app_password: string;
  imap_host?: string;
  imap_port?: number;
  label?: string;
}

export function getEmailAccounts(): Promise<EmailAccount[]> {
  return apiClient.get<EmailAccount[]>('/email-accounts');
}

export function connectEmail(data: ConnectEmailRequest): Promise<EmailAccount> {
  return apiClient.post<EmailAccount>('/email-accounts', data);
}

export function disconnectEmail(accountId: string): Promise<void> {
  return apiClient.delete<void>(`/email-accounts/${accountId}`);
}

export function syncEmail(accountId: string): Promise<{ new_entries: number }> {
  return apiClient.post<{ new_entries: number }>(`/email-accounts/${accountId}/sync`);
}

export function testEmailConnection(data: {
  email_address: string;
  app_password: string;
  imap_host?: string;
  imap_port?: number;
}): Promise<{ success: boolean; message: string }> {
  return apiClient.post<{ success: boolean; message: string }>('/email-accounts/test', data);
}
