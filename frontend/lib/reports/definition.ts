/**
 * **What a report IS** — [TASK-1417](../../../docs/BACKLOG.md), against 📁
 * `Fortune Signora Reports.dc.html`.
 *
 * ## 🔴 One definition. The three renderings are [`modes.ts`](modes.ts)
 *
 * 📁 **The design's subtitle is the architecture**: ***"Built once, read three
 * ways — screen, presentation and board pack."*** 📁 **And its acceptance
 * sentence**: ***"The same blocks, re-laid out — never a separate deck to
 * maintain."***
 *
 * ⛔ **So there is exactly one thing here that holds content, and it is this
 * file.** **A presentation is not a second definition, an export is not a
 * third, and an executive summary is not a fourth** — 📁 the row names *three
 * renderers* as its own risk, and **a renderer that owned any content would be
 * the deck the design refuses**, passing a screenshot review while creating
 * the maintenance burden the sentence exists to prevent.
 *
 * ## ⚡ Where a report is STORED, and why nothing new was built to store it
 *
 * 📁 **[455 §4](../../../docs/architecture/455-context-definitions-r02-r03.md)
 * names the consumers of the saved-view store**: *"Companies · App Shell ·
 * Global Search · **Reports**"*, and the store keeps *"the query, the filters
 * and the sort — **not the results**"*. ✅ **That is a report definition,
 * exactly.**
 *
 * ⚡ **So a report is a saved-view declaration** — **no new table, no new
 * module, no new endpoint** — and 📁 the store's lifecycle is already the
 * design's: *"a declaration is never edited; a change is a new version naming
 * the one it replaces"* beside the design's own ***"v7 · autosaved"***.
 *
 * ⛔ **The store will never validate any of this** (455 §4: *"never parses,
 * validates… never knows what a filter or a sort means"*), ✅ **so the refusals
 * below are this screen's, and there is nowhere else they could live.**
 *
 * ## ⚠️ What is deliberately NOT here, each with its reason
 *
 * ⛔ **Scheduling, exports and sharing.** 📁 The row names them: *"scheduled
 * delivery is a job runner, export is a rendering pipeline, sharing is a link
 * with its own authorization"* — **three capabilities that do not exist.**
 *
 * ⛔ **And a fourth the row did not name: GENERATING the narrative.** 📁
 * `ai_platform` publishes exactly one endpoint — `account_narration`, scoped
 * to an account — **so nothing can write a report's commentary.** ⚡ **What is
 * built instead is the rule that survives a regeneration**
 * ([`narrative.ts`](narrative.ts)), **which is a law over sentences and needs
 * no model** ([§10](../../../CLAUDE.md): *never ask a model to invent what the
 * system already knows*, and never fabricate one that it does not).
 */

import { whyNotReadable, type DeclarationKind } from '@/lib/views/declaration';

export const REPORT_DECLARATION_VERSION = 1;

const REPORT: DeclarationKind = {
  kind: 'report',
  version: REPORT_DECLARATION_VERSION,
  screen: 'Reports',
};

/**
 * 📁 **The design's four query chips** — *"Period · Region · Segment ·
 * Include"* — **above the sentence *"Every block inherits this"*.**
 *
 * ⛔ **There is no per-block query and there will not be one.** ⚡ **That
 * single sentence is what makes three renderings of one definition possible
 * at all**: blocks that each carried a query could disagree with one another,
 * and a board pack whose figures contradict its own charts is the failure this
 * whole screen is built to prevent.
 */
export interface ReportQuery {
  /** 📁 *"Q3 FY26"*. */
  readonly period: string;
  /** 📁 *"EMEA"*. `null` is **every region**, never *"unknown"*. */
  readonly region: string | null;
  /** 📁 *"Enterprise"*. `null` is **every segment**. */
  readonly segment: string | null;
  /**
   * ⚡ **What the query yields**, and 🔴 **the reason `whyCannotAdd` can
   * answer at all.**
   *
   * ⛔ **The CATALOGUE of measures is not invented here.** 📁 The design says
   * *"3,104 opportunities"* — a real count from a real query — **and the
   * server that produces it does not exist yet**, so this field carries what
   * that server will one day answer. ✅ **The MECHANISM is the product rule and
   * is built; the vocabulary arrives with the query engine.**
   */
  readonly produces: readonly string[];
}

/** 📁 *"Blocks are chart, table, metric, narrative or divider."* — the five. */
export type BlockKind = 'metric' | 'chart' | 'table' | 'narrative' | 'divider';

export interface ReportBlock {
  readonly id: string;
  readonly kind: BlockKind;
  /** 📁 *"Plan to commit — what moved"*. */
  readonly title: string;
  /**
   * ⚡ **Which figures this block draws.** ⛔ **Empty for a divider and for a
   * narrative**, which draw no number of their own — 📁 the design's narrative
   * is *"written from the blocks above, not from a separate prompt, so the
   * prose cannot contradict the charts."*
   */
  readonly reads: readonly string[];
}

/** ⚡ **A report, and the whole of one.** */
export interface ReportDefinition {
  readonly kind: 'report';
  readonly version: number;
  readonly name: string;
  readonly query: ReportQuery;
  readonly blocks: readonly ReportBlock[];
}

/**
 * 🔴 **The design's own refusal, made executable.**
 *
 * > 📁 ***"A block that would show a number the query cannot produce refuses
 * > to save."***
 *
 * ⚡ **Returns the sentence, never a boolean** — the builder has to say WHICH
 * figure is missing, or the person is left removing blocks at random to find
 * the one the form dislikes.
 *
 * ⛔ **Checked before the save, not by the server.** 📁 455 §4 is explicit that
 * the store *"never parses, validates… a declaration"* — ⚠️ **so a report
 * saved without this check would persist happily and fail silently at read
 * time**, which is the shape of defect this repository keeps finding.
 */
export function whyCannotAdd(block: ReportBlock, query: ReportQuery): string | null {
  const missing = block.reads.filter((field) => !query.produces.includes(field));
  if (missing.length === 0) return null;

  // ⚡ **Every missing figure, not the first.** A person who removes one field
  // and is told about the next has learned nothing about how long this will
  // take — the same reason the invite form classifies every pasted address at
  // once rather than one round trip at a time.
  return `This report's query does not produce ${missing.join(', ')}, so this block would have nothing to show.`;
}

/**
 * ⚡ **Whether a stored declaration is one of ours** — the three refusals
 * shared with every other consumer of the store
 * ([`declaration.ts`](../views/declaration.ts)).
 */
export function whyNotReadableHere(declaration: unknown): string | null {
  const frame = whyNotReadable(declaration, REPORT);
  if (frame !== null) return frame;

  const candidate = declaration as Partial<ReportDefinition>;

  /**
   * ⛔ **A report with no query is not a narrower report — it is a report
   * whose figures have no basis at all**, and 📁 *"every block inherits this"*
   * has nothing to inherit. **Refused rather than defaulted**: a default
   * period would silently answer a different question from the one saved.
   */
  if (typeof candidate.query !== 'object' || candidate.query === null) {
    return 'This report was saved without the query its blocks read from.';
  }
  if (!Array.isArray(candidate.blocks)) {
    return 'This report was saved without its blocks.';
  }

  return null;
}

/**
 * **The current report, as something the store can hold.**
 *
 * ⛔ **Returns a plain object rather than writing anything.** ⚡ **The store
 * takes an opaque declaration** (455 §4), **so this is the whole contract with
 * it** — and keeping the write out of here is what lets every rule above be
 * tested without a server.
 */
export function declare(
  name: string,
  query: ReportQuery,
  blocks: readonly ReportBlock[],
): ReportDefinition {
  return { kind: 'report', version: REPORT_DECLARATION_VERSION, name, query, blocks };
}

/**
 * 🔴 **Reordering a block, and this is an ACCESSIBILITY requirement rather
 * than a convenience.**
 *
 * > ♿ **The row**: ***"Drag-to-reorder MUST have a keyboard equivalent — a
 * > drag-only builder is unusable without a mouse."***
 *
 * ⚡ **So the move is a pure function over the definition and the pointer is
 * one caller of it, not the owner of it.** ⛔ **A reorder implemented inside a
 * drag handler is a reorder a keyboard cannot reach**, and that is exactly how
 * a builder ends up mouse-only — not by anybody deciding it should be.
 *
 * ⛔ **Returns the SAME array when the move is impossible** — the first block
 * cannot rise and the last cannot fall. ⚡ **Identity is the signal**, so a
 * caller can tell *nothing happened* from *something happened* without
 * comparing contents, and a focus announcement is not made for a move that
 * did not occur.
 */
export function reorder(
  blocks: readonly ReportBlock[],
  id: string,
  direction: 'up' | 'down',
): readonly ReportBlock[] {
  const from = blocks.findIndex((block) => block.id === id);
  if (from === -1) return blocks;

  const to = direction === 'up' ? from - 1 : from + 1;
  if (to < 0 || to >= blocks.length) return blocks;

  const moved = [...blocks];
  const [block] = moved.splice(from, 1);
  moved.splice(to, 0, block!);
  return moved;
}

/**
 * ⚡ **What a screen reader is told after a move.**
 *
 * ⛔ **A silent reorder is an invisible one.** **A keyboard user who has just
 * pressed a key has no way to know whether anything happened** — the visual
 * change is the whole feedback for everybody else, and there is none here.
 */
export function describeMove(
  blocks: readonly ReportBlock[],
  id: string,
): string {
  const at = blocks.findIndex((block) => block.id === id);
  if (at === -1) return '';
  return `${blocks[at]!.title}, position ${at + 1} of ${blocks.length}.`;
}

/**
 * 📁 **The design's chips**, in its order — *Period · Region · Segment*.
 *
 * ⛔ **A `null` narrowing is omitted rather than printed as *"All"***, because
 * the strip states what the report IS scoped to; **a chip reading *"Region:
 * All"* claims a narrowing that is not there.**
 */
export function describeQuery(query: ReportQuery): readonly { k: string; v: string }[] {
  const chips: { k: string; v: string }[] = [{ k: 'Period', v: query.period }];
  if (query.region !== null) chips.push({ k: 'Region', v: query.region });
  if (query.segment !== null) chips.push({ k: 'Segment', v: query.segment });
  return chips;
}
