'use client';

/**
 * **What Home needs to resolve a composition** — 📁 `Fortune Signora Home.dc.html`.
 *
 * ⚡ **Adding a file is a use of the frozen foundation rather than a change to
 * it** ([§20c](../../../../CLAUDE.md)), on the precedent `commercial.ts` set.
 */

import { useQuery } from '@tanstack/react-query';

import { queryKeys } from '@/lib/query/keys';

import { apiRequest } from '@/lib/api/client';
import { getOnboarding, type OnboardingRun } from '@/lib/api/onboarding';
import type { ActivationStep } from '@/lib/api/types';
import {
  activationProgress,
  activationRegistry,
  hasWorkingCapability,
  type ActivationCardId,
  type ActivationEntry,
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


const REGISTRY_STALE_MS = 10 * 60_000;

/**
 * 🔴 **The activation registry, from the server.**
 *
 * 📁 **Contract 5** — *"the activation registry is fetched from the server;
 * card order comes from its priority integer, not from array position."*
 *
 * ⛔ **It used to be a frozen array in this bundle**, and that made two things
 * impossible: a step could not be withdrawn without shipping a frontend, and
 * 📁 `AC-H09` — *"return the activation registry as an empty array"* — could
 * not occur at all, so **state 12 was unreachable rather than unimplemented**.
 *
 * ⚡ **Two reads, because two modules own the steps.** Connecting a system is
 * the connections module's; getting colleagues in is membership's. **Neither
 * imports the other**, and this composes them by the integer each declares —
 * which is what the design means by *"a new source declares its own integer;
 * Home does not know the set in advance."*
 *
 * ⚠️ **`resolved` is not `isLoading`, for the same reason it is not anywhere
 * else on Home.** ⛔ An unread registry looks exactly like an empty one, and
 * rendering *"setup steps could not be loaded"* at somebody whose steps were
 * merely still in flight would be the page inventing a fault.
 */
export function useActivationRegistry(workspaceId: string | null): {
  readonly resolved: boolean;
  readonly failed: boolean;
  readonly registry: readonly ActivationEntry[];
  readonly refetch: () => void;
} {
  // ⚡ **A reviewed catalog rather than a customer's data**, so both carry the
  // same long `staleTime`: it changes when a release does, and re-reading it on
  // every window focus would buy nothing.
  const connections = useQuery({
    queryKey: queryKeys.activationSteps(workspaceId ?? '', 'integrations'),
    enabled: workspaceId !== null,
    staleTime: REGISTRY_STALE_MS,
    queryFn: () =>
      apiRequest<ActivationStep[]>(`/workspaces/${workspaceId}/integrations/activation-steps`),
  });
  const membership = useQuery({
    queryKey: queryKeys.activationSteps(workspaceId ?? '', 'membership'),
    enabled: workspaceId !== null,
    staleTime: REGISTRY_STALE_MS,
    queryFn: () =>
      apiRequest<ActivationStep[]>(`/workspaces/${workspaceId}/membership/activation-steps`),
  });

  return {
    resolved: connections.data !== undefined && membership.data !== undefined,
    // ⛔ **A failed read must never render as an empty result** — 📁 `P-A`, and
    // it is the distinction state 12 turns on: *"could not be loaded"* is what
    // a fault says, and an empty registry that ARRIVED says the same sentence
    // for a different reason. Both are the no-data state; neither is silence.
    failed: connections.isError || membership.isError,
    registry: activationRegistry(connections.data, membership.data),
    refetch: () => {
      void connections.refetch();
      void membership.refetch();
    },
  };
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
export function useActivationState(
  workspaceId: string | null,
  registry: readonly ActivationEntry[],
): {
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
    progress: activationProgress(registry, complete),
    inviteHidden: preferences.data?.invite_hidden ?? false,
  };
}
