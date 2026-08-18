'use client';

import { useSearchParams } from 'next/navigation';

import { useWorkspaces } from '@/lib/query/hooks';
import { lastUsedWorkspaceId } from '@/lib/state/workspace-provider';

import { resolveEntry } from './index';
import { INTENT_PARAM, captureIntent, classifyIntent, decodeIntent } from './intent';
import { observedSession } from './observed';
import type { EntryDecision, Intent, Membership } from './session';

/**
 * **The engine's one production caller** — [TASK-1401](../../../docs/BACKLOG.md).
 *
 * 📁 **The design's sentence, and it is the whole specification of this file:**
 * *"Engineering implements this as one component with one ordered rule list;
 * **no module performs its own entry redirect**."*
 *
 * ## 🔴 The state that decides correctness is `unresolved`, not `resolved`
 *
 * 📁 **[P-A](../../../docs/DOMAIN_DISCOVERY_REGISTER.md): *a failed read must
 * never render as an empty result*** — ⚡ **and on this decision the empty
 * result is a REDIRECT.**
 *
 * ⛔ **If `useWorkspaces()` fails and the failure is treated as *no
 * memberships*, rule 10 fires and a customer with five workspaces is sent to
 * `/workspaces/none` and told they belong to nothing.** 🔴 **That is worse than
 * every other version of P-A this repository has found**, because the others
 * render a wrong screen and this one *navigates* to it — **the person loses the
 * page they were on, and going back returns them to a screen that will decide
 * the same thing again.**
 *
 * ✅ **So the outcome is a three-state union rather than a nullable decision.**
 * ⛔ **A `decision: EntryDecision | null` would let a caller write
 * `decision ?? goHome()`** — the same defect in a nicer shape, and the argument
 * [`index.ts`](./index.ts) already makes for `EntryOutcome`.
 *
 * ⚠️ **The loading half is the same rule one beat earlier**: *an unresolved read
 * must not render as an empty one.* **A query that has not answered has not
 * said the person has no workspaces.**
 *
 * ### 🔴 What the `isError` branch actually protects, stated after fire-testing it
 *
 * ⛔ **It is NOT what it looks like.** ⚠️ **Deleting it does not produce the
 * redirect described above**: on a failed query `data` is `undefined`, so the
 * next branch catches it and returns `resolving`. **The routing property is
 * protected twice, and the second guard is the load-bearing one.**
 *
 * ✅ **What deleting it DOES produce is a person stranded on a spinner
 * forever** — ⚡ **and inside a flow whose only exit is this decision, that is
 * not a cosmetic failure: onboarding has no other way out.** 🔴 **So the branch
 * is kept for the property it genuinely has**, and
 * [`entry-observed.test.ts`](../../tests/unit/entry-observed.test.ts) asserts
 * *failure is distinguishable from loading* rather than *failure does not
 * redirect* — **because only one of those two goes red when the branch is
 * removed** ([§2](../../../CLAUDE.md), *a guard that cannot fail is
 * documentation pretending to be code*).
 *
 * ## ✅ Rules 12, 13 and 14 resolve now, and C-1522 is how they did not
 *
 * ⚠️ **`lastUsedWorkspaceId` was passed as `null`, so rules 11–14 resolved on
 * membership COUNT alone** — 📁 [C-1522](../../../docs/LANE_COORDINATION.md).
 * **The reasoning was right and the conclusion was temporary**: the key is a
 * private constant inside [`lib/state/workspace-provider.tsx`](../state/workspace-provider.tsx),
 * and re-declaring the string here would have been two authoritative
 * representations of one fact ([§2](../../../CLAUDE.md)).
 *
 * ✅ **The provider publishes a reader instead**, so the fact has one owner and
 * one key. ⛔ **Not `activeWorkspace` from the provider** — that falls back to
 * `workspaces[0]` when nothing is stored, so it is never null while a
 * membership exists, **which would make rule 13 (`AMBIGUOUS`) unreachable and
 * silently enter somebody's first workspace instead of showing them the chooser
 * the design specifies.**
 */
export type EntryState =
  /** ⚡ **Nothing is known yet.** ⛔ **Never routes.** */
  | { readonly status: 'resolving' }
  /**
   * 🔴 **The read failed and the engine was NOT asked.** ⛔ **Never routes** —
   * the caller reports the failure and leaves the person where they are.
   */
  | { readonly status: 'unresolved'; readonly error: Error }
  | { readonly status: 'resolved'; readonly decision: EntryDecision };

/**
 * **Resolve where this person belongs, from their memberships and their intent.**
 */
export function useEntryDecision(): EntryState {
  const workspaces = useWorkspaces();
  const params = useSearchParams();

  if (workspaces.isError) {
    return {
      status: 'unresolved',
      error:
        workspaces.error instanceof Error
          ? workspaces.error
          : new Error('the workspace list could not be read'),
    };
  }
  if (workspaces.isPending || workspaces.data === undefined) {
    return { status: 'resolving' };
  }

  const workspaceIds = workspaces.data.items.map((w) => w.id);
  /**
   * ✅ **[C-1522](../../../docs/LANE_COORDINATION.md) is closed.** ⚡ **The
   * provider that owns the key now publishes a reader**, so rules 12, 13 and 14
   * resolve on the fact rather than on membership count alone — and there is
   * still exactly one authoritative representation of where it is stored.
   */
  const session = observedSession({
    workspaceIds,
    lastUsedWorkspaceId: lastUsedWorkspaceId(),
  });

  return {
    status: 'resolved',
    decision: resolveEntry(session, intentFrom(params, session.memberships)),
  };
}

/**
 * ⚡ **The route the person was trying to reach, classified against their own
 * memberships.**
 *
 * ⛔ **`not_member` is decided locally and the server is never consulted** —
 * 📁 [`intent.ts`](./intent.ts): *"asking would leak through timing what the
 * status code withholds."*
 *
 * ⚠️ **Every path this classifier is allowed to ask about answers `granted`,
 * and that is not a permission claim.** 🔴 **The membership check above is the
 * only local decision; the destination is still guarded by the server on the
 * request it makes** ([§20c](../../../CLAUDE.md) — *a client check is a
 * courtesy, never enforcement*). ⛔ **`forbidden` and `missing` are the
 * server's to say and no client-side source for them exists**, so claiming
 * either here would be inventing an authorization answer.
 */
function intentFrom(
  params: URLSearchParams | null,
  memberships: readonly Membership[],
): Intent | null {
  const path = captureIntent(decodeIntent(params?.get(INTENT_PARAM)));
  if (path === null) return null;
  return classifyIntent(path, memberships, () => 'granted');
}
