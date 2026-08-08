/**
 * Preference API operations — [TASK-470](../../../docs/BACKLOG.md), Workflow 9.
 *
 * ⚡ **A read never fails for want of a row.** Somebody who has never opened
 * the profile has the defaults, so there is no *no preferences yet* state for
 * a panel to render — and therefore none for a panel to get wrong.
 */

import { apiRequest } from '@/lib/api/client';

export type Theme = 'light' | 'dark' | 'system';
export type Density = 'comfortable' | 'compact';
export type TimeFormat = '24h' | '12h';
export type AnswerStyle = 'direct' | 'detailed';

export interface Preferences {
  theme: Theme;
  density: Density;
  time_format: TimeFormat;
  /** ⛔ **`null` means *not chosen*, not UTC.** The timezone offer can only be
   * made while this is still null-or-different, so a client that substituted a
   * default here would silently retire the design's prompt. */
  timezone: string | null;
  language: string | null;
  pronouns: string | null;
  display_name: string | null;
  ai_insights: boolean;
  ai_drafts: boolean;
  always_show_citations: boolean;
  answer_style: AnswerStyle;
  /** The design's control offers 3 · 4 · 5. */
  confidence_floor: number;
}

export async function getPreferences(workspaceId: string): Promise<Preferences> {
  return apiRequest<Preferences>(`/workspaces/${workspaceId}/preferences`, { workspaceId });
}

/**
 * Change some of them.
 *
 * 🔴 **Send only what is being changed.** The server distinguishes *absent*
 * from `null`, so a panel that spread the whole object would clear every field
 * it does not own. **Pass one key, change one thing.**
 */
export async function changePreferences(
  workspaceId: string,
  changes: Partial<Preferences>,
): Promise<Preferences> {
  return apiRequest<Preferences>(`/workspaces/${workspaceId}/preferences`, {
    method: 'PATCH',
    body: changes,
    workspaceId,
  });
}
