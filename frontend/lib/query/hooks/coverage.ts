'use client';

/**
 * Query hook for *"is Signora still watching this company?"* — A7.
 *
 * **Its own file, on the precedent `commercial.ts` set and for the same
 * reason.** It also happens to be the honest place: this reads Provider
 * Platform, and every hook in `commercial.ts` reads Commercial Profile. A file
 * mixing the two would hide, at the one layer that can see both, that they are
 * separate modules the frontend is deliberately composing.
 */

import { useQuery } from '@tanstack/react-query';

import { apiRequest } from '@/lib/api/client';
import type { SubjectCoverage } from '@/lib/api/types';
import { queryKeys } from '@/lib/query/keys';

/**
 * When Signora last looked at each of these companies.
 *
 * **Composed with the declaration rather than joined to it.** The list is
 * Commercial Profile's and the attempts are Provider Platform's, and the
 * dependency runs list → attempts — so no backend module may return both, and
 * this screen is where they meet. The same arrangement the attention list uses
 * to put names on accounts.
 *
 * **The subjects are the key.** A company name is exactly what a customer
 * typed and is exactly what a sync was given, so there is nothing to resolve
 * between the two sides. Removing a company changes the key, which is correct:
 * the answer to a different question should not be served from cache.
 *
 * Disabled when nothing is declared — the endpoint refuses an empty request,
 * and a workspace that has named nobody has nothing to ask about.
 */
export function useTargetAccountCoverage(
  workspaceId: string | null,
  subjects: readonly string[],
) {
  return useQuery({
    queryKey: queryKeys.targetAccountCoverage(workspaceId ?? '', subjects),
    queryFn: () => {
      const query = subjects
        .map((subject) => `subjects=${encodeURIComponent(subject)}`)
        .join('&');
      return apiRequest<SubjectCoverage[]>(
        `/workspaces/${workspaceId}/target-account-coverage?${query}`,
        { workspaceId: workspaceId ?? undefined },
      );
    },
    enabled: workspaceId !== null && subjects.length > 0,
  });
}
