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
  data: { title?: string; group_id?: string | null }
): Promise<Feed> {
  return apiClient.put<Feed>(`/feeds/${feedId}`, data);
}
