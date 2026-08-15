'use client';

import { useRouter } from 'next/navigation';
import { useCallback } from 'react';

import { useEntryDecision } from '@/lib/entry/use-entry';

/**
 * **Where onboarding lets go** — [TASK-469](../../../../docs/BACKLOG.md), and
 * **now [TASK-1401](../../../../docs/BACKLOG.md), which is the row that was
 * always going to replace it.**
 *
 * ## ✅ The seam was built to be deleted, and this is the deletion
 *
 * 📁 **The coordination notice that created this file:**
 *
 * > ***"'Authenticated Entry' is now the authority for ALL post-login
 * > behaviour. TASK-468 and TASK-469 (both yours) have NO DEFINED EXIT and the
 * > spec says both must exit through `resolveEntry` with `intent=null` — do NOT
 * > choose a destination in either flow."***
 *
 * 📁 **And the promise the previous slice left**: *"When D-193/D-194 reach
 * `integration`, this function becomes `resolveEntry({ intent: null })` and
 * nothing else in the flow changes."* ⚡ **It has, and it does** — **the three
 * call sites keep their shape and none of them chooses a destination.**
 *
 * 🔴 **This is the engine's FIRST production caller.** 📁 [`principal.ts`](../../../../lib/entry/principal.ts)
 * has said *"`resolveEntry` has zero callers"* since it was written; **that
 * sentence stops being true here.**
 *
 * ## ⛔ Why the exit had to stop being a plain string
 *
 * ⚠️ **`resolveEntry` needs the person's memberships, and memberships arrive
 * over the network.** ⛔ **A synchronous `string` cannot express *not known
 * yet***, so the seam becomes a hook — **which is the whole change; the buttons
 * still call one thing and still choose nothing.**
 *
 * ## 🔴 What happens when the read FAILS, and why it is not a P-A breach
 *
 * 📁 **[P-A](../../../../docs/DOMAIN_DISCOVERY_REGISTER.md): *a failed read
 * must never render as an empty result*.** ⚡ **The forbidden move here would be
 * treating a failed workspace read as *no memberships*** — rule 10 — **and
 * sending somebody who has just finished onboarding to a screen that tells them
 * they belong to nothing.** ✅ **[`use-entry.ts`](../../../../lib/entry/use-entry.ts)
 * refuses to ask the engine at all in that case.**
 *
 * ✅ **So a failed read exits to `/`, which is exactly where onboarding landed
 * before this row and assumes nothing about the person.** ⛔ **That is not a
 * fallback dressed as a decision** — it is the one destination that makes no
 * claim, and the alternative is stranding somebody inside a finished flow.
 */

/**
 * ⛔ **The destination that assumes nothing**, used only when the engine could
 * not be asked. ⚡ **Not a product decision** — it is the behaviour this flow
 * already had.
 */
export const EXIT_WHEN_UNRESOLVED = '/';

export interface OnboardingExit {
  /** ⚡ **Navigate.** Chooses nothing: the engine's answer, or the destination that assumes nothing. */
  readonly exit: () => void;
  /**
   * ⚠️ **The memberships have not arrived.** ⛔ **A caller shows a pending
   * control rather than exiting** — 📁 *an unresolved read must not render as
   * an empty one*, and here the empty one is a redirect.
   */
  readonly resolving: boolean;
}

export function useOnboardingExit(): OnboardingExit {
  const router = useRouter();
  const state = useEntryDecision();

  const exit = useCallback(() => {
    router.push(state.status === 'resolved' ? state.decision.route : EXIT_WHEN_UNRESOLVED);
  }, [router, state]);

  return { exit, resolving: state.status === 'resolving' };
}
