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

/** How the intelligence behind an opportunity is holding up. */
export type EvidenceState = 'current' | 'cooling' | 'stale';

/** Which way the score last moved. */
export type Trend = 'rising' | 'falling' | 'steady';

/** Why an account rose to attention. The Buying Score Engine's vocabulary,
 * not a paraphrase of it — a reason a seller can check against the record. */
export type ScoreTrigger =
  | 'signal_generated'
  | 'signal_superseded'
  | 'model_changed'
  | 'profile_changed'
  | 'evidence_aged';

/** Where an opportunity sits in the seller's workflow. */
export type Stage =
  | 'tracking'
  | 'engaged'
  | 'qualified'
  | 'proposed'
  | 'closed_won'
  | 'closed_lost';

/**
 * One account on the attention list.
 *
 * `score`, `trend`, `score_change` and `trigger` are null together: they all
 * come from the live buying score, and when the evidence behind it has
 * expired there is no live score to read. The opportunity is still open —
 * it outlives the score that created it.
 */
export interface AccountAttention {
  id: string;
  account_id: string;
  score: number | null;
  trend: Trend | null;
  score_change: number | null;
  trigger: ScoreTrigger | null;
  contested: boolean;
  evidence: EvidenceState;
  stage: Stage;
  owner_id: string | null;
  opened_at: string;
}
