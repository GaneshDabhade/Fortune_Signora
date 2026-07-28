'use client';

import { usePathname } from 'next/navigation';
import type { ReactNode } from 'react';

import { AppShell } from '@/components/shell/app-shell';
import { RouteGuard } from '@/components/shell/route-guard';
import { Button } from '@/components/ui';
import { WorkspaceProvider } from '@/lib/state/workspace-provider';

/**
 * The client half of the authenticated layout.
 *
 * Split from `layout.tsx` because the session check must run on the server
 * while the shell needs client-side hooks. Passing only the email across
 * the boundary keeps the session object itself server-side.
 */
export function AuthenticatedShell({
  email,
  children,
}: {
  email: string;
  children: ReactNode;
}) {
  const pathname = usePathname();

  // TODO(M2.1): the caller's role comes from their membership in the
  // active workspace. The API exposes it via the members endpoint, but
  // resolving it here needs a `GET /workspaces/{id}/me` that does not
  // exist yet — adding one is an API change, not a frontend decision, so
  // it is raised rather than assumed. Until then the shell treats every
  // member as `owner` for *presentation only*; the server's Casbin check
  // is unaffected and remains the authorization decision.
  const role = 'owner' as const;

  return (
    <WorkspaceProvider>
      <AppShell role={role} signOut={<SignOutButton email={email} />}>
        <RouteGuard pathname={pathname} role={role}>
          {children}
        </RouteGuard>
      </AppShell>
    </WorkspaceProvider>
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
