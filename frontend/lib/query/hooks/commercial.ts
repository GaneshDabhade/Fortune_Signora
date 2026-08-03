'use client';

/**
 * Query hooks for the Commercial Profile.
 *
 * **Its own file, deliberately.** `lib/query/hooks.ts` is touched by almost
 * every product-surface slice, which makes it the frontend's busiest merge
 * point. Adding a *new* file is a use of the frozen foundation rather than a
 * change to it (§20c), and it means two development lanes editing the query
 * layer at the same time never edit the same lines.
 */

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';

import { apiRequest } from '@/lib/api/client';
import type {
  BuyingCommittee,
  CommercialFocus,
  CursorPage,
  DeclareBuyingCommittee,
  DeclareFocus,
  DeclareIcp,
  DeclareTargetAccounts,
  IcpDeclaration,
  IcpSegmentSummary,
  ProductCatalog,
  PublishProductCatalog,
  TargetAccountList,
} from '@/lib/api/types';
import { queryKeys } from '@/lib/query/keys';

/**
 * What this workspace sells.
 *
 * **Never 404s.** A workspace that has declared nothing gets version 0 and an
 * empty list, so there is no "not found" state to render — only "nothing
 * declared yet", which is the state every workspace starts in.
 */
export function useProductCatalog(workspaceId: string | null) {
  return useQuery({
    queryKey: queryKeys.products(workspaceId ?? ''),
    queryFn: () =>
      apiRequest<ProductCatalog>(`/workspaces/${workspaceId}/products`, {
        workspaceId: workspaceId ?? undefined,
      }),
    enabled: workspaceId !== null,
  });
}

/**
 * Declare the catalog, as a complete statement.
 *
 * **The whole list is sent, not a change to it.** The catalog is the unit
 * that gets versioned, so "add this one" would make what is stored depend on
 * what was there when the request arrived — the lost update two people
 * editing a list produce.
 *
 * `expected_version` is what turns a colleague's concurrent save into a 409
 * this caller can act on. **The mutation deliberately does not retry**: a
 * retry would re-send a version the server has already rejected once, and
 * every attempt would fail identically while looking like a network problem.
 */
export function usePublishProductCatalog(workspaceId: string | null) {
  const client = useQueryClient();

  return useMutation({
    mutationFn: (catalog: PublishProductCatalog) =>
      apiRequest<ProductCatalog>(`/workspaces/${workspaceId}/products`, {
        method: 'PUT',
        body: catalog,
        workspaceId: workspaceId ?? undefined,
      }),
    // Not optimistic. A catalog that flipped locally and was then refused on
    // version would be the one place the product stated something untrue,
    // and the refusal is precisely the case worth showing accurately.
    onSuccess: (published) => {
      client.setQueryData(queryKeys.products(workspaceId ?? ''), published);
    },
  });
}

/**
 * Who buys what this workspace sells.
 *
 * **Never 404s**, and never a match. It returns what the customer described,
 * at version 0 with no profiles until they have described anybody.
 */
export function useIcpDeclaration(workspaceId: string | null) {
  return useQuery({
    queryKey: queryKeys.icp(workspaceId ?? ''),
    queryFn: () =>
      apiRequest<IcpDeclaration>(`/workspaces/${workspaceId}/icp`, {
        workspaceId: workspaceId ?? undefined,
      }),
    enabled: workspaceId !== null,
  });
}

/**
 * Describe the ideal customer, as a complete statement.
 *
 * The whole description is sent, for the same reason the whole catalog is: the
 * declaration is the unit that gets versioned, so *"describe this one"* would
 * make what is stored depend on what was there when the request arrived.
 *
 * **Deliberately does not retry.** A retry would re-send a version the server
 * has already rejected once, and every attempt would fail identically while
 * looking like a network problem.
 */
export function useDeclareIcp(workspaceId: string | null) {
  const client = useQueryClient();

  return useMutation({
    mutationFn: (declaration: DeclareIcp) =>
      apiRequest<IcpDeclaration>(`/workspaces/${workspaceId}/icp`, {
        method: 'PUT',
        body: declaration,
        workspaceId: workspaceId ?? undefined,
      }),
    // Not optimistic. A description that flipped locally and was then refused
    // on version would be the one place the product stated something untrue.
    onSuccess: (declared) => {
      client.setQueryData(queryKeys.icp(workspaceId ?? ''), declared);
    },
  });
}

/**
 * Who decides about what this workspace sells.
 *
 * **Never 404s, and never an assessment.** It returns the roles the customer
 * said are involved; whether a real company's committee is complete is a
 * conclusion nobody has drawn.
 */
export function useBuyingCommittee(workspaceId: string | null) {
  return useQuery({
    queryKey: queryKeys.buyingCommittee(workspaceId ?? ''),
    queryFn: () =>
      apiRequest<BuyingCommittee>(`/workspaces/${workspaceId}/buying-committee`, {
        workspaceId: workspaceId ?? undefined,
      }),
    enabled: workspaceId !== null,
  });
}

/**
 * Declare the committee, as a complete statement.
 *
 * The whole declaration is sent, for the third time in this module and the
 * same reason each time: the declaration is the unit that gets versioned.
 *
 * **Deliberately does not retry.** A retry would re-send a version the server
 * has already rejected once.
 */
export function useDeclareBuyingCommittee(workspaceId: string | null) {
  const client = useQueryClient();

  return useMutation({
    mutationFn: (declaration: DeclareBuyingCommittee) =>
      apiRequest<BuyingCommittee>(`/workspaces/${workspaceId}/buying-committee`, {
        method: 'PUT',
        body: declaration,
        workspaceId: workspaceId ?? undefined,
      }),
    // Not optimistic, for the same reason as the other two: a declaration
    // that flipped locally and was then refused on version would be the one
    // place the product stated something untrue.
    onSuccess: (declared) => {
      client.setQueryData(queryKeys.buyingCommittee(workspaceId ?? ''), declared);
    },
  });
}

/**
 * What this company is pushing right now.
 *
 * **Never 404s, and applied to nothing.** It reports the products the customer
 * said they are pushing; no screen and no consumer yet does anything with it.
 */
export function useCommercialFocus(workspaceId: string | null) {
  return useQuery({
    queryKey: queryKeys.commercialFocus(workspaceId ?? ''),
    queryFn: () =>
      apiRequest<CommercialFocus>(`/workspaces/${workspaceId}/focus`, {
        workspaceId: workspaceId ?? undefined,
      }),
    enabled: workspaceId !== null,
  });
}

/**
 * Declare the focus, as a complete statement.
 *
 * The whole focus is sent, for the fourth time in this module and the same
 * reason each time: the declaration is the unit that gets versioned.
 *
 * **Deliberately does not retry.** A retry would re-send a version the server
 * has already rejected once.
 */
export function useDeclareFocus(workspaceId: string | null) {
  const client = useQueryClient();

  return useMutation({
    mutationFn: (focus: DeclareFocus) =>
      apiRequest<CommercialFocus>(`/workspaces/${workspaceId}/focus`, {
        method: 'PUT',
        body: focus,
        workspaceId: workspaceId ?? undefined,
      }),
    // Not optimistic, for the same reason as the other three.
    onSuccess: (declared) => {
      client.setQueryData(queryKeys.commercialFocus(workspaceId ?? ''), declared);
    },
  });
}

/**
 * Which companies this workspace watches.
 *
 * **Never 404s.** A workspace that has named nobody gets version 0 and an
 * empty list, which is the state every workspace starts in.
 */
export function useTargetAccounts(workspaceId: string | null) {
  return useQuery({
    queryKey: queryKeys.targetAccounts(workspaceId ?? ''),
    queryFn: () =>
      apiRequest<TargetAccountList>(`/workspaces/${workspaceId}/target-accounts`, {
        workspaceId: workspaceId ?? undefined,
      }),
    enabled: workspaceId !== null,
  });
}

/**
 * Declare the watch list, as a complete statement.
 *
 * **The only write in this module that anything downstream hears about.** The
 * server records the list and announces the change in one transaction; this
 * client sends the whole list, for the same reason as the other four — the
 * declaration is the unit that gets versioned.
 *
 * **Deliberately does not retry.** A retry would re-send a version the server
 * has already rejected once.
 */
export function useDeclareTargetAccounts(workspaceId: string | null) {
  const client = useQueryClient();

  return useMutation({
    mutationFn: (declaration: DeclareTargetAccounts) =>
      apiRequest<TargetAccountList>(`/workspaces/${workspaceId}/target-accounts`, {
        method: 'PUT',
        body: declaration,
        workspaceId: workspaceId ?? undefined,
      }),
    // Not optimistic, for the same reason as the other four — and with more
    // at stake here, because a list shown as saved but refused would be a
    // customer believing Signora had been told to watch something.
    onSuccess: (declared) => {
      client.setQueryData(queryKeys.targetAccounts(workspaceId ?? ''), declared);
    },
  });
}

/**
 * Every customer segment this organization sells to.
 *
 * **The question the product could not answer.** An ideal customer used to be
 * reachable only through the product it belonged to, so there was no page that
 * showed everything a workspace had said about its buyers.
 *
 * Archived segments are excluded unless asked for — they are retired rather
 * than deleted, and they are not what somebody means by *"who do we sell
 * to?"*
 */
export function useIcpSegments(
  workspaceId: string | null,
  options: { includeArchived?: boolean; cursor?: string | null } = {},
) {
  const { includeArchived = false, cursor = null } = options;
  const search = new URLSearchParams();
  if (includeArchived) search.set('include_archived', 'true');
  if (cursor) search.set('cursor', cursor);
  const query = search.toString();

  return useQuery({
    queryKey: [
      ...queryKeys.icpSegments(workspaceId ?? '', cursor),
      includeArchived ? 'with-archived' : 'live',
    ],
    queryFn: () =>
      apiRequest<CursorPage<IcpSegmentSummary>>(
        `/workspaces/${workspaceId}/icp-segments${query ? `?${query}` : ''}`,
        { workspaceId: workspaceId ?? undefined },
      ),
    enabled: workspaceId !== null,
  });
}
