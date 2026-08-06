'use client';

/**
 * Finding an account by name.
 *
 * **Its own file**, on the same reasoning as `timeline.ts` and `commercial.ts`:
 * `lib/query/hooks.ts` is the frontend's busiest merge point, and adding a file
 * is a use of the frozen foundation rather than a change to it (§20c).
 */

import { keepPreviousData, useQuery } from '@tanstack/react-query';

import { apiRequest } from '@/lib/api/client';
import type { SearchGroup } from '@/lib/api/types';
import { queryKeys } from '@/lib/query/keys';

/** The server refuses one character, and so does this — a customer who has
 * typed one letter has not asked a question yet. Stated in both places
 * deliberately: the server's rule is the enforcement, and this one exists so
 * the browser does not send a request it knows will be refused. */
export const MINIMUM_QUERY = 2;

/** Enough to choose from, short enough to read without scrolling. */
const RESULT_LIMIT = 8;

/**
 * Accounts matching what the customer typed.
 *
 * **`keepPreviousData` is the whole difference between a usable typeahead and
 * an unusable one.** Without it the list empties on every keystroke and the
 * customer watches results flicker in and out while they finish the word.
 * With it the previous answer stays on screen until the next one arrives, so
 * the list only ever *changes* rather than disappearing.
 *
 * **No `staleTime`.** A search is asked once and acted on immediately; caching
 * it would mean an account named this morning is missing from a search this
 * afternoon, which is the one thing a customer would call broken.
 */
export function useAccountSearch(workspaceId: string | null, text: string) {
  const trimmed = text.trim();

  return useQuery({
    queryKey: queryKeys.accountSearch(workspaceId ?? '', trimmed),
    enabled: Boolean(workspaceId) && trimmed.length >= MINIMUM_QUERY,
    placeholderData: keepPreviousData,
    queryFn: () => {
      const query = new URLSearchParams({ q: trimmed, limit: String(RESULT_LIMIT) });
      return apiRequest<SearchGroup[]>(`/workspaces/${workspaceId}/account-search?${query}`);
    },
  });
}
