/**
 * **The activation progress line** — [TASK-1424](../../../docs/BACKLOG.md),
 * against 📁 `Fortune Signora Home.dc.html` §*Activation*.
 *
 * 📁 ***"Progress counts BLOCKING cards only. 'Step 2 of 3' with an optional
 * card present reads 'Step 2 of 2 · 1 optional'."***
 *
 * ⛔ **Counting the optional card would make activation look longer than it
 * is** — and would tell somebody they are two-thirds done when they are
 * finished.
 *
 * 📁 ***"Skipping… is reversible from the progress line."*** ⚡ **This is that
 * line**, which is why the restore control lives here and not on a card that,
 * by definition, is not on screen.
 */

'use client';

import { useActivationRegistry, useActivationState } from '@/lib/query/hooks/home';
import { useSkipInvite } from '@/lib/query/hooks/preferences';
import { useWorkspaceContext } from '@/lib/state/workspace-provider';

export function ActivationProgress() {
  const { activeWorkspace } = useWorkspaceContext();
  const workspaceId = activeWorkspace?.id ?? null;
  const skip = useSkipInvite(workspaceId);
  // ⚠️ **Derived once, in `useActivationState`.** ⛔ This component held its own
  // copy of *"CRM complete means a working `crm_activity`"* and so did the
  // cards; the greeting would have been a third (§2).
  // 📁 **Contract 5** — the set and which of it blocks are the server's, so
  // the count is taken from the registry rather than from a constant here.
  const registry = useActivationRegistry(workspaceId);
  const { resolved, progress, inviteHidden } = useActivationState(
    workspaceId,
    registry.registry,
  );

  // ⛔ **Silent until every answer is known.** ⚡ A progress line that counted
  // an unread connection as *not done* would tell somebody they had made no
  // progress, which is worse than saying nothing for a moment.
  if (!resolved || !registry.resolved) return null;

  return (
    <p className="flex items-center gap-2 text-2xs text-content-subtle">
      <span>
        {/* 📁 **The design's own sentence shape.** ⛔ The optional card is
            reported BESIDE the count, never inside it. */}
        Step {Math.min(progress.done + 1, progress.total)} of {progress.total}
        {progress.optional > 0 ? ` · ${progress.optional} optional` : ''}
      </span>

      {inviteHidden ? (
        /* 📁 ***"…and is reversible from the progress line."*** ⚡ **The card is
           hidden, so the control to bring it back cannot live on the card** —
           this line is the only place a person can reach it, which is exactly
           why the design put it here. */
        <button
          type="button"
          onClick={() => skip.mutate(false)}
          disabled={skip.isPending}
          className="rounded underline decoration-border underline-offset-4 transition-colors hover:text-content focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-accent disabled:cursor-not-allowed"
        >
          Show the skipped step
        </button>
      ) : null}
    </p>
  );
}
