'use client';

import { usePathname } from 'next/navigation';
import { useCallback, useEffect, useState, type ReactNode } from 'react';

import { RegionBoundary } from '@/components/ui/region-boundary';
import { Navigation } from '@/components/shell/navigation';
import { Copilot } from '@/components/shell/copilot';
import { ShellPalette } from '@/components/shell/shell-palette';
import { ShortcutsReference } from '@/components/shell/shortcuts-reference';
import { RouteAnnouncer } from '@/components/shell/route-announcer';
import { SKIP_TARGETS, SkipLinks } from '@/components/shell/skip-links';
import { TopBar } from '@/components/shell/top-bar';
import { UtilityPanelDock, UtilityPanelProvider } from '@/components/shell/utility-panel';
import { WorkspaceSwitcher } from '@/components/shell/workspace-switcher';
import { Container, ShellBanners, type ShellBanner } from '@/components/ui';
import { cn } from '@/lib/design/cn';
import type { Crumb } from '@/lib/shell/breadcrumb';
import { RAIL_WIDTH } from '@/lib/shell/rail';
import { useIsRefreshing } from '@/lib/shell/refreshing';
import { useRailCollapse } from '@/lib/shell/use-rail-collapse';
import type { WorkspaceRole } from '@/lib/state/permissions';

export interface AppShellProps {
  children: ReactNode;
  role: WorkspaceRole | null;
  /** 🔴 **Whether the role has ARRIVED** — [B-253](../../../docs/BUGS.md). */
  roleKnown: boolean;
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
  /** 📁 §11 *"Always states name, email, role and workspace."* — [B-429](../../../docs/BUGS.md). ⛔ `null` when the session carries none. */
  name: string | null;
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
 * The application frame: **one rail, a top bar and a content region.**
 *
 * ## 🔴 [TASK-1461](../../../docs/BACKLOG.md) — the rail MOVES; it is never duplicated
 *
 * ⛔ **This shell mounted two navigations and hid one with CSS.** 📁 The design's
 * landmark table names exactly one — *"`nav[navigation]` — the rail, labelled
 * 'Primary'. Workspace switcher is its first child"* — **and `display:none`
 * leaves an element in the DOM**, so `nav[aria-label="Primary"]` returned **2 at
 * 390, 1024, 1280 and 1600.** ⚠️ **`getByRole` could not see it**, which is why
 * it survived a suite that asserts the rail on every screen, and why 📁
 * [B-180](../../../docs/BUGS.md)'s overlap guard could not fail anywhere.
 *
 * ✅ **The bottom bar is deleted rather than restyled** — 📁 the band's
 * sentence is *"Rail becomes a sheet from a top-bar button"*, **and a bottom bar
 * is not a sheet.**
 *
 * ## ⚡ How one element is in flow at ≥1024 and off-canvas below it
 *
 * 📁 **CSS owns the POSITION and JavaScript owns the SEMANTICS**, and the split
 * is what keeps the first paint correct:
 *
 * | | |
 * |---|---|
 * | **≥1024** | `smalllaptop:` puts the container back in flow. **Unchanged behaviour** |
 * | **<1024, closed** | `fixed`, translated off the left edge **and `invisible`** — ⛔ `visibility:hidden` is what takes it out of the tab order and the accessibility tree, which `translate` alone does not |
 * | **<1024, open** | Slid in over a backdrop, closed by Escape, the backdrop, or following a link |
 *
 * ⛔ **The server cannot know the viewport**, so the band is never used to
 * decide whether the rail EXISTS — only what it means. ✅ **The markup is
 * correct at both bands before JavaScript runs**, and there is exactly one
 * `nav[aria-label="Primary"]` at every width.
 *
 * ⚡ **The band itself is reused, not remeasured** — 📁 {@link useRailCollapse}
 * already resolves `deviceClassFor(window.innerWidth)` against the design's
 * 1024, because collapse is remembered per device class. **A second listener
 * would be a second answer to *which band is this*** ([§2](../../../CLAUDE.md)).
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
  roleKnown,
  signOut,
  email,
  userId = null,
  banners = [],
  inSandbox = false,
  breadcrumb = [],
  name,
}: AppShellProps) {
  // 📁 **Rule: the rail collapses to 56px and the state is remembered.**
  // ⛔ The shell owns the frame's own state; it still owns no navigation
  // decision ([D-193](../../../docs/DECISION_REGISTER.md)).
  const rail = useRailCollapse(userId);

  const pathname = usePathname();

  /**
   * 📁 **The sheet's open state** — [TASK-1461](../../../docs/BACKLOG.md).
   *
   * ⛔ **Held here rather than in the rail or the top bar**, because the two
   * doors are in different subtrees: **the trigger is in the top bar and the
   * surface is the rail**, and the frame is the only thing that contains both.
   * ⚡ **The same shape [`ShortcutsReference`](shortcuts-reference.tsx) already
   * draws for its own two doors.**
   */
  const [navOpen, setNavOpen] = useState(false);
  // 📁 **§16 tier three.** ⚡ **Read at the shell because the bar is under the
  // top bar and the dim is over the whole content region** — both are frame
  // decisions, and neither is any single module's to make.
  const refreshing = useIsRefreshing();
  const compact = rail.device === 'compact';
  const closeNav = useCallback(() => setNavOpen(false), []);

  /**
   * ⛔ **Following a link must close the sheet.** ⚠️ **A sheet is over the
   * content**, so leaving it open after navigation lands somebody on a screen
   * they cannot see — and on a phone that reads as the link not working.
   *
   * ⚡ **And it closes when the viewport grows past 1024**: the rail returns to
   * flow there, and an `open` flag left set would put it back over the content
   * the moment somebody narrowed the window again.
   */
  useEffect(() => setNavOpen(false), [pathname, compact]);

  /**
   * 📁 *"Escape closes the topmost layer."* ⛔ **Bound only while the sheet is
   * open**, so it never competes with a dialog's own Escape — the sheet cannot
   * be open underneath one, because opening it closes on navigation and the
   * trigger is in the top bar.
   */
  useEffect(() => {
    if (!navOpen) return;
    const onKey = (event: KeyboardEvent) => {
      if (event.key === 'Escape') setNavOpen(false);
    };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [navOpen]);

  return (
    /* 📁 **[TASK-1445](../../../docs/BACKLOG.md) — *"`?` opens the reference
       from anywhere."*** ⚡ **Mounted at the shell for the literal reason the
       design gives**: *anywhere* is a property of the shell, and a reference
       owned by one screen is reachable from one screen.

       ⚠️ **It WRAPS rather than sits beside, from [TASK-1458](../../../docs/BACKLOG.md)**:
       📁 the design gives the rail's `Shortcuts` entry `meta: '?'`, so the rail
       is a second door onto the SAME overlay — ⛔ **and a sibling could not be
       opened by the rail without a second copy of the surface.** */
    /* 📁 **The vertical order is fixed and non-negotiable**: banners, then the
       top bar, then everything else. ⚡ **The banner region sits ABOVE the
       frame's columns** because it spans them — a banner inside the content
       column would leave the rail beside a warning that does not apply to it. */
    /* 📁 **§13's dock, wrapping the whole frame** —
       [TASK-1433](../../../docs/BACKLOG.md). ⚡ **Outside `<SkipLinks />`
       deliberately**: the skip link to the panel exists only when the panel
       does, and both read `useUtilityPanelPresent` so they cannot disagree.
       ⛔ **The module segment is the FIRST path segment, not the route** —
       📁 *"remembers its open state per module"*, and a per-ROUTE memory would
       forget the moment somebody opened a different account. */
    <UtilityPanelProvider userId={userId ?? null} module={moduleOf(pathname)}>
    <ShortcutsReference>
    {/* 🔴 **The assistant's state lifts to a provider** —
        [TASK-1470](../../../docs/BACKLOG.md). 📁 §12 is *"four doors, one
        room"*, and the rail is one of them — ⛔ **so the rail's entry and the
        keyboard both open the SAME drawer.** ⚡ **The same shape
        `ShortcutsReference` already uses**, and for the same reason: a second
        `useState` would be a second answer to *is it open*. */}
    <Copilot>
    <div className="relative flex min-h-screen flex-col">
      {/* 📁 **Rule 2.4.1**, and first in the DOM because a skip link somebody
          has already tabbed past is not a skip link. */}
      <SkipLinks />

      {/* 📁 **Rule 4.1.3** — a client-side route change is silent otherwise. */}
      <RouteAnnouncer />

      {/* 📁 **`header[banner]`** — *"environment and trial banners, then the
          top bar. First in the DOM, first in tab order."*
          ⚠️ **The design asks for ONE header holding both, and this shell
          cannot express it**: the rail is full-height, so the banner strip
          spans the frame while the top bar sits inside the content column
          beside it. ⛔ **A second `<header>` here produced TWO `banner`
          landmarks, which is worse than the gap** — a screen-reader user
          choosing "banner" would get a menu of two. ✅ **So the top bar keeps
          the landmark and this stays a plain region**; the structural question
          is [C-278](../../../docs/LANE_COORDINATION.md)'s. */}
      <ShellBanners banners={banners} inSandbox={inSandbox} />

      <div className="flex min-h-0 flex-1">
      {/* 🔴 **A `<div>`, not an `<aside>`** — [B-234](../../../docs/BUGS.md).
          📁 **The design's landmark table gives the rail exactly one role**:
          *"`nav[navigation]` — the rail, labelled 'Primary'"* — **and reserves
          `aside[complementary]` for the UTILITY PANEL.** ⛔ **An `<aside>` here
          is a second, unnamed `complementary` landmark wrapping a `<nav>` that
          already carries the right one**, and the moment
          [TASK-1433](../../../docs/BACKLOG.md) mounted the panel the page had
          TWO — the same defect [TASK-1444](../../../docs/BACKLOG.md) found
          with `banner`, where a screen-reader user choosing a landmark gets a
          menu of two and neither says which is which. */}
      <div
        // ⛔ **The width is the design's, from `RAIL_WIDTH`, not a literal** —
        // 232px expanded and 56px collapsed.
        //
        // ⚡ **A sheet is never collapsed** — 📁 the band gives the rail
        // `railW: 0` and then shows it whole; **56px of icons sliding over the
        // content is neither the rail nor the sheet.** ⛔ **`compact` is false
        // on the server**, so this is the expanded width at first paint either
        // way and the collapsed rail still settles from its stored preference.
        style={{ width: !compact && rail.collapsed ? RAIL_WIDTH.collapsed : RAIL_WIDTH.expanded }}
        data-collapsed={rail.collapsed}
        data-sheet-open={compact && navOpen ? 'true' : undefined}
        className={cn(
          'shrink-0 border-r border-border bg-surface',
          // 🔴 **A COLUMN, and this is a defect the sheet exposed rather than
          // introduced** — measured at 390×844: 📁 the rail's `<nav>` is
          // `h-full`, so it took the container's whole 844px **while starting
          // 106px down, below the wordmark row and the workspace switcher.**
          // ⛔ **Its pinned utilities therefore sat at y=872 — 28px below the
          // fold — and `Shortcuts` could not be clicked.** ⚡ **At ≥1024 the
          // same 106px of overflow existed and the page could scroll it away;
          // a `fixed` sheet has nowhere to scroll to**, which is why a latent
          // defect became a reachability one.
          'flex flex-col overflow-hidden',
          // 📁 **Below 1024 — the sheet.** ⛔ `fixed`, so it is out of flow and
          // the content keeps the full width the band's `railW: 0` promises.
          'fixed inset-y-0 left-0 z-40 transition-transform duration-200 motion-reduce:transition-none',
          navOpen ? 'translate-x-0' : '-translate-x-full invisible',
          // 📁 **At and above 1024 — the rail, exactly as it was.** ⚡ `visible`
          // and `static` are what undo the two lines above; **the element is the
          // same one, in a different place.**
          'smalllaptop:visible smalllaptop:static smalllaptop:z-auto smalllaptop:translate-x-0',
          'smalllaptop:transition-[width] smalllaptop:duration-150',
        )}
      >
        <div className="flex h-topbar items-center justify-between gap-2 px-5">
          {/* ⚡ The wordmark goes when the rail does — 56px cannot hold it,
              and a clipped wordmark reads as a rendering fault. */}
          {!compact && rail.collapsed ? null : (
            <span className="text-sm font-semibold tracking-tight">Signora</span>
          )}
          {/* ⛔ **A sheet closes; it does not collapse.** ⚠️ **Collapsing an
              overlay to 56px leaves it covering the content in a narrower
              strip**, which is not a state the design has — so below 1024 the
              same corner carries the only action that makes sense there.
              ⚡ **The sheet needs a control of its own regardless**: Escape and
              the backdrop are not discoverable, and a pointer user who opened
              it must be able to close it the way they opened it. */}
          {compact ? (
            <button
              type="button"
              onClick={closeNav}
              aria-label="Close navigation"
              className="rounded p-1 text-content-subtle transition-colors hover:text-content focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent"
            >
              ✕
            </button>
          ) : (
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
          )}
        </div>
        {/* 📁 **The rail's FIRST CHILD** — [TASK-1441](../../../docs/BACKLOG.md),
            *"placement at the top of the rail matches the mental model:
            everything below belongs to it."* ⚡ **Its own boundary**: a failing
            switcher must not take the navigation with it, which is the rule
            every other region here already follows. */}
        <RegionBoundary subject="your organizations">
          <WorkspaceSwitcher collapsed={rail.collapsed} />
        </RegionBoundary>
        {/* ⚡ **The flex child that gives `Navigation`'s `h-full` something
            finite to be full OF.** ⛔ [`RegionBoundary`](../ui/region-boundary.tsx)
            **is `components/ui` and takes no `className`** — 🔴 widening it for
            one caller is what [§20c](../../../CLAUDE.md) forbids — **so the
            sizing is a wrapper here rather than a prop there.** */}
        <div className="flex min-h-0 flex-1 flex-col">
          <RegionBoundary subject="the navigation">
            {/* ⚡ **The rail is told it is collapsed rather than measuring it** —
                TASK-1439. The frame owns the collapse state (`useRailCollapse`);
                a second reader would be a second answer to the same question. */}
            <Navigation role={role} roleKnown={roleKnown} collapsed={!compact && rail.collapsed} />
          </RegionBoundary>
        </div>
      </div>

      {/* ⚡ **The backdrop, and it exists only while the sheet is open.**
          ⛔ **Not `smalllaptop:hidden` on an always-mounted node**: a
          transparent overlay that is merely invisible still swallows clicks on
          the screen behind it, which is the defect class this whole row is
          about. 📁 `aria-hidden` because the sheet already has a close control
          and Escape — **a screen-reader user is not helped by an unlabelled
          region they can focus.** */}
      {compact && navOpen ? (
        <div
          onClick={closeNav}
          aria-hidden
          className="fixed inset-0 z-30 bg-content/30 smalllaptop:hidden"
        />
      ) : null}

      <div className="flex min-w-0 flex-1 flex-col">
        {/* 📁 **The top bar is now the design's slot set** —
            [TASK-1440](../../../docs/BACKLOG.md). ⛔ **The frame no longer
            arranges controls; it hands the bar what the bar needs and the slot
            order is `TopBar`'s.** ⚡ **The theme toggle and `Sign out` left this
            file for the account menu**, which is where the design puts both. */}
        <TopBar
          breadcrumb={breadcrumb}
          role={role}
          email={email}
          name={name}
          signOut={signOut}
          // 📁 **[TASK-1461](../../../docs/BACKLOG.md)** — *"Rail becomes a
          // sheet from a top-bar button."* ⛔ **The button had never existed**,
          // so below 1024 the rail's own entries were unreachable and a bottom
          // bar carried seven of them instead.
          onOpenNavigation={() => setNavOpen(true)}
          navigationOpen={navOpen}
        />

        {/* 🔴 **§16's third loading tier** — [TASK-1463](../../../docs/BACKLOG.md).
            📁 *"In-place refreshes show a 2px bar under the top bar and dim
            stale figures to 60%; they never cover data that is already
            readable."*

            ⛔ **Under the top bar, in flow, and 2px** — 📁 *"No overlay, no
            spinner, no layout shift."* ⚡ **The strip occupies its 2px whether
            or not a refresh is running**, so the content below never moves; the
            bar inside it is what appears. **A conditionally rendered 2px node
            would shift every screen by two pixels on every refetch**, which is
            the one thing the design rules out by name. */}
        <div className="h-[2px] shrink-0 overflow-hidden bg-surface-sunken">
          {refreshing ? (
            <div
              role="progressbar"
              aria-label="Refreshing"
              data-testid="refresh-bar"
              className={cn(
                'h-full w-1/3 bg-accent',
                'animate-pulse motion-reduce:animate-none',
              )}
            />
          ) : null}
        </div>

        {/* The main region is the one place a failure is acceptable to
            isolate: the frame around it stays usable.

            ✅ **`pb-20 smalllaptop:pb-6` is GONE with the bar that required it**
            — [TASK-1461](../../../docs/BACKLOG.md). ⛔ **It reserved 80px at the
            foot of every screen below 1024 for a fixed bottom navigation**, and
            📁 [B-180](../../../docs/BUGS.md) measured that padding covering the
            bar exactly. **Nothing is fixed over the content now**, so the
            reservation is not a smaller number — **it is no longer a thing that
            exists.** */}
        {/* 📁 **`main`** — *"the content region. Receives focus on route change
            and announces the new page title."* ⚡ `tabIndex={-1}` is what makes
            it a focus target without putting it in the tab order. */}
        <main
          id={SKIP_TARGETS.content}
          tabIndex={-1}
          // 🔴 **The padding moved into [`Container`](../ui/container.tsx)** —
          // [TASK-1460](../../../docs/BACKLOG.md). ⛔ **`flex-1` with NO maximum
          // was this repository's measured root cause for eleven screens
          // inventing their own width**: content ran edge to edge on a wide
          // monitor, so every screen constrained itself instead. ⚡ **`min-w-0`
          // stays and is right** — it is what lets a wide table shrink rather
          // than push the rail off the frame.
          // 🔴 **§16's other half** — 📁 *"dim stale figures to 60% … existing
          // figures stay readable at 60% until replaced."* ⛔ **`opacity`
          // rather than a colour or an overlay**: it costs no layout, it dims
          // the figures rather than covering them, and **the text underneath is
          // still selectable and still read by a screen reader** — which is
          // what *"never cover data that is already readable"* asks for.
          data-refreshing={refreshing ? 'true' : undefined}
          className={cn(
            'min-w-0 flex-1 outline-none',
            'transition-opacity duration-150 motion-reduce:transition-none',
            refreshing && 'opacity-60',
          )}
        >
          {/* 📁 *"12-column grid, 24px gutters, 1600px content maximum"* —
              Design System v2's `inherited` block. ⚡ **The shell is the ONE
              consumer this slice gives it**, deliberately: 📁
              [455 §4](../../../docs/architecture/455-context-definitions-r02-r03.md)
              — *"a port with seven simultaneous first callers has no chance of
              being corrected cheaply."* ⛔ **The eleven ad-hoc widths are NOT
              migrated here**; the list is on the row and the migration is its
              own slice. */}
          <Container>
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
          </Container>
        </main>
      </div>

      {/* 📁 **§13's dock — the THIRD column, and the design's own word is
          *"pushes content"***. ⛔ **In flow beside the content, never over it**:
          a panel that covered the table would make somebody close it to read
          what it describes. ⚡ **Rendered here rather than by the provider**,
          because a panel that pushes has to be a sibling of what it pushes. */}
      <UtilityPanelDock />
      </div>

      {/* 📁 **The command palette** — [TASK-1442](../../../docs/BACKLOG.md),
          resolving [C-259](../../../docs/LANE_COORDINATION.md). ⛔ **It was
          complete, tested, and mounted by nothing**, while `⌘K` opened account
          search instead. ⚡ **Mounted at the shell because it must reach
          destinations no single module knows** — which is exactly why C-259
          found that neither candidate row could mount it alone. */}
      <ShellPalette role={role} />
      {/* ⚡ **[TASK-482](../../../docs/BACKLOG.md) — §12's assistant entry.**
          ⛔ **Mounted beside the palette rather than floating over the content**:
          📁 the design refuses a corner bubble by name, *"a persistent circle
          in the corner is a consumer pattern and it covers data."* */}
      {/* ✅ **The phone's bottom navigation used to be mounted here and is
          deleted** — [TASK-1461](../../../docs/BACKLOG.md). ⛔ **It was a second
          `nav[aria-label="Primary"]`, mounted at EVERY width and hidden by CSS
          at most of them.** ⚡ **The rail above is now the only navigation there
          is**, at every band, and it keeps the boundary this node had. */}
    </div>
    </Copilot>
    </ShortcutsReference>
    </UtilityPanelProvider>
  );
}

/**
 * ⚡ **Which module a route belongs to**, for the panel's per-module memory.
 *
 * 📁 ***"Remembers its open state per module."*** ⛔ **The first path segment,
 * never the whole route**: `/accounts/abc` and `/accounts/def` are the same
 * module, and a per-route key would make somebody re-open the panel on every
 * record they looked at — **which is the opposite of remembering.**
 */
function moduleOf(pathname: string | null): string {
  const first = (pathname ?? '/').split('/').filter((part) => part !== '')[0];
  return first ?? 'home';
}
