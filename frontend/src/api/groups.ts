import { apiClient } from './client';
import type { Group } from '@/types';

export function getGroups(): Promise<Group[]> {
  return apiClient.get<Group[]>('/groups');
}

export function createGroup(name: string): Promise<Group> {
  return apiClient.post<Group>('/groups', { name });
}

export function updateGroup(groupId: string, name: string): Promise<Group> {
  return apiClient.put<Group>(`/groups/${groupId}`, { name });
}

export function deleteGroup(groupId: string): Promise<void> {
  return apiClient.delete<void>(`/groups/${groupId}`);
}
