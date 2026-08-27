'use client';

import { Lock } from 'lucide-react';

import { SystemState } from '@/components/ui/system-state';
import { HM_COPY_08 } from '@/lib/home/copy';
import { useWorkspaceMembers } from '@/lib/query/hooks/team';

/**
 * 📁 **Home's state 09 — `state.forbidden`.**
 *
 * > Entry: *"The person's role excludes a card in their composition — e.g. an
 * > analyst in the operations composition without access-request rights."*
 * >
 * > Renders: *"The card is **replaced in place by a same-footprint panel naming
 * > the missing permission and the approvers**. **Never hidden — hiding it makes
 * > people think the capability is absent.**"*
 * >
 * > **P-11** — *"Forbidden cards stay visible. Named permission, named approvers,
 * > same footprint. **Hidden capability is the most common cause of 'the product
 * > does not do X' when it does.**"*
 * >
 * > **`AC-H11`** — *"An analyst in the operations composition sees the forbidden
 * > panel for Pending requests **at the same footprint as the card it
 * > replaces**."*
 *
 * ## ⛔ It names the permission and the approvers, never the withheld data
 *
 * 📁 The design's own rule for this panel. ⚡ **A person who cannot see a card
 * must still learn two things**: what would let them, and who can grant it.
 *
 * ## ⚠️ Approvers are addresses, because the API has no names
 *
 * 📁 **ADR-0026** puts user identity in Better Auth, in the Next.js tier — **the
 * Python API has no name to give**, which is why `Membership` carries
 * `member_email` and nothing else a person would recognise. ⛔ **A membership
 * added by identifier has neither**, and 📁 D23's ruling for the team list is the
 * wording used here rather than an id dressed as information.
 */
export interface ForbiddenCardProps {
  /** 📁 The card's own title — the panel names what it replaced. */
  readonly card: string;
  /** 📁 *"The missing permission"*, in the customer's words rather than a slug. */
  readonly permission: string;
  readonly workspaceId: string | null;
  readonly testId?: string;
}

export function ForbiddenCard({ card, permission, workspaceId, testId }: ForbiddenCardProps) {
  const members = useWorkspaceMembers(workspaceId);

  /**
   * ⚡ **Owners are the approvers**, because `policy.csv` grants every
   * `member:*` action to `owner` alone.
   *
   * ⚠️ **This reads one page of members**, which is what the endpoint returns —
   * 🔴 [B-284](../../../docs/BUGS.md) is the defect that taught this, and here it
   * is a smaller matter: **naming three of a workspace's owners is useful; naming
   * none is not.** ⛔ The sentence therefore says *"an owner"* rather than
   * claiming a complete list when the page holds none.
   */
  const approvers = (members.data?.items ?? [])
    .filter((member) => member.role === 'owner')
    .map((member) => member.member_email)
    .filter((email): email is string => email !== null && email !== undefined);

  return (
    <div data-testid={testId} className="h-full">
      <SystemState
        scope="region"
        /**
         * 🔴 **`region-error`, and its severity is `risk` — so this panel is
         * danger-tinted, and it should not be.** 📁
         * [C-1576](../../../docs/LANE_COORDINATION.md).
         *
         * ⛔ **The grammar's rule is unambiguous**: *"warn for permission and
         * interruption, risk for genuine failure. **The colour is never
         * decorative.**"* ⚠️ **And this file argues the same thing two comments
         * down and then contradicts it.**
         *
         * ⛔ **It is NOT changed, because there is nothing legal to change it
         * to.** ⚡ **The design's scope table gives region exactly four
         * states** — retry, skeleton, region error, empty result — **and
         * assigns `permission required` to Page**, while §05 names *"Permission
         * required — **in place**"* as a distinct thing that happens on a page
         * you can see. **The two halves of one document disagree.**
         *
         * ⚠️ **Adding the state was tried and reverted.** 📁
         * [`scope-ladder.test.ts`](../../tests/unit/scope-ladder.test.ts) reads
         * the design document at test time and refused it — **correctly**: *"the
         * ladder is the design's, not a transcription of it."* ⛔ **Weakening
         * that guard to fit a tint would trade the one mechanism that keeps
         * this file honest for a colour.**
         */
        state="region-error"
        glyph={Lock}
        title={`${card} needs the ${permission} permission`}
        /* 📁 `HM-COPY-08`, verbatim — *"{card} needs the {permission} permission.
           Approvers: …"* ⛔ **And never the withheld data**, which is the one
           thing the design says this panel must not name. */
        description={HM_COPY_08(
          card,
          permission,
          approvers.length > 0 ? approvers.join(', ') : 'an owner of this organization',
        )}
        /* ⛔ **Same footprint as the card it replaces** — 📁 `AC-H11`, *"so the
           grid is stable"*. ⚡ **Solid rather than the dashed border state 08
           uses**: this is not a failure, and drawing it as one would tell
           somebody something is broken when nothing is. */
        className="h-full"
      />
    </div>
  );
}
