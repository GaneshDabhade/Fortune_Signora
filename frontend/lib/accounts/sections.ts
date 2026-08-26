/**
 * **What Account 360 is made of, and what the platform can actually supply** —
 * [TASK-1415](../../../docs/BACKLOG.md), against 📁
 * `Fortune Signora Account 360.dc.html`.
 *
 * ## 🔴 The row's own claim is the constraint
 *
 * > 📁 ***"Account score with its delta · customer health · buying intent · the
 * > signals timeline · a research summary · open opportunities — each a
 * > composition of intelligence the platform ALREADY produces."***
 *
 * ⚠️ **That claim is half true, and this file is the measurement rather than
 * the assumption.** ✅ **Seven of the design's twenty-one sections have a read
 * behind them today.** ⛔ **Fourteen do not** — and 📁 [§20c](../../../CLAUDE.md)
 * decides what happens to those: *"screens without a shipped module behind them
 * ship a designed empty state"*, **never invented figures.**
 *
 * ## 🔴 The count said FIFTEEN and the design's own page navigation says EIGHTEEN
 *
 * ⛔ **Six sections the design declares were missing from this file entirely** —
 * not marked `absent`, **absent from the declaration**: 📁 `pageNav`'s
 * *Emails · Files · Notes · Tasks · Custom fields · History*.
 *
 * ⚠️ **Which is the one failure this file exists to prevent.** Its own words,
 * below: *"a page that omits a section nobody built is indistinguishable from a
 * page with a bug, and the next lane cannot tell which."* **Six of them were
 * exactly that, inside the register written to stop it.**
 *
 * ⚡ **Twenty-one rather than eighteen** because the design splits *"Score &
 * health"* across `scoreDrivers` and `healthRows`, and draws `intentRows` and
 * the narration as their own blocks — **four sections the rail names as two.**
 *
 * ## ⚡ Why a declaration rather than the page just rendering what it has
 *
 * ⛔ **A page that omits a section nobody built is indistinguishable from a page
 * with a bug**, and the next lane cannot tell which. ✅ **Naming all fifteen and
 * marking seven `absent` makes the gap a fact somebody can act on** — and it is
 * what the *"On this page"* rail needs anyway, since 📁 the design gives that
 * rail a count per section.
 *
 * 🔴 **`absent` is never *"coming soon"*.** 📁 The rail already paid for that
 * once — *"at M12.3, three of six said `coming soon` on the screen a customer
 * sees first"* — **so an absent section states what it would show and what
 * Signora cannot answer yet, in the customer's words.**
 */

/** ⚡ **Whether the platform can fill this section today.** */
export type SectionSupply =
  /** ✅ A read exists and returns real data. */
  | 'supplied'
  /**
   * ⛔ **Nothing produces this.** ⚠️ **Distinct from *empty***: an empty
   * section means *this account has none*; an absent one means **Signora
   * cannot answer the question at all**, and the two must never render alike
   * ([P-A](../../../docs/DOMAIN_DISCOVERY_REGISTER.md), applied to a section
   * rather than to a row).
   */
  | 'absent';

export interface AccountSection {
  /**
   * 📁 **The design's own anchor, verbatim** — `pageNav`'s `href` with its
   * `#` removed.
   *
   * 🔴 **Not a slug this file chose.** ⚡ **The anchor is a CONTRACT**, and the
   * design's own `stateRules` say so twice: *"anchor links from the page nav
   * auto-expand the target section"* and *"the URL updates so an expanded
   * section is shareable."* ⛔ **A shareable URL that does not match the design
   * is a different URL.**
   *
   * ⚠️ **Seven were the descriptive long form rather than the design's** —
   * `#opportunities` for `#opps`, `#org-chart` for `#org`, `#relationships`
   * for `#graph`, `#tech-stack` for `#tech`, `#competitors` for `#compete`,
   * `#emails` for `#email`, `#custom-fields` for `#fields`.
   * 📁 [B-299](../../../docs/BUGS.md) ④.
   */
  readonly id: string;
  /**
   * 📁 **The design's own SECTION HEADING, verbatim** — the `14.5px/600` title
   * the mockup draws above the section's content.
   */
  readonly label: string;
  /**
   * 📁 **The design's own RAIL entry, verbatim** — `pageNav`'s label, **which
   * is a different string from the heading on seven sections.**
   *
   * ⚡ **Two vocabularies, both the design's**, and the divergence is the
   * point rather than an inconsistency: *Contacts & committee* in a 184px rail,
   * ***Contacts & decision makers*** over the section itself. ⛔ **The rail
   * rendered the heading**, so the design's compact vocabulary reached no
   * screen at all.
   *
   * ⚠️ **Omitted where the design uses ONE string for both**, which is most of
   * them — ⛔ **stating it twice would invite the two copies to disagree**
   * ([§2](../../../CLAUDE.md)), and the seven that differ are then the only
   * seven this field appears on.
   */
  readonly rail?: string;
  readonly supply: SectionSupply;
  /**
   * ⚡ **What fills it, or what would.** ✅ **A hook name when supplied** — so a
   * reader can check the claim — ⛔ **and the missing capability when absent**,
   * stated in engineering terms because this string never reaches a screen.
   */
  readonly source: string;
  /**
   * 📁 **What a customer is told where a section cannot be filled.** ⛔ **Only
   * on an absent section**, and never *"coming soon"*: it says what the section
   * would show and what Signora cannot answer yet.
   *
   * ## 🔴 It says what SIGNORA does not do, never what the READER has not done
   *
   * ⛔ **Four of these asserted that a provider was not connected** —
   * [B-299](../../../docs/BUGS.md) ⑦ — ***"No intent source is connected to
   * your organization yet"***, ***"None is connected"***, ***"Signora is not
   * reading those for this account"***.
   *
   * ⚠️ **Measured on the Playground: five enrichment providers are connected
   * and syncing** — `apollo`, `bombora`, `builtwith`, `coresignal`,
   * `crunchbase` — **and every one of the four sections that claimed
   * otherwise has observations on company entities**: 29 `intent_topic_surge`,
   * 36 `person_identity` carrying `reports_to`, 2 `technology_detected`,
   * `funding_round` and `acquisition`. ⛔ **The product told a customer to
   * connect something they had already connected, and pointed them away from
   * the timeline where it was already showing.**
   *
   * 🔴 **The shape, and it is this file's version of the defect the whole
   * screen keeps producing**: ⚡ **a static declaration answered a question it
   * had never read.** ⛔ **A workspace's connections are per-workspace and
   * this module has no connection read** — so any sentence about them is a
   * guess that happens to be right in one direction.
   *
   * ✅ **The rule that follows is checkable rather than remembered**, and
   * `account-sections.test.tsx` checks it: **a capability statement is this
   * file's to make; a setup statement is not.** ⚡ **What each of these
   * sections would need in order to stop being absent is
   * [C-1564](../../../docs/LANE_COORDINATION.md)** — the data is on the
   * account, no route publishes a grouping, and the grain is the producing
   * module's question. ⚡ **It also survives the
   * product growing** — the day a mailbox provider ships, *"Signora does not
   * read mailboxes yet"* becomes false loudly, where *"none is connected"*
   * would have become false silently.
   */
  readonly absence?: string;
}

/**
 * 📁 **The design's sections, in the design's order.**
 *
 * ⚠️ **Measured on 2026-08-10 against `lib/query/hooks.ts`**, which publishes
 * every account-scoped read this product has: `useAccountIdentities`,
 * `useAccountScore`, `useAccountOpportunity`, `useAccountNarration`,
 * `useAccountValidation`, `useAccountResearch`, `useAccountObservations`,
 * `useAccountTimeline` — **plus the two workspace-scoped declarations a record
 * page reads**, `useBuyingCommittee` and `useCompetitors`.
 */
export const ACCOUNT_SECTIONS: readonly AccountSection[] = [
  {
    id: 'summary',
    label: 'Summary',
    supply: 'supplied',
    source: 'useAccountNarration — the plain-language reading, with its evidence',
  },
  {
    id: 'score',
    label: 'Account score',
    rail: 'Score & health',
    supply: 'supplied',
    source: 'useAccountScore — the score, its delta and every contribution',
  },
  {
    id: 'health',
    label: 'Customer health',
    supply: 'absent',
    // 📁 The design's own figures are *"91% usage"* and a healthy/at-risk
    // verdict. ⛔ Nothing in this product ingests product-usage telemetry.
    source: 'no product-usage source exists; no provider supplies telemetry',
    absence:
      'Signora does not yet read how this customer uses your product, so it cannot tell you whether usage supports the deal or contradicts it.',
  },
  {
    id: 'intent',
    label: 'Buying intent',
    supply: 'absent',
    // 🔴 **This read *"no third-party intent provider is connected"*, and on
    // the Playground that is FALSE** — [B-299](../../../docs/BUGS.md) ⑦.
    // ⛔ **`bombora` is connected and syncing**, and 29 `intent_topic_surge`
    // observations carry `topic`, `score` and `trend` on company entities.
    // ⚡ **What is missing is the design's INDEX** — *"intent index"* over
    // `intentRows` — **which needs a read that groups them, and no route
    // publishes one.**
    source:
      'bombora delivers intent_topic_surge as observations on the account; nothing publishes the design’s intent index — no route groups them',
    absence:
      'Third-party intent — which topics this account is researching, and how strongly — reaches Signora as signals and appears in the timeline. Signora does not yet gather them into an index.',
  },
  {
    id: 'signals',
    label: 'Signals timeline',
    supply: 'supplied',
    // 🔴 **This said *"what changed, and what Signora made of it"* and the
    // second half is not true** — [B-299](../../../docs/BUGS.md) ⑨.
    // ⛔ **`AccountObservation` carries `attribute`, `provider`, `kind`,
    // `direction` and `magnitude` — a change and its provenance, and no
    // interpretation at all.**
    //
    // ⚠️ **📁 The design's `signalEvents` are one layer up**: each has a
    // `tag` (*Risk*), an `action` (*Open call*) and a rationale. **Those are
    // SIGNALS**, and the posture that tags them is published — `GET
    // /scoring-model` returns `TypePosture[]` precisely so no client builds a
    // second vocabulary. ⛔ **What does not exist is a per-account signal
    // read**: `/triage` is workspace-wide with no account filter.
    // ⚡ **So the section renders the nearest producer that exists, and
    // 📁 [C-1564](../../../docs/LANE_COORDINATION.md) carries what the
    // design's version would need.**
    source:
      'useAccountObservations — what changed and who reported it. NOT what Signora made of it: the design draws postured signals, and no per-account signal read exists',
  },
  {
    id: 'research',
    label: 'Research summary',
    rail: 'Research',
    supply: 'supplied',
    source: 'useAccountResearch — company, market and relationship research',
  },
  {
    id: 'opps',
    label: 'Open opportunities',
    rail: 'Opportunities',
    supply: 'supplied',
    source: 'useAccountOpportunity — the opportunity and its stage',
  },
  {
    id: 'contacts',
    label: 'Contacts & decision makers',
    rail: 'Contacts & committee',
    // 🔴 **Corrected from `supplied` — [TASK-1476](../../../docs/BACKLOG.md),
    // 2026-08-12.** ⚠️ **The old cell hedged with *"partially"* and named
    // `useBuyingCommittee` as the source, and that read is a DIFFERENT
    // QUESTION.** 📁 Its own summary is *"who decides about what this
    // workspace **sells**"* — `commercial_profile`'s ICP committee, **the
    // same answer on every account in the workspace.** ⛔ **Rendering it under
    // this heading would tell a rep that Acme has these six people.** ⚡ **Same
    // words, different subject**, and `supplied` is the claim that cost the
    // rail an entry it could never anchor.
    supply: 'absent',
    // ⚠️ **`people` is the near miss, and naming it is the point.**
    // `AffiliationReader.at_company(...)` is published and would give **a
    // title, a seniority band and the period held** — ⛔ **and no name, ever**:
    // [C-221](../../../docs/LANE_COORDINATION.md) is that module's
    // specification rather than a limitation, the `person` table has no name
    // column, and whether a provider could even supply one is ❓1 of
    // [ADR-0400](../../../docs/architecture/adr/0400-person-as-an-entity.md),
    // gated on [TASK-429](../../../docs/BACKLOG.md) — **a commercial decision,
    // not an engineering one.** ⛔ **The design's row is `name` · `role`
    // *(Champion / Blocker / Economic buyer)* · `relationship` ·
    // `engagement %`**: the second is a judgement `people/public` refuses by
    // AST test, the third and fourth need interaction history nothing records.
    // ⚡ **An anonymous title list is not this section** — it is a different one
    // the design does not draw, and inventing it is what [§21](../../../CLAUDE.md) forbids.
    source:
      'people publishes AffiliationReader.at_company (title, seniority, interval) but never a name — C-221, TASK-429; the design needs name, buying role, relationship and engagement, and no read supplies any of the four',
    absence:
      'Signora records that a role was held at this company and for how long, but not who holds it. Named contacts, their part in the decision and how warm each relationship is are not something Signora can see yet.',
  },
  {
    id: 'org',
    label: 'Organisation chart',
    rail: 'Org chart',
    supply: 'absent',
    // 🔴 **This said *"nothing infers reporting lines"* and that is FALSE** —
    // [B-299](../../../docs/BUGS.md) ⑦. ⛔ **`person_identity` carries
    // `reports_to` with `source: 'inferred' | 'confirmed'`**, 36 observations
    // on the Playground. ⚠️ **What `people` refuses to publish is the NAME**
    // ([C-221](../../../docs/LANE_COORDINATION.md)), **and a chart of
    // anonymous boxes is not this section.**
    source:
      'person_identity observations carry reports_to (inferred|confirmed); people publishes no name — C-221 — and a chart without names is a different section',
    absence:
      'Signora sees that this company has reporting lines and does not record who is in them. A chart of unnamed boxes would not tell you anything you could act on.',
  },
  {
    id: 'graph',
    label: 'Relationship graph',
    supply: 'absent',
    source: 'nothing measures relationship strength between people',
    absence:
      'Signora cannot yet tell you who on your side knows whom on theirs, or how well.',
  },
  {
    id: 'tech',
    label: 'Technology stack',
    rail: 'Tech stack',
    supply: 'absent',
    // 🔴 **This said *"no enrichment provider detects installed technology"*
    // and told the customer none was connected — both FALSE** —
    // [B-299](../../../docs/BUGS.md) ⑦. ⛔ **`builtwith` is connected and
    // syncing**, and `technology_detected` / `technology_removed` arrive as
    // observations on the account. ⚡ **The design's section is an
    // INVENTORY** — *"14 detected · 1 competitor present"* — **which is a
    // current-state read, not a stream of detections, and nothing publishes
    // one.**
    source:
      'builtwith delivers technology_detected/technology_removed as observations; the design’s section is a current inventory with a competitor flag, and no route publishes one',
    absence:
      'Signora sees technology being detected and removed at this account and reports each as a signal. It does not yet keep a running list of what is installed today.',
  },
  {
    id: 'compete',
    label: 'Competitors',
    supply: 'supplied',
    // ⚠️ The declared competitor list, not *"mentioned in the last 90 days"* —
    // nothing counts mentions. The section shows what is declared.
    source: 'useCompetitors (hooks/commercial) — the competitors this organization declared',
  },
  {
    id: 'market',
    label: 'Market signals',
    supply: 'absent',
    // 🔴 **This said Signora *"is not reading those for this account"* and
    // that is FALSE** — [B-299](../../../docs/BUGS.md) ⑦. ⛔ **`crunchbase` is
    // connected**, and `funding_round` and `acquisition` arrive as
    // observations on the account.
    source:
      'crunchbase delivers funding_round and acquisition as observations; the design’s section groups them with a regulatory kind nothing produces, and no route publishes the grouping',
    absence:
      'Funding and acquisition news about this account reaches Signora and appears in the timeline as it happens. Signora does not yet collect it into a market view.',
  },
  {
    id: 'activity',
    label: 'Recent activity',
    rail: 'Activity',
    supply: 'supplied',
    source: 'useAccountTimeline (hooks/timeline) — everything recorded about this account',
  },
  {
    id: 'email',
    label: 'Emails',
    supply: 'absent',
    // 📁 The design draws 38 threads with unanswered counts. ⛔ Nothing
    // ingests mail: `sales_engagement` records an approach, never a message.
    // ⚡ **Restated to say what SIGNORA does not do** — [B-299](../../../docs/BUGS.md) ⑦.
    // ⛔ **It told the reader no mailbox was connected**, which this file
    // cannot know; ✅ **that no mailbox can be connected is a fact about the
    // product**, and it is the one worth stating.
    source: 'no mailbox integration exists; sales_engagement records an approach, never a message',
    absence:
      'Signora does not read mailboxes yet, so the email exchanged with this account is not something it can show you.',
  },
  {
    id: 'meetings',
    label: 'Meetings',
    supply: 'absent',
    source: 'no calendar or conversation-intelligence integration exists',
    absence:
      'Signora does not read calendars yet, so the meetings held with this account are not something it can show you.',
  },
  {
    id: 'files',
    label: 'Files',
    supply: 'absent',
    // 📁 *"18 files."* ⛔ No module stores a document, and object storage is
    // behind a port nothing implements for customer files.
    source: 'no document store; nothing in backend/modules/ holds a file',
    absence:
      'Documents shared with this account appear here once Signora can read a file store. It cannot yet.',
  },
  {
    id: 'notes',
    label: 'Notes',
    supply: 'absent',
    // ⚠️ **Not the same as a decision's reason**, which IS recorded — 📁
    // `decision-history.tsx`. A note is unattached prose about an account and
    // nothing holds one.
    source: 'no note entity; decision reasons are recorded, free notes are not',
    absence:
      'Notes your team writes about this account appear here. Signora records the reasoning behind decisions, but has nowhere to keep a free note yet.',
  },
  {
    id: 'tasks',
    label: 'Tasks',
    supply: 'absent',
    // ⛔ **`action_batch` is not this**, and the same mistake was made once on
    // Home: its `proposed_by` is a person's bulk edit awaiting approval, not
    // somebody's to-do against an account.
    source: 'no task entity; action_batch holds approvals, not assignments',
    absence:
      'Work somebody owes on this account appears here. Signora does not keep a task list yet.',
  },
  {
    id: 'fields',
    label: 'Custom fields',
    supply: 'absent',
    // 📁 *"12 fields."* ⛔ The account record's shape is fixed; nothing lets a
    // customer declare a field, so there is no schema to render.
    source: 'no customer-defined field schema exists on the account record',
    absence:
      'Fields your organization has added to an account appear here. Signora does not let you define one yet.',
  },
  {
    id: 'history',
    // 📁 **The design's heading is *"Historical timeline"*** — the
    // `14.5px/600` title above the section — **and its rail entry is
    // *"History"***. ⚡ Two strings, both `pageNav` and the mockup's own.
    label: 'Historical timeline',
    rail: 'History',
    supply: 'absent',
    /**
     * ⚠️ **This is NOT the timeline, and the difference is why it is absent
     * rather than a second view of `activity`.**
     *
     * 📁 The design's own points are **commercial milestones** — *"First
     * contract"*, *"Expansion +420 seats"*, *"Renewal · 3 years"*, *"Renewal
     * due"* — with a zoom of `Milestones · Quarters · All`. ⛔ **The timeline
     * carries observation and business-event kinds**, and nothing records a
     * contract lifecycle. **Rendering activity under this heading would answer
     * a different question with the data to hand.**
     */
    source: 'no contract lifecycle; the timeline carries activity, not milestones',
    absence:
      'The commercial history of this account — first contract, expansions, renewals — appears here. Signora does not read contract records yet.',
  },
] as const;

/** 📁 The *"On this page"* rail — ⚡ **every section, including the absent ones.** */
export function onThisPage(): readonly AccountSection[] {
  return ACCOUNT_SECTIONS;
}

/** ✅ The sections a screen can actually fill today. */
export function supplied(): readonly AccountSection[] {
  return ACCOUNT_SECTIONS.filter((section) => section.supply === 'supplied');
}

/**
 * ⛔ **The sections nothing can fill**, each with what a customer is told.
 *
 * ⚡ **Exported so the gap is countable** — 📁 a repository that can measure
 * *"seven of fifteen"* can prioritise it; one where the absence is spread
 * across a JSX file cannot.
 */
export function absent(): readonly AccountSection[] {
  return ACCOUNT_SECTIONS.filter((section) => section.supply === 'absent');
}
