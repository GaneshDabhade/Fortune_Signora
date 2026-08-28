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

/**
 * The signed-in person's own standing in a workspace.
 *
 * 🔴 **[B-284](../../docs/BUGS.md).** Deliberately not `Membership`: that type
 * answers *"who is in this workspace?"* and is served a page at a time, and
 * reading a page to find yourself is what locked an owner out of their own
 * Settings. **This is the answer to a different question**, and the endpoint
 * behind it can only ever answer it about the caller.
 */
export interface ViewerRoleResponse {
  workspace_id: string;
  user_id: string;
  role: 'owner' | 'member';
}

export interface Membership {
  id: string;
  workspace_id: string;
  user_id: string;
  role: 'owner' | 'member';
  created_at: string;
  /**
   * The address this membership was created with, when one is known.
   *
   * `null` for memberships added by identifier before invitations existed.
   * The screen says *"Somebody here"* — the wording D23 established, rather
   * than an identifier dressed as information.
   */
  member_email: string | null;
}

/**
 * An offer of membership, addressed to an email that may not be a user yet.
 *
 * **`state` is sent, not derived.** The browser must not compute it from
 * `expires_at`: two clocks would disagree and the one that matters is the
 * server's — the same reason evidence state travels on the wire.
 */
export interface Invitation {
  id: string;
  workspace_id: string;
  invited_email: string;
  role: 'owner' | 'member';
  state: 'pending' | 'accepted' | 'revoked' | 'expired';
  expires_at: string;
  created_at: string;
  /** Provenance, never an owner — it does not move when the inviter leaves. */
  invited_by: string;
}

/**
 * One thing that happened to an organization.
 *
 * **An id and a snapshot for each person** (46-team-management.md §24): the
 * snapshot is what was true then, the id is what a screen resolves when a
 * reader needs to act rather than merely read. **No rendered sentence** — the
 * words live in a reviewed catalog at this edge, so improving one is a deploy.
 */
export interface HistoryEntry {
  occurred_at: string;
  kind:
    | 'joined'
    | 'invited'
    | 'invitation_withdrawn'
    | 'invitation_accepted'
    | 'role_changed'
    | 'removed';
  actor_id: string | null;
  actor_email: string | null;
  subject_email: string | null;
  subject_membership_id: string | null;
  previous_role: string | null;
  new_role: string | null;
  reason: string | null;
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
  /**
   * When this stage and owner were last recorded.
   *
   * **A fact, never a judgement.** Signora records workflow decisions and
   * cannot see a call, an email or a meeting, so it must not say an account is
   * neglected — it says how long it has been since anything it *can* see
   * happened, and the reader decides what that means.
   */
  since: string;
}

/** One hypothesis type, named by the catalog that owns it. */
export interface SignalTypeName {
  key: string;
  title: string;
  /** Why this kind of hypothesis is commercially interesting — a fact about
   * the **type**, true before any account exhibits it. **The only explanation
   * the catalog carries**: what a hypothesis proposes, cannot prove and how to
   * check it are per-account questions the validation surface answers, and the
   * same prose in two places means one of them goes stale. */
  why_it_matters: string;
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
/**
 * **What kind of thing an account is** — [TASK-440](../../../docs/BACKLOG.md).
 *
 * ⛔ **Read it rather than assuming `company`.** 📁 The browse endpoint's own
 * words: *"the list answers for companies today and the graph knows more kinds
 * than it can search."* ⚡ **A screen that hard-codes the word `company` will
 * be wrong the first time the graph lists anything else**, and it will be wrong
 * silently.
 */
export type EntityKind = 'company' | 'person' | 'product' | 'technology';

/**
 * **One account on a browse page** — [TASK-440](../../../docs/BACKLOG.md),
 * `GET /workspaces/{id}/accounts-list`.
 *
 * 🔴 **This is NOT `AccountAttention`, and the difference decides the screen.**
 * 📁 `/accounts` is `attention_list` — *"accounts worth attention, most
 * pressing first"* — **a ranked, narrowed set.** ⚡ **This read is *"show me my
 * accounts"* — browse, not search, and not triage.**
 *
 * ⛔ **It is also not `AccountMatch`**, and the endpoint states why: a match
 * carries `matched_name`, `matched_source` and `is_renamed` **because a search
 * result has to explain why it is in the list. A browse row is in the list
 * because it exists**, and those three would be null on every one of them.
 *
 * ⚠️ **Three fields, and that is the whole contract.** **Score, owner, trend
 * and every other column the design draws are NOT published by this read** —
 * 📁 [§20c](../../../CLAUDE.md): *"screens without a shipped module behind them
 * ship a designed empty state"*, ⛔ **and inventing them here would be the mock
 * business data that rule forbids.**
 *
 * ⚡ **`commercial` was the third, added 2026-08-16** — 📁 [ADR-0409](../../../docs/architecture/adr/0409-commercial-account-facts.md),
 * ratified: *Signora owns Open ACV, Renewal and commercial stage.* **The read
 * path is built; its fields are `null` until a customer's system supplies
 * them.**
 */
export interface ListedAccount {
  account: AccountIdentity;
  kind: EntityKind;
  commercial: AccountCommercial;
}

/**
 * **What an account is worth, and where it stands.**
 *
 * 📁 [ADR-0409](../../../docs/architecture/adr/0409-commercial-account-facts.md)
 * §5: *"a claim is only produced where the provider supplies the fact.
 * **Absence is never inferred, defaulted or zero-filled.**"*
 *
 * 🔴 **So every field is nullable and `null` means nobody has said.** ⛔ **A
 * `0` ACV would be a figure a seller would act on**, and rendering absence as
 * zero is the fabrication this contract exists to make impossible.
 *
 * ⚠️ **The object is always present even when all three are `null`** — that is
 * how a caller tells *nothing said* from *not asked*, the same distinction
 * `SearchCoverage` draws one read away.
 */
export interface AccountCommercial {
  open_acv: Money | null;
  renewal_date: string | null;
  stage: CommercialStage | null;
}

/**
 * **One row of the commercial batch** — `GET /workspaces/{id}/account-commercials`.
 *
 * ⚡ **The sibling of the identity batch**, for a surface that does not start
 * from a browse page. 📁 Home's attention card starts from the signal queue: it
 * holds five ids, and paging `/accounts-list` until they appeared would read a
 * whole book to find five rows.
 *
 * ⛔ **Joined by `account_id`, never by position** — a plain list in no
 * particular order, exactly like `AccountIdentity[]`.
 */
export interface AccountCommercialEntry {
  account_id: string;
  commercial: AccountCommercial;
}

/** ⛔ **Never a bare number** — 📁 ADR-0409 §3: *"a figure without its currency
 * is not a fact."* ⚠️ **`amount` is in the source system's own minor units,
 * uninterpreted**, and Signora never converts: a rate is applied at a moment,
 * so a converted figure is correct briefly and wrong permanently. */
export interface Money {
  amount: number;
  currency: string;
}

/**
 * Where a relationship stands — **in Signora's word and the customer's**.
 *
 * ⚠️ **`position` is `null` when the customer's own stage maps to nothing
 * canonical.** 📁 The CRM Integrations design shows exactly this: *"214
 * opportunities now sit in stages Signora treats as unmapped."* ⛔ **Not
 * unknown, not missing — mapped to nothing, and the screen says so.**
 *
 * ⛔ **Never branch on `label`.** It is the customer's word, carried for
 * display, and they rename it the following week.
 */
export interface CommercialStage {
  position:
    | 'qualifying'
    | 'evaluating'
    | 'negotiating'
    | 'closed_won'
    | 'closed_lost'
    | null;
  label: string;
}

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

/**
 * **Who one account is, and what kind of thing it is** — 🔴
 * [B-261](../../../docs/BUGS.md).
 *
 * 📁 Account 360 persists a collapsed section ***"per user and per account
 * TYPE, not per record"***, and ⛔ **no read the page made carried a type**:
 * `AccountAttention` has none, and `AccountIdentity` deliberately holds none.
 * ⚡ **So the page stored nothing rather than store a preference under a
 * guess** — a rep who collapses *Technology stack* on companies would have
 * found it re-made on every account they opened.
 *
 * ⛔ **`kind` sits BESIDE the identity and never inside it**, which is
 * `ListedAccount`'s arrangement and for its reason: **an identity answers *who
 * is this*, and a classification is a different question about the same
 * account.** Folding it in would put a classification inside an identity
 * resolver, and the same argument already keeps `created_at` out.
 */
export interface AccountIdentityEntry {
  account: AccountIdentity;
  kind: EntityKind;
}

/** What kind of thing a search result is.
 *
 * **Read it from the result, never from the endpoint you called.** Signora
 * searches companies today; a type it cannot search yet is **absent from the
 * results rather than returned as an empty group**, because an empty group
 * would claim it looked and found nothing. */
/**
 * 🔴 **Every kind the graph knows about**, mirroring `EntityKind` in
 * `backend/modules/knowledge_graph/domain/identity.py`.
 *
 * ⚠️ **`person` was added to the backend on 2026-08-06 and not here**, and the
 * search endpoint returns one group per kind — so every search reached
 * `KIND_LABEL['person']`, got `undefined`, and **crashed the whole search
 * region on `.toLowerCase()`** ([B-288](../../../docs/BUGS.md)).
 *
 * ⛔ **`tests/unit/search-kinds.test.ts` reads the enum and fails if this drifts
 * again**, because a hand-mirrored union is a second representation of one
 * truth and the two will part company.
 */
export type SearchResultType = 'company' | 'technology' | 'person';

/** One search result: the account, its type, and **why it is here**.
 *
 * A search matches every name a source has ever claimed, while the list shows
 * the newest one — so a company that renamed comes back under a name the
 * customer did not type and cannot see on the row. `matched_name` is that
 * name, and `is_renamed` marks the rows where the two differ. **Those are the
 * only rows worth annotating**: a surface that explains every match teaches
 * people to stop reading the explanations. */
export interface SearchResult {
  account: AccountIdentity;
  result_type: SearchResultType;
  matched_name: string;
  matched_source: string;
  is_renamed: boolean;
}

/**
 * Whether Signora looked for this kind of thing, and if not why not.
 *
 * **Read before `results`, always.** *"The absence of results and the absence
 * of the group represent different business meanings"* — product owner,
 * 2026-08-05 — so an empty list means nothing until this says which emptiness
 * it is.
 */
export type SearchCoverage = 'searched' | 'not_applicable' | 'not_requested';

/**
 * One kind of thing, what Signora did about it, and what it found.
 *
 * **The group is present whether or not it has results.** A surface that
 * rendered `results` without reading `coverage` would collapse *"nothing
 * matched"* into *"we did not look"*, which is the distinction the group
 * exists to keep.
 */
export interface SearchGroup {
  result_type: SearchResultType;
  coverage: SearchCoverage;
  results: SearchResult[];
}

/** What a reading implies commercially. **Never a sign in the arithmetic** —
 * two accounts can score the same and mean opposite things, and this is the
 * only place that difference survives. */
export type Posture = 'expansionary' | 'contractionary' | 'neutral';

/** How central a hypothesis is to this workspace's ideal customer profile.
 * Declared, never measured. */
export type Relevance = 'primary' | 'supporting' | 'contextual' | 'ignored';

/**
 * **What one kind of finding implies** — `GET /workspaces/{id}/scoring-model`.
 *
 * 📁 Home's attention rows carry severity as *"the left rule, the tag word and
 * the tint together"*, and severity has to be right on the first paint. ⛔ **A
 * per-account score read cannot supply it** — the card holds five accounts and
 * no scores — **and a posture table in the browser would be the second
 * vocabulary the signal catalog exists to prevent.**
 *
 * ⚠️ **`key` and `posture`, and deliberately nothing else.** The weights are
 * the input to a ranking the Buying Score Engine performs; a client able to
 * read them could compute a second ranking that disagrees with the score.
 */
export interface TypePosture {
  key: string;
  posture: Posture;
}

export interface ScoringModel {
  /** ⚡ **A posture that moved between two reads is a model change, not news
   * about a company** — which is the difference this field exists to make
   * visible. */
  version: number;
  types: TypePosture[];
}

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

/**
 * An opportunity a person opened, whatever the score said.
 *
 * **Always `tracking`.** Opening one is a suggestion becoming a record;
 * taking it on is a separate, deliberate act. `generation` counts how many
 * times this account has been opened before — **a reopening is a new
 * opportunity rather than an edited one**, so the deal that closed keeps its
 * history, its reasons and its outcome.
 */
export interface OpenedOpportunity {
  id: string;
  account_id: string;
  stage: Stage;
  generation: number;
  opened_at: string;
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
 * One sentence a model wrote, and the evidence it rests on.
 *
 * ⛔ **`evidence` is never empty** — 📁 the backend refuses an uncited statement
 * before the package is stored, so a caller may render the citation count
 * without guarding for zero.
 */
export interface ReasonedStatement {
  text: string;
  /** Citation tokens (`kind:id`), not prose. */
  evidence: string[];
}

/** A reading that was considered and set aside, with the reason it was. */
export interface AlternativeReading {
  signal_type: string;
  reason: string;
}

/** What the conclusion stands on, in the pipeline's own counted terms. */
export interface DecisionSupport {
  level: string;
  corroborating_providers: string[];
  contributing_events: number;
  evidence_state: EvidenceState;
  /** Whether signals read the same evidence differently. */
  contested: boolean;
  dissenting_signals: number;
}

/** When the reading beneath the conclusion was taken, and which way it moved. */
export interface DecisionTemporal {
  trigger: string;
  basis_at: string;
  computed_at: string;
  /** Signed. **Zero on a first reading**, which is a fact rather than a gap. */
  delta: number;
  trend: string;
  evidence_state: EvidenceState;
  valid_until: string | null;
  supersedes: string | null;
}

/**
 * One conclusion about one account, **and everything needed to disagree with it**.
 *
 * 📁 The endpoint's own words: *"a conclusion arrives with what argues against
 * it."* ⛔ **`limitations` is never empty** — a package that stated none is
 * refused at construction, because an empty one means the catalog was never
 * consulted. ⚠️ **`alternative_readings` MAY be empty, and that is a real
 * answer**: it means nothing else was tested, not that nothing else was
 * possible.
 *
 * ⚡ **The field order is the order of the argument** — what Signora concluded,
 * why, what it rests on, what argues against it, what it cannot see, how to
 * check it, and who produced it.
 */
export interface DecisionPackage {
  account_id: string;
  proposition: ReasonedStatement;
  /** The conclusion in one sentence, cited like any other. */
  summary: ReasonedStatement;
  stated_reasoning: ReasonedStatement[];
  supporting_evidence: string[];
  support: DecisionSupport;
  temporal: DecisionTemporal;
  alternative_readings: AlternativeReading[];
  limitations: string[];
  suggested_validation: string[];
  catalog_version: number;
  model: string;
  vendor: string;
  prompt_name: string;
  prompt_version: number;
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

/**
 * 🔴 **What one declared criterion actually predicted** — `GET
 * /workspaces/{id}/icp-performance`.
 *
 * 📁 The endpoint's own words: ***"lift is `P(won | criterion holds) ÷ P(won
 * overall)`. Above 1.0 the criterion predicts; at 1.0 it tells you nothing;
 * below 1.0 it is selecting against you"*** — the last being the most useful
 * thing it can say and the one nobody expects.
 *
 * ⚡ **This is the sentence the ICP Builder design opens with**: 📁 `Design
 * Documents/Fortune Signora ICP Builder.html` — ***"Every criterion is scored
 * against closed-won evidence, not opinion."***
 */
export interface CriterionLift {
  /** Which part of the description this measures — `industry`, `country` or
   *  `employees`. */
  criterion: string;
  /**
   * ⛔ **`null` when it cannot be measured** — nothing satisfied it, nothing
   * was measured, or nothing has been won yet. 📁 The schema is emphatic:
   * ***"Never render null as 1.0."***
   */
  lift: number | null;
  /** Decided accounts where this criterion held. **The sample size behind
   *  `lift`** — read it before the multiple. */
  satisfied: number;
  satisfied_won: number;
  /** Every decided account this could be measured on, satisfied or not. */
  measured: number;
  measured_won: number;
  /** ⛔ **Dropped because no source described the account**, and they do NOT
   *  count against the criterion. */
  unmeasured: number;
  /** 📁 True below 22 satisfying accounts — **the threshold the design itself
   *  states**: *"treat as directional, not settled."* */
  is_directional: boolean;
}

/**
 * What one product's ideal-customer description predicted.
 *
 * ⛔ **No overall verdict, and that is the endpoint's deliberate choice**:
 * rolling the criteria into *"your ICP is good"* needs a rule for the ones
 * nothing was observed for, and every available rule is a judgement.
 */
export interface IcpMeasurement {
  product_id: string;
  /** **The honest denominator** — if this is small, nothing above it is
   *  settled. */
  decided: number;
  /** One entry per criterion kind, always all three, in a stable order. */
  criteria: CriterionLift[];
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
  /**
   * Who decided — **not the same person as who held it**.
   *
   * An account nobody ever took on can still be dismissed, so `owner_id` left
   * that judgement unattributable: the row could say *yours* only when the
   * reader had *held* it. Resolved through the roster the page already has.
   */
  decided_by: string | null;
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
 * When Signora last looked at one company, and whether it found anything — A7.
 *
 * **Provider Platform's, not Commercial Profile's**, which is why it arrives on
 * its own request rather than as a field on `TargetAccountList`. The module
 * holding the list may not read the module holding the attempts — the
 * dependency runs the other way — so this screen composes the two, exactly as
 * the attention list composes account identities.
 *
 * **Two fields carry four states**, and none of them may collapse:
 *
 * | `last_attempt` | `stored_anything` | |
 * |---|---|---|
 * | `null` | `false` | Nobody has ever looked |
 * | a moment | `false` | Looked, and found nothing — the case A4 could not say |
 * | a moment | `true` | Looked, and evidence arrived |
 * | `null` | `true` | Read before Signora recorded when it looked |
 */
export interface SubjectCoverage {
  /** The company name exactly as declared. Unresolved by design — it keys a
   * declaration entry, never an entity. */
  subject: string;
  /** When a provider last **completed** a read, whether or not anything came
   * back. Null is two different things; read `stored_anything` to tell them
   * apart. */
  last_attempt: string | null;
  /** Whether any read has ever stored evidence. */
  stored_anything: boolean;
}

/** One technology this workspace competes against. */
export interface Competitor {
  id: string;
  name: string;
}

/**
 * Who this workspace competes against, and who last said so.
 *
 * **The sixth declaration, and the first about a risk.** Signora records the
 * names and grades none of them: how much a rival moves an account is decided
 * by a reviewed model, not by anything a customer types here.
 */
export interface DeclaredCompetitors {
  /** **0 when nothing has been declared** — which is different from a customer
   * who declared an empty list, and that reads as version 1. */
  version: number;
  competitors: Competitor[];
  /** Null only at version 0. */
  updated_at: string | null;
  /** Null only at version 0. */
  updated_by: string | null;
}

/** A complete statement of the competitor list, replacing `expected_version`. */
export interface DeclareCompetitors {
  expected_version: number;
  competitors: Competitor[];
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

/**
 * What happened when Signora last actually tried to use a connection.
 *
 * **Distinct from `state`, and the distinction is the whole point.** `state`
 * says what the records imply — a grant exists, nothing expired, nobody
 * revoked it — and a credential that quietly lost a permission holds a perfect
 * state and does not work.
 *
 * **`unknown` means nothing has been tried. It does not mean working.**
 */
export type ConnectionHealth = 'healthy' | 'degraded' | 'unknown';

export interface Connection {
  id: string;
  integration: string;
  label: string;
  state: string;
  connected_at: string | null;
  attention: ConnectionAttention;
  reason: string | null;
  health: ConnectionHealth;
}

/**
 * 📁 **Session Continuity tier 4** — one record this person opened.
 *
 * ⛔ **No title.** An account's name is the Knowledge Graph's to state and moves
 * without this fact hearing about it; the card resolves names through the
 * identity surface, exactly as the attention card does.
 */
export interface ViewedRecord {
  entity_id: string;
  kind: 'account' | 'report' | 'research';
  viewed_at: string;
}

/**
 * **One run of the research agent** — `GET /workspaces/{id}/research`.
 *
 * 📁 Home's `card.agentqueue` and `card.agentruns` both depend on
 * `agents.runs`, and this is it: *"scheduled and triggered runs"* with where
 * each got to.
 */
export interface ResearchRun {
  request_id: string;
  account_id: string;
  requested_by: string;
  requested_at: string;
  /**
   * ⚠️ **`nothing_to_research` is NOT a failure** — the run finished and found
   * nothing worth comparing, which is a real answer on a thin account.
   */
  status: 'requested' | 'running' | 'completed' | 'nothing_to_research' | 'failed';
  updated_at: string;
  /** Why it failed, verbatim. **Null unless `status` is `failed`.** */
  detail: string | null;
  /**
   * How many distinct sources the run read. **Null unless it completed** —
   * ⛔ **`0` is a different fact**: it completed and cited nothing.
   */
  sources: number | null;
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

/**
 * One recorded change to a company, and who says so.
 *
 * **The layer beneath a claim on the brief.** The account header says *"grew
 * headcount 15% over 32 days"*; this is what that rests on — every observed
 * transition, with the provider that reported it and the moment it says the
 * new value became true.
 *
 * `previous_value` is `null` on a first sighting, which is **not** the same as
 * a change from nothing: the first time a provider reports a value there is no
 * transition, and rendering one would invent a history the pipeline never saw.
 */
export interface AccountObservation {
  id: string;
  /** What changed — a `ClaimAttribute` key, in the pipeline's vocabulary. */
  attribute: string;
  /** Who reported it. Named, because two providers can disagree and a reader
   * deciding whether to believe a change needs to know whose change it is. */
  provider: string;
  /** Whether this is a transition between values or a one-off event. */
  kind: string;
  /** Which way it moved, or that it did not move. */
  direction: string;
  /** What it was. **Null on a first sighting**, where there is no transition. */
  previous_value: unknown | null;
  /** What it became. */
  current_value: unknown;
  /** How far it moved, where that is meaningful. Null where it is not — a
   * change of country has no magnitude, and inventing `1` would be a number a
   * reader could sort by. */
  magnitude: number | null;
  /** When the provider says the new value was true. **Not when Signora saw
   * it** — those differ, and only one of them is a fact about the company. */
  observed_at: string;
  previous_observed_at: string | null;
  /** When Signora recorded it. */
  recorded_at: string;
}

/**
 * Where a signal stands in the triage queue — **three states, none stored.**
 *
 * Derived from the decision in force and the current time, which is exactly
 * why a snoozed signal comes back on its own: the clock moves, and nothing has
 * to run. `closed` is deliberately not `done` — a dismissal closes a signal
 * and means Signora was wrong, which is the opposite of finished.
 */
export type QueueState = 'open' | 'snoozed' | 'closed';

/** One decision somebody recorded about one signal. Immutable — a correction
 * is a new record naming the one it replaces, never an edit. */
export interface Resolution {
  id: string;
  signal_id: string;
  /** `actioned` · `assigned` · `snoozed` · `dismissed`. */
  outcome: string;
  assigned_to: string | null;
  snoozed_until: string | null;
  /** Present only on a dismissal, where it is required. */
  reason: string | null;
  actor_id: string;
  recorded_at: string;
  /** The earlier decision this replaces. Null on the first. */
  supersedes: string | null;
}

/**
 * One row of the triage queue.
 *
 * **`resolution: null` means still open and is not a decision to do nothing** —
 * that is what `actioned` is for, and conflating them loses the difference
 * between work somebody finished and work nobody has looked at.
 */
export interface QueueEntry {
  signal_id: string;
  signal_type: string;
  /** Which account. Load-bearing on the workspace queue — an entry that cannot
   * say which company it concerns is one nobody can act on. */
  entity_id: string;
  /** Why this matters *here*, and what it rests on — authored per signal where
   * the reasoning happens. ⛔ **Never recomposed in a component**: the catalog's
   * `why_it_matters` is a fact about the TYPE, so rendering that instead would
   * put one sentence under fifty different signals and read as right. */
  rationale: string;
  state: QueueState;
  resolution: Resolution | null;
}

/** What a person decided. A discriminated union, so a dismissal without a
 * reason is unconstructable rather than merely rejected. */
export type ResolveOutcome =
  | { kind: 'actioned' }
  | { kind: 'assigned'; to: string }
  | { kind: 'snoozed'; until: string }
  | { kind: 'dismissed'; reason: string };

/**
 * **Pipeline health — the executive composition's one card, in one response.**
 *
 * 📁 [TASK-1425](../../../docs/BACKLOG.md), against
 * `Fortune Signora Home.dc.html`'s registry entry **`card.pipeline` —
 * *"Coverage, stage distribution, movement"***. ⚡ **The read is
 * [TASK-438](../../../docs/BACKLOG.md)'s and is already on `main`**:
 * `GET /workspaces/{id}/pipeline-health`. ⛔ **Nothing new is built behind it.**
 *
 * ⚠️ **The design's *coverage* has no source and is not modelled here.**
 * Coverage is pipeline against a target, and **nothing in this product holds a
 * target** — a computed zero would read as *"you have no coverage"*, which is
 * a different claim and a false one. **The same refusal the backend already
 * makes about ICP coverage, one layer up.**
 */
export interface StageConversion {
  from_stage: Stage;
  to_stage: Stage;
  entered: number;
  advanced: number;
  rate: number;
}

export interface StageAgeing {
  stage: Stage;
  open_count: number;
  median_days: number;
  oldest_days: number;
}

export interface OwnerLoad {
  owner_id: string;
  open_count: number;
  won: number;
  lost: number;
}

export interface PipelineMovement {
  opportunity_id: string;
  account_id: string;
  stage: Stage;
  previous_stage: Stage;
  owner_id: string;
  actor_id: string;
  reason: string;
  occurred_at: string;
}

export interface PipelineHealth {
  conversions: StageConversion[];
  ageing: StageAgeing[];
  owners: OwnerLoad[];
  movements: PipelineMovement[];
  /** ⚡ **Echoed by the API so a card can say *"since 1 August"* without
   * remembering what it asked for.** 📁 The design: *"every empty card names
   * what was checked and when."* */
  movements_since: string;
}

/**
 * **One person's preferences in one workspace** — [TASK-1424](../../../docs/BACKLOG.md).
 *
 * ⚠️ **Only the fields this product actually reads are declared.** ⛔ The API
 * publishes twelve more — theme, density, answer style — and **a type that
 * mirrored an endpoint rather than a caller would make every unused field look
 * like a capability somebody had built a screen for.** ⚡ They join this type
 * when a screen reads them.
 */
/**
 * 🔴 **What entering a workspace reports about the entry** — Home hierarchy 2.
 *
 * 📁 Entry rule 12's confirmation strip is *"dismissible, never blocking, and
 * **gone on the second visit that day**"*, and Home state 13 suppresses it.
 *
 * ⛔ **The answer, not the moment.** *"The same calendar day"* is a question about
 * a zone and a clock the server owns; a client deriving it from a timestamp would
 * answer differently on a device whose clock or timezone is wrong.
 */
export interface WorkspaceEntry {
  first_entry_today: boolean;
  /**
   * 🔴 **Authenticated Entry rule 22** — *"the new workspace becomes active, with
   * a **welcome strip**"*, and that strip *"replaces the confirmation strip"*.
   *
   * ⚡ **`true` on somebody's very first arrival in this workspace**, which is
   * what tells the two strips apart: **rule 12 confirms a workspace you have been
   * in before; rule 22 welcomes you to one you have not.**
   *
   * ⛔ **Derived server-side from `last_entered_at`, never a flag the client
   * sends.** A query parameter would survive a bookmark and a share, so a link
   * could welcome somebody to a workspace they have used for a year.
   */
  first_entry_ever: boolean;
  /**
   * 🔴 **Authenticated Entry rule 21** — *"a notice naming what changed and by
   * whom. The composition may differ from yesterday and **that must not be
   * silent**."*
   *
   * ⛔ **`null` on every ordinary arrival.** ⚡ Answered from the same read that
   * decides `first_entry_today`, because *"since last session"* is a question
   * about `last_entered_at` and recording the entry overwrites it.
   */
  role_change: {
    previous_role: 'owner' | 'member';
    new_role: 'owner' | 'member';
    changed_by: string;
    /** ⚠️ **An address, not a name** — ADR-0026 leaves the API no names. */
    changed_by_email: string | null;
    at: string;
  } | null;
}

export interface PersonPreferences {
  /**
   * 🔴 **Whether this person has closed the first-run overlay.**
   *
   * ⚡ **The fact, not the moment** — the server stores when, and a client that
   * received a timestamp it did not need is a client that could display it
   * wrongly.
   */
  first_run_dismissed: boolean;
  /**
   * 🔴 **Whether the invite-the-team card is hidden RIGHT NOW.**
   *
   * ⛔ **The answer, not the moment and not the window.** 📁 *"Hides them for 30
   * days"* is a question about the server's clock — ⚡ **a client computing it
   * from a timestamp would answer differently on a device whose clock is
   * wrong**, and this is the one field where that would silently un-hide a card
   * somebody put away.
   */
  invite_hidden: boolean;
  /**
   * 🔴 **Home state 04** — whether this person has already been told setup
   * finished. 📁 *"A one-time strip"*, and `AC-H03`'s *"shown exactly once"*.
   *
   * ⛔ **Not whether setup IS complete.** That is derived from the workspace's
   * own connections and never stored; this is a fact about a reader.
   */
  setup_complete_seen: boolean;
  /**
   * 🔴 **Home §10's *Customise* arrangement, per composition** — 📁 `3.2.3`'s
   * *"card order within a composition is stable across visits."*
   *
   * ⛔ **An absent key is *never customised***, which renders the registry's own
   * order. ⚡ Not the same as *customised to nothing*, which would be an empty
   * Home and is a thing a person can actually ask for.
   */
  home_layout: Record<string, { order: string[]; hidden: string[] }>;
  /**
   * 📁 **Screen `07`'s first consent** — *"Surface insights I did not ask for ·
   * Ranked findings on your home page. Off means Signora only answers
   * questions."*
   *
   * ⚡ **It joins this type because a screen now reads it**, which is exactly
   * what the note above describes. ⛔ **Not a new capability** — migration
   * `0045_ai_preferences` has carried it since it landed; onboarding is the
   * first surface that asks.
   */
  ai_insights: boolean;
  /**
   * 📁 **Screen `07`'s second** — *"Draft emails and summaries · Drafts only.
   * Nothing sends without your approval, ever."*
   */
  ai_drafts: boolean;
  /**
   * 📁 **Home's resolution rule 2** — *"Person has set a start-page preference of
   * a specific composition… Honoured over role."*
   *
   * ⛔ **`null` means *not set*, and that is not `'seller'`.** The resolver falls
   * through to the role rules when it is absent, so treating `null` as a value
   * would make rule 3 unreachable.
   */
  home_composition: 'executive' | 'seller' | 'revenue_operations' | 'activation' | null;
}

/**
 * 🔴 **One label a customer put on their own accounts** —
 * [TASK-466](../../../docs/BACKLOG.md), against
 * [ADR-0411](../../../docs/architecture/adr/0411-customer-organized-account-metadata.md).
 *
 * ⛔ **Not a `ClaimAttribute` and never one.** 📁 The ruling decides it by
 * authorship: *"a claim records what a provider asserted; nobody asserted a
 * customer's own tag."*
 */
export interface AccountTag {
  id: string;
  /** ⚡ **As the customer typed it**, never the folded form uniqueness uses. */
  name: string;
  /**
   * 📁 The design's chip token. ⛔ **`ai` is not among the values the server
   * will ever send** — that tone is reserved for what Signora inferred, and a
   * human opinion wearing it is the one confusion the evidence model exists to
   * prevent.
   */
  tone: 'risk' | 'warn' | 'pos' | 'neutral';
}

/**
 * **Which labels each of the requested accounts wears.**
 *
 * ⛔ **An account with no tags is ABSENT rather than present-and-empty**, and
 * the request named exactly which accounts were asked about — so *"we looked
 * and found none"* is unambiguous without a key for it.
 */
export interface AccountTagAssignments {
  assignments: Record<string, string[]>;
}

/**
 * 🔴 **One named set of capabilities** — [TASK-1479](../../../docs/BACKLOG.md)
 * ⓸, against
 * [ADR-0410](../../../docs/architecture/adr/0410-authorization-capability-layer.md).
 *
 * ⛔ **No permission list on the role, and that is the contract rather than an
 * omission.** 📁 ADR-0410 §2 keeps the grants in `policy.csv`, so a copy here
 * would be the second authorization model the ruling forbids — **stale the
 * moment somebody edits the file the enforcer actually reads.**
 *
 * ⚡ **What a role permits is asked ABOUT A PERSON**, through
 * `EffectivePermissions` below, because that is the only question the enforcer
 * can answer honestly.
 */
export interface CapabilityRole {
  role_id: string;
  /** ⚡ **As the customer typed it.** `Analyst`, never `cap:analyst`. */
  name: string;
  /**
   * ⚠️ **How many people hold it**, derived on read. ⛔ **What a *delete*
   * control must ask before offering itself** — the database refuses to remove
   * a role somebody holds, and a control it would reject is one that goes
   * nowhere.
   */
  holders: number;
}

/** One thing somebody may do. Both halves are the platform's vocabulary, so
 * neither reaches a screen unrendered (ADR-0034). */
export interface Permission {
  resource: string;
  action: string;
}

/**
 * 🔴 **What one person may actually do here** — the design's *Effective
 * permissions*.
 *
 * 📁 **ADR-0410 §3: computed, never stored.** ⚡ **Every entry was asked of the
 * same enforcer that decided the request which returned it**, so this screen
 * and the enforcement point cannot disagree.
 */
export interface EffectivePermissions {
  user_id: string;
  /**
   * ⚠️ **`null` means they authorize as their membership role** — including
   * when a role they were assigned no longer resolves. ⛔ **Showing a role
   * somebody is not effectively holding is the stale claim §3 forbids arriving
   * by a different route.**
   */
  role_name: string | null;
  permissions: Permission[];
}

/**
 * 🔴 **What a role change would trade** — the design's *Change role — Member →
 * Analyst*.
 *
 * 📁 **Its own words: *"Both directions are shown, because a role change is a
 * trade rather than a promotion."*** ⛔ **No `gains`/`loses` on the wire**:
 * they are the set difference of these two lists, and a third representation
 * of one fact is the duplication §2 forbids.
 */
export interface RoleChangePreview {
  user_id: string;
  current: EffectivePermissions;
  proposed: EffectivePermissions;
}

/**
 * **How many accounts the workspace holds** —
 * `GET /workspaces/{id}/accounts-count`.
 *
 * 📁 **The design's Companies header prints two numbers** — *"8,412 total · 312
 * in view"* — ⚡ **and they answer different questions.** *In view* is a
 * property of the page the customer is looking at and the screen already knows
 * it; **total is a property of their whole book.**
 *
 * ⛔ **Not derivable from the list.** `accounts-list` is keyset-paginated and
 * returns at most a page, so a screen counting loaded rows learns how much it
 * has fetched — **and printing that beside the word *total* would be a
 * falsehood that grows with every page.**
 */
export interface AccountCount {
  /** Every account in the workspace. **Zero is a real answer**, and the
   * designed empty state is reached through this read rather than instead of
   * it. */
  total: number;
}

/**
 * **A view somebody saved and everybody shares** —
 * `GET /workspaces/{id}/saved-views`.
 *
 * 📁 **The finalized Companies design's tab row.** ⚡ **Shared rather than
 * personal**, which is the endpoint's own rule: *"filtering by author would
 * make a shared capability read as a private one."*
 *
 * ⛔ **No count and no badge.** 📁 The design draws *41* beside a name and
 * *Live* / *AI* / *Shared* after it; **neither is published.** A count needs
 * `declaration` executed against the book, and a badge is a classification
 * nothing stores — **so the tabs carry names, and never a number nobody
 * measured.**
 */
export interface SavedView {
  id: string;
  workspace_id: string;
  name: string;
  /** ⚠️ **The view's own query, shape defined by whoever wrote it.** ⛔ Not
   * interpreted here: this screen renders the name and selects by id. */
  declaration: Record<string, unknown>;
  created_by: string;
  created_at: string;
  supersedes: string | null;
  retired_at: string | null;
}


/**
 * One step a workspace must take before Signora is useful, as a module declares it.
 *
 * **The declaration, never the progress.** Whether it is done is derived from
 * what the workspace actually has — a connection that works, a colleague who
 * joined — and folding the two together would make a static registry look like
 * per-tenant state.
 */
export interface ActivationStep {
  /** Stable. The client keys its own presentation from it. */
  id: string;
  /** Lower is earlier. Order by this, never by array position. */
  priority: number;
  /** Whether Signora can conclude anything without it. */
  blocking: boolean;
}


/**
 * One item in the notification panel.
 *
 * ⛔ **No actor name and no subject title, and both absences are contracts.**
 * 📁 `C-203` is deferred with a concrete trigger — *"nothing in the product can
 * render a person's name"* — because Better Auth is the sole Authentication
 * Authority and the Python tier only verifies. ⚡ **An agent's name IS returned**,
 * because the platform authored it rather than resolving it.
 *
 * ⚠️ **`subject_id` without a title is deliberate too**: a cached account name
 * would render one that changed last week, and the surface being opened already
 * holds the current one.
 */
export interface AppNotification {
  id: string;
  /** 📁 The panel's tabs are these plus *All*. */
  category: 'needs_you' | 'mention';
  actor_kind: 'person' | 'agent';
  actor_person_id: string | null;
  /** Present only for an agent — a person's name is `C-203`. */
  actor_agent_name: string | null;
  subject_kind: string;
  subject_id: string;
  /** What happened, in the customer's vocabulary. */
  summary: string;
  /** What is expected of the recipient. */
  expectation: string;
  occurred_at: string;
  /** ⛔ `null` means unread. **The panel's dot reads this**, never the badge
   *  count, which says how many without saying which. */
  read_at: string | null;
}

export interface NotificationFeed {
  notifications: AppNotification[];
}

/** 📁 *"Count badge caps at 99+."* — the cap is the server's, not the shell's. */
export interface UnreadBadge {
  unread: number;
  /** ⛔ Read this rather than comparing `unread` to `cap`. */
  capped: boolean;
  cap: number;
}
