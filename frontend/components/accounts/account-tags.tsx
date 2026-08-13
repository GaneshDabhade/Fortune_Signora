/**
 * **The Companies table's Tags column** — [TASK-466](../../../docs/BACKLOG.md),
 * against 📁 `Fortune Signora Companies.dc.html` and
 * [ADR-0411](../../../docs/architecture/adr/0411-customer-organized-account-metadata.md).
 *
 * ## ✅ Reused, not rebuilt
 *
 * 📁 [`Badge`](../ui/badge.tsx) already renders a token-coloured chip and
 * already reserves the `ai` hue. ⛔ **A `TagChip` would have been a second
 * component for one caller** — [§20c](../../../CLAUDE.md): *"add to the library
 * rather than around it"*, and the library already had this.
 *
 * ## 🔴 `ai` is unreachable from a customer tag, in both tiers
 *
 * ⛔ **The server's `TagTone` has four members and `ai` is not one**, and the
 * map below is total over exactly those four. ⚡ **So a customer label cannot
 * wear the tone the design reserves for what Signora inferred** — 📁 `Badge`'s
 * own words: *"a notice and a generated claim are different things to a reader
 * deciding whether to trust what they are looking at."*
 */
import type { AccountTag } from '@/lib/api/types';
import type { BadgeTone } from '@/components/ui/badge';
import { Badge } from '@/components/ui/badge';

/**
 * 📁 **The design's chip tones, mapped to the ones the library publishes.**
 *
 * ⚠️ **A `Record` over the server's four rather than a lookup with a
 * fallback**: a fallback would silently render an unknown tone as `neutral`,
 * and **an unknown tone is a contract change the screen should fail on rather
 * than paper over.**
 */
export const TAG_TONES: Record<AccountTag['tone'], BadgeTone> = {
  risk: 'danger',
  warn: 'warning',
  pos: 'success',
  neutral: 'neutral',
};

/**
 * ⚡ **Resolve a row's tag ids against the workspace's vocabulary.**
 *
 * ⛔ **An id with no tag is dropped rather than rendered as a placeholder.**
 * The two reads are separate requests, so a tag created between them is a
 * transient the customer should never see as a broken chip — **and the next
 * vocabulary fetch resolves it.**
 *
 * ✅ **Order is the vocabulary's**, which is name order from the server — so
 * the same account renders its chips the same way on every visit. 📁 *"a list
 * a person scans that reorders between two visits is the kind of defect nobody
 * files and everybody notices."*
 */
export function tagsFor(
  accountId: string,
  assignments: Readonly<Record<string, string[]>> | undefined,
  vocabulary: readonly AccountTag[] | undefined,
): readonly AccountTag[] {
  const held = assignments?.[accountId];
  if (held === undefined || vocabulary === undefined) return [];
  const wanted = new Set(held);
  return vocabulary.filter((tag) => wanted.has(tag.id));
}

export interface AccountTagsProps {
  readonly tags: readonly AccountTag[];
}

/**
 * ⛔ **Renders nothing when an account has no tags** — not an em dash, not
 * *"None"*.
 *
 * 📁 The table's own law, from [`table.ts`](../../lib/accounts/table.ts):
 * *"a column of `—` is worse than an absent column: it says Signora looked and
 * found nothing, when the truth is that nothing was ever asked."* ⚡ **Here the
 * truth is that the customer has not labelled this account**, which is a fact
 * about them rather than about Signora — **and a placeholder would make it
 * look like a gap the product should fill.**
 */
export function AccountTags({ tags }: AccountTagsProps) {
  if (tags.length === 0) return null;
  return (
    <span className="inline-flex flex-wrap gap-1">
      {tags.map((tag) => (
        <Badge key={tag.id} tone={TAG_TONES[tag.tone]}>
          {tag.name}
        </Badge>
      ))}
    </span>
  );
}
