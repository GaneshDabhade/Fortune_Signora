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
import type { ProductCatalog, PublishProductCatalog } from '@/lib/api/types';
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
