/** Workspace API operations, typed against the backend contract. */

import { apiRequest } from '@/lib/api/client';
import type { CursorPage, Membership, Workspace } from '@/lib/api/types';

export async function listWorkspaces(cursor?: string): Promise<CursorPage<Workspace>> {
  const query = cursor ? `?cursor=${encodeURIComponent(cursor)}` : '';
  return apiRequest<CursorPage<Workspace>>(`/workspaces${query}`);
}

export async function createWorkspace(name: string): Promise<Workspace> {
  return apiRequest<Workspace>('/workspaces', { method: 'POST', body: { name } });
}

export async function getWorkspace(workspaceId: string): Promise<Workspace> {
  return apiRequest<Workspace>(`/workspaces/${workspaceId}`, { workspaceId });
}

export async function listMembers(workspaceId: string): Promise<CursorPage<Membership>> {
  return apiRequest<CursorPage<Membership>>(`/workspaces/${workspaceId}/members`, {
    workspaceId,
  });
}
