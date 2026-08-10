/**
 * **What survives a regeneration** — [TASK-1417](../../../docs/BACKLOG.md).
 *
 * ## 📁 The design's sentence, and it is a guarantee rather than a feature
 *
 * > ***"Edited sentences are preserved through regeneration and marked, so the
 * > board sees what a person asserted versus what the model derived."***
 *
 * ⚡ **The row's Playwright coverage names the same thing**: *"an edited
 * narrative survives a regeneration."*
 *
 * ## 🔴 Nothing here generates anything, and that is measured rather than a
 * scoping preference
 *
 * ⚠️ **`ai_platform` publishes exactly ONE endpoint** — `account_narration`,
 * *"what the evidence about this account says, in plain language"*, **scoped
 * to an account.** ⛔ **There is no capability that writes a report's
 * commentary**, and [§10](../../../CLAUDE.md) forbids inventing one: **a
 * fabricated inference is worse than an absent one, because it is
 * indistinguishable from a working system.**
 *
 * ✅ **So `regenerate` takes the incoming sentences as an ARGUMENT.** ⚡ **It
 * calls nothing, awaits nothing and knows no model.** **The merge is the
 * product law and is testable today; the generator arrives behind
 * [C-283](../../../docs/LANE_COORDINATION.md).**
 *
 * ## ⛔ Three things a regeneration may never do
 *
 * **① Delete a sentence a person wrote.** ⚡ **The model does not get to
 * overrule a person by omission** — 📁 the design's whole claim is that a board
 * can tell *"what a person asserted"* from what was derived, and a person's
 * assertion that vanished on the next refresh was never an assertion.
 *
 * **② Relabel a person's sentence as generated.** ⚠️ **This is the worse
 * failure of the two and the quieter one**: the text is still on the page, so
 * nothing looks lost, **and the board is now told a human judgement came from
 * the model.**
 *
 * **③ Move a person's sentence.** 📁 The narrative is an argument in order —
 * *"the corrective action is already measured"* only follows from the
 * paragraph before it.
 */

/**
 * ⛔ **Two authors, and they are never collapsed into a boolean.** 📁 *"Generated
 * commentary is marked, and human edits are marked differently"* — **two marks,
 * so an `isEdited` flag would lose which of them the reader is looking at.**
 */
export type SentenceAuthor = 'generated' | 'person';

export interface NarrativeSentence {
  /**
   * ⚡ **Stable across a regeneration**, and it is what makes the merge
   * possible at all: **matching on TEXT would treat a person's edit as a
   * deletion plus an insertion**, which is exactly the outcome ① forbids.
   */
  readonly id: string;
  readonly text: string;
  readonly author: SentenceAuthor;
  /**
   * 📁 *"edited by M. Reinhardt"*. ⛔ **Required to be present whenever the
   * author is a person and absent otherwise** — `assertMarked` below is what
   * makes that checkable rather than hoped for.
   */
  readonly editedBy: string | null;
}

/**
 * **A person takes a sentence over.**
 *
 * ⚡ **The id does not change**, which is the whole mechanism: the next
 * regeneration will find this id in its incoming set and must yield to it.
 */
export function edit(
  sentence: NarrativeSentence,
  text: string,
  editedBy: string,
): NarrativeSentence {
  return { id: sentence.id, text, author: 'person', editedBy };
}

/**
 * 🔴 **The merge, and it is the row's acceptance criterion.**
 *
 * @param current what is on the page, including every edit a person has made
 * @param incoming what the model has just produced — ⛔ **never fetched here**
 */
export function regenerate(
  current: readonly NarrativeSentence[],
  incoming: readonly NarrativeSentence[],
): NarrativeSentence[] {
  const byId = new Map(current.map((sentence) => [sentence.id, sentence]));
  const taken = new Set<string>();

  const merged = incoming.map((fresh) => {
    const held = byId.get(fresh.id);
    taken.add(fresh.id);

    // ⚡ **① and ② together.** The person's sentence is returned unchanged —
    // its text, its author AND its attribution — rather than the incoming one
    // with a flag copied across.
    if (held !== undefined && held.author === 'person') return held;

    return fresh;
  });

  /**
   * ⛔ **Sentences the model no longer offers.** ⚡ **A generated one is
   * dropped — the data moved and the model has nothing to say there any
   * more** — **but a person's is kept**, because ① is about omission and this
   * is the omission it means.
   *
   * ⚠️ **Reinserted at its original index rather than appended**, which is ③:
   * appending would put a person's paragraph after a conclusion it was written
   * to precede.
   */
  const orphaned = current.filter(
    (sentence) => sentence.author === 'person' && !taken.has(sentence.id),
  );

  for (const sentence of orphaned) {
    const wasAt = current.indexOf(sentence);
    merged.splice(Math.min(wasAt, merged.length), 0, sentence);
  }

  return merged;
}

/**
 * ⚡ **What the reader is told beside a sentence**, or `null` for the ordinary
 * generated case.
 *
 * ⛔ **Nothing is said about generated prose here** — 📁 **the block already
 * carries the AI attribution strip** ([TASK-1411](../../../docs/BACKLOG.md)),
 * **so a per-sentence *"generated"* label would state the same fact a second
 * time** ([§2](../../../CLAUDE.md): *truth has exactly one authoritative
 * representation*) **and turn a paragraph into a wall of chips.**
 */
export function markOf(sentence: NarrativeSentence): string | null {
  if (sentence.author !== 'person') return null;
  return sentence.editedBy === null ? 'Edited' : `Edited by ${sentence.editedBy}`;
}

/**
 * ⚠️ **A person's sentence with no attribution is a defect, not a variant.**
 *
 * 📁 The design's claim is that a board can see *"what a person asserted"* —
 * ⛔ **an assertion nobody signed does not satisfy it**, and the failure is
 * silent because the sentence still reads correctly.
 */
export function unattributed(sentences: readonly NarrativeSentence[]): NarrativeSentence[] {
  return sentences.filter(
    (sentence) =>
      (sentence.author === 'person' && sentence.editedBy === null) ||
      (sentence.author === 'generated' && sentence.editedBy !== null),
  );
}
