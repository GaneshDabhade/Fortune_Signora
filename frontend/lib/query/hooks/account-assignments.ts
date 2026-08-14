/**
 * **Who owns each company, and who looks after it** —
 * [TASK-1479](../../../../docs/BACKLOG.md) slice ⓶, on
 * [ADR-0411](../../../../docs/architecture/adr/0411-customer-organized-account-metadata.md).
 *
 * ## ⛔ The server returns a `member_user_id` and no name
 *
 * 📁 **The ruling stores a reference precisely so a name is never duplicated**
 * — *"a person who leaves must not leave a dangling string"*. ⚡ **So the screen
 * resolves the id against the member list it already has**, and a name never
 * travels on this response. **A name here would be stale the day somebody
 * changed theirs.**
 */
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';

import { apiRequest } from '@/lib/api/client';
import { queryKeys } from '@/lib/query/keys';

export type AccountRole = 'owner' | 'csm';

export interface AccountAssignment {
  readonly account_id: string;
  readonly role: AccountRole;
  readonly member_user_id: string;
}

interface AccountAssignmentList {
  readonly assignments: readonly AccountAssignment[];
}

/**
 * The assignments on the companies currently on screen.
 *
 * ⛔ **Disabled on an empty list rather than asked** — the same reason the tag
 * assignments hook gives: a request that can only return nothing is a round
 * trip to learn what the caller already knew, ⚡ **and a query key of `[]`
 * would cache that nothing against every future empty page.**
 */
export function useAccountAssignments(
  workspaceId: string | null,
  accountIds: readonly string[],
) {
  return useQuery({
    queryKey: queryKeys.accountAssignments(workspaceId ?? '', accountIds),
    enabled: workspaceId !== null && accountIds.length > 0,
    queryFn: () =>
      apiRequest<AccountAssignmentList>(
        `/workspaces/${workspaceId}/account-assignments?${accountIds
          .map((id) => `account_ids=${encodeURIComponent(id)}`)
          .join('&')}`,
      ),
  });
}

/**
 * **Put a member on a selection of companies.**
 *
 * ⚠️ **The response counts what MOVED, not what was sent.** 📁 An account
 * already held by that person is `unchanged`, and telling the customer *"41
 * updated"* when 6 moved would be a number they could disprove by looking.
 */
export function useAssignAccounts(workspaceId: string | null) {
  const client = useQueryClient();
  return useMutation({
    mutationFn: (request: {
      account_ids: readonly string[];
      role: AccountRole;
      member_user_id: string;
    }) =>
      apiRequest<{ role: AccountRole; changed: number; unchanged: number }>(
        `/workspaces/${workspaceId}/account-assignments`,
        { method: 'POST', body: { ...request, account_ids: [...request.account_ids] } },
      ),
    onSuccess: () => {
      // ⚡ **Every assignment query, because a page's answer is keyed by the
      // accounts it asked about** and this write may have touched any of them.
      void client.invalidateQueries({
        queryKey: ['workspace', workspaceId, 'account-assignments'],
      });
    },
  });
}
