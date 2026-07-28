'use client';

import type { ReactNode } from 'react';

import { ErrorBoundary } from '@/components/feedback/error-boundary';
import { Navigation } from '@/components/shell/navigation';
import { ThemeToggle } from '@/components/shell/theme-toggle';
import { WorkspaceSelector } from '@/components/shell/workspace-selector';
import type { WorkspaceRole } from '@/lib/state/permissions';

export interface AppShellProps {
  children: ReactNode;
  role: WorkspaceRole | null;
  signOut: ReactNode;
}

/**
 * The application frame: sidebar, top bar, content region.
 *
 * Each region has **its own error boundary**. A single boundary around the
 * whole shell would let a failing navigation component blank the page
 * including the sign-out control, which strands the user with nothing to
 * do but reload.
 *
 * Widths come from `--sidebar-width` and `--topbar-height` rather than
 * literals, so the layout is one edit and not three.
 */
export function AppShell({ children, role, signOut }: AppShellProps) {
  return (
    <div className="flex min-h-screen">
      <aside className="hidden w-sidebar shrink-0 border-r border-border bg-surface md:block">
        <div className="flex h-topbar items-center px-5 text-sm font-semibold tracking-tight">
          Signora
        </div>
        <ErrorBoundary region="Navigation">
          <Navigation role={role} />
        </ErrorBoundary>
      </aside>

      <div className="flex min-w-0 flex-1 flex-col">
        <header className="flex h-topbar shrink-0 items-center justify-between gap-4 border-b border-border bg-surface px-4">
          <ErrorBoundary region="Workspace selector">
            <WorkspaceSelector />
          </ErrorBoundary>
          <div className="flex items-center gap-3">
            <ThemeToggle />
            {signOut}
          </div>
        </header>

        {/* The main region is the one place a failure is acceptable to
            isolate: the frame around it stays usable. */}
        <main className="min-w-0 flex-1 p-6">
          <ErrorBoundary>{children}</ErrorBoundary>
        </main>
      </div>
    </div>
  );
}
