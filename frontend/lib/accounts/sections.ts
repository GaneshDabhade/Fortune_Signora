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
 * the assumption.** ✅ **Eight of the design's fifteen sections have a read
 * behind them today.** ⛔ **Seven do not** — and 📁 [§20c](../../../CLAUDE.md)
 * decides what happens to those: *"screens without a shipped module behind them
 * ship a designed empty state"*, **never invented figures.**
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
  readonly id: string;
  /** 📁 The design's own heading, verbatim. */
  readonly label: string;
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
    // 📁 *"Third-party intent data · last refreshed 06:00."* ⛔ There is no
    // third-party intent provider, and inventing an index would be a number
    // with no author.
    source: 'no third-party intent provider is connected',
    absence:
      'Buying intent comes from third-party research data. No intent source is connected to your organization yet.',
  },
  {
    id: 'signals',
    label: 'Signals timeline',
    supply: 'supplied',
    source: 'useAccountObservations — what changed, and what Signora made of it',
  },
  {
    id: 'research',
    label: 'Research summary',
    supply: 'supplied',
    source: 'useAccountResearch — company, market and relationship research',
  },
  {
    id: 'opportunities',
    label: 'Open opportunities',
    supply: 'supplied',
    source: 'useAccountOpportunity — the opportunity and its stage',
  },
  {
    id: 'contacts',
    label: 'Contacts & decision makers',
    supply: 'supplied',
    // ⚠️ **Partially.** The buying committee is a workspace-level DECLARATION
    // rather than this account's known people — the design's *"24 known"* has
    // no source. The section renders what exists and says what it is.
    source: 'useBuyingCommittee (hooks/commercial) — the declared committee',
  },
  {
    id: 'org-chart',
    label: 'Organisation chart',
    supply: 'absent',
    source: 'nothing infers reporting lines; no email or calendar ingestion',
    absence:
      'An organisation chart is inferred from email, calendar and public sources. Signora is not reading any of those yet.',
  },
  {
    id: 'relationships',
    label: 'Relationship graph',
    supply: 'absent',
    source: 'nothing measures relationship strength between people',
    absence:
      'Signora cannot yet tell you who on your side knows whom on theirs, or how well.',
  },
  {
    id: 'tech-stack',
    label: 'Technology stack',
    supply: 'absent',
    source: 'no enrichment provider detects installed technology',
    absence:
      'Detected technology comes from an enrichment source. None is connected to your organization yet.',
  },
  {
    id: 'competitors',
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
    source: 'no external news or filings source is ingested for this account',
    absence:
      'Market signals come from news, filings and public sources. Signora is not reading those for this account yet.',
  },
  {
    id: 'activity',
    label: 'Recent activity',
    supply: 'supplied',
    source: 'useAccountTimeline (hooks/timeline) — everything recorded about this account',
  },
  {
    id: 'meetings',
    label: 'Meetings',
    supply: 'absent',
    source: 'no calendar or conversation-intelligence integration',
    absence:
      'Meetings appear here once a calendar is connected. None is connected to your organization yet.',
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
