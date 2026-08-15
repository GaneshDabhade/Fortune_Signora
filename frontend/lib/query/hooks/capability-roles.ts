'use client';

/**
 * Naming a role, putting somebody on it, and asking what that would trade.
 *
 * 📁 **[TASK-1479](../../../../docs/BACKLOG.md) ⓸**, against
 * [ADR-0410](../../../../docs/architecture/adr/0410-authorization-capability-layer.md)
 * §6 — ✅ **Settings** *Roles & permissions* and *New role*; ✅ **Team
 * Management** *Change to Analyst*, *Effective permissions*, *A Member will be
 * able to*.
 *
 * ## ⛔ Nothing here decides what a role may do
 *
 * 📁 **ADR-0410 §2 forbids *"a second independent authorization model"***, and
 * a permission list held in the browser would be exactly that. ⚡ **Every
 * answer about what somebody may do comes from the server, which asked the same
 * enforcer that decides their requests** — so the screen and the enforcement
 * point cannot disagree.
 *
 * **Its own file**, on the reasoning `team.ts` records: `hooks.ts` is the
 * frontend's busiest merge point, and a new file is a *use* of the frozen query
 * layer rather than a change to it ([§20c](../../../../CLAUDE.md)).
 */

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';

import { apiRequest } from '@/lib/api/client';
import type {
  CapabilityRole,
  EffectivePermissions,
  Permission,
  RoleChangePreview,
} from '@/lib/api/types';
import { queryKeys } from '@/lib/query/keys';

interface CapabilityRoleList {
  roles: CapabilityRole[];
}

/**
 * Every role this organization has defined.
 *
 * ⚡ **A member may read this and may not change it** — `policy.csv` grants
 * `member, capability_role, read` and withholds `update`. 📁 Team Management
 * shows a colleague's role to everyone; **defining roles is administration.**
 */
export function useCapabilityRoles(workspaceId: string | null) {
  return useQuery({
    queryKey: queryKeys.capabilityRoles(workspaceId ?? ''),
    queryFn: () =>
      apiRequest<CapabilityRoleList>(`/workspaces/${workspaceId}/capability-roles`, {
        workspaceId: workspaceId ?? undefined,
      }),
    enabled: workspaceId !== null,
  });
}

/**
 * Who holds which role — **the chip beside every name in Team Management.**
 *
 * ⛔ **Somebody who holds none is ABSENT from the map**, not present with an
 * empty value. ⚡ The request named a workspace, so *"we looked and they hold
 * nothing"* needs no key — the same shape the account-tag assignments use.
 *
 * 🔴 **One request for the whole roster.** ⛔ Asking per row would be an N+1 on
 * the one screen that renders every colleague.
 */
export function useCapabilityAssignments(workspaceId: string | null) {
  return useQuery({
    queryKey: queryKeys.capabilityAssignments(workspaceId ?? ''),
    queryFn: () =>
      apiRequest<{ assignments: Record<string, string> }>(
        `/workspaces/${workspaceId}/capability-assignments`,
        { workspaceId: workspaceId ?? undefined },
      ),
    enabled: workspaceId !== null,
  });
}

/**
 * Name a new role — the design's *New role*.
 *
 * ⚠️ **What this creates grants nothing.** 📁 ADR-0410 §5: *"a capability that
 * is not yet granted denies, which is the safe direction."* ⛔ **So the dialog
 * has to say so** rather than imply a working role, and `holders: 0` on the
 * response is the only honest thing it can report.
 */
export function useCreateCapabilityRole(workspaceId: string | null) {
  const client = useQueryClient();
  return useMutation({
    mutationFn: (input: { name: string }) =>
      apiRequest<CapabilityRole>(`/workspaces/${workspaceId}/capability-roles`, {
        method: 'POST',
        body: input,
        workspaceId: workspaceId ?? undefined,
      }),
    onSuccess: () =>
      client.invalidateQueries({ queryKey: queryKeys.capabilityRoles(workspaceId ?? '') }),
  });
}

/**
 * *Change to Analyst*, and *change back*.
 *
 * ⛔ **`roleId: null` is *change back***, deliberately a value rather than an
 * omission — the same convention the `PUT` uses, and the state everybody starts
 * in.
 *
 * 🔴 **Invalidates the whole workspace scope, not just the roster.** ⚡ **This
 * mutation can change what the SIGNED-IN person may do** — an owner may narrow
 * themselves — **and every cached list was fetched under the old subject.**
 * ⛔ Invalidating only the roles list would leave a screen showing data the
 * server would now refuse to serve.
 */
export function useAssignCapabilityRole(workspaceId: string | null) {
  const client = useQueryClient();
  return useMutation({
    mutationFn: (input: { userId: string; roleId: string | null }) =>
      apiRequest<void>(
        `/workspaces/${workspaceId}/members/${input.userId}/capability-role`,
        {
          method: 'PUT',
          body: { role_id: input.roleId },
          workspaceId: workspaceId ?? undefined,
        },
      ),
    onSuccess: () =>
      client.invalidateQueries({ queryKey: queryKeys.workspaceScope(workspaceId ?? '') }),
  });
}

/**
 * What this person is actually able to do here.
 *
 * ⛔ **Never cached beyond the screen that asked.** 📁 ADR-0410 §3 forbids
 * storing it, and **a long-lived cache entry is a stored copy with a nicer
 * name** — one that would keep asserting a permission after somebody removed
 * it.
 */
export function useEffectivePermissions(workspaceId: string | null, userId: string | null) {
  return useQuery({
    queryKey: queryKeys.effectivePermissions(workspaceId ?? '', userId ?? ''),
    queryFn: () =>
      apiRequest<EffectivePermissions>(
        `/workspaces/${workspaceId}/members/${userId}/effective-permissions`,
        { workspaceId: workspaceId ?? undefined },
      ),
    enabled: workspaceId !== null && userId !== null,
    staleTime: 0,
  });
}

/**
 * What changing this person's role would gain them, and what it would cost.
 *
 * 📁 **The design: *"Both directions are shown, because a role change is a
 * trade rather than a promotion."*** ⚡ **Both sides are asked of the same
 * enforcer as the request path**, so the dialog cannot promise something the
 * server will refuse.
 *
 * ⛔ **`enabled` gates on the dialog being open**, because a preview fetched for
 * every row of a roster would ask the server a question nobody had asked yet.
 */
export function useRoleChangePreview(
  workspaceId: string | null,
  userId: string | null,
  roleId: string | null,
  { enabled }: { enabled: boolean },
) {
  return useQuery({
    queryKey: queryKeys.roleChangePreview(workspaceId ?? '', userId ?? '', roleId),
    queryFn: () =>
      apiRequest<RoleChangePreview>(
        `/workspaces/${workspaceId}/members/${userId}/capability-role/preview` +
          (roleId === null ? '' : `?role_id=${roleId}`),
        { workspaceId: workspaceId ?? undefined },
      ),
    enabled: enabled && workspaceId !== null && userId !== null,
    staleTime: 0,
  });
}

/**
 * The two directions of a trade.
 *
 * ⚡ **Derived here rather than sent**, because `gains` and `loses` are the set
 * difference of two lists the response already carries — 📁 [§2](../../../../CLAUDE.md),
 * *truth has exactly one authoritative representation.*
 *
 * ⛔ **Keyed on `resource:action`**, not on object identity: two responses
 * describing the same permission are two objects, and a `Set` of objects would
 * report every permission as both gained and lost.
 */
export function trade(preview: RoleChangePreview): {
  gains: Permission[];
  loses: Permission[];
} {
  const key = (one: Permission) => `${one.resource}:${one.action}`;
  const now = new Set(preview.current.permissions.map(key));
  const after = new Set(preview.proposed.permissions.map(key));
  return {
    gains: preview.proposed.permissions.filter((one) => !now.has(key(one))),
    loses: preview.current.permissions.filter((one) => !after.has(key(one))),
  };
}
