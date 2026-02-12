import { apiClient } from './client';
import type { Feed } from '@/types';

export interface AddFeedRequest {
  url: string;
  group_id?: string;
}

export function getFeeds(): Promise<Feed[]> {
  return apiClient.get<Feed[]>('/feeds');
}

export function addFeed(data: AddFeedRequest): Promise<Feed> {
  return apiClient.post<Feed>('/feeds', data);
}

export function deleteFeed(feedId: string): Promise<void> {
  return apiClient.delete<void>(`/feeds/${feedId}`);
}

export function importOpml(
  file: File
): Promise<{ added: number; skipped: number; failed: number }> {
  const formData = new FormData();
  formData.append('file', file);
  return apiClient.upload<{ added: number; skipped: number; failed: number }>(
    '/feeds/import-opml',
    formData
  );
}

export interface DiscoveredFeed {
  url: string;
  title: string;
}

export function discoverFeeds(url: string): Promise<{ feeds: DiscoveredFeed[] }> {
  return apiClient.get<{ feeds: DiscoveredFeed[] }>(`/feeds/discover?url=${encodeURIComponent(url)}`);
}

export function updateFeed(
  feedId: string,
  data: { title?: string; group_id?: string | null; status?: 'active' | 'paused' }
): Promise<Feed> {
  return apiClient.put<Feed>(`/feeds/${feedId}`, data);
}

export interface OpmlPreviewFeed {
  title: string;
  url: string;
  site_url: string | null;
  group: string | null;
  status: 'new' | 'duplicate';
}

export interface OpmlPreviewGroup {
  name: string;
  feed_count: number;
  is_new: boolean;
}

export interface OpmlPreviewResult {
  groups: OpmlPreviewGroup[];
  feeds: OpmlPreviewFeed[];
  summary: { total: number; new: number; duplicate: number };
}

export function previewOpml(file: File): Promise<OpmlPreviewResult> {
  const formData = new FormData();
  formData.append('file', file);
  return apiClient.upload<OpmlPreviewResult>('/feeds/preview-opml', formData);
}

export function exportOpml(): void {
  window.open('/api/feeds/export-opml', '_blank');
}
