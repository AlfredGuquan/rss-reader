import { apiClient } from './client';
import type { Entry, PaginatedResponse } from '@/types';

export interface GetEntriesParams {
  feed_id?: string;
  group_id?: string;
  status?: 'all' | 'unread' | 'starred';
  page?: number;
  per_page?: number;
}

export function getEntries(params: GetEntriesParams): Promise<PaginatedResponse<Entry>> {
  const searchParams = new URLSearchParams();
  if (params.feed_id) searchParams.set('feed_id', params.feed_id);
  if (params.group_id) searchParams.set('group_id', params.group_id);
  if (params.status) searchParams.set('status', params.status);
  if (params.page) searchParams.set('page', String(params.page));
  if (params.per_page) searchParams.set('per_page', String(params.per_page));
  const qs = searchParams.toString();
  return apiClient.get<PaginatedResponse<Entry>>(`/entries${qs ? `?${qs}` : ''}`);
}

export function refreshFeed(feedId: string): Promise<{ new_entries: number }> {
  return apiClient.post<{ new_entries: number }>(`/feeds/${feedId}/refresh`);
}

export function getEntry(entryId: string): Promise<Entry> {
  return apiClient.get<Entry>(`/entries/${entryId}`);
}

export function markEntryRead(entryId: string): Promise<{ success: boolean }> {
  return apiClient.put<{ success: boolean }>(`/entries/${entryId}/read`);
}

export function markEntryUnread(entryId: string): Promise<{ success: boolean }> {
  return apiClient.put<{ success: boolean }>(`/entries/${entryId}/unread`);
}

export function starEntry(entryId: string): Promise<{ success: boolean }> {
  return apiClient.put<{ success: boolean }>(`/entries/${entryId}/star`);
}

export function unstarEntry(entryId: string): Promise<{ success: boolean }> {
  return apiClient.put<{ success: boolean }>(`/entries/${entryId}/unstar`);
}

export function markAllRead(params: { feed_id?: string; group_id?: string }): Promise<{ count: number }> {
  return apiClient.post<{ count: number }>('/entries/mark-all-read', params);
}
