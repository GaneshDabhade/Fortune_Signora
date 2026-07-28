/**
 * API response types.
 *
 * Mirrors the OpenAPI schema the backend generates. These are regenerated
 * from `/openapi.json` rather than hand-maintained long-term; they are
 * written out here so the frontend compiles before a generation step is
 * wired into CI (M1.3).
 */

export interface Workspace {
  id: string;
  name: string;
  created_at: string;
  updated_at: string;
}

export interface Membership {
  id: string;
  workspace_id: string;
  user_id: string;
  role: 'owner' | 'member';
  created_at: string;
}

/** The cursor-page envelope every collection endpoint returns. */
export interface CursorPage<T> {
  items: T[];
  next_cursor: string | null;
  has_more: boolean;
}
