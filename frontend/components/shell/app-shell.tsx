'use client';

import type { ReactNode } from 'react';

import { ErrorBoundary } from '@/components/feedback/error-boundary';
import { AccountSearch } from '@/components/intelligence/account-search';
import { MobileNavigation, Navigation } from '@/components/shell/navigation';
import { ThemeToggle } from '@/components/shell/theme-toggle';
import { WorkspaceSelector } from '@/components/shell/workspace-selector';
import type { WorkspaceRole } from '@/lib/state/permissions';

export interface AppShellProps {
  children: ReactNode;
  role: WorkspaceRole | null;
  signOut: ReactNode;
}

/**
 * The application frame: sidebar, top bar, content region — **and, on a phone,
 * a bottom navigation bar** (CX-07).
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
        <header className="flex h-topbar shrink-0 items-center justify-between gap-3 border-b border-border bg-surface px-4">
          {/* **The wordmark lives in the sidebar, which does not exist on a
              phone.** Shown here below `md` so the product is still named on
              the one viewport where the frame is otherwise anonymous. */}
          <span className="shrink-0 text-sm font-semibold tracking-tight md:hidden">Signora</span>
          <ErrorBoundary region="Workspace selector">
            <WorkspaceSelector />
          </ErrorBoundary>
          {/* **Search is a verb, not a place** (A1), so it sits here rather
              than becoming a navigation entry. Its own boundary on the same
              reasoning as every other region: a failing search must not take
              the workspace selector or sign-out down with it. */}
          <ErrorBoundary region="Account search">
            <AccountSearch />
          </ErrorBoundary>
          <div className="flex items-center gap-3">
            <ThemeToggle />
            {signOut}
          </div>
        </header>

        {/* The main region is the one place a failure is acceptable to
            isolate: the frame around it stays usable.

            **`pb-20 md:pb-6` is not padding taste** — below `md` the bottom
            navigation is `fixed`, so it is out of flow and would sit on top of
            whatever the page ends with. The last row of the attention list is
            the row a seller scrolls to; covering it is the defect this slice
            exists to avoid rather than one to introduce. */}
        <main className="min-w-0 flex-1 p-4 pb-20 sm:p-6 md:pb-6">
          <ErrorBoundary>{children}</ErrorBoundary>
        </main>
      </div>

      {/* **Outside the column, because it is fixed to the viewport.** Its own
          boundary for the same reason the sidebar has one: a failure here must
          not take the page with it, and on a phone this is the only navigation
          there is. */}
      <ErrorBoundary region="Navigation">
        <MobileNavigation role={role} />
      </ErrorBoundary>
    </div>
  );
}
