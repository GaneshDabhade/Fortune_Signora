'use client';

import { useRouter } from 'next/navigation';
import { useEffect, type ReactNode } from 'react';

import { SkeletonText } from '@/components/ui';
import { can, guardFor } from '@/lib/state/permissions';
import type { WorkspaceRole } from '@/lib/state/permissions';

export interface RouteGuardProps {
  pathname: string;
  role: WorkspaceRole | null;
  children: ReactNode;
}

/**
 * Redirects away from a route the caller's role does not permit.
 *
 * **Redirects rather than renders-and-hides.** Rendering the page and then
 * concealing it means the data was already fetched and is sitting in the
 * DOM — visible to anyone who opens devtools, and to any screen reader
 * that ignores `display: none` on a live region.
 *
 * This is a UX affordance, not a security control: the server enforces the
 * same rule via Casbin on every request (ADR-0010).
 */
export function RouteGuard({ pathname, role, children }: RouteGuardProps) {
  const router = useRouter();
  const guard = guardFor(pathname);
  const permitted = guard === undefined || can(role, guard.requires);

  useEffect(() => {
    if (!permitted) router.replace('/');
  }, [permitted, router]);

  // While redirecting, show a skeleton rather than the page. Returning the
  // children here would flash the guarded content for a frame.
  if (!permitted) return <SkeletonText lines={3} />;

  return <>{children}</>;
}
