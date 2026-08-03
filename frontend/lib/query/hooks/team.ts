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

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';

import { apiRequest } from '@/lib/api/client';
import type { CursorPage, Invitation, Membership } from '@/lib/api/types';
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
    // **Corrected at TM-04.** This said a stale role only ever *hides* a
    // control the server would allow. That stopped being true the moment a
    // role could change: a demoted owner would keep seeing owner controls
    // until the cache expired, and the server would refuse each one. Five
    // minutes is still right for a fact that changes this rarely — what
    // changed is that the mutation now invalidates it, so the window is a
    // *concurrent* demotion rather than one the same person performed.
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

/**
 * Who has been invited, and what became of it.
 *
 * **Every state, including the settled ones.** An expired invitation is what
 * tells an administrator that somebody was invited and never arrived; a list
 * that quietly omitted it would leave them believing a colleague had access.
 *
 * **Not paginated**, matching the endpoint: an organization sends a handful of
 * these, not thousands.
 */
export function useInvitations(workspaceId: string | null) {
  return useQuery({
    queryKey: queryKeys.invitations(workspaceId ?? ''),
    queryFn: () =>
      apiRequest<Invitation[]>(`/workspaces/${workspaceId}/invitations`, {
        workspaceId: workspaceId ?? undefined,
      }),
    enabled: workspaceId !== null,
  });
}

/**
 * Invite a colleague.
 *
 * **No optimistic update.** An invitation spends nothing and breaks nothing,
 * but showing it as sent before the server agrees would tell an administrator
 * a colleague had been contacted when the address may have been refused as a
 * duplicate. The list is refetched instead.
 */
export function useInviteMember(workspaceId: string | null) {
  const client = useQueryClient();
  return useMutation({
    mutationFn: (input: { email: string; role: 'owner' | 'member' }) =>
      apiRequest<Invitation>(`/workspaces/${workspaceId}/invitations`, {
        method: 'POST',
        body: input,
        workspaceId: workspaceId ?? undefined,
      }),
    onSuccess: () =>
      client.invalidateQueries({ queryKey: queryKeys.invitations(workspaceId ?? '') }),
  });
}

/** Withdraw an offer. `POST` rather than `DELETE`: nothing is deleted. */
export function useRevokeInvitation(workspaceId: string | null) {
  const client = useQueryClient();
  return useMutation({
    mutationFn: (invitationId: string) =>
      apiRequest<Invitation>(
        `/workspaces/${workspaceId}/invitations/${invitationId}/revoke`,
        { method: 'POST', workspaceId: workspaceId ?? undefined },
      ),
    onSuccess: () =>
      client.invalidateQueries({ queryKey: queryKeys.invitations(workspaceId ?? '') }),
  });
}

/**
 * Send a live invitation again.
 *
 * **The same row, re-delivered.** Not a new invitation: the address, the role
 * and the expiry are unchanged, so the list does not grow and the audit trail
 * still says *invited once*.
 */
export function useResendInvitation(workspaceId: string | null) {
  const client = useQueryClient();
  return useMutation({
    mutationFn: (invitationId: string) =>
      apiRequest<Invitation>(
        `/workspaces/${workspaceId}/invitations/${invitationId}/resend`,
        { method: 'POST', workspaceId: workspaceId ?? undefined },
      ),
    onSuccess: () =>
      client.invalidateQueries({ queryKey: queryKeys.invitations(workspaceId ?? '') }),
  });
}

/** Remove somebody from this organization. The record survives; access does not. */
export function useRemoveMember(workspaceId: string | null) {
  const client = useQueryClient();
  return useMutation({
    mutationFn: (input: { membershipId: string; reason?: string }) =>
      apiRequest<Membership>(
        `/workspaces/${workspaceId}/members/${input.membershipId}/remove`,
        {
          method: 'POST',
          body: { reason: input.reason ?? null },
          workspaceId: workspaceId ?? undefined,
        },
      ),
    onSuccess: () =>
      client.invalidateQueries({ queryKey: queryKeys.members(workspaceId ?? '') }),
  });
}

/**
 * Change what somebody is allowed to do.
 *
 * **Invalidates the roster and the viewer's own role**, because an owner may
 * demote themselves and would otherwise keep seeing controls the server has
 * just started refusing.
 */
export function useChangeRole(workspaceId: string | null) {
  const client = useQueryClient();
  return useMutation({
    mutationFn: (input: { membershipId: string; role: 'owner' | 'member' }) =>
      apiRequest<Membership>(
        `/workspaces/${workspaceId}/members/${input.membershipId}/role`,
        { method: 'POST', body: { role: input.role }, workspaceId: workspaceId ?? undefined },
      ),
    onSuccess: () =>
      client.invalidateQueries({ queryKey: queryKeys.members(workspaceId ?? '') }),
  });
}

/**
 * Hand the organization over.
 *
 * **One request, because it is one operation.** Two calls would leave a window
 * with two owners that nobody asked for, and the second could fail.
 */
export function useTransferOwnership(workspaceId: string | null) {
  const client = useQueryClient();
  return useMutation({
    mutationFn: (input: { fromMembershipId: string; toMembershipId: string }) =>
      apiRequest<Membership[]>(`/workspaces/${workspaceId}/ownership`, {
        method: 'POST',
        body: {
          from_membership_id: input.fromMembershipId,
          to_membership_id: input.toMembershipId,
        },
        workspaceId: workspaceId ?? undefined,
      }),
    onSuccess: () =>
      client.invalidateQueries({ queryKey: queryKeys.members(workspaceId ?? '') }),
  });
}
