import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { getGroups, createGroup, updateGroup, deleteGroup, reorderGroups } from '@/api/groups';

export function useGroups() {
  return useQuery({
    queryKey: ['groups'],
    queryFn: getGroups,
  });
}

export function useCreateGroup() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: createGroup,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['groups'] });
    },
  });
}

export function useUpdateGroup() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ groupId, name }: { groupId: string; name: string }) =>
      updateGroup(groupId, name),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['groups'] });
    },
  });
}

export function useReorderGroups() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: reorderGroups,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['groups'] });
    },
  });
}

export function useDeleteGroup() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: deleteGroup,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['groups'] });
      queryClient.invalidateQueries({ queryKey: ['feeds'] });
    },
  });
}
