'use client';

/**
 * **What Home needs to resolve a composition** — 📁 `Fortune Signora Home.dc.html`.
 *
 * ⚡ **Adding a file is a use of the frozen foundation rather than a change to
 * it** ([§20c](../../../../CLAUDE.md)), on the precedent `commercial.ts` set.
 */

import { useQuery } from '@tanstack/react-query';

import { getOnboarding, type OnboardingRun } from '@/lib/api/onboarding';
import {
  ACTIVATION_CARDS,
  activationProgress,
  hasWorkingCapability,
  type ActivationCardId,
  type ActivationProgress as ActivationProgressCount,
} from '@/lib/home/activation';
import type { StatedRole } from '@/lib/home/composition';
import { useIntegrations } from '@/lib/query/hooks/integrations';
import { usePreferences } from '@/lib/query/hooks/preferences';
import { useWorkspaceMembers } from '@/lib/query/hooks/team';

/**
 * 📁 **The person's stated role**, from onboarding screen `05` — *"Role sets the
 * home page and the alert routing."*
 *
 * ### ⛔ `getOnboarding`, never `startOnboarding`
 *
 * ⚠️ **`startOnboarding` is idempotent and would OPEN a run.** ⛔ **Reading
 * somebody's Home must not create an onboarding record for a customer who
 * finished months ago** — a read that writes is the shape [§7](../../../../CLAUDE.md)
 * keeps out of a GET.
 *
 * ### ⚡ A 404 is a real answer and is not retried
 *
 * **Somebody who never onboarded has no run**, which resolves rule 5 — *"anything
 * else"* — and that is correct rather than degraded. ⛔ **Retrying a 404 would
 * delay Home for the one reader it cannot help.**
 */
export function useStatedRole(workspaceId: string | null) {
  return useQuery({
    // ⚡ **Its own key, not the onboarding run's.** ⛔ The flow's own hook holds
    // the whole run and replaces it on every autosave; Home wants one field that
    // changes about once in a career, and sharing a key would refetch Home's
    // resolution every time somebody edited a step.
    queryKey: ['workspace', workspaceId ?? '', 'home', 'stated-role'] as const,
    enabled: workspaceId !== null,
    retry: false,
    // ⚡ **A role changes about once in a career.** The design resolves the
    // composition once per entry, so re-reading this on a refetch would cost a
    // request to learn the same answer.
    staleTime: 10 * 60_000,
    queryFn: async (): Promise<StatedRole | null> => {
      const run: OnboardingRun = await getOnboarding(workspaceId!);
      return (run.role?.value ?? null) as StatedRole | null;
    },
  });
}

/**
 * 🔴 **Activation's completion, derived once.**
 *
 * ⚠️ **Three callers derive this and there were two before the greeting needed
 * it** — the cards, the progress line and now the greeting. 📁 §2, *"truth has
 * exactly one authoritative representation; everything else derives from it"*,
 * and a third copy of *"CRM complete means a working `crm_activity`"* is a third
 * place that goes wrong when the capability's own contract moves.
 *
 * 📁 ***"Completion is derived from the source of truth, never stored on
 * Home"*** — which is what makes this a hook over two reads rather than state.
 *
 * ⛔ **`resolved` is not `isLoading`.** ⚡ Every caller needs the same refusal:
 * **say nothing until both reads have landed.** A progress line that counted an
 * unread connection as *not done*, or a greeting that opened with *"let us get
 * you connected"* to somebody who already had, is worse than a moment's silence.
 */
export function useActivationState(workspaceId: string | null): {
  readonly resolved: boolean;
  readonly complete: Readonly<Record<ActivationCardId, boolean>>;
  readonly progress: ActivationProgressCount;
  /** 📁 Whether the optional step is inside its 30-day skip window. */
  readonly inviteHidden: boolean;
} {
  const systems = useIntegrations(workspaceId);
  const preferences = usePreferences(workspaceId);
  const members = useWorkspaceMembers(workspaceId);

  const complete = {
    'connect-a-crm': hasWorkingCapability(systems.data, 'crm_activity'),
    'connect-calls': hasWorkingCapability(systems.data, 'meetings'),
    // ⚡ **The roster IS the source of truth** — 📁 *"invite complete means
    // members count is greater than one."* ⚠️ **Both earlier derivations passed
    // `false` here** because neither needed it: the progress helper filters to
    // blocking cards, and the card component reads the roster itself. ✅ **The
    // greeting's state 14 needs the real answer**, so it is answered here.
    'invite-the-team': (members.data?.items.length ?? 0) > 1,
  } satisfies Record<ActivationCardId, boolean>;

  return {
    resolved:
      systems.data !== undefined && preferences.data !== undefined && members.data !== undefined,
    complete,
    progress: activationProgress(ACTIVATION_CARDS, complete),
    inviteHidden: preferences.data?.invite_hidden ?? false,
  };
}
