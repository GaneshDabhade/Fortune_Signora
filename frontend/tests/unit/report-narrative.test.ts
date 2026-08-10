/**
 * **An edited narrative survives a regeneration** —
 * [TASK-1417](../../../docs/BACKLOG.md)'s Playwright coverage item, asserted
 * where the rule actually lives.
 *
 * ⚡ **Nothing here calls a model, and that is not a shortcut**: 📁 the merge is
 * a law over sentences, and `ai_platform` publishes no endpoint that could
 * write a report's commentary
 * ([C-283](../../../docs/LANE_COORDINATION.md)).
 */
import { describe, expect, it } from 'vitest';

import {
  edit,
  markOf,
  regenerate,
  unattributed,
  type NarrativeSentence,
} from '@/lib/reports/narrative';

function generated(id: string, text: string): NarrativeSentence {
  return { id, text, author: 'generated', editedBy: null };
}

describe('🔴 what a regeneration may never do', () => {
  it("⛔ ① never overwrites a person's sentence with the model's", () => {
    const current = [generated('s1', 'the model said this'), generated('s2', 'and this')];
    const edited = [edit(current[0]!, 'M. Reinhardt asserted this', 'M. Reinhardt'), current[1]!];

    const after = regenerate(edited, [
      generated('s1', 'the model has changed its mind'),
      generated('s2', 'and this, differently'),
    ]);

    expect(after[0]!.text).toBe('M. Reinhardt asserted this');
    // ⚡ **The generated one DID move** — that is the feature, and it is what
    // makes the first assertion mean something.
    expect(after[1]!.text).toBe('and this, differently');
  });

  it('⛔ ② never relabels a person’s sentence as generated — the quieter failure', () => {
    /**
     * ⚠️ **The text is still on the page, so nothing looks lost** — **and the
     * board is now told a human judgement came from the model.**
     */
    const edited = [edit(generated('s1', 'derived'), 'asserted', 'M. Reinhardt')];

    const after = regenerate(edited, [generated('s1', 'derived again')]);

    expect(after[0]!.author).toBe('person');
    expect(after[0]!.editedBy).toBe('M. Reinhardt');
    expect(markOf(after[0]!)).toBe('Edited by M. Reinhardt');
  });

  it('⛔ ① never DELETES a person’s sentence, even when the model drops it', () => {
    // ⚡ The data moved and the model has nothing to say there any more. A
    // person's assertion that vanished on the next refresh was never one.
    const edited = [
      generated('s1', 'first'),
      edit(generated('s2', 'second'), 'two of the three remain recoverable', 'M. Reinhardt'),
      generated('s3', 'third'),
    ];

    const after = regenerate(edited, [generated('s1', 'first, revised'), generated('s3', 'third')]);

    expect(after.map((s) => s.text)).toContain('two of the three remain recoverable');
  });

  it('⛔ ③ keeps a preserved sentence in its ORIGINAL position, never appended', () => {
    // 📁 The narrative is an argument in order — *"the corrective action is
    // already measured"* only follows from the paragraph before it.
    const edited = [
      generated('s1', 'first'),
      edit(generated('s2', 'second'), 'the human middle', 'M. Reinhardt'),
      generated('s3', 'third'),
    ];

    const after = regenerate(edited, [generated('s1', 'first'), generated('s3', 'third')]);

    expect(after.map((s) => s.text)).toEqual(['first', 'the human middle', 'third']);
  });

  it('⚡ drops a GENERATED sentence the model no longer offers', () => {
    // ⛔ The asymmetry is the whole rule: omission overrules the model and
    // never overrules a person.
    const after = regenerate([generated('s1', 'a'), generated('s2', 'b')], [generated('s1', 'a')]);

    expect(after.map((s) => s.id)).toEqual(['s1']);
  });

  it('accepts a brand-new sentence from the model', () => {
    const after = regenerate([generated('s1', 'a')], [generated('s1', 'a'), generated('s2', 'new')]);

    expect(after.map((s) => s.id)).toEqual(['s1', 's2']);
  });
});

describe('⚡ the two marks are two, never a boolean', () => {
  it('says nothing beside generated prose', () => {
    // 📁 The block already carries the AI attribution strip (TASK-1411), so a
    // per-sentence label would state the same fact twice.
    expect(markOf(generated('s1', 'derived'))).toBeNull();
  });

  it("🔴 reports a person's sentence that nobody signed as a defect", () => {
    /**
     * ⚠️ **An assertion nobody signed does not satisfy *"the board sees what a
     * person asserted"***, and the failure is silent because the sentence
     * still reads correctly.
     */
    const wrong: NarrativeSentence = { id: 's1', text: 'x', author: 'person', editedBy: null };

    expect(unattributed([wrong])).toEqual([wrong]);
    expect(unattributed([edit(generated('s1', 'x'), 'y', 'M. Reinhardt')])).toEqual([]);
  });

  it('reports a generated sentence carrying an editor, which is the same lie inverted', () => {
    const wrong: NarrativeSentence = {
      id: 's1',
      text: 'x',
      author: 'generated',
      editedBy: 'M. Reinhardt',
    };

    expect(unattributed([wrong])).toEqual([wrong]);
  });
});
