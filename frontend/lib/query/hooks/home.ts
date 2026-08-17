'use client';

/**
 * **What Home needs to resolve a composition** — 📁 `Fortune Signora Home.dc.html`.
 *
 * ⚡ **Adding a file is a use of the frozen foundation rather than a change to
 * it** ([§20c](../../../../CLAUDE.md)), on the precedent `commercial.ts` set.
 */

import { useQuery } from '@tanstack/react-query';

import { getOnboarding, type OnboardingRun } from '@/lib/api/onboarding';
import type { StatedRole } from '@/lib/home/composition';

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
