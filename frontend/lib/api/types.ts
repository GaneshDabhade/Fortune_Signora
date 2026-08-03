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
export type Stage = 'tracking' | 'engaged' | 'closed_won' | 'closed_lost' | 'dismissed';

/** Who decided this account was worth tracking. */
export type Qualification = 'automatic' | 'manual';

/**
 * One account on the attention list.
 *
 * `score`, `trend`, `score_change` and `signal_type` are null together: they
 * all come from the live buying score, and when the evidence behind it has
 * expired there is no live score to read. The opportunity is still open —
 * it outlives the score that created it.
 *
 * **`signal_type` is a catalog key and never a title.** The module that ranks
 * accounts is forbidden from reaching the one that forms hypotheses, so the
 * key travels and `useSignalCatalog` supplies the words. A translation table
 * here would be a second vocabulary, and two representations of one truth
 * become contradictory truth.
 */
export interface AccountAttention {
  id: string;
  account_id: string;
  score: number | null;
  trend: Trend | null;
  score_change: number | null;
  signal_type: string | null;
  /** What the leading hypothesis implies commercially. **Null with
   * `signal_type`** — both come from the live score, so an account whose
   * evidence expired has neither. Sent by the server precisely so no component
   * maps catalog keys to a meaning: that mapping belongs to the pipeline, and a
   * copy here would be a second vocabulary. */
  posture: Posture | null;
  contested: boolean;
  evidence: EvidenceState;
  stage: Stage;
  owner_id: string | null;
  opened_at: string;
}

/** One hypothesis type, named by the catalog that owns it. */
export interface SignalTypeName {
  key: string;
  title: string;
}

/**
 * The hypothesis vocabulary in force.
 *
 * Names only — what a hypothesis proposes and cannot prove are per-account
 * questions the validation surface answers. A change to the catalog is a new
 * version of a reviewed artifact rather than an edit, so this can be held for
 * as long as a session lasts.
 */
export interface SignalCatalog {
  version: number;
  types: SignalTypeName[];
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
  /** When the newest evidence about this account was observed, across every
   * attribute rather than only the name. `null` when no source has ever
   * reported anything. **Not when Signora last looked** — see `Freshness`. */
  last_observed_at: string | null;
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
  /**
   * Which stages this may legally become from where it stands.
   *
   * **Sent by the server, never inferred here.** The transition rules belong
   * to the Opportunity Engine's domain, and a client that reimplemented them
   * would be a second copy — wrong the moment either changed. Empty on a won
   * deal, which does not reopen.
   */
  allowed_next: Stage[];
}

/** A human deciding something about an account.
 *
 * There is no `actor_id`: who decided is taken from the verified caller, and a
 * request able to name its own actor could sign somebody else's name to a
 * dismissal. */
export interface RecordDecision {
  stage: Stage;
  reason: string;
  owner_id?: string;
}

/** One sentence of a grounded explanation, and the facts it rests on. */
export interface NarrationStatement {
  text: string;
  /** Citation tokens (`kind:id`). **Never empty** — an uncited statement is
   * refused before it is stored, so a sentence you cannot check never arrives. */
  evidence: string[];
}

/**
 * One fact a statement cites — **exactly what the model was given**.
 *
 * Not a record fetched afterwards: the summary and attributes here are the ones
 * assembled into the prompt, which is the strongest available form of *"here is
 * what it was told."* The wording belongs to the module that owns the concept,
 * so a citation resolves into the pipeline's vocabulary rather than a paraphrase.
 */
export interface EvidenceFact {
  /** The citation this answers, exactly as it appears on a statement. */
  token: string;
  /** `opportunity`, `buying_score`, `signal_contribution` — which layer of the
   * argument the sentence is standing on. */
  kind: string;
  summary: string;
  /** The figures behind the summary, in canonical order. **Text, not numbers**:
   * the textual form is what the model saw and what the digest covers. */
  attributes: Record<string, string>;
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
  /** The facts the statements cite, each **once** however many sentences rest
   * on it. Empty when the evidence could not be re-derived — an answer, not an
   * error, and always accompanied by `evidence_unchanged: false`. */
  facts: EvidenceFact[];
  /** Whether the evidence behind this account is still byte-identical to what
   * the model was shown. **False means these sentences are dated, not wrong** —
   * a narration is never edited to catch up with its account. */
  evidence_unchanged: boolean;
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
/**
 * One recorded thing that happened at this account.
 *
 * **The specific half of generic guidance** (R2-01). A check is a property of
 * the hypothesis *type* and is word-for-word identical on every account holding
 * it — deliberately, because that is what keeps it from being a recommendation.
 * These are not: they are this company's own events, and they differ.
 */
export interface SupportingEvent {
  /** The same citation the score's ledger carries — opens the evidence drawer. */
  business_event_id: string;
  /** The Business Event Engine's own sentence. **Never a paraphrase.** */
  summary: string;
  occurred_at: string;
}

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
  /** **What this account actually did to earn the hypothesis** (R2-01). Empty
   * only when the cited events no longer resolve — a signal cannot exist
   * citing nothing. */
  observed: SupportingEvent[];
}

/** What to check on an account, and what its evidence cannot tell you. */
export interface AccountValidation {
  account_id: string;
  /** Most relevant first. Empty when nothing is currently held — an answer, not an error. */
  hypotheses: HypothesisValidation[];
}

/** One provider's reading — the fact under the fact. */
export interface EvidenceObservation {
  provider: string;
  attribute: string;
  /** What it was before, or null on a first reading. **The half that makes a
   * change checkable**: a current value alone cannot be argued with. */
  previous_value: unknown;
  current_value: unknown;
  direction: string;
  /** When the *provider* observed it — never when Signora stored it. */
  observed_at: string;
}

/**
 * What happened, and every reading that says so.
 *
 * **The end of a citation.** Every other surface says something *about* a fact
 * — the signal interprets it, the score weighs it, the narration describes it.
 * The observations here are the only content Signora did not write.
 */
export interface BusinessEventEvidence {
  id: string;
  type_key: string;
  /** Signora's sentence, rendered from the same fields the readings carry. */
  summary: string;
  occurred_at: string;
  /** Every provider whose readings independently support this. **One is not a
   * weakness** — it is a differently-supported fact. */
  corroborating_providers: string[];
  /** Oldest first: a change reads forwards. */
  observations: EvidenceObservation[];
}

/**
 * One thing the customer sells.
 *
 * **Declared, never derived.** Every other type in this file describes
 * something Signora computed about the world; a product is a sentence
 * somebody typed. It is the first customer-authored shape to reach the
 * product surface.
 */
export interface Product {
  /** Stable across every revision of the catalog. **Chosen by the client**,
   * which is what makes saving idempotent — a retried save cannot duplicate
   * a product — and what lets everything declared later cite one. */
  id: string;
  name: string;
  /** What it does, in the customer's own words. May be empty. */
  description: string;
}

/**
 * What this workspace sells, and who last said so.
 *
 * **Versioned as a whole.** The catalog is the unit: a version is a complete
 * statement, so a product absent from `products` is one the workspace no
 * longer sells — and the version that contained it stays readable. Saving
 * quotes the version being replaced, which turns a colleague's concurrent
 * edit into a refusal rather than an overwrite neither of you sees.
 */
export interface ProductCatalog {
  /** **0 when nothing has been declared** — the state every workspace starts
   * in, and an answer rather than an absence. */
  version: number;
  products: Product[];
  /** Null only at version 0. */
  updated_at: string | null;
  /** Null only at version 0. A declaration names its author permanently:
   * the row is never edited, so this cannot be reattributed. */
  updated_by: string | null;
}

/** A complete statement of the catalog, replacing `expected_version`. */
export interface PublishProductCatalog {
  expected_version: number;
  products: Product[];
}

/**
 * How big the companies that buy a product are.
 *
 * **A count of people, not a revenue band.** Either bound may be null —
 * *"anything over 500"* and *"under 50"* are both real answers.
 */
export interface EmployeeRange {
  minimum: number | null;
  maximum: number | null;
}

/**
 * Who buys one product, as the customer describes them.
 *
 * **Their words, not a controlled list.** `industries` and `countries` are
 * free text: Signora records what the customer states, and nothing here is
 * matched against anything. A profile carries no score, rank or verdict, and
 * the API has no field that could.
 */
export interface ProductIcp {
  /** A product from the catalog, and one the workspace currently sells. */
  product_id: string;
  industries: string[];
  countries: string[];
  /** Null when size was not stated. */
  employees: EmployeeRange | null;
  /** Anything the fields above cannot hold. May be empty. */
  notes: string;
}

/**
 * Who buys what this workspace sells, and who last said so.
 *
 * **Versioned as a whole, and separately from the catalog.** Renaming a
 * product does not mint a version here, and describing a buyer does not mint
 * one there — two aggregates, so neither audit history is filled with the
 * other's changes.
 */
export interface IcpDeclaration {
  /** **0 when nothing has been described** — the state every workspace starts
   * in, and an answer rather than an absence. */
  version: number;
  /** One per product described. A product with no entry has no ideal customer
   * described yet. */
  profiles: ProductIcp[];
  /** Null only at version 0. */
  updated_at: string | null;
  /** Null only at version 0. */
  updated_by: string | null;
}

/** A complete statement of the ideal customer, replacing `expected_version`. */
export interface DeclareIcp {
  expected_version: number;
  profiles: ProductIcp[];
}

/**
 * One sentence a model wrote in a research brief, and the findings under it.
 *
 * The same shape as `NarrationStatement` and deliberately not the same type:
 * these cite **findings**, not pipeline rows, and the findings are on the same
 * response — so following a claim here costs no request at all.
 */
export interface ResearchStatement {
  text: string;
  /** `research_finding:<uuid>` tokens. **Never empty**, and every one resolves
   * against `findings` on the same payload. */
  cites: string[];
}

/**
 * One deterministic comparison research performed. **DERIVED, not written.**
 *
 * The half of a research brief nobody has to trust: a customer who disagrees
 * opens the rows in `cites` and runs the same comparison. That is what makes
 * research something other than a second opinion.
 */
export interface ResearchFinding {
  id: string;
  /** How a statement addresses this finding. Matched against `cites`. */
  ref: string;
  /** Which comparison was performed — the name of the code that computed it. */
  derivation: string;
  /** What it was performed to answer, **in the catalog's own reviewed words**.
   * On the wire so no client maps a derivation key to a sentence of its own. */
  question: string;
  /** What the comparison produced, rendered for display. */
  attributes: Record<string, string>;
  /** The pipeline rows it compared, in the citation form the evidence drawer
   * already resolves — so a finding leads on to the business event beneath it. */
  cites: string[];
}

/** One completed run: what was compared, and what was made of it. */
export interface ResearchArtifact {
  task_id: string;
  produced_at: string;
  /** **INFERRED.** */
  statements: ResearchStatement[];
  /** **DERIVED.** */
  findings: ResearchFinding[];
  prompt_name: string;
  prompt_version: number;
  model: string;
  evidence_digest: string;
}

/**
 * Where research on one account stands.
 *
 * `nothing_to_research` is **not a failure**: the run finished and found
 * nothing worth comparing, which is a real answer on an account with little
 * evidence. A client that rendered it as an error would have the product
 * apologising for behaving correctly.
 */
export type ResearchStatus =
  'requested' | 'running' | 'completed' | 'nothing_to_research' | 'failed';

export interface AccountResearch {
  request_id: string;
  status: ResearchStatus;
  requested_at: string;
  updated_at: string;
  /** Why it failed, verbatim. **Null unless `status` is `failed`.** */
  detail: string | null;
  /** The brief. **Null unless `status` is `completed`**, and never null when
   * it is. */
  artifact: ResearchArtifact | null;
}

/**
 * The part a role plays in a purchase.
 *
 * **Five values, and they are ordinary sales language** rather than a taxonomy
 * a customer must translate their own business into. Owned by Commercial
 * Profile; no provider has any say in it.
 */
export type CommitteePart =
  'economic_buyer' | 'champion' | 'evaluator' | 'user' | 'gatekeeper';

/**
 * One seat at the table.
 *
 * **A role, never a person.** The title is what the customer calls the job —
 * *VP of Revenue Operations* — and Signora holds no individuals here. There is
 * no influence, weight or seniority: those would be judgements about a real
 * deal, and this is a declaration.
 */
export interface CommitteeRole {
  title: string;
  part: CommitteePart;
}

/** Who decides about one product. At least one role. */
export interface ProductCommittee {
  product_id: string;
  /** In the order the customer arranged them, which carries no rank. */
  roles: CommitteeRole[];
}

/**
 * Who decides about what this workspace sells, and who last said so.
 *
 * Versioned separately from the catalog and the ideal customer, because a
 * committee changes on a different day from either.
 */
export interface BuyingCommittee {
  /** **0 when nothing has been declared.** */
  version: number;
  committees: ProductCommittee[];
  /** Null only at version 0. */
  updated_at: string | null;
  /** Null only at version 0. */
  updated_by: string | null;
}

/** A complete statement of the committee, replacing `expected_version`. */
export interface DeclareBuyingCommittee {
  expected_version: number;
  committees: ProductCommittee[];
}

/**
 * What this company is pushing right now.
 *
 * **No rank and no order.** A product is in focus or it is not — the roadmap
 * calls this capability *business priorities*, and an ordinal here is one
 * consumer away from a weight in a score. There is also no period: `updated_at`
 * already says when the customer last declared this, and a typed *"Q3 2026"*
 * would be free to disagree with it.
 */
export interface CommercialFocus {
  /** **0 when nothing has been declared.** */
  version: number;
  /** Product ids. Unordered and unranked. */
  products: string[];
  /** What they are trying to do, in their words. May be empty. */
  objective: string;
  /** Null only at version 0. Also the answer to whether the focus is current. */
  updated_at: string | null;
  /** Null only at version 0. */
  updated_by: string | null;
}

/** A complete statement of the focus, replacing `expected_version`. */
export interface DeclareFocus {
  expected_version: number;
  products: string[];
  objective: string;
}

/**
 * One account somebody finished with, and what they said about it.
 *
 * **No score, no trend, no evidence state.** An open account is triaged on
 * those; a decided one is *recalled*, and a live number beside a settled
 * judgement invites re-litigating it against something that moved afterwards.
 * The account's own brief — where reopening lives — is one click away.
 */
export interface DecidedAccount {
  account_id: string;
  opportunity_id: string;
  /** **`dismissed` and `closed_lost` are different answers.** One says Signora
   * should not have surfaced this account, the other says it was worth
   * pursuing and did not close. Never merge them. */
  stage: Stage;
  /** Why, in the words the person typed. The only place in the product that
   * shows a customer their own judgement back. */
  reason: string;
  /** Compared against the reader to say *yours*. Never a name — the tier
   * verifies tokens without learning who anybody is (**D23**). */
  owner_id: string | null;
  decided_at: string;
}

/**
 * One company the customer wants watched.
 *
 * **The name is exactly what they typed** — Signora does not ask for a domain
 * or a registration number, because working out which company they mean is its
 * job rather than theirs. The id is chosen by the client and stable across
 * every revision, which is what lets a rename be told apart from a
 * remove-and-re-add.
 */
export interface TargetAccount {
  id: string;
  name: string;
}

/**
 * Which companies this workspace watches, and who last said so.
 *
 * **The declaration the rest of the platform reads.** Its `version` is the same
 * integer that travels on the event announcing a change, so it is part of a
 * published contract rather than this screen's bookkeeping.
 *
 * It carries **no status**: whether Signora has looked at an account, what it
 * found, and when it will look again belong to other parts of the product.
 */
export interface TargetAccountList {
  /** **0 when nothing has been declared.** */
  version: number;
  accounts: TargetAccount[];
  /** Null only at version 0. */
  updated_at: string | null;
  /** Null only at version 0. */
  updated_by: string | null;
}

/** A complete statement of the watch list, replacing `expected_version`. */
export interface DeclareTargetAccounts {
  expected_version: number;
  accounts: TargetAccount[];
}

/**
 * What has happened with an account, newest first.
 *
 * **`kind` is engineering's word and never reaches a screen.** ADR-0034 puts
 * the translation at the presentation edge; `components/timeline/feed.tsx`
 * owns the phrasing a seller reads. The API deliberately sends no rendered
 * sentence — an entry is immutable, so a stored one could never be improved.
 */
export type TimelineEntryKind =
  | 'observation_recorded'
  | 'observation_superseded'
  | 'business_event_detected'
  | 'business_event_superseded'
  | 'signal_generated'
  | 'signal_superseded'
  | 'buying_score_updated'
  | 'opportunity_created'
  | 'opportunity_stage_changed';

export interface TimelineEntry {
  id: string;
  kind: TimelineEntryKind;
  /** When it happened in the domain — never when Signora processed it. */
  occurred_at: string;
  source_module: string;
  source_ref: string;
  detail: Record<string, unknown>;
}

/**
 * A system Signora understands, and what an organization has of it.
 *
 * `integration` and `capabilities` are engineering's words; the Connection
 * Center supplies the customer's. The API sends no rendered prose, so improving
 * a sentence is a deploy rather than a migration.
 */
export type IntegrationCapability =
  | 'crm_activity'
  | 'meetings'
  | 'email_engagement'
  | 'message_delivery';

export type ConnectionAttention = 'none' | 'soon' | 'now';

export interface Connection {
  id: string;
  integration: string;
  label: string;
  state: string;
  connected_at: string | null;
  attention: ConnectionAttention;
  reason: string | null;
}

export interface IntegrationSystem {
  integration: string;
  capabilities: IntegrationCapability[];
  connectable: boolean;
  /** At least one connection Signora can currently use — not merely present. */
  working: boolean;
  needs_attention: boolean;
  connections: Connection[];
}


/**
 * One customer segment, as the list reads it.
 *
 * **Ids rather than names for products**, deliberately: the catalog owns
 * names, and a product removed from it must still leave the row readable.
 * The screen resolves them and says plainly when one is gone.
 */
export interface IcpSegmentSummary {
  id: string;
  name: string;
  state: 'draft' | 'published' | 'archived';
  version: number;
  product_ids: string[];
  last_changed_at: string;
  last_changed_by: string;
}
