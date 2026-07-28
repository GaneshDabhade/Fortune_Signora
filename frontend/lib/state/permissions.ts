/**
 * Client-side route permissions.
 *
 * **This is presentation, not enforcement.** Casbin on the server is the
 * authorization decision (ADR-0010); hiding a link the caller may not use
 * is a courtesy so they do not navigate into a 403. Every route guarded
 * here is also guarded server-side, and the server's answer is the only
 * one that matters.
 *
 * Stated explicitly because the failure mode is subtle: a client-side
 * check that *looks* like enforcement invites someone to skip the server
 * one later, and nothing fails until it is exploited.
 */

export type WorkspaceRole = 'owner' | 'member';

/** Actions the shell needs to reason about. Mirrors the Casbin policy
 * rather than inventing a parallel vocabulary. */
export type Capability =
  'workspace:read' | 'workspace:update' | 'member:add' | 'member:remove';

const ROLE_CAPABILITIES: Record<WorkspaceRole, readonly Capability[]> = {
  owner: ['workspace:read', 'workspace:update', 'member:add', 'member:remove'],
  member: ['workspace:read'],
};

export function can(role: WorkspaceRole | null, capability: Capability): boolean {
  // No role means no membership resolved yet. Fail closed: showing a
  // control and then removing it reads as a bug, and showing one the
  // caller cannot use reads as a broken feature.
  if (role === null) return false;
  return ROLE_CAPABILITIES[role].includes(capability);
}

export interface RouteGuard {
  href: string;
  requires: Capability;
}

/**
 * Routes requiring more than membership. A route absent from this list
 * needs only a resolved workspace.
 */
export const GUARDED_ROUTES: readonly RouteGuard[] = [
  { href: '/settings', requires: 'workspace:update' },
];

export function guardFor(pathname: string): RouteGuard | undefined {
  return GUARDED_ROUTES.find(
    (guard) => pathname === guard.href || pathname.startsWith(`${guard.href}/`),
  );
}
