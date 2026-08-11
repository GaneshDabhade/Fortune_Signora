/**
 * **What AI Research asks for, and what the engine publishes** —
 * [TASK-1418](../../../docs/BACKLOG.md), against 📁
 * `Fortune Signora AI Research.dc.html`.
 *
 * ## 🔴 Measured first, because [TASK-1415](../../../docs/BACKLOG.md) proved
 * the row's framing cannot be trusted on its own
 *
 * ⚠️ **That row claimed every section was *"a composition of intelligence the
 * platform already produces"* and seven of fifteen had nothing behind them.**
 * ✅ **So this file is the measurement, taken before any screen.**
 *
 * ## ⛔ The engine publishes two endpoints, and one of them is a write
 *
 * 📁 **`ai_research_engine/interface/router.py`**: `POST …/accounts/{id}/research`
 * and `GET …/accounts/{id}/research`. ⚡ **The read returns a status and, when
 * the run finished, one artifact** — `statements`, `findings`, `prompt_name`,
 * `prompt_version`, `model`, `evidence_digest`.
 *
 * 🔴 **And the shape of the ASK is the finding.** ⛔ **Research is scoped to an
 * ACCOUNT.** 📁 **The design's subject is a question** — *"Why is EMEA
 * enterprise slipping?"* — **scoped to a segment and a quarter.** ⚠️ **Nothing
 * in this product can be asked a question**, and a screen with a question box
 * would be inventing the product's central promise.
 */

/** ⚡ Whether the platform can answer this part of the design today. */
export type ResearchCapability =
  /** ✅ A read exists and returns it. */
  | 'published'
  /**
   * ⚠️ **The engine models it and does not expose the detail the design
   * draws.** ⛔ **Distinct from absent**: the coarse answer is real, so the
   * screen can say something true rather than nothing.
   */
  | 'partial'
  /** ⛔ **Nothing produces this.** */
  | 'absent';

export interface ResearchFeature {
  readonly id: string;
  /** 📁 The design's own words for it. */
  readonly label: string;
  readonly capability: ResearchCapability;
  /** ⚡ What supplies it, or what would. ⛔ Engineering terms; never a screen. */
  readonly source: string;
  /** 📁 What a customer is told where it cannot be shown. */
  readonly absence?: string;
}

/**
 * 📁 **Measured 2026-08-11** against `ai_research_engine`'s router, the
 * `AccountResearch` and `ResearchArtifact` types, and `ResearchStatus`.
 */
export const RESEARCH_FEATURES: readonly ResearchFeature[] = [
  {
    id: 'ask',
    label: 'Ask a question',
    capability: 'absent',
    // 🔴 **The design's central promise, and the largest gap.** Research is
    // requested FOR AN ACCOUNT; there is no question, no scope and no segment.
    source: 'research is account-scoped; no free-text question is accepted anywhere',
    absence:
      'Signora researches one account at a time. Asking a question across a segment or a quarter is not something it can do yet.',
  },
  {
    id: 'answer',
    label: 'The answer, with its sources',
    capability: 'published',
    source: 'ResearchArtifact.statements and .findings — the brief and what it rests on',
  },
  {
    id: 'progress',
    label: 'Live progress',
    capability: 'partial',
    // ⚡ **`requested` and `running` are real**, and the read already polls
    // while either holds. ⛔ **The design's *"step 4 of 5 · 8.4s elapsed"* is
    // per-section detail the engine does not publish.**
    source: 'ResearchStatus requested/running is published; per-step progress is not',
    absence:
      'Signora can tell you research is running. It cannot yet tell you which part it is on.',
  },
  {
    id: 'provenance',
    label: 'Which prompt, which model',
    capability: 'published',
    source: 'ResearchArtifact.prompt_name, .prompt_version, .model, .evidence_digest',
  },
  {
    id: 'versions',
    label: 'Versions',
    capability: 'absent',
    // 📁 The design shows *"· v3"*. ⛔ One artifact per request; nothing
    // supersedes anything.
    source: 'one artifact per request; no supersession chain is stored',
    absence: 'Research is not versioned yet, so there is no earlier answer to compare against.',
  },
  {
    id: 'comments',
    label: 'Comments',
    capability: 'absent',
    source: 'no comment store exists in any module',
    absence: 'Comments on a research document are not something Signora holds yet.',
  },
  {
    id: 'editing',
    label: 'Editing, preserved through regeneration',
    capability: 'partial',
    /**
     * 🔴 **The law exists and the STORE does not** — and the law is the harder
     * half. 📁 [`lib/research/edits.ts`](edits.ts) is the merge, extracted from
     * [TASK-1417](../../../docs/BACKLOG.md)'s report narrative on its second
     * caller. ⛔ **Nothing persists an edit**, so it survives a regeneration
     * and not a reload.
     */
    source: 'the merge law is built (lib/research/edits.ts); no store persists an edit',
    absence:
      'Your edits are kept when Signora rewrites an answer, but they are not saved between visits yet.',
  },
  {
    id: 'graph',
    label: 'Knowledge graph',
    capability: 'absent',
    source: 'knowledge_graph publishes no account-research projection',
    absence:
      'Signora is not yet able to show you how the things it found connect to each other.',
  },
  {
    id: 'share',
    label: 'Share and export',
    capability: 'absent',
    // ⚡ The same two capabilities [TASK-1417](../../../docs/BACKLOG.md) named
    // as missing for Reports: a rendering pipeline and a link with its own
    // authorization.
    source: 'no export pipeline and no share link with its own authorization',
    absence: 'Sharing and exporting a research document are not built yet.',
  },
] as const;

/** ✅ What a screen can fill from a real read. */
export function published(): readonly ResearchFeature[] {
  return RESEARCH_FEATURES.filter((feature) => feature.capability === 'published');
}

/**
 * ⚠️ **What the engine answers coarsely.** ⛔ **Never rendered as absent** — the
 * coarse answer is true, and hiding it would understate what the product does.
 */
export function partial(): readonly ResearchFeature[] {
  return RESEARCH_FEATURES.filter((feature) => feature.capability === 'partial');
}

/** ⛔ What nothing produces. */
export function absent(): readonly ResearchFeature[] {
  return RESEARCH_FEATURES.filter((feature) => feature.capability === 'absent');
}
