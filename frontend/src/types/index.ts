export interface Feed {
  id: string;
  user_id: string;
  url: string;
  title: string;
  site_url: string | null;
  description: string | null;
  favicon_url: string | null;
  group_id: string | null;
  fetch_interval_minutes: number;
  last_fetched_at: string | null;
  status: 'active' | 'error' | 'paused';
  error_count: number;
  unread_count: number;
  created_at: string;
  updated_at: string;
}

export interface Group {
  id: string;
  user_id: string;
  name: string;
  sort_order: number;
  created_at: string;
}

export interface Entry {
  id: string;
  feed_id: string;
  guid: string;
  title: string;
  url: string;
  author: string | null;
  summary: string | null;
  content: string | null;
  content_fetched: boolean;
  published_at: string;
  created_at: string;
  is_read: boolean;
  is_starred: boolean;
  feed_title?: string;
  feed_favicon_url?: string;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  per_page: number;
  total_pages: number;
}
