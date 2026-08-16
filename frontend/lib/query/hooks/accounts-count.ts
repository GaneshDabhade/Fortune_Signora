import { useQuery } from '@tanstack/react-query';

import { apiRequest } from '@/lib/api/client';
import type { AccountCount } from '@/lib/api/types';
import { queryKeys } from '@/lib/query/keys';

/**
 * **How big the customer's book is** — [TASK-1475](../../../../docs/BACKLOG.md),
 * `GET /workspaces/{id}/accounts-count`.
 *
 * ## 📁 Why the header needs a second read at all
 *
 * **The design states two numbers side by side** — *"8,412 total · 312 in
 * view"* — ⚡ **and only the second is knowable on the client.** *In view* is
 * the page the customer is looking at; **total is a property of the workspace,
 * and `accounts-list` is keyset-paginated**, so counting loaded rows measures
 * how much has been fetched rather than how much exists.
 *
 * ⛔ **Printing the loaded count beside the word *total* would be wrong by
 * more with every page** — the quiet kind of wrong, because it looks right on
 * the first screen.
 *
 * ## ⚡ Its own query, deliberately
 *
 * ⛔ **Not a field on the page envelope.** `CursorPage` is platform-owned and
 * frozen ([§20a](../../../../CLAUDE.md)), and a `COUNT(*)` attached to every
 * page would be charged to a customer who is only scrolling. **This runs once
 * and stays cached while they page.**
 */
export function useAccountsCount(workspaceId: string | null) {
  return useQuery({
    queryKey: queryKeys.accountsCount(workspaceId ?? ''),
    enabled: workspaceId !== null,
    queryFn: () =>
      apiRequest<AccountCount>(`/workspaces/${workspaceId}/accounts-count`, {
        workspaceId: workspaceId ?? undefined,
      }),
  });
}
