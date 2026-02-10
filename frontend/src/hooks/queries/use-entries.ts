import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  getEntries,
  refreshFeed,
  getEntry,
  markEntryRead,
  markEntryUnread,
  starEntry,
  unstarEntry,
  markAllRead,
} from '@/api/entries';
import type { GetEntriesParams } from '@/api/entries';

export function useEntries(params: GetEntriesParams) {
  return useQuery({
    queryKey: ['entries', params],
    queryFn: () => getEntries(params),
    enabled: !!(params.feed_id || params.group_id),
  });
}

export function useRefreshFeed() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: refreshFeed,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['entries'] });
      queryClient.invalidateQueries({ queryKey: ['feeds'] });
    },
  });
}

export function useEntry(entryId: string | null) {
  return useQuery({
    queryKey: ['entry', entryId],
    queryFn: () => getEntry(entryId!),
    enabled: !!entryId,
  });
}

export function useMarkRead() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: markEntryRead,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['entries'] });
      queryClient.invalidateQueries({ queryKey: ['feeds'] });
    },
  });
}

export function useMarkUnread() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: markEntryUnread,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['entries'] });
      queryClient.invalidateQueries({ queryKey: ['feeds'] });
    },
  });
}

export function useToggleStar() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ entryId, starred }: { entryId: string; starred: boolean }) =>
      starred ? starEntry(entryId) : unstarEntry(entryId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['entries'] });
      queryClient.invalidateQueries({ queryKey: ['entry'] });
    },
  });
}

export function useMarkAllRead() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: markAllRead,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['entries'] });
      queryClient.invalidateQueries({ queryKey: ['feeds'] });
    },
  });
}
