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

/** Whether your sources agree on what an account is called. */
export type NameAgreement = 'unknown' | 'single_source' | 'agreed' | 'disputed';

/**
 * Who an account is, and how sure Signora is about it.
 *
 * **Not a string.** An account's name is a `legal_name` claim from a provider
 * at a time, and providers can disagree — so the identity carries the name it
 * chose *and* whether anything else agreed. `name`, `source` and `observed_at`
 * are null together when nobody has named the account.
 */
export interface AccountIdentity {
  account_id: string;
  name: string | null;
  agreement: NameAgreement;
  source_count: number;
  source: string | null;
  observed_at: string | null;
}

/** What a reading implies commercially. **Never a sign in the arithmetic** —
 * two accounts can score the same and mean opposite things, and this is the
 * only place that difference survives. */
export type Posture = 'expansionary' | 'contractionary' | 'neutral';

/** How central a hypothesis is to this workspace's ideal customer profile.
 * Declared, never measured. */
export type Relevance = 'primary' | 'supporting' | 'contextual' | 'ignored';

/**
 * One line of a score's explanation — a single business event's contribution.
 *
 * `reason` is the sentence, rendered by the pipeline from the same fields an
 * auditor checks. **The browser never composes its own**: the signal type's
 * title belongs to the Signal Catalog, and a second set of wordings here would
 * eventually disagree with it.
 */
export interface ScoreContribution {
  business_event_id: string;
  signal_id: string;
  posture: Posture;
  relevance: Relevance;
  /** fresh, recent, or ageing — the decay step this evidence sits in. */
  evidence_age: string;
  points: number;
  counted: boolean;
  dissenting: boolean;
  reason: string;
}

/**
 * One account's score, with everything needed to challenge it.
 *
 * **Every number arrives computed.** `points`, `ceiling` and
 * `attention_by_posture` are derived server-side from the ledger, so the screen
 * displays the arithmetic rather than performing it — a figure assembled in the
 * browser would be a second implementation of the thing the ledger exists to
 * make singular.
 */
export interface AccountScore {
  account_id: string;
  score: number;
  trend: Trend;
  score_change: number;
  trigger: ScoreTrigger;
  contested: boolean;
  computed_at: string;
  valid_until: string | null;
  /** Whether the stated validity period still holds. */
  is_current: boolean;
  /** The raw point total of the counted lines, before normalising. */
  points: number;
  /** The point total that reads as 100, from the model in force when computed. */
  ceiling: number;
  attention_by_posture: Partial<Record<Posture, number>>;
  contributions: ScoreContribution[];
}
