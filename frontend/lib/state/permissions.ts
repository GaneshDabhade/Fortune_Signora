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

/**
 * 🔴 **A capability in the customer's words** — 📁 Home state 09's panel *"names
 * the missing permission"*, and `HM-COPY-08` puts it in a sentence a person
 * reads: *"Pending requests needs the **Access admin** permission."*
 *
 * ⛔ **`member:add` is engineering's word.** 📁 [ADR-0034](../../../docs/architecture/adr/0034-ubiquitous-language.md)
 * puts the translation at the frontend edge, and a slug in a sentence is the
 * *"explaining Row-Level Security in a dialog"* failure that ADR names.
 */
export const PERMISSION_NAME: Readonly<Record<Capability, string>> = Object.freeze({
  'workspace:read': 'Read this organization',
  'workspace:update': 'Organization admin',
  'member:add': 'Invite members',
  'member:remove': 'Remove members',
});

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
