'use client';

/**
 * **What a kind of finding implies** — the Buying Score Engine's model, read
 * without an account in hand.
 *
 * ⚡ **Its own file, on `triage.ts`'s precedent** — `lib/query/hooks.ts` is the
 * frontend's busiest merge point, and adding a file is a *use* of the frozen
 * foundation rather than a change to it ([§20c](../../../CLAUDE.md)).
 */

import { useQuery } from '@tanstack/react-query';

import { apiRequest } from '@/lib/api/client';
import type {
  AccountCommercial,
  AccountCommercialEntry,
  Posture,
  ScoringModel,
} from '@/lib/api/types';
import { queryKeys } from '@/lib/query/keys';

/**
 * 📁 **Home's attention severity** — *"the left rule, the tag word and the tint
 * together"*, `Fortune Signora Home.dc.html` §10 (1.4.1).
 *
 * ⛔ **Not the per-account score.** That read needs an account and the card
 * holds five of them; severity would arrive after the paint, and a row whose
 * colour changes under the cursor is worse than one that never had it.
 *
 * ⛔ **And not a table in this file.** 📁 The signal catalog's own reason: *"a
 * translation table in the client would be a second vocabulary that drifts
 * within a release."* **Posture is Signora's judgement about a hypothesis type,
 * and it is published by the module that holds it.**
 *
 * ⚡ **Returned as a `Map`**, matching `useSignalCatalog`: every caller looks a
 * key up, and none of them iterates.
 *
 * **Held for the session.** The model is a reviewed, versioned artifact — a
 * change is a new version rather than an edit, so a held copy cannot go subtly
 * wrong, only become older than the newest.
 */
export function useScoringModel(workspaceId: string | null) {
  return useQuery({
    queryKey: queryKeys.scoringModel(workspaceId ?? ''),
    queryFn: async (): Promise<ReadonlyMap<string, Posture>> => {
      const model = await apiRequest<ScoringModel>(
        `/workspaces/${workspaceId}/scoring-model`,
        { workspaceId: workspaceId ?? undefined },
      );
      return new Map(model.types.map((type) => [type.key, type.posture]));
    },
    enabled: workspaceId !== null,
    staleTime: Infinity,
  });
}

/**
 * **What a set of accounts is worth**, in one request.
 *
 * ⚡ **The exact sibling of `useAccountIdentities`**, and composed the same way:
 * a lookup rather than an array, because every caller joins it to rows it
 * already holds.
 *
 * ⛔ **Not `useAccountsList`.** That is a keyset page over the whole book; a
 * card holding five ids would have to walk it until they appeared.
 *
 * **Every requested id comes back**, carrying three `null`s when nothing has
 * been said — 📁 [ADR-0409](../../../../docs/architecture/adr/0409-commercial-account-facts.md)
 * §5: *"absence is never inferred, defaulted or zero-filled."*
 */
export function useAccountCommercials(workspaceId: string | null, accountIds: string[]) {
  const ids = [...new Set(accountIds)].sort();

  return useQuery({
    queryKey: queryKeys.commercials(workspaceId ?? '', ids),
    queryFn: async (): Promise<ReadonlyMap<string, AccountCommercial>> => {
      const query = ids.map((id) => `ids=${encodeURIComponent(id)}`).join('&');
      const rows = await apiRequest<AccountCommercialEntry[]>(
        `/workspaces/${workspaceId}/account-commercials?${query}`,
        { workspaceId: workspaceId ?? undefined },
      );
      return new Map(rows.map((row) => [row.account_id, row.commercial]));
    },
    // ⛔ **An empty request is a round trip whose answer is known** — the same
    // guard the identity batch uses.
    enabled: workspaceId !== null && ids.length > 0,
    // Commercial facts move with a CRM sync rather than with a page view.
    staleTime: 60_000,
  });
}
