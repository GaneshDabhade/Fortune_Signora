/** Workspace API operations, typed against the backend contract. */

import { apiRequest } from '@/lib/api/client';
import type { CursorPage, Membership, Workspace } from '@/lib/api/types';

export async function listWorkspaces(cursor?: string): Promise<CursorPage<Workspace>> {
  const query = cursor ? `?cursor=${encodeURIComponent(cursor)}` : '';
  return apiRequest<CursorPage<Workspace>>(`/workspaces${query}`);
}

/**
 * 📁 **Screen `03`** — a name and the address it lives at, together.
 *
 * ⛔ **`slug` is required and is not derived here.** The server refuses to
 * invent one, and the client's suggestion (`lib/workspace/slug.ts`) is only
 * what the field is pre-filled with — **what is sent is what the person
 * accepted.**
 */
export async function createWorkspace(name: string, slug: string): Promise<Workspace> {
  return apiRequest<Workspace>('/workspaces', { method: 'POST', body: { name, slug } });
}

/** 📁 *"Checked as you type, 300ms after you stop."*
 *
 * ⚡ **Three states, not two** — available · taken · malformed. A screen given
 * one boolean would have to say *"taken"* about text that is not an address.
 */
export interface SlugAvailability {
  slug: string;
  available: boolean;
  reason: string | null;
}

export async function checkSlug(slug: string): Promise<SlugAvailability> {
  return apiRequest<SlugAvailability>(
    `/workspaces/slug-available?slug=${encodeURIComponent(slug)}`,
  );
}

export async function getWorkspace(workspaceId: string): Promise<Workspace> {
  return apiRequest<Workspace>(`/workspaces/${workspaceId}`, { workspaceId });
}

export async function listMembers(workspaceId: string): Promise<CursorPage<Membership>> {
  return apiRequest<CursorPage<Membership>>(`/workspaces/${workspaceId}/members`, {
    workspaceId,
  });
}
