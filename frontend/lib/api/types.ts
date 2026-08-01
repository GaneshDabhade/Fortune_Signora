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

/**
 * Where an opportunity sits in the seller's workflow.
 *
 * **Corrected at M12.2.** This listed `qualified` and `proposed`, which the
 * domain has never had, and omitted `dismissed`, which it has always had —
 * hand-written types drifting from the model they mirror. `dismissed` is not a
 * sales outcome: it means *we should not have been shown this*, and it is the
 * only feedback Signora gets about its own qualification quality.
 *
 * Only `tracking` can be reached without a person. Every stage beyond it names
 * who decided — *intelligence suggests; humans commit.*
 */
export type Stage =
  | 'tracking'
  | 'engaged'
  | 'closed_won'
  | 'closed_lost'
  | 'dismissed';

/** Who decided this account was worth tracking. */
export type Qualification = 'automatic' | 'manual';

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

/** One workflow state, exactly as it was recorded. Append-only, never edited. */
export interface WorkflowState {
  stage: Stage;
  owner_id: string | null;
  /** Null only on the opening entry — the one state Signora may author. */
  decided_by: string | null;
  reason: string;
  occurred_at: string;
}

/**
 * What Signora committed to about an account, and what has happened since.
 *
 * **Then beside now.** `score_at_open` is a fact about the moment of
 * commitment and never changes; `score` is today. `score_change_since_open` is
 * derived server-side from the two — `null` rather than `0` when no score is
 * live, because zero is a reading that has not moved and null is the absence
 * of one.
 */
export interface AccountOpportunity {
  id: string;
  account_id: string;
  stage: Stage;
  owner_id: string | null;
  opened_at: string;
  opened_by: Qualification;
  score_at_open: number;
  contested_at_open: boolean;
  score: number | null;
  score_change_since_open: number | null;
  evidence: EvidenceState;
  history: WorkflowState[];
}

/** One sentence of a grounded explanation, and the facts it rests on. */
export interface NarrationStatement {
  text: string;
  /** Citation tokens (`kind:id`). **Never empty** — an uncited statement is
   * refused before it is stored, so a sentence you cannot check never arrives. */
  evidence: string[];
}

/**
 * The grounded explanation of one account, with what produced it.
 *
 * **Statements, not a paragraph.** Each carries its own citations, and joining
 * them into prose would discard the mapping from claim to evidence — which is
 * the only reason to trust any of it. There is deliberately no summary field:
 * the sentence a reader looks at first must not be the one exempt from
 * grounding.
 *
 * `prompt`, `model` and `generated_at` are provenance, and they are on the
 * response rather than reachable from it: a customer reading generated language
 * is entitled to know what generated it while they are reading it.
 */
export interface AccountNarration {
  account_id: string;
  statements: NarrationStatement[];
  /** `name@version` of the prompt — a reviewed, versioned repository artifact. */
  prompt: string;
  model: string;
  /** Who served the call. Provenance only; no behaviour depends on it. */
  vendor: string;
  generated_at: string;
}

/**
 * One live hypothesis, and what a seller should do about it.
 *
 * **Not a recommendation.** Nothing here is about this account: `limitations`
 * and `suggested_validation` are properties of the hypothesis *type*, owned and
 * versioned by the Signal Catalog. What `expansion_opportunity` fails to prove
 * is identical on Tuesday and Wednesday and for every workspace.
 */
export interface HypothesisValidation {
  signal_id: string;
  title: string;
  /** What it *proposes*, phrased as a possibility — a signal suggests, never asserts. */
  hypothesis: string;
  relevance: Relevance;
  /** **What this hypothesis does not prove.** Never empty. */
  limitations: string[];
  /** What to confirm before acting. Never empty. */
  suggested_validation: string[];
}

/** What to check on an account, and what its evidence cannot tell you. */
export interface AccountValidation {
  account_id: string;
  /** Most relevant first. Empty when nothing is currently held — an answer, not an error. */
  hypotheses: HypothesisValidation[];
}
