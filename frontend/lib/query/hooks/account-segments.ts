/**
 * **A customer's saved groupings of companies** —
 * [TASK-1479](../../../../docs/BACKLOG.md) slice ⓶b, on
 * [ADR-0411](../../../../docs/architecture/adr/0411-customer-organized-account-metadata.md).
 *
 * ## ⚠️ *Segment* means the enumerated grouping here, and it is ruled
 *
 * 📁 **[D-235](../../../../docs/DECISION_REGISTER.md) ②** closed
 * [C-1503](../../../../docs/LANE_COORDINATION.md): **a customer says *ICP* for
 * [ADR-0041](../../../../docs/architecture/adr/0041-icp-aggregate.md)'s stored
 * predicate and *Segment* for the customer-organized enumerated grouping.**
 * ⛔ **`icp_segment` stays an internal name and nothing is renamed** — so
 * `useIcpSegments` elsewhere in this directory is a different concept with a
 * similar spelling, deliberately.
 *
 * ## 🔴 Two reads, and the empty grouping is why
 *
 * ⛔ **A segment with nobody in it comes back with `account_count: 0`, never
 * absent.** 📁 It is the state every grouping passes through between being
 * named and being curated, and **vanishing from the panel in that window would
 * look like the creation had failed** —
 * [P-A](../../../../docs/DOMAIN_DISCOVERY_REGISTER.md), in the window the
 * customer is looking at.
 */
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';

import { apiRequest } from '@/lib/api/client';
import { queryKeys } from '@/lib/query/keys';

export interface AccountSegment {
  readonly segment_id: string;
  readonly name: string;
  /** ⚡ **Derived on read, never stored** — a stored count goes stale the next
   *  time anybody adds a company. */
  readonly account_count: number;
}

interface AccountSegmentDirectory {
  readonly segments: readonly AccountSegment[];
}

export interface AccountSegmentMembership {
  readonly account_id: string;
  readonly segment_ids: readonly string[];
}

interface AccountSegmentMembershipList {
  readonly memberships: readonly AccountSegmentMembership[];
}

/** **Every saved grouping the workspace has, with how many companies are in
 *  each** — the design's *Segments* panel. */
export function useAccountSegments(workspaceId: string | null) {
  return useQuery({
    queryKey: queryKeys.accountSegments(workspaceId ?? ''),
    enabled: workspaceId !== null,
    queryFn: () =>
      apiRequest<AccountSegmentDirectory>(`/workspaces/${workspaceId}/account-segments`),
  });
}

/**
 * **Which groupings the companies on screen are in.**
 *
 * ⛔ **Disabled on an empty list rather than asked** — the same reason the tag
 * and assignment hooks give: a request that can only return nothing is a round
 * trip to learn what the caller already knew, ⚡ **and a query key of `[]`
 * would cache that nothing against every future empty page.**
 *
 * ⚡ **`POST` for a read**, because a page of forty account ids does not fit a
 * query string a proxy will keep, and splitting it would reintroduce the N+1
 * the batch read exists to remove.
 */
export function useAccountSegmentMemberships(
  workspaceId: string | null,
  accountIds: readonly string[],
) {
  return useQuery({
    queryKey: queryKeys.accountSegmentMemberships(workspaceId ?? '', accountIds),
    enabled: workspaceId !== null && accountIds.length > 0,
    queryFn: () =>
      apiRequest<AccountSegmentMembershipList>(
        `/workspaces/${workspaceId}/account-segment-memberships`,
        { method: 'POST', body: { account_ids: [...accountIds] } },
      ),
  });
}

/**
 * **Name a new grouping.**
 *
 * ⚠️ **201, and the contrast with *Add tag*'s 200 is the design's.** *Add tag*
 * selects an existing label because the control is meant to be pressed twice;
 * ⛔ **this opens a naming affordance, and a name already in use is a mistake
 * worth telling the customer about** rather than a repeat they intended.
 */
export function useCreateAccountSegment(workspaceId: string | null) {
  const client = useQueryClient();
  return useMutation({
    mutationFn: (request: { name: string }) =>
      apiRequest<AccountSegment>(`/workspaces/${workspaceId}/account-segments`, {
        method: 'POST',
        body: request,
      }),
    onSuccess: () => {
      void client.invalidateQueries({
        queryKey: ['workspace', workspaceId, 'account-segments'],
      });
    },
  });
}

/**
 * **Put a selection of companies into a grouping.**
 *
 * ⚠️ **The response counts what was ADDED, not what was sent.** 📁 A company
 * already in the grouping comes back as `unchanged`, and telling the customer
 * *"41 added"* when 38 moved would be a number they could disprove by looking.
 */
export function useAddToAccountSegment(workspaceId: string | null) {
  const client = useQueryClient();
  return useMutation({
    mutationFn: (request: { segment_id: string; account_ids: readonly string[] }) =>
      apiRequest<{ segment_id: string; added: number; unchanged: number }>(
        `/workspaces/${workspaceId}/account-segments/${request.segment_id}/accounts`,
        { method: 'POST', body: { account_ids: [...request.account_ids] } },
      ),
    onSuccess: () => {
      // ⚡ **Both queries**: the panel's counts moved, and so did the membership
      // of whichever page was on screen.
      void client.invalidateQueries({
        queryKey: ['workspace', workspaceId, 'account-segments'],
      });
      void client.invalidateQueries({
        queryKey: ['workspace', workspaceId, 'account-segment-memberships'],
      });
    },
  });
}
