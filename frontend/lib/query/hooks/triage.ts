'use client';

/**
 * Query hooks for the Signal Center.
 *
 * **Its own file, on `commercial.ts`'s precedent** — `lib/query/hooks.ts` is
 * the frontend's busiest merge point, and a new file is a use of the frozen
 * foundation rather than a change to it (§20c).
 */

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';

import { apiRequest } from '@/lib/api/client';
import type {
  CursorPage,
  QueueEntry,
  QueueState,
  Resolution,
  ResolveOutcome,
} from '@/lib/api/types';
import { queryKeys } from '@/lib/query/keys';

/**
 * What is waiting on somebody, across the whole workspace.
 *
 * **The read that did not exist until TASK-439** — the per-account triage
 * answers *"what is outstanding here"*, and the Signal Center asks *"what is
 * outstanding"*. Same liveness, same derivation, no account.
 *
 * **`state` is part of the key rather than a filter over one cached list.**
 * Queue state is derived on the server from the decision in force and the
 * clock; a browser re-filtering a cached page would be re-deriving it from
 * stale inputs, and a snooze that had elapsed would keep looking snoozed.
 */
export function useWorkspaceTriage(
  workspaceId: string | null,
  state: QueueState | 'all' = 'open',
) {
  return useQuery({
    queryKey: queryKeys.workspaceTriage(workspaceId ?? '', state),
    queryFn: () =>
      apiRequest<CursorPage<QueueEntry>>(
        `/workspaces/${workspaceId}/triage${state === 'all' ? '' : `?state=${state}`}`,
        { workspaceId: workspaceId ?? undefined },
      ),
    enabled: workspaceId !== null,
  });
}

/**
 * Record what somebody decided about a signal.
 *
 * **Invalidates every triage view, not the one that was showing.** A decision
 * moves a signal *between* lists — out of `open` and into `closed` or
 * `snoozed` — so refreshing only the list the seller was looking at would
 * leave the other two describing a queue that no longer exists.
 *
 * **Deliberately does not retry.** Recording a decision twice would create a
 * second resolution superseding the first, which is a correction nobody asked
 * for and which is visible forever in the audit trail.
 */
export function useResolveSignal(workspaceId: string | null) {
  const client = useQueryClient();

  return useMutation({
    retry: false,
    mutationFn: ({ signalId, outcome }: { signalId: string; outcome: ResolveOutcome }) =>
      apiRequest<Resolution>(
        `/workspaces/${workspaceId}/signals/${signalId}/resolution`,
        {
          method: 'POST',
          body: { outcome },
          workspaceId: workspaceId ?? undefined,
        },
      ),
    onSuccess: () => {
      void client.invalidateQueries({
        queryKey: ['workspace', workspaceId ?? '', 'triage'],
      });
    },
  });
}
