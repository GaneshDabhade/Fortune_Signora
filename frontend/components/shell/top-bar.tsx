'use client';

import { HelpCircle, Menu } from 'lucide-react';
import Link from 'next/link';
import { useEffect, useState, type ReactNode } from 'react';

import { AccountSearch } from '@/components/intelligence/account-search';
import { AccountMenu } from '@/components/shell/account-menu';
import { Notifications } from '@/components/shell/notifications';
import { Breadcrumb, OfflineStatus } from '@/components/ui';
import { RegionBoundary } from '@/components/ui/region-boundary';
import { cn } from '@/lib/design/cn';
import type { Crumb } from '@/lib/shell/breadcrumb';
import { bandFor } from '@/lib/shell/rail';
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
  /**
   * 🔴 **[B-429](../../../docs/BUGS.md)** — 📁 §11: *"Always states name,
   * email, role and workspace."* ⛔ **Passed through rather than derived**:
   * the top bar states nothing about a person it was not told.
   */
  name: string | null;
  signOut: ReactNode;
  /**
   * 📁 **The `<1024` sheet trigger** — [TASK-1461](../../../docs/BACKLOG.md),
   * App Shell `breakpoints`: *"Rail becomes a sheet from a top-bar button."*
   *
   * ⛔ **The bar does not own the sheet's state and must not**: the trigger is
   * here and the surface is the rail, so 📁 [`app-shell.tsx`](app-shell.tsx) —
   * the only thing containing both — holds it and passes both halves down.
   *
   * ⚡ **Optional, so every existing test and story that renders the bar alone
   * keeps working** — ⛔ and **the button is omitted rather than rendered dead**
   * when nothing is passed, on the rule [`navigation.tsx`](navigation.tsx)'s
   * `RailAction` already follows.
   */
  onOpenNavigation?: () => void;
  navigationOpen?: boolean;
}

export function TopBar({
  breadcrumb,
  role,
  email,
  name,
  signOut,
  onOpenNavigation,
  navigationOpen = false,
}: TopBarProps) {
  /**
   * 🔴 **§07: *"Search … widens to 320px on focus at ≥1600px."*** ⚡ **Two
   * conditions, and both are needed** — 📁 the design widens the field only on
   * the band that has room for it, **so a laptop focusing the search must NOT
   * grow** and take 96px from the breadcrumb beside it.
   *
   * ⚠️ **`focus` and `blur` rather than `:focus-within`** — ⛔ **the width comes
   * from [`SEARCH_WIDTH`](../../lib/shell/top-bar.ts) and a CSS pseudo-class
   * cannot read it.** ✅ **The alternative was two Tailwind arbitrary values
   * restating `224` and `320` in the markup**, which is exactly what the
   * contract exists to prevent and what this row was told not to do.
   */
  const [searchFocused, setSearchFocused] = useState(false);
  /**
   * ⚡ **Reused, never re-derived** — 📁 [`bandFor`](../../lib/shell/rail.ts) is
   * the repository's single answer to *which band is this*, and
   * `SEARCH_WIDTH.focusWidensAbove` is the design's own threshold rather than a
   * literal typed here. ⛔ **A second boundary would be a second answer**
   * ([§2](../../../CLAUDE.md)).
   *
   * ⚠️ **Starts at the reference band and corrects on mount.** **The server
   * cannot know the viewport**, so the first paint is the design's reference
   * layout — never a guess that a customer sees jump.
   */
  const [viewportWidth, setViewportWidth] = useState<number>(SEARCH_WIDTH.focusWidensAbove);
  useEffect(() => {
    const measure = () => setViewportWidth(window.innerWidth);
    measure();
    window.addEventListener('resize', measure);
    return () => window.removeEventListener('resize', measure);
  }, []);

  const widened = searchFocused && bandFor(viewportWidth) === 'desktop';

  return (
    <header className="flex h-topbar shrink-0 items-center gap-2 border-b border-border-soft bg-surface px-4">
      {/* 📁 **The sheet trigger** — [TASK-1461](../../../docs/BACKLOG.md).
          ⛔ **Not a slot, on the wordmark's own precedent below**: 📁
          [`lib/shell/top-bar.ts`](../../lib/shell/top-bar.ts)'s union is the
          design's ANATOMY — *"no module may add anything to the top bar"* — and
          this control belongs to the `<1024` BAND rather than to that table.
          ✅ **So `TOP_BAR_SLOTS` stays closed and is not widened for one
          viewport**, which is the change the closed union exists to refuse.

          ⚡ **First in the bar, before the wordmark**: it is the only way to
          reach navigation at this width, and a control that IS the navigation
          cannot sit after the identity. */}
      {onOpenNavigation === undefined ? null : (
        <button
          type="button"
          onClick={onOpenNavigation}
          aria-label="Open navigation"
          aria-expanded={navigationOpen}
          aria-haspopup="dialog"
          className={cn(
            'flex h-8 w-8 shrink-0 items-center justify-center rounded-md text-content-subtle',
            'transition-colors hover:bg-surface-sunken hover:text-content',
            'focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2',
            'focus-visible:outline-accent',
            // ⛔ **The rail is in flow at and above 1024**, so the trigger is
            // not merely redundant there — it would open a sheet over a rail
            // that is already visible.
            'smalllaptop:hidden',
          )}
        >
          <Menu className="h-4 w-4" aria-hidden />
        </button>
      )}

      {/* **The wordmark lives in the rail, which does not exist on a phone.**
          Shown here below `md` so the product is still named on the one
          viewport where the frame is otherwise anonymous. ⛔ Not a slot — the
          design's five begin after it, and above `md` it is absent. */}
      <span className="shrink-0 text-sm font-semibold tracking-tight smalllaptop:hidden">Signora</span>

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
      {/* 📁 **`search` landmark, labelled "Search Signora"** —
          [TASK-1444](../../../docs/BACKLOG.md), App Shell `landmarks`. ⛔ **The
          slot published no landmark at all**, so a screen-reader user could not
          jump to search the way they can jump to navigation.

          ⚠️ **`Signora`, not `Fortune Signora`** — [TASK-1466](../../../docs/BACKLOG.md),
          on the product owner's ruling at [C-1422](../../../docs/LANE_COORDINATION.md):
          ***"the application is already inside Signora; the newer brand rule
          explicitly says the in-product product name is `Signora`; the
          finalized design copy is therefore superseded for this specific
          wording."*** 📁 **App Shell §21 `landmarks` still reads *"Search
          Fortune Signora"*, and it is NOT edited** — ⛔ [D-138](../../../docs/DECISION_REGISTER.md):
          **a snapshot is refreshed, never edited**, and the discrepancy is
          recorded on C-1422 for the next refresh. */}
      {/* 🔴 **§07's focus rule, which the contract has always held and nothing
          called** — [TASK-1474](../../../docs/BACKLOG.md). 📁 *"Search — opens
          the palette on click or ⌘K. **Widens to 320px on focus at ≥1600px**."*

          ⚡ **Both numbers and the threshold come from `SEARCH_WIDTH`** — ⛔ **not
          restated here**, which is the whole reason the contract exists and the
          row's explicit instruction. ⚠️ **`transition-[width]` and not
          `transition-all`**: only the width may animate, so a focus ring
          appears at once rather than fading in behind the growth. */}
      <div
        data-slot="search"
        role="search"
        aria-label="Search Signora"
        data-widened={widened ? 'true' : undefined}
        onFocus={() => setSearchFocused(true)}
        onBlur={() => setSearchFocused(false)}
        style={{
          width: widened ? SEARCH_WIDTH.focused : SEARCH_WIDTH.rest,
          height: SLOT_SPEC.search.height,
        }}
        className="hidden shrink-0 transition-[width] duration-150 motion-reduce:transition-none phone:block"
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
          ✅ **BUILT** — [TASK-495](../../../docs/BACKLOG.md) slice ⓑ. 📁 *"32 × 32.
          Count badge caps at 99+. Opens a 400px panel, not a page."*

          ⚠️ **The comment that stood here said the absence was deliberate**, and
          it was right at the time: 📁 [C-275](../../../docs/LANE_COORDINATION.md),
          *"a bell that opens an empty 400px panel is the defect
          [TASK-1433](../../../docs/BACKLOG.md) was parked for"*, and it recorded
          the measurement — **no notification endpoint, no feed, no unread count
          anywhere in `lib/api`.**

          ⚡ **All three exist now.** Slice ⓐ shipped the feed, the badge and the
          read state; `ai_research_engine` publishes into it when a research run
          finishes. ⛔ **The panel had something to show before it got a bell**,
          which is the order C-275 asked for. */}
      <Notifications />

      {/* ── Slot 5 · Help & account ────────────────────────────────────────
          📁 *"32 + 32. Help before account, always last."*

          ✅ **BOTH HALVES NOW.** ⛔ **Help was absent because it had no
          destination** — 📁 [C-275](../../../docs/LANE_COORDINATION.md), *"a
          design with nothing built behind it"*. ⚡ **[TASK-1420](../../../docs/BACKLOG.md)
          built `/help`**, so the control has somewhere to go and the slot is
          complete in the design's order: **help before account, always last.** */}
      <Link
        href="/help"
        data-slot="help"
        aria-label="Help and support"
        title="Help & support"
        style={{ width: SLOT_SPEC.help.width, height: SLOT_SPEC.help.height }}
        className={cn(
          'flex shrink-0 items-center justify-center rounded-md text-content-subtle',
          'transition-colors hover:bg-surface-sunken hover:text-content',
          'focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2',
          'focus-visible:outline-accent',
        )}
      >
        <HelpCircle className="h-4 w-4" aria-hidden />
      </Link>

      <div data-slot="account" className="shrink-0">
        <AccountMenu email={email} name={name} role={role} signOut={signOut} />
      </div>
    </header>
  );
}
