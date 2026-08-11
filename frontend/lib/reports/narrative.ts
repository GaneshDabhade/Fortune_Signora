/**
 * **The report narrative's edits** — [TASK-1417](../../../docs/BACKLOG.md).
 *
 * ⚡ **The law moved to [`lib/research/edits.ts`](../research/edits.ts) when AI
 * Research became its second caller** ([TASK-1418](../../../docs/BACKLOG.md)),
 * because 📁 **both designs write the same sentence**: *edits are preserved
 * through regeneration*.
 *
 * ⛔ **Nothing about the report's use of it changed**, which is the point — the
 * extraction is behaviour-preserving and this file's own tests prove it by
 * passing unchanged.
 */

export {
  edit,
  markOf,
  regenerate,
  unattributed,
  type NarrativeSentence,
  type SentenceAuthor,
} from '@/lib/research/edits';
