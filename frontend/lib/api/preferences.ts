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
/** ⚡ The design's segmented control: *100% · 112% · 125%*. ⛔ Stored without
 *  the symbol — the percent sign is how it renders, not what it is. */
export type TextSize = '100' | '112' | '125';
/** The design's segmented control: *Concise · Detailed*. */
export type ScreenReaderVerbosity = 'concise' | 'detailed';

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

  // ── Language & region ────────────────────────────────────────────────────
  /** ⛔ **A string, not a union, and deliberately.** ⚡ The design shows ONE
   *  value for each — *"31 Dec 2026"*, *"1.234,56"*, *"Monday"* — and never
   *  lists the options, so a union here would decide which formats Signora
   *  supports. `language` and `timezone` above are typed the same way. */
  date_format: string | null;
  number_format: string | null;
  week_starts_on: string | null;

  // ── Accessibility ────────────────────────────────────────────────────────
  /** 🔴 **The OVERRIDE, not the device's setting.** ⚡ `globals.css` already
   *  carries `@media (prefers-reduced-motion: reduce)` and the shell uses
   *  `motion-reduce:` — ⛔ **so this is *on regardless of what the device
   *  says*, and `false` leaves the media query in charge** rather than meaning
   *  *motion is fine*. */
  reduce_motion: boolean;
  increase_contrast: boolean;
  always_show_focus_ring: boolean;
  /** ⚡ **Defaults on**, because the design shows links underlined. */
  underline_links: boolean;
  text_size: TextSize;
  screen_reader_verbosity: ScreenReaderVerbosity;
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
