/**
 * **The same blocks, re-laid out** — [TASK-1417](../../../docs/BACKLOG.md).
 *
 * ## 🔴 The row names its own risk, and this file is where it is taken
 *
 * > ⚠️ **Risk, named before it is met**: ***"Three renderers."***
 * > ✅ **Definition of Done**: ***"One definition renders in three modes."***
 * > 📁 **The design**: ***"never a separate deck to maintain."***
 *
 * ⛔ **A second renderer would satisfy a screenshot review.** ⚡ **It is
 * refused here at the level of the TYPES**: a laid-out block carries a
 * `ReportBlock` **taken from the definition** and has no field into which any
 * title, figure or sentence could be introduced. **There is nowhere to put
 * invented content** ([§2](../../../CLAUDE.md): *prefer a violation that is
 * unrepresentable over one that is merely discouraged*).
 *
 * ⚡ **So a mode decides three things and only three**: **which blocks appear ·
 * in what order · at what scale.** **It never decides what they say.**
 *
 * ## ⛔ Nothing is dropped silently, and that is the design's own rule
 *
 * 📁 **The sharing section**: *"rows they cannot access are withheld with a
 * count, never silently dropped, **so totals stay honest**."* ⚡ **The same
 * applies to a mode**: **executive mode shows at most three of nine blocks**,
 * and a reader who cannot see that six were left out believes they are looking
 * at the whole report. ✅ **`withheld` is that count.**
 */

import type { ReportBlock, ReportDefinition } from './definition';

/** 📁 The design's three sections: **Builder · Presentation · Executive**. */
export type ReportMode = 'screen' | 'presentation' | 'executive';

/**
 * ⚡ **How a chart draws itself in this mode.** 📁 *"Charts redraw at
 * presentation scale: fewer ticks, larger labels, no hover-only content."*
 *
 * ⛔ **`hover` is the load-bearing one.** **A figure available only on hover
 * does not exist in a room with a projector**, and a chart that quietly keeps
 * its tooltip in presentation mode is a chart whose data is missing for
 * everybody watching.
 */
export type ChartScale = 'screen' | 'presentation';

export interface LaidOutBlock {
  /** 🔴 **The definition's own block.** ⛔ **Never a copy, never a variant.** */
  readonly block: ReportBlock;
  readonly scale: ChartScale;
  /**
   * ⚡ **Whether hover-only content may be used.** ⛔ **False away from a
   * screen**, and it is a separate field from `scale` because the question a
   * component asks is *may I hide this behind a pointer* rather than *how big
   * am I*.
   */
  readonly pointerAvailable: boolean;
}

export interface Rendering {
  readonly mode: ReportMode;
  readonly blocks: readonly LaidOutBlock[];
  /**
   * ⛔ **How many of the definition's blocks this mode does not show.** ⚡ **A
   * count rather than a silence** — 📁 the design's own rule about withheld
   * rows, applied to a mode that deliberately shows less.
   */
  readonly withheld: number;
}

/**
 * ⚡ **What executive mode keeps, and it is an ORDER rather than a filter.**
 *
 * 📁 *"Three points maximum, **each a claim rather than a topic**"* — ⛔ **so a
 * narrative comes first: it is the only block that states a claim in a
 * sentence.** ⚡ **A metric is a figure and can carry one; a table is evidence
 * for a claim rather than the claim.**
 *
 * ⛔ **A chart is not in this list at all.** 📁 *"No chart unless it changes
 * the decision; the detail stays one click away."* ⚠️ **Nothing in the product
 * can currently decide whether a chart changes a decision** — **so charts are
 * withheld and COUNTED, never included on a guess.** ✅ **Refusing to guess is
 * what keeps the count honest; including them would make executive mode a
 * shorter screen mode, which is not what the design asks for.**
 */
const EXECUTIVE_PRIORITY: readonly ReportBlock['kind'][] = ['narrative', 'metric', 'table'];

/** 📁 *"Three points maximum."* */
const EXECUTIVE_MAXIMUM = 3;

/**
 * **One definition, rendered.**
 *
 * ⛔ **Takes the whole definition and returns a view of it** — ⚡ **it does not
 * take a mode's own block list, because a caller that could supply one would
 * be the separate deck.**
 */
export function layOut(definition: ReportDefinition, mode: ReportMode): Rendering {
  const total = definition.blocks.length;

  if (mode === 'screen') {
    // ⚡ **Everything, in the author's order, at screen scale.** 📁 The builder
    // is where a divider means something: it is where the author put a break.
    return {
      mode,
      blocks: definition.blocks.map((block) => ({
        block,
        scale: 'screen' as const,
        pointerAvailable: true,
      })),
      withheld: 0,
    };
  }

  if (mode === 'presentation') {
    /**
     * ⛔ **Dividers are dropped, and they are the only thing dropped.** 📁
     * *"One idea per slide"* — ⚡ **the slide boundary IS the divider**, so
     * carrying one through would produce an empty slide whose whole content
     * was a horizontal rule.
     */
    const shown = definition.blocks.filter((block) => block.kind !== 'divider');
    return {
      mode,
      blocks: shown.map((block) => ({
        block,
        scale: 'presentation' as const,
        pointerAvailable: false,
      })),
      withheld: total - shown.length,
    };
  }

  /**
   * ⚡ **Executive mode, and the ordering is by CLAIM rather than by the
   * author's sequence** — 📁 *"three things a CRO should take from this
   * quarter"*, which is a different question from *what did the author put
   * first*.
   *
   * ⛔ **Stable within a kind.** Two narratives keep the author's order
   * between them: **re-sorting content a person deliberately sequenced would
   * change the argument** ([§2](../../../CLAUDE.md): *hidden inputs are
   * architecture defects* — and the author's order is a declared input).
   */
  const ranked = EXECUTIVE_PRIORITY.flatMap((kind) =>
    definition.blocks.filter((block) => block.kind === kind),
  );
  const shown = ranked.slice(0, EXECUTIVE_MAXIMUM);

  return {
    mode,
    blocks: shown.map((block) => ({
      block,
      scale: 'presentation' as const,
      pointerAvailable: false,
    })),
    withheld: total - shown.length,
  };
}

/**
 * ⚡ **What a reader is told about what they cannot see.**
 *
 * ⛔ **Never rendered when nothing is withheld** — a line reading *"0 blocks
 * are not shown"* is noise, and 📁 the attribution strip established the same
 * rule for an absent confidence: **state an absence, never approximate it.**
 */
export function describeWithheld(rendering: Rendering): string | null {
  if (rendering.withheld === 0) return null;
  const plural = rendering.withheld === 1 ? 'block is' : 'blocks are';
  return `${rendering.withheld} ${plural} in this report but not in this view.`;
}

/**
 * 📁 **The design's timestamp rule**, and it is about honesty rather than
 * decoration: ***"Presenting from live data shows the timestamp; a frozen
 * snapshot says so explicitly."***
 *
 * ⛔ **There is no third answer.** ⚠️ **A presentation whose figures are of
 * unstated age is the one case the design refuses outright** — somebody in the
 * room will act on a number, and *when* is part of the number.
 */
export function describeFreshness(readAt: Date | null): string {
  if (readAt === null) return 'Frozen snapshot — these figures are not live.';
  const time = readAt.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  return `Data live · read at ${time}`;
}
