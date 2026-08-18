/**
 * **This person's preferences** — [TASK-1424](../../../../docs/BACKLOG.md).
 *
 * ⚡ **Workspace-scoped, because the record is.** 📁 `person_preferences` is
 * keyed by `(workspace_id, user_id)`, so somebody's answer in one organization
 * is not their answer in another — **and a query key that dropped the workspace
 * would show a returning customer's dismissal to them in a workspace they had
 * just joined.**
 */

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';

import { apiRequest } from '@/lib/api/client';
import type { PersonPreferences, WorkspaceEntry } from '@/lib/api/types';
import { queryKeys } from '@/lib/query/keys';

export function usePreferences(workspaceId: string | null) {
  return useQuery({
    queryKey: queryKeys.preferences(workspaceId ?? ''),
    queryFn: () =>
      apiRequest<PersonPreferences>(`/workspaces/${workspaceId}/preferences`, {
        workspaceId: workspaceId ?? undefined,
      }),
    enabled: workspaceId !== null,
  });
}

/**
 * 📁 ***"Dismissible forever."***
 *
 * ⛔ **No body, because the endpoint takes none.** ⚡ The only two facts are
 * *who* — the caller's verified identity — and *when*, which is the server's
 * clock. **A moment a browser supplied would let it decide when somebody
 * stopped being new.**
 *
 * ✅ **The response IS the new preferences**, so the cache is set from what the
 * server returned rather than invalidated and re-fetched. ⚡ **One round trip,
 * and no window in which the overlay reappears** between the write landing and
 * the read coming back.
 */
export function useDismissFirstRun(workspaceId: string | null) {
  const client = useQueryClient();

  return useMutation({
    mutationFn: () =>
      apiRequest<PersonPreferences>(
        `/workspaces/${workspaceId}/preferences/first-run-dismissal`,
        { method: 'POST', workspaceId: workspaceId ?? undefined },
      ),
    onSuccess: (preferences) => {
      client.setQueryData(queryKeys.preferences(workspaceId ?? ''), preferences);
    },
  });
}

/**
 * 🔴 **Home hierarchy 2 and state 13** — the workspace confirmation strip.
 *
 * 📁 Entry rule 12: *"Enter the last used. **The workspace strip confirms which
 * for four seconds.**"* 📁 Home state 13: *"second or later entry on the same
 * calendar day"* renders *"identical to state 06 with the workspace confirmation
 * strip suppressed. **Home does not congratulate people for returning.**"*
 *
 * ⚡ **A mutation, because entering is an event.** 📁 [D-196](../../../../docs/DECISION_REGISTER.md)
 * built the last-used mechanism and **nothing called it**, so `last_entered_at`
 * was `NULL` for everybody and rule 12 could never fire. **This is the caller.**
 *
 * ⛔ **The answer comes back from the WRITE, never from a read after it.**
 * Recording the entry sets `last_entered_at` to now, so *"is this the first entry
 * today?"* is `false` for anything that asks afterwards.
 */
export function useRecordEntry(workspaceId: string | null) {
  return useMutation({
    mutationFn: () =>
      apiRequest<WorkspaceEntry>(`/workspaces/${workspaceId}/entry`, {
        method: 'POST',
        workspaceId: workspaceId ?? undefined,
      }),
  });
}

/**
 * 🔴 **Home state 04's *"shown exactly once"*** — `AC-H03`.
 *
 * ⚡ **Fired by the strip itself, on its first render**, because *once* is a
 * property of having been shown rather than of having been clicked. ⛔ **A
 * dismiss button would make it *"shown until dismissed"***, and somebody who
 * navigated away without clicking would meet it again tomorrow.
 *
 * ⛔ **It records only that a reader was told**, never that setup is complete —
 * 📁 completion is *"derived from the source of truth, never stored on Home."*
 */
export function useAcknowledgeSetupComplete(workspaceId: string | null) {
  const client = useQueryClient();

  return useMutation({
    mutationFn: () =>
      apiRequest<PersonPreferences>(
        `/workspaces/${workspaceId}/preferences/setup-complete-acknowledgement`,
        { method: 'POST', workspaceId: workspaceId ?? undefined },
      ),
    onSuccess: (preferences) => {
      client.setQueryData(queryKeys.preferences(workspaceId ?? ''), preferences);
    },
  });
}

/**
 * 📁 ***"Non-blocking cards can be skipped, which hides them for 30 days per
 * person and is reversible from the progress line."***
 *
 * ⚡ **One mutation for both directions**, matching the endpoint — ⛔ **two
 * would let a screen ship the hide and forget the way back**, which is the
 * shape that rule exists to prevent.
 */
export function useSkipInvite(workspaceId: string | null) {
  const client = useQueryClient();

  return useMutation({
    mutationFn: (skip: boolean) =>
      apiRequest<PersonPreferences>(
        `/workspaces/${workspaceId}/preferences/invite-skip?skip=${skip}`,
        { method: 'POST', workspaceId: workspaceId ?? undefined },
      ),
    // ✅ **Set from what the server returned**, so there is no window in which
    // the card flickers back between the write landing and a re-read.
    onSuccess: (preferences) => {
      client.setQueryData(queryKeys.preferences(workspaceId ?? ''), preferences);
    },
  });
}

/**
 * 📁 **Change one preference** — screen `07`'s AI consents.
 *
 * ⚡ **Adding a hook is a *use* of the frozen foundation rather than a change
 * to it** ([§20c](../../../../CLAUDE.md)), on the precedent this file's own
 * header sets.
 *
 * ### 🔴 One key, one thing
 *
 * ⛔ **The endpoint distinguishes *absent* from `null`**, so a caller spreading
 * the whole object would clear every field it does not own. **This takes a
 * `Partial` and sends exactly what it was given** — the same contract
 * `changePreferences` in `lib/api/preferences.ts` states, reached through the
 * cache key every other reader of this resource already uses.
 *
 * ### ✅ The response is the new state
 *
 * ⚡ **Set rather than invalidated.** A toggle that flipped back for one frame
 * while a re-read landed would look like a control that failed, and a *consent*
 * control that appears to fail is the one worth spending a round trip to avoid.
 */
export function useChangePreferences(workspaceId: string | null) {
  const client = useQueryClient();

  return useMutation({
    mutationFn: (changes: Partial<PersonPreferences>) =>
      apiRequest<PersonPreferences>(`/workspaces/${workspaceId}/preferences`, {
        method: 'PATCH',
        body: changes,
        workspaceId: workspaceId ?? undefined,
      }),
    onSuccess: (preferences) => {
      client.setQueryData(queryKeys.preferences(workspaceId ?? ''), preferences);
    },
  });
}
