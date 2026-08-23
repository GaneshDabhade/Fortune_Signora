'use client';

import { useRouter } from 'next/navigation';
import { useState } from 'react';

import { Button, Dialog } from '@/components/ui';
import { ApiError } from '@/lib/api/client';
import { useLeaveOrganization } from '@/lib/query/hooks/team';
import { useWorkspaceContext } from '@/lib/state/workspace-provider';

/**
 * 📁 **User Profile → Activity → *"Your data"*** — the design's `dataRights`
 * block.
 *
 * ## ⚡ Why this exists now, and why only one of its three rows is live
 *
 * 📁 **The design draws three rows**: *Download your data*, *Activity
 * retention* and *Leave this workspace*. ⛔ **Two of them describe capabilities
 * the platform does not have** — there is no export endpoint anywhere in the
 * 117 the API publishes, and nothing implements an 18-month purge. ⚡ **So they
 * are ABSENT rather than drawn inert**: 📁 [§20c](../../../CLAUDE.md) —
 * *"screens without a shipped module behind them ship a designed empty state"*
 * — and a row offering *Request export* that does nothing is the placeholder
 * that rule forbids.
 *
 * ✅ **The third row is fully producer-backed and was blocked on a row that has
 * since closed.** 📁 `POST /workspaces/{id}/membership/leave` ships, and its
 * own docstring calls it *"the half of team management the product never
 * had"*. 📁 [C-207](../../../docs/LANE_COORDINATION.md) — *"Casbin cannot
 * express an action on yourself"* — is **`CLOSED`, 2026-08-05, by
 * [ADR-0404](../../../docs/architecture/adr/0404-platform-composition.md)**,
 * and the row's own *unblocks* column names this exact capability:
 * ***"Leaving an organization, and every self-directed operation after it."***
 * ⛔ **`settings/team/page.tsx` still carried a comment saying leaving *"is
 * blocked on C-207"*** — a stale blocker outliving its ruling by eighteen days.
 *
 * ## 🔴 The design's body copy asserts two behaviours the platform does not have
 *
 * 📁 **The design says**: *"You lose access immediately. **Work you own must be
 * reassigned first, and your administrator is notified.**"*
 *
 * ⛔ **Neither is true.** `leave_workspace.py` locks the membership, counts
 * live owners and refuses to leave a workspace ownerless — **and does nothing
 * else.** **No reassignment is required and no notification is sent.** ⚠️
 * **Rendering that sentence would tell a customer their work is safe because
 * something reassigned it**, which is the exact class of false claim
 * 📁 [§2](../../../CLAUDE.md) forbids and this lane has now found five times.
 *
 * ✅ **So the consequence rendered here is the one the code actually
 * produces**, and the divergence is recorded as
 * [C-1552](../../../docs/LANE_COORDINATION.md) rather than silently dropped.
 */
export function DataRightsPanel() {
  const router = useRouter();
  const { activeWorkspace } = useWorkspaceContext();
  const workspaceId = activeWorkspace?.id ?? null;
  const leave = useLeaveOrganization(workspaceId);
  const [confirming, setConfirming] = useState(false);

  return (
    <section aria-labelledby="profile-data-heading">
      {/* 📁 The design's own heading for the block. */}
      <h2 id="profile-data-heading" className="text-label font-semibold text-content">
        Your data
      </h2>

      {/* 📁 *"border: var(--risk)"* — the design gives this row the risk edge
          because it is the destructive one, and it is the only row in the
          block that is drawn that way. */}
      <div className="mt-3 rounded-lg border border-danger bg-surface p-5">
        <p className="text-label font-semibold text-danger">Leave this organization</p>
        {/* ⛔ **NOT the design's sentence.** See the docblock: it promises
            reassignment and a notification, and neither exists. ✅ This states
            what leaving actually does, and borrows the honest half of the
            removal dialog's wording — *"what they have already decided stays
            on the record"* — because that part IS true. */}
        <p className="mt-1.5 max-w-prose text-sm leading-6 text-content-muted">
          You lose access to this organization&rsquo;s accounts, evidence and decisions
          immediately. What you have already decided stays on the record.
        </p>
        <div className="mt-3.5">
          <Button variant="danger" onClick={() => setConfirming(true)}>
            Leave organization
          </Button>
        </div>
      </div>

      <Dialog
        open={confirming}
        onClose={() => setConfirming(false)}
        title="Leave this organization"
        /* ⚡ **Names the consequence, never *"are you sure"*** — the rule
           `settings/team/page.tsx` states for the removal dialog, and the same
           reason applies: it is a question the customer has no way to answer. */
        description="You will lose access to this organization immediately. What you have already decided stays on the record."
        footer={
          <>
            <Button variant="secondary" onClick={() => setConfirming(false)}>
              Cancel
            </Button>
            <Button
              variant="danger"
              loading={leave.isPending}
              onClick={() =>
                leave.mutate(undefined, {
                  /* ⚡ **Entry resolution decides where they land**, not this
                     component — the caller may still belong to other
                     organizations, and 📁 D-193 makes that the shell's
                     decision. ⛔ A hardcoded destination here would be a
                     second answer to a question the entry engine owns. */
                  onSuccess: () => {
                    setConfirming(false);
                    router.push('/');
                  },
                })
              }
            >
              Leave organization
            </Button>
          </>
        }
      />

      {/* 🔴 **The server's refusal, rendered.** 📁 The domain refuses to leave a
          workspace ownerless and ADR-0404 put that check in the application
          layer deliberately, because *"a check in an interface can be raced by
          a second tab"*. ⛔ **So this component pre-checks nothing** and shows
          what the server said. */}
      {leave.error ? (
        <p role="alert" className="mt-3 text-sm leading-6 text-danger">
          {leave.error instanceof ApiError
            ? leave.error.message
            : 'You could not be removed from this organization. Nothing has changed.'}
        </p>
      ) : null}
    </section>
  );
}
