'use client';

import type { ReactNode } from 'react';

import { AccountSearch } from '@/components/intelligence/account-search';
import { AccountMenu } from '@/components/shell/account-menu';
import { Breadcrumb, OfflineStatus } from '@/components/ui';
import { RegionBoundary } from '@/components/ui/region-boundary';
import type { Crumb } from '@/lib/shell/breadcrumb';
import { SEARCH_WIDTH, SLOT_SPEC } from '@/lib/shell/top-bar';
import type { WorkspaceRole } from '@/lib/state/permissions';

/**
 * **The top bar** — [TASK-1440](../../../docs/BACKLOG.md), against 📁
 * `docs/design-snapshot/screens/Fortune Signora App Shell.dc.html`
 * ([D-138](../../../docs/DECISION_REGISTER.md)).
 *
 * ## ⚡ The law already existed. This is only the surface
 *
 * ⛔ **No rule is decided in this file.** 📁 [`lib/shell/top-bar.ts`](../../lib/shell/top-bar.ts)
 * — shipped by [TASK-1408](../../../docs/BACKLOG.md) and covered by seven tests
 * — **already carries the closed slot union, each slot's geometry,
 * `statusLabelVisible`'s asymmetry and `badgeLabel`'s cap.** ⚡ **This component
 * reads it and adds nothing**, which is the same relationship
 * `lib/shell/scope.ts` has to the filter strip.
 *
 * ## 🔴 All six of that file's exports had ZERO production callers, and this row fixes three
 *
 * ⚠️ **Measured on 2026-08-10 before this file existed, not assumed** —
 * `TOP_BAR_SLOTS` · `SLOT_SPEC` · `SEARCH_WIDTH` · `statusLabelVisible` ·
 * `BADGE_CAP` · `badgeLabel`, **all zero.** ⚡ **The slot law had been shipped,
 * tested and never consulted by the bar it governs.**
 *
 * ✅ **This row gives `SLOT_SPEC` and `SEARCH_WIDTH` their first callers.**
 * ⛔ **`statusLabelVisible`, `badgeLabel` and `BADGE_CAP` still have none, and
 * that is reported rather than papered over**: their slots have no data source
 * — see slots 3 and 4 below. **A caller invented to satisfy a count would be
 * the [§2](../../../CLAUDE.md) defect this very measurement exists to find.**
 *
 * ⚠️ **This is the sixth instance of the pattern**: 📁 the entry engine, the
 * narrowing law, the command palette, `confidence.tsx`, `drawer.tsx`, and this
 * slot set — **each built, tested, and left without a surface**
 * ([500](../../../docs/architecture/500-authenticated-entry-reconciliation.md) §9).
 * ⛔ **The law shipping first is not the defect; the surface never arriving is.**
 *
 * ## 📁 What was in the frame before, and where each control went
 *
 * | Was in the top bar | Now |
 * |---|---|
 * | Breadcrumb | ✅ **Slot 1, unchanged** — it was already right |
 * | Account search | ✅ **Inside slot 2's geometry** — see the slot's own note |
 * | `OfflineStatus` | ✅ **Slot 3**, now honouring `statusLabelVisible` |
 * | Theme toggle | ✅ **Moved into the account menu** — 📁 the design has no top-bar theme control, and its account menu has a three-way one |
 * | `Sign out` | ✅ **Moved into the account menu**, 📁 *"below a hairline"* |
 * | Workspace selector | ✅ **GONE — it is the rail's first child now** ([TASK-1441](../../../docs/BACKLOG.md)) |
 *
 * ## ✅ The workspace switcher has LEFT, and [C-274](../../../docs/LANE_COORDINATION.md) closes with it
 *
 * ⛔ **[TASK-1440](../../../docs/BACKLOG.md) said it should leave and this
 * component kept it**, because 📁 [TASK-1441](../../../docs/BACKLOG.md) — where
 * the design puts it, the rail's first child — **was blocked, and removing a
 * control whose destination does not exist deletes it rather than moving it.**
 *
 * ✅ **[D-225](../../../docs/DECISION_REGISTER.md) §4 ruled that reasoning**:
 * *"do not remove currently valid, reachable navigation that is required for an
 * existing user role."* ⚡ **The rail was rebuilt, [TASK-1441](../../../docs/BACKLOG.md)
 * freed, and the switcher moved.** **The bar is the design's five slots now.**
 */
export interface TopBarProps {
  breadcrumb: readonly Crumb[];
  role: WorkspaceRole | null;
  email: string;
  signOut: ReactNode;
}

export function TopBar({ breadcrumb, role, email, signOut }: TopBarProps) {
  return (
    <header className="flex h-topbar shrink-0 items-center gap-2 border-b border-border bg-surface px-4">
      {/* **The wordmark lives in the rail, which does not exist on a phone.**
          Shown here below `md` so the product is still named on the one
          viewport where the frame is otherwise anonymous. ⛔ Not a slot — the
          design's five begin after it, and above `md` it is absent. */}
      <span className="shrink-0 text-sm font-semibold tracking-tight md:hidden">Signora</span>

      {/* ── Slot 1 · Breadcrumb ────────────────────────────────────────────
          📁 *"flex, min 0. Truncates from the middle. Never wraps. Always
          present below level one."* ✅ **Already correct before this row**, so
          it is placed and not rewritten — 📁 [D-217](../../../docs/DECISION_REGISTER.md)
          §6 cuts both ways, and existing code being right IS an argument for
          keeping it. */}
      <div className="flex min-w-0 flex-1 items-center" data-slot="breadcrumb">
        <Breadcrumb trail={breadcrumb} />
      </div>

      {/* ── Slot 2 · Search ────────────────────────────────────────────────
          📁 *"224 × 32. Opens the palette on click or ⌘K. Widens to 320px on
          focus at ≥1600px."*

          ⛔ **The slot is this row's; its OCCUPANT is not.** 📁
          [C-259](../../../docs/LANE_COORDINATION.md) closed on exactly this
          question and ruled that **[TASK-1442](../../../docs/BACKLOG.md) mounts
          the palette and account search becomes one group inside it.** ⚡ So
          this row gives the search the design's geometry and position, and
          leaves the working control in it until the row that replaces the
          occupant runs.

          ✅ **`AccountSearch` is not decoration** — it finds accounts today,
          which is why it stays rather than being swapped for a palette opener
          that would open nothing. */}
      <div
        data-slot="search"
        style={{ width: SEARCH_WIDTH.rest, height: SLOT_SPEC.search.height }}
        className="hidden shrink-0 sm:block"
      >
        <RegionBoundary subject="account search">
          <AccountSearch />
        </RegionBoundary>
      </div>

      {/* ── Slot 3 · System status ─────────────────────────────────────────
          📁 *"auto × 32. Green pill hides its label at <1280px; amber and red
          always show it."*

          ⚠️ **`OfflineStatus` fills this slot and does NOT call
          `statusLabelVisible`** — ✅ **read, not assumed.** ⛔ **And it is
          correct not to**: the helper's whole content is what the GREEN tone
          does, and `OfflineStatus` never renders a green tone. 📁 Its own note:
          *"online with an empty queue renders `null` — not a green 'Online'
          pill… a pill whose only content is everything is fine is chrome that
          costs a slot every screen inherits."*

          🔴 **So the design's healthy pill is genuinely absent, and nothing
          publishes the state it would show.** 📁 The design lists five
          subsystems — Application, CRM sync, Scoring service, Conversation
          ingest, Exports — ✅ **and none of them is published by any module.**
          ⛔ **Raised as [C-275](../../../docs/LANE_COORDINATION.md) with slot 4;
          `statusLabelVisible` stays uncalled until there is a source, rather
          than gaining a caller that invents one.** */}
      <div data-slot="system-status" className="shrink-0">
        <OfflineStatus />
      </div>

      {/* ── Slot 4 · Notifications ─────────────────────────────────────────
          ⛔ **NOT BUILT, and the absence is deliberate.** 📁 The design wants
          *"a 400px popover… grouped by day… unread is a 6px dot"* and a badge
          that *"caps at 99+"*. ⚡ `badgeLabel` already implements the cap.

          🔴 **Nothing in the platform publishes a notification.** ✅ Measured:
          no notification endpoint, no event feed, no unread count anywhere in
          `lib/api`. **A bell that opens an empty 400px panel is the defect
          [TASK-1433](../../../docs/BACKLOG.md) was parked for** — *"an empty
          panel does not reserve space for a future feature, it takes space from
          the one the customer is using today."*

          ⛔ **Raised as [C-275](../../../docs/LANE_COORDINATION.md).** An empty
          slot is left rather than a placeholder rendered. */}

      {/* ── Slot 5 · Help & account ────────────────────────────────────────
          📁 *"32 + 32. Help before account, always last."*

          ⛔ **Help is ABSENT because it has no destination.** ✅ Measured
          against the route tree: there is no help, docs or support route, and
          📁 `Fortune Signora Help Center.dc.html` is a design with nothing
          built behind it. ⚡ **A help control that goes nowhere is
          [C-269](../../../docs/LANE_COORDINATION.md)'s finding in miniature**,
          and it gets the same answer.

          ✅ **Account is built.** */}
      <div data-slot="account" className="shrink-0">
        <AccountMenu email={email} role={role} signOut={signOut} />
      </div>
    </header>
  );
}
