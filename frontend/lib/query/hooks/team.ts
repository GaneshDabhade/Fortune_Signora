'use client';

/**
 * Query hooks for the people in a workspace.
 *
 * **Its own file**, on the reasoning `commercial.ts` records: `hooks.ts` is the
 * frontend's busiest merge point, and a new file is a *use* of the frozen query
 * layer rather than a change to it (§20c).
 *
 * ### The endpoint has existed since M1 and nothing called it
 *
 * `GET /workspaces/{id}/members` is built, authorized through Casbin, and
 * covered by tests. `queryKeys.members` has been declared in the key registry
 * the whole time, and `Membership` has been declared in `lib/api/types.ts`.
 * **None of the three had a caller** — the shell needed a role and assumed
 * resolving one required an endpoint that does not exist.
 */

import { useQuery } from '@tanstack/react-query';

import { apiRequest } from '@/lib/api/client';
import type { CursorPage, Membership } from '@/lib/api/types';
import { queryKeys } from '@/lib/query/keys';
import type { WorkspaceRole } from '@/lib/state/permissions';

/**
 * Everyone who belongs to this workspace.
 *
 * **Identities, not names.** The payload carries `user_id` and `role` and
 * nothing else a person would recognise — Better Auth owns user identity and
 * runs in the Next.js tier, so the Python API has no name to give
 * ([ADR-0026](../../../docs/architecture/adr/0026-jwt-boundary-architecture.md)).
 * Rendering a readable team list therefore needs a decision this hook
 * deliberately does not make; see [C-024](../../../docs/LANE_COORDINATION.md).
 */
export function useWorkspaceMembers(workspaceId: string | null) {
  return useQuery({
    queryKey: queryKeys.members(workspaceId ?? ''),
    queryFn: () =>
      apiRequest<CursorPage<Membership>>(`/workspaces/${workspaceId}/members`, {
        workspaceId: workspaceId ?? undefined,
      }),
    enabled: workspaceId !== null,
    // Membership changes rarely and a stale role only ever *hides* a control
    // the server would allow — never reveals one it would refuse.
    staleTime: 5 * 60_000,
  });
}

/** What the shell knows about the signed-in person's standing here. */
export interface ViewerRole {
  role: WorkspaceRole | null;
  /** **False while the answer is still unknown.** Distinct from `role === null`,
   * which means *resolved, and this person is not a member*. Collapsing the two
   * would send somebody to the front page for the half-second before their own
   * membership arrived. */
  resolved: boolean;
}

/**
 * The signed-in person's role in this workspace.
 *
 * **Resolved from the members list, not from a `/me` endpoint.** The shell has
 * carried a `TODO(M2.1)` since M2 saying this needed `GET /workspaces/{id}/me`
 * and that adding one was an API change rather than a frontend decision — so it
 * hardcoded `owner` for everybody. **The premise was wrong**: `MembershipResponse`
 * already carries `user_id` and `role`, and the session already carries the
 * signed-in user's id. The answer was reachable the whole time.
 *
 * **Presentation only, and that does not change here.** Casbin on the server is
 * the authorization decision (§20c, ADR-0010). Getting this right stops the
 * product offering a member controls the server will refuse — a control that
 * goes nowhere costs more trust than an absent one.
 */
export function useViewerRole(workspaceId: string | null, viewerId: string | null): ViewerRole {
  const { data, isError } = useWorkspaceMembers(workspaceId);

  // **No workspace means nothing to have a role in**, and that is an answer
  // rather than a pending one — otherwise a signed-in person with no
  // organization waits forever on a query that will never run.
  if (workspaceId === null || viewerId === null) return { role: null, resolved: true };

  // **A failed request resolves to no role.** Fail closed: the alternative is
  // showing controls on the strength of a request that did not happen.
  if (isError) return { role: null, resolved: true };
  if (data === undefined) return { role: null, resolved: false };

  const mine = data.items.find((member) => member.user_id === viewerId);
  return { role: mine?.role ?? null, resolved: true };
}
