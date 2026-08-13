import { useQuery } from '@tanstack/react-query';

import { apiRequest } from '@/lib/api/client';
import type { AccountTag, AccountTagAssignments } from '@/lib/api/types';
import { queryKeys } from '@/lib/query/keys';

/**
 * **A customer's own labels** — [TASK-466](../../../../docs/BACKLOG.md),
 * against [ADR-0411](../../../../docs/architecture/adr/0411-customer-organized-account-metadata.md).
 *
 * ## ⛔ Two reads and not one, because they answer different questions
 *
 * ⚡ **The vocabulary is the workspace's and changes rarely**; **the
 * assignments are this page's and change with every scroll.** 📁 One query
 * would re-fetch the whole vocabulary on every page turn and cache neither
 * usefully.
 *
 * ## ⚠️ Why the assignments read is a POST
 *
 * **The account list IS the query.** A table showing forty rows would otherwise
 * put forty ids in a URL. ⛔ **It reads and writes nothing** — the method is
 * about the size of the question, not about a side effect.
 */
export function useAccountTags(workspaceId: string | null) {
  return useQuery({
    queryKey: queryKeys.accountTags(workspaceId ?? ''),
    enabled: workspaceId !== null,
    queryFn: () =>
      apiRequest<{ tags: AccountTag[] }>(`/workspaces/${workspaceId}/account-tags`),
  });
}

/**
 * **Which labels each of these accounts wears.**
 *
 * ⛔ **Disabled on an empty list rather than asked.** 📁 The server answers
 * `{}` for no accounts, and a request that can only return nothing is a round
 * trip to learn what the caller already knew — ⚡ **and a query key of `[]`
 * would cache that nothing against every future empty page.**
 */
export function useAccountTagAssignments(
  workspaceId: string | null,
  accountIds: readonly string[],
) {
  return useQuery({
    queryKey: queryKeys.accountTagAssignments(workspaceId ?? '', accountIds),
    enabled: workspaceId !== null && accountIds.length > 0,
    queryFn: () =>
      apiRequest<AccountTagAssignments>(
        `/workspaces/${workspaceId}/account-tags/assignments`,
        { method: 'POST', body: { accounts: [...accountIds] } },
      ),
  });
}
