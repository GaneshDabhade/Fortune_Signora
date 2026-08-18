/**
 * **What the research agent has been doing in this workspace** —
 * `GET /workspaces/{id}/research`.
 *
 * 📁 **Home's `agents.runs` dependency**, read by both agent cards:
 * `card.agentqueue` — *"agent output awaiting a person"* — and
 * `card.agentruns` — *"scheduled and triggered runs, failures first."*
 *
 * ⚡ **One query for two cards.** The server returns the runs in the order they
 * happened and each card ranks what it was given; 📁 *"failures first"* is one
 * card's ranking of the same list the other reads by recency, and a read per
 * card would spend two requests on one answer.
 */

import { useQuery } from '@tanstack/react-query';

import { apiRequest } from '@/lib/api/client';
import type { ResearchRun } from '@/lib/api/types';
import { queryKeys } from '@/lib/query/keys';

export function useResearchRuns(workspaceId: string | null) {
  return useQuery({
    queryKey: queryKeys.researchRuns(workspaceId ?? ''),
    queryFn: () =>
      apiRequest<ResearchRun[]>(`/workspaces/${workspaceId}/research`, {
        workspaceId: workspaceId ?? undefined,
      }),
    enabled: workspaceId !== null,
  });
}
