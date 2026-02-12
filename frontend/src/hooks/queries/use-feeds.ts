import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { getFeeds, addFeed, deleteFeed, importOpml, previewOpml, updateFeed } from '@/api/feeds';

export function useFeeds() {
  return useQuery({
    queryKey: ['feeds'],
    queryFn: getFeeds,
  });
}

export function useAddFeed() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: addFeed,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['feeds'] });
    },
  });
}

export function useDeleteFeed() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: deleteFeed,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['feeds'] });
    },
  });
}

export function useImportOpml() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: importOpml,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['feeds'] });
      queryClient.invalidateQueries({ queryKey: ['groups'] });
    },
  });
}

export function usePreviewOpml() {
  return useMutation({ mutationFn: previewOpml });
}

export function useUpdateFeed() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({
      feedId,
      data,
    }: {
      feedId: string;
      data: { title?: string; group_id?: string | null; status?: 'active' | 'paused' };
    }) => updateFeed(feedId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['feeds'] });
    },
  });
}
