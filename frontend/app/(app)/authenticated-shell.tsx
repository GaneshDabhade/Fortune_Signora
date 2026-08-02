'use client';

import { usePathname } from 'next/navigation';
import type { ReactNode } from 'react';

import { AppShell } from '@/components/shell/app-shell';
import { RouteGuard } from '@/components/shell/route-guard';
import { Button, SkeletonText } from '@/components/ui';
import { useSession } from '@/lib/auth/client';
import { useViewerRole } from '@/lib/query/hooks/team';
import { WorkspaceProvider, useWorkspaceContext } from '@/lib/state/workspace-provider';

/**
 * The client half of the authenticated layout.
 *
 * Split from `layout.tsx` because the session check must run on the server
 * while the shell needs client-side hooks. Passing only the email across
 * the boundary keeps the session object itself server-side.
 *
 * ### It used to tell everybody they were an owner
 *
 * A `TODO(M2.1)` sat here for four milestones: *"resolving it here needs a
 * `GET /workspaces/{id}/me` that does not exist yet — adding one is an API
 * change, not a frontend decision."* Until then it hardcoded `owner` **for
 * everybody**.
 *
 * **The premise was wrong.** `Membership` already carries `user_id` and `role`,
 * the members endpoint already returns them, and the session already carries
 * the signed-in user's id. No new endpoint was ever needed — and the TODO had
 * outlived the belief that produced it.
 *
 * ### Presentation, never enforcement
 *
 * Casbin on the server is the authorization decision (§20c, ADR-0010) and
 * nothing here changes that. What changes is that a member is no longer offered
 * controls the server will refuse — **a control that goes nowhere costs more
 * trust than an absent one**, which is the rule this surface already applies to
 * citations and to workflow actions.
 */
export function AuthenticatedShell({
  email,
  children,
}: {
  email: string;
  children: ReactNode;
}) {
  return (
    <WorkspaceProvider>
      {/* **Inside the provider, deliberately.** A role is a fact about a person
          *in a workspace*, so it cannot be resolved above the thing that knows
          which workspace is active. */}
      <ShellForViewer email={email}>{children}</ShellForViewer>
    </WorkspaceProvider>
  );
}

function ShellForViewer({ email, children }: { email: string; children: ReactNode }) {
  const pathname = usePathname();
  const { activeWorkspace } = useWorkspaceContext();
  const { data: session } = useSession();

  const { role, resolved } = useViewerRole(
    activeWorkspace?.id ?? null,
    session?.user.id ?? null,
  );

  // **Nothing is guarded until the role is known.** `RouteGuard` fails closed
  // and *redirects*, which is right once the answer is in and wrong before it:
  // an owner opening Settings directly would be bounced to the front page in
  // the moment before their own membership arrived, and would not be sent
  // back. The frame renders throughout; only its contents wait.
  return (
    <AppShell role={resolved ? role : null} signOut={<SignOutButton email={email} />}>
      {resolved ? (
        <RouteGuard pathname={pathname} role={role}>
          {children}
        </RouteGuard>
      ) : (
        <SkeletonText lines={3} />
      )}
    </AppShell>
  );
}

function SignOutButton({ email }: { email: string }) {
  return (
    <form action="/api/auth/sign-out" method="post" className="flex items-center gap-3">
      <span className="hidden text-sm text-content-muted sm:inline">{email}</span>
      <Button type="submit" variant="secondary" size="sm">
        Sign out
      </Button>
    </form>
  );
}
