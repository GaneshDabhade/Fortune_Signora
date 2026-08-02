'use client';

/**
 * Query hooks for an account's history.
 *
 * **Its own file, deliberately** — the same reasoning as `commercial.ts`.
 * `lib/query/hooks.ts` is touched by almost every product-surface slice and is
 * the frontend's busiest merge point; adding a new file is a use of the frozen
 * foundation rather than a change to it (§20c).
 */

import { useInfiniteQuery } from '@tanstack/react-query';

import { apiRequest } from '@/lib/api/client';
import type { CursorPage, TimelineEntry } from '@/lib/api/types';
import { queryKeys } from '@/lib/query/keys';

/** A page small enough to read and large enough to be worth a request. */
export const TIMELINE_PAGE_SIZE = 25;

/**
 * What has happened with this account, newest first.
 *
 * **Paged rather than fetched whole.** An account the pipeline has watched for
 * a year has thousands of entries, and a feed that loads all of them is a
 * screen that never finishes on the accounts that matter most — the ones with
 * the most activity.
 *
 * **`useInfiniteQuery` over manual state** because the server's cursor is
 * opaque by contract: pages are walked by echoing back what the last one
 * returned, never by computing an offset. That is what keeps a page boundary
 * stable while the pipeline keeps writing.
 */
export function useAccountTimeline(workspaceId: string | null, accountId: string | null) {
  return useInfiniteQuery({
    queryKey: queryKeys.accountTimeline(workspaceId ?? '', accountId ?? ''),
    enabled: Boolean(workspaceId && accountId),
    initialPageParam: null as string | null,
    queryFn: ({ pageParam }) => {
      const query = new URLSearchParams({ limit: String(TIMELINE_PAGE_SIZE) });
      if (pageParam) query.set('cursor', pageParam);
      return apiRequest<CursorPage<TimelineEntry>>(
        `/workspaces/${workspaceId}/accounts/${accountId}/timeline?${query}`,
      );
    },
    // `has_more` rather than `next_cursor != null`: the server sends both, and
    // the explicit flag is the one that reads correctly at a page boundary
    // where a cursor exists but there is nothing after it.
    getNextPageParam: (last: CursorPage<TimelineEntry>) =>
      last.has_more ? last.next_cursor : undefined,
  });
}
