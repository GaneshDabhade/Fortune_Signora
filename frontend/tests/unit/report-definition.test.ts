/**
 * **The report definition, and the three renderings of it** —
 * [TASK-1417](../../../docs/BACKLOG.md).
 *
 * ⚡ **The row's Definition of Done is one sentence** — *"one definition
 * renders in three modes and the narrative survives regeneration"* — **and
 * these are the two halves of it.**
 */
import { describe, expect, it } from 'vitest';

import {
  declare,
  describeMove,
  describeQuery,
  reorder,
  whyCannotAdd,
  whyNotReadableHere,
  type ReportBlock,
  type ReportQuery,
} from '@/lib/reports/definition';
import { describeWithheld, layOut } from '@/lib/reports/modes';

const QUERY: ReportQuery = {
  period: 'Q3 FY26',
  region: 'EMEA',
  segment: 'Enterprise',
  produces: ['commit', 'plan', 'coverage', 'moved'],
};

function block(id: string, kind: ReportBlock['kind'], reads: string[] = []): ReportBlock {
  return { id, kind, title: id, reads };
}

describe("📁 the design's refusal — a block the query cannot feed does not save", () => {
  it('accepts a block whose every figure the query produces', () => {
    expect(whyCannotAdd(block('a', 'metric', ['commit', 'plan']), QUERY)).toBeNull();
  });

  it('🔴 refuses a block reading a figure the query does not produce, and NAMES it', () => {
    const why = whyCannotAdd(block('a', 'chart', ['commit', 'win_rate']), QUERY);

    // ⛔ **The name is the point.** A refusal that does not say which figure is
    // missing leaves somebody deleting blocks at random to find the one the
    // form dislikes.
    expect(why).toContain('win_rate');
    expect(why).not.toContain('commit');
  });

  it('⚡ names EVERY missing figure, not the first', () => {
    const why = whyCannotAdd(block('a', 'chart', ['win_rate', 'churn']), QUERY);

    expect(why).toContain('win_rate');
    expect(why).toContain('churn');
  });

  it('lets a narrative and a divider through, because they draw no number', () => {
    expect(whyCannotAdd(block('n', 'narrative'), QUERY)).toBeNull();
    expect(whyCannotAdd(block('d', 'divider'), QUERY)).toBeNull();
  });
});

describe('🔴 a stored declaration this screen cannot read is REFUSED', () => {
  it('reads its own', () => {
    expect(whyNotReadableHere(declare('Q3 board pack', QUERY, []))).toBeNull();
  });

  it("⛔ refuses another screen's view — the commonest real case", () => {
    // 📁 455 §4: the store is workspace-wide and names four consumers, so a
    // working-list view and a report sit in one list.
    expect(whyNotReadableHere({ kind: 'working-list', version: 1 })).toMatch(/different screen/);
  });

  it("refuses a newer Signora's report rather than partly applying it", () => {
    expect(whyNotReadableHere({ kind: 'report', version: 99 })).toMatch(/newer version/);
  });

  it('refuses anything malformed, including an array', () => {
    expect(whyNotReadableHere(null)).not.toBeNull();
    expect(whyNotReadableHere('a report')).not.toBeNull();
    expect(whyNotReadableHere([])).not.toBeNull();
  });

  it('⛔ refuses a report with no query rather than defaulting one', () => {
    // ⚡ A default period would silently answer a different question from the
    // one that was saved.
    const why = whyNotReadableHere({ kind: 'report', version: 1, blocks: [] });
    expect(why).toMatch(/query/);
  });

  it('refuses a report with no blocks', () => {
    expect(whyNotReadableHere({ kind: 'report', version: 1, query: QUERY })).toMatch(/blocks/);
  });

  it('⚡ an OLDER version stays readable, and that is deliberate', () => {
    // The version bumps only when an old declaration would be MISREAD — never
    // when a field is added, because a missing key means *not narrowed*.
    expect(whyNotReadableHere({ kind: 'report', version: 0, query: QUERY, blocks: [] })).toBeNull();
  });
});

describe("⚡ the query strip states what the report IS scoped to", () => {
  it("omits a null narrowing rather than printing 'All'", () => {
    // ⛔ A chip reading *Region: All* claims a narrowing that is not there.
    const chips = describeQuery({ ...QUERY, region: null, segment: null });

    expect(chips).toEqual([{ k: 'Period', v: 'Q3 FY26' }]);
  });
});

describe('🔴 one definition, three renderings — the row\'s named risk', () => {
  const definition = declare('Q3 board pack', QUERY, [
    block('metrics', 'metric', ['commit']),
    block('bridge', 'chart', ['plan', 'commit']),
    block('rule', 'divider'),
    block('moved', 'table', ['moved']),
    block('commentary', 'narrative'),
  ]);

  it('⛔ NO mode can introduce a block the definition does not have', () => {
    /**
     * 🔴 **This is the acceptance criterion for *"never a separate deck to
     * maintain"***, asserted as a property across all three modes rather than
     * by reading the code.
     */
    const declared = new Set(definition.blocks.map((b) => b.id));

    for (const mode of ['screen', 'presentation', 'executive'] as const) {
      for (const laid of layOut(definition, mode).blocks) {
        expect(declared.has(laid.block.id), `${mode} introduced ${laid.block.id}`).toBe(true);
        // ⚡ **The same object, not a copy** — a copy is where a divergent
        // title would eventually be written.
        expect(definition.blocks).toContain(laid.block);
      }
    }
  });

  it('the builder shows everything, in the author’s order', () => {
    const screen = layOut(definition, 'screen');

    expect(screen.blocks.map((b) => b.block.id)).toEqual([
      'metrics',
      'bridge',
      'rule',
      'moved',
      'commentary',
    ]);
    expect(screen.withheld).toBe(0);
  });

  it('⚡ presentation drops the divider and ONLY the divider', () => {
    // 📁 *"One idea per slide"* — the slide boundary is the divider, so
    // carrying one through produces a slide whose content is a horizontal rule.
    const presentation = layOut(definition, 'presentation');

    expect(presentation.blocks.map((b) => b.block.id)).toEqual([
      'metrics',
      'bridge',
      'moved',
      'commentary',
    ]);
    expect(presentation.withheld).toBe(1);
  });

  it('🔴 presentation makes hover-only content unavailable', () => {
    // ⛔ **A figure available only on hover does not exist in a room with a
    // projector.** 📁 *"no hover-only content."*
    for (const laid of layOut(definition, 'presentation').blocks) {
      expect(laid.pointerAvailable).toBe(false);
      expect(laid.scale).toBe('presentation');
    }
    for (const laid of layOut(definition, 'screen').blocks) {
      expect(laid.pointerAvailable).toBe(true);
    }
  });

  it("executive keeps at most three, ordered by CLAIM rather than by the author's sequence", () => {
    // 📁 *"Three points maximum, each a claim rather than a topic"* — so the
    // narrative leads, though the author put it last.
    const executive = layOut(definition, 'executive');

    expect(executive.blocks.map((b) => b.block.id)).toEqual(['commentary', 'metrics', 'moved']);
  });

  it('⛔ executive withholds every chart, and COUNTS what it withheld', () => {
    /**
     * 📁 *"No chart unless it changes the decision"* — ⚠️ **nothing in the
     * product can decide that today**, so charts are withheld rather than
     * included on a guess, and the count is what keeps that honest.
     */
    const executive = layOut(definition, 'executive');

    expect(executive.blocks.some((b) => b.block.kind === 'chart')).toBe(false);
    expect(executive.withheld).toBe(2);
    expect(describeWithheld(executive)).toMatch(/2 blocks are in this report but not in this view/);
  });

  it('🔴 withholds a chart even when there is ROOM for it under the cap', () => {
    /**
     * ⚠️ **The assertion above was DECORATIVE and a fire-test found it.**
     * ⛔ **Its fixture has three non-charts, so the cap of three excluded the
     * chart whether or not the rule existed** — **admitting charts to the
     * priority list left every assertion green.**
     *
     * ✅ **This fixture has two blocks and one is a chart**, so the cap
     * excludes nothing and **only the rule can.** 📁 *"No chart unless it
     * changes the decision"*, and nothing in the product can decide that yet.
     */
    const sparse = declare('two blocks', QUERY, [
      block('bridge', 'chart', ['plan']),
      block('commentary', 'narrative'),
    ]);

    const executive = layOut(sparse, 'executive');

    expect(executive.blocks.map((b) => b.block.id)).toEqual(['commentary']);
    expect(executive.withheld).toBe(1);
    expect(describeWithheld(executive)).toMatch(/1 block is in this report/);
  });

  it('says nothing when nothing is withheld', () => {
    // ⛔ A line reading *0 blocks are not shown* is noise.
    expect(describeWithheld(layOut(definition, 'screen'))).toBeNull();
  });

  it('⚡ keeps the author’s order WITHIN a kind', () => {
    // ⛔ Re-sorting content a person deliberately sequenced changes the
    // argument — the author's order is a declared input, not a hidden one.
    const two = declare('two claims', QUERY, [
      block('second', 'narrative'),
      block('first', 'narrative'),
    ]);

    expect(layOut(two, 'executive').blocks.map((b) => b.block.id)).toEqual(['second', 'first']);
  });
});

describe('♿ blocks reorder by keyboard as well as by drag', () => {
  // 🔴 The row: *"a drag-only builder is unusable without a mouse."* The move
  // is a pure function so the pointer is one caller of it, never its owner.
  const blocks = [block('a', 'metric'), block('b', 'chart'), block('c', 'table')];

  it('moves a block up and down', () => {
    expect(reorder(blocks, 'b', 'up').map((x) => x.id)).toEqual(['b', 'a', 'c']);
    expect(reorder(blocks, 'b', 'down').map((x) => x.id)).toEqual(['a', 'c', 'b']);
  });

  it('⛔ returns the SAME array when the move is impossible, so identity is the signal', () => {
    // ⚡ A caller can tell *nothing happened* without comparing contents, and
    // does not announce a move that did not occur.
    expect(reorder(blocks, 'a', 'up')).toBe(blocks);
    expect(reorder(blocks, 'c', 'down')).toBe(blocks);
    expect(reorder(blocks, 'nonexistent', 'up')).toBe(blocks);
  });

  it('never loses or duplicates a block', () => {
    const after = reorder(blocks, 'a', 'down');
    expect([...after].map((x) => x.id).sort()).toEqual(['a', 'b', 'c']);
  });

  it('⛔ says where the block landed — a silent reorder is an invisible one', () => {
    // A keyboard user has no visual feedback; the announcement is the whole of it.
    expect(describeMove(reorder(blocks, 'b', 'up'), 'b')).toBe('b, position 1 of 3.');
  });
});
