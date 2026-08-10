'use client';

import type { ReactNode } from 'react';

import { RegionBoundary } from '@/components/ui/region-boundary';
import { MobileNavigation, Navigation } from '@/components/shell/navigation';
import { TopBar } from '@/components/shell/top-bar';
import { ShellBanners, type ShellBanner } from '@/components/ui';
import type { Crumb } from '@/lib/shell/breadcrumb';
import { RAIL_WIDTH } from '@/lib/shell/rail';
import { useRailCollapse } from '@/lib/shell/use-rail-collapse';
import type { WorkspaceRole } from '@/lib/state/permissions';

export interface AppShellProps {
  children: ReactNode;
  role: WorkspaceRole | null;
  signOut: ReactNode;
  /**
   * ⚡ **The signed-in address, for the account menu's identity block** —
   * [TASK-1440](../../../docs/BACKLOG.md). 📁 The design: *"always states name,
   * email, role and workspace."*
   *
   * ⛔ **It was already crossing this boundary, buried inside the `signOut`
   * node.** ⚡ **Naming it is what lets slot five state an identity instead of
   * rendering an opaque control**, and it is the whole of this row's change
   * outside `components/shell/**`.
   */
  email: string;
  /**
   * ⚡ **Required for the rail's collapse to be remembered** —
   * [TASK-1408](../../../docs/BACKLOG.md), 📁 *"the state persists per user,
   * per device class."* ⛔ **`null` when the viewer is not resolved yet**, and
   * the rail then remembers nothing rather than sharing one key across every
   * account on the machine.
   */
  userId?: string | null;
  /**
   * 📁 **The banner region, in the design's fixed order** — environment
   * before commercial, at most two, commercial suppressed in sandbox.
   * ⛔ **The shell reserves the slot; it never invents a banner.**
   * ⚠️ **Empty today** — [C-256](../../../docs/LANE_COORDINATION.md): sandbox
   * and trial are sequenced behind Settings and Billing, and impersonation
   * has no design home at all.
   */
  banners?: readonly ShellBanner[];
  inSandbox?: boolean;
  /**
   * 📁 **The breadcrumb's trail** — ⛔ **supplied by the page, never derived
   * here.** **A `/accounts/[id]` segment is an account's NAME**, and only the
   * module holding that record knows it; deriving it would put routing in the
   * shell ([D-193](../../../docs/DECISION_REGISTER.md)).
   */
  breadcrumb?: readonly Crumb[];
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
export function AppShell({
  children,
  role,
  signOut,
  email,
  userId = null,
  banners = [],
  inSandbox = false,
  breadcrumb = [],
}: AppShellProps) {
  // 📁 **Rule: the rail collapses to 56px and the state is remembered.**
  // ⛔ The shell owns the frame's own state; it still owns no navigation
  // decision ([D-193](../../../docs/DECISION_REGISTER.md)).
  const rail = useRailCollapse(userId);

  return (
    /* 📁 **The vertical order is fixed and non-negotiable**: banners, then the
       top bar, then everything else. ⚡ **The banner region sits ABOVE the
       frame's columns** because it spans them — a banner inside the content
       column would leave the rail beside a warning that does not apply to it. */
    <div className="flex min-h-screen flex-col">
      <ShellBanners banners={banners} inSandbox={inSandbox} />

      <div className="flex min-h-0 flex-1">
      <aside
        // ⛔ **The width is the design's, from `RAIL_WIDTH`, not a literal** —
        // 232px expanded and 56px collapsed.
        style={{ width: rail.collapsed ? RAIL_WIDTH.collapsed : RAIL_WIDTH.expanded }}
        data-collapsed={rail.collapsed}
        className="hidden shrink-0 border-r border-border bg-surface transition-[width] duration-150 md:block"
      >
        <div className="flex h-topbar items-center justify-between gap-2 px-5">
          {/* ⚡ The wordmark goes when the rail does — 56px cannot hold it,
              and a clipped wordmark reads as a rendering fault. */}
          {rail.collapsed ? null : (
            <span className="text-sm font-semibold tracking-tight">Signora</span>
          )}
          <button
            type="button"
            onClick={rail.toggle}
            // ♿ The control names the outcome, not the glyph — a screen
            // reader user cannot see which way the chevron points.
            aria-label={rail.collapsed ? 'Expand navigation' : 'Collapse navigation'}
            aria-expanded={!rail.collapsed}
            className="rounded p-1 text-content-subtle transition-colors hover:text-content focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent"
          >
            {rail.collapsed ? '»' : '«'}
          </button>
        </div>
        <RegionBoundary subject="the navigation">
          {/* ⚡ **The rail is told it is collapsed rather than measuring it** —
              TASK-1439. The frame owns the collapse state (`useRailCollapse`);
              a second reader would be a second answer to the same question. */}
          <Navigation role={role} collapsed={rail.collapsed} />
        </RegionBoundary>
      </aside>

      <div className="flex min-w-0 flex-1 flex-col">
        {/* 📁 **The top bar is now the design's slot set** —
            [TASK-1440](../../../docs/BACKLOG.md). ⛔ **The frame no longer
            arranges controls; it hands the bar what the bar needs and the slot
            order is `TopBar`'s.** ⚡ **The theme toggle and `Sign out` left this
            file for the account menu**, which is where the design puts both. */}
        <TopBar breadcrumb={breadcrumb} role={role} email={email} signOut={signOut} />

        {/* The main region is the one place a failure is acceptable to
            isolate: the frame around it stays usable.

            **`pb-20 md:pb-6` is not padding taste** — below `md` the bottom
            navigation is `fixed`, so it is out of flow and would sit on top of
            whatever the page ends with. The last row of the attention list is
            the row a seller scrolls to; covering it is the defect this slice
            exists to avoid rather than one to introduce. */}
        <main className="min-w-0 flex-1 p-4 pb-20 sm:p-6 md:pb-6">
          {/* ⛔ **The one boundary whose default reassurance would be false.**
              *"Everything else on this page is unaffected"* is exactly wrong
              when the content region IS the page — what survives is the frame,
              so the frame is what it names. */}
          <RegionBoundary
            subject="this page"
            reassurance="The navigation and your organizations are unaffected"
          >
            {children}
          </RegionBoundary>
        </main>
      </div>
      </div>

      {/* **Outside the column, because it is fixed to the viewport.** Its own
          boundary for the same reason the sidebar has one: a failure here must
          not take the page with it, and on a phone this is the only navigation
          there is. */}
      <RegionBoundary subject="the navigation">
        <MobileNavigation role={role} />
      </RegionBoundary>
    </div>
  );
}
