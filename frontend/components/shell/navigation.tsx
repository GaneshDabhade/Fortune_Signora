'use client';

import {
  BarChart3,
  BookOpen,
  Briefcase,
  Building2,
  Home,
  // 📁 The design's `navIcon('key')` for `Shortcuts`.
  KeyRound,
  LineChart,
  Lock,
  Radio,
  Settings as SettingsIcon,
  // 📁 The design's assistant glyph, and the same one `Copilot` already uses.
  Sparkles,
} from 'lucide-react';
import Link from 'next/link';

import { useCopilot } from '@/components/shell/copilot';
import { useShortcutsReference } from '@/components/shell/shortcuts-reference';
import { usePathname } from 'next/navigation';
import { useState } from 'react';

import { SKIP_TARGETS } from '@/components/shell/skip-links';
import { workspaceHome } from '@/lib/entry';
import { useWorkspaceContext } from '@/lib/state/workspace-provider';
import { Tooltip } from '@/components/ui';
import { cn } from '@/lib/design/cn';
import { railViolations, visibleDestinations, type RailDestination } from '@/lib/shell/rail';
import {
  can,
  guardFor,
  type Capability,
  type WorkspaceRole,
} from '@/lib/state/permissions';

/**
 * **The navigation rail** — [TASK-1439](../../../docs/BACKLOG.md), rebuilt
 * against 📁 `docs/design-snapshot/screens/Fortune Signora App Shell.dc.html`
 * ([D-138](../../../docs/DECISION_REGISTER.md), [D-225](../../../docs/DECISION_REGISTER.md)).
 *
 * ## ⚡ What was rebuilt, and what was kept — [D-225](../../../docs/DECISION_REGISTER.md) drew the line
 *
 * 📁 **§1 released the row for everything the design specifies**: *hierarchy,
 * levels, labels, icons, active state, count slot, pinned utility group,
 * structure, responsive and collapse behaviour.* ✅ **All of that is the
 * design's now and none of it was before.**
 *
 * 🔴 **§4 is the clause that decides the ENTRY SET, and it is a ruling rather
 * than a preference**: ⛔ ***"Do not remove currently valid, reachable
 * navigation that is required for an existing user role."***
 *
 * ⚡ **So `/` and `/business` stay**, though the design's `navItems` names
 * neither — 📁 **nine of the design's thirteen entries have no route at all**
 * ([C-269](../../../docs/LANE_COORDINATION.md), and
 * [500](../../../docs/architecture/500-authenticated-entry-reconciliation.md) §3
 * measured the same absence from the other side: **eighteen of the entry
 * engine's twenty-four destinations return `404`**). ⛔ **Building the
 * design's list literally would remove two working destinations and add nine
 * that do not resolve** — and this file already paid that price once: ⚠️ **at
 * M12.3, *three of six said `coming soon` on the screen a customer sees
 * first.***
 *
 * ✅ **The reconciliation is therefore structural, not editorial: the design's
 * RAIL, holding the entries that exist.** **Home, Forecast, Pipeline, Deals,
 * Conversations, Reports, Accounts and the two sub-entries arrive as their
 * routes do** — 📁 [TASK-1438](../../../docs/BACKLOG.md) builds the first of
 * them — **and each is one line here.**
 *
 * ## 🔴 The law existed and nothing used it. Six exports, zero callers
 *
 * ⚠️ **Measured 2026-08-10 before this rebuild**: 📁 [`lib/shell/rail.ts`](../../lib/shell/rail.ts)
 * exports `MAX_DESTINATIONS`, `MAX_DEPTH`, `TAB_ORDER`, `RailDestination`,
 * `railViolations` and `visibleDestinations` — **all six with no production
 * caller.** ⛔ **The rail's rules were written, tested and never consulted by
 * the rail.**
 *
 * ⚡ **This is the seventh instance of one pattern** — the entry engine, the
 * narrowing law, the top-bar slot set, the command palette, `confidence.tsx`,
 * `drawer.tsx`, and this. ✅ **This file now consumes it**, which is the only
 * thing that turns a law into a rule.
 *
 * ## 🔴 A restricted destination is now VISIBLE, and that reverses this file's own rule
 *
 * ⛔ **This component used to remove what a member could not reach**, and said
 * so: *"a link the caller cannot follow is not rendered. Rendering it disabled
 * would advertise a capability they do not have."*
 *
 * 📁 **The design refuses that, and [`rail.ts`](../../lib/shell/rail.ts) rule ①
 * already carried the reasoning this file was contradicting**: *"Restricted
 * destinations stay visible at 45% with a lock and explain on click… a hidden
 * destination teaches a person the feature does not exist, so they ask for the
 * wrong thing or ask nobody."*
 *
 * ⚡ **[D-154](../../../docs/DECISION_REGISTER.md) settles which wins**:
 * *"if an existing visual implementation differs from the finalized design,
 * the design wins. Always."* ⚠️ **And the old rule was not wrong in general** —
 * it is right for a BUTTON, which promises an action. **A rail is a map, and a
 * map that hides the rooms you may not enter is a map you cannot trust.**
 *
 * 🔴 **Presentational, never enforcement** ([§20c](../../../CLAUDE.md)):
 * **Casbin on the server is the authorization decision and is unchanged.**
 * Dimming an item is a courtesy; the server refuses the request either way.
 */

interface RailEntryBase extends RailDestination {
  icon: typeof SettingsIcon;
  /**
   * 📁 **The design's right-aligned meta glyph** — `railUtility` gives
   * `Shortcuts` `meta: '?'` and the other two an empty string.
   */
  meta?: string;
}

/** ⚡ An entry that goes somewhere. */
interface RailItem extends RailEntryBase {
  href: string;
}

/**
 * ⚡ **An entry that opens something instead of going somewhere** —
 * [TASK-1458](../../../docs/BACKLOG.md).
 *
 * 🔴 **`Shortcuts` is the first, and it is why this type exists.** 📁 The design
 * gives it `meta: '?'` — ⛔ **which says it is the thing the `?` key opens, not
 * a destination.** ⚠️ **A `/shortcuts` route beside the overlay would be two
 * representations of one truth** ([§2](../../../CLAUDE.md)) and they would
 * diverge the first time somebody edited one.
 */
interface RailAction extends RailEntryBase {
  opens: 'shortcuts' | 'assistant';
}

/**
 * 🔴 **An entry that WILL go somewhere, once the workspace is known** —
 * [TASK-1471](../../../docs/BACKLOG.md), §16 tier one.
 *
 * ⛔ **A third member rather than an optional `href` on {@link RailItem}**, for
 * the reason the union header already gives: **an optional href makes a dead
 * entry ordinary code that happens to be wrong.** ⚡ **A pending entry is a
 * different THING from a broken one** — it holds the frame's shape while the
 * workspace read is in flight — **and the type says which it is.**
 *
 * ⚠️ **It exists for exactly one entry today**, `Home`, because it is the only
 * destination whose path carries a `[workspace]` segment. **If a second gains
 * one, it gets this behaviour for free.**
 */
interface RailPending extends RailEntryBase {
  pending: true;
}

/**
 * ⛔ **A union, so a rail entry with NEITHER a route nor an action cannot be
 * written.** 📁 [§2](../../../CLAUDE.md): *"prefer a violation that is
 * unrepresentable over one that is merely discouraged."* ⚡ **The alternative —
 * an optional `href` — makes the dead entry ordinary code that happens to be
 * wrong**, which is exactly the shape [C-269](../../../docs/LANE_COORDINATION.md)
 * refuses.
 */
type RailEntry = RailItem | RailAction | RailPending;

function goesSomewhere(entry: RailEntry): entry is RailItem {
  return 'href' in entry;
}

/** ⚡ **Present in the frame, not yet a destination** — §16 tier one. */
function isPendingEntry(entry: RailEntry): entry is RailPending {
  return 'pending' in entry;
}

/**
 * 📁 **The destinations, in the design's funnel order**, holding the entries
 * that resolve.
 *
 * ⛔ **`depth` and `count` are the design's slots, not decoration** — a second
 * level indents to 30px and never nests further, and `railViolations` refuses
 * a tenth destination or a third level at test time.
 */
const DESTINATIONS: readonly RailItem[] = [
  // ✅ **`Home` gains its route** — [TASK-1438](../../../docs/BACKLOG.md).
  // ⛔ **It was the first entry the design draws and the rail could not carry
  // it**, because `/w/:workspace/home` did not exist and
  // [C-269](../../../docs/LANE_COORDINATION.md) refuses an entry that leads
  // nowhere.
  //
  // ⚡ **Declared as the ROUTE names itself, and resolved at render.** 📁
  // `infra/reachability.py` reads static route strings, and its `href:`
  // property pattern matches quoted strings ONLY — **a backtick template here
  // would be invisible to it**, and a route entered only through a helper call
  // reads as having no entrance at all. ⛔ **The check would have been right to
  // fail: it cannot verify what it cannot see.**
  { id: 'home', label: 'Home', href: '/w/[workspace]/home', icon: Home, depth: 1 },
  { id: 'attention', label: 'Attention', href: '/', icon: LineChart, depth: 1 },
  { id: 'business', label: 'Your business', href: '/business', icon: Briefcase, depth: 1 },
  // 📁 *"Counts are neutral; a dot means unread and only Signals uses it."*
  // ⛔ **No count is passed** — nothing publishes one, and a rail that invents
  // a number is worse than a rail without one.
  { id: 'signals', label: 'Signals', href: '/signals', icon: Radio, depth: 1 },
  // ✅ **`Reports` gains its route** — [TASK-1417](../../../docs/BACKLOG.md).
  //
  // ⚠️ **This lane first decided NOT to add the line**, reasoning from the
  // warning above: *"at M12.3, three of six said `coming soon` on the screen a
  // customer sees first."* 🔴 **`reachability.py` refused that** — *"no
  // entrance at all: 1 ← every one is a defect"* — **and it was right.**
  //
  // ⚡ **The distinction the caution missed**: ⛔ **`coming soon` is a screen
  // that does not exist yet.** ✅ **This one resolves, states in the customer's
  // words what a report needs and why Signora cannot answer it today, and
  // names the eight charts it will draw.** **A route a customer cannot reach
  // is a route that does not exist**, which is the worse of the two.
  // ✅ **`Accounts` gains its route** — [TASK-440](../../../docs/BACKLOG.md),
  // and this is the line [C-229](../../../docs/LANE_COORDINATION.md) was
  // waiting for.
  //
  // 🔴 **The entrance question is CLOSED, not assumed.** ⛔ [D38](../../../docs/architecture/39-product-review-findings.md)
  // removed *Companies* from navigation by name — *"a company is what an
  // account is"* — **and the finalized design puts it back**: 📁 the App
  // Shell's rail reads `Home · Forecast · Pipeline · Accounts (8,412) · Deals
  // · Conversations · Signals (14) · Reports`. ⚡ **`8,412` is the exact row
  // count [TASK-440](../../../docs/BACKLOG.md) cites**, so this is the same
  // screen and not a coincidence. 📁 [D-141](../../../docs/DECISION_REGISTER.md) ①
  // closed the item on that evidence, and [D-128](../../../docs/DECISION_REGISTER.md)
  // makes the finalized design the authority over historical UI.
  //
  // ⚠️ **D38 is superseded on navigation and NOT deleted** — it remains an
  // accurate record of a decision taken on 2026-08-02 ([§2](../../../CLAUDE.md)).
  //
  // ⛔ **No count is passed**, for the reason every other entry here gives:
  // nothing publishes one, and the design's `8,412` is a mockup's number.
  { id: 'accounts', label: 'Accounts', href: '/accounts', icon: Building2, depth: 1 },
  { id: 'reports', label: 'Reports', href: '/reports', icon: BarChart3, depth: 1 },
];

/**
 * 📁 **The pinned utility group** — *"Utilities and the assistant pin to the
 * bottom above the fold"*, and *"utilities at the bottom keep the funnel order
 * uninterrupted at the top."*
 *
 * 📁 **The design names three: Settings, Shortcuts, Docs & support.**
 * ✅ **All three are here now** — [TASK-1458](../../../docs/BACKLOG.md).
 *
 * ⚡ **`Shortcuts` was absent for a good reason and the reason expired.** 📁 This
 * comment used to read *"`Shortcuts` still has none and stays absent rather than
 * rendered as a dead end"*, and [C-269](../../../docs/LANE_COORDINATION.md) is
 * why. ⛔ **[TASK-1445](../../../docs/BACKLOG.md) built the surface**, so the
 * entry has somewhere to go — ✅ **and it arrives because the destination now
 * exists, not because anybody grew tired of the gap.**
 */
const UTILITIES: readonly RailEntry[] = [
  /**
   * 🔴 **FIRST in the pinned group, above the utilities** —
   * [TASK-1470](../../../docs/BACKLOG.md).
   *
   * 📁 **The design's rail puts `Ask Signora` immediately after the divider and
   * BEFORE `railUtility`**, in the intelligence tint. ⛔ **It sat below them**,
   * mounted outside the rail entirely — **which is ordering, not absence, and
   * is why a test that only checks it exists passes against the defect.**
   *
   * ⚠️ **`meta` is the shortcut this product actually binds.** 📁 The design's
   * rail row shows `⌘K`, **which is the PALETTE's key** — §15's shortcut table
   * gives the assistant `⌘⇧A`, and [TASK-1458](../../../docs/BACKLOG.md) built
   * it. ⛔ **Printing `⌘K` here would teach a key that opens something else.**
   */
  { id: 'assistant', label: 'Ask Signora', opens: 'assistant', meta: '⌘⇧A', icon: Sparkles, depth: 1 },
  { id: 'settings', label: 'Settings', href: '/settings', icon: SettingsIcon, depth: 1 },
  // ✅ **`Docs & support` gains its route** — [TASK-1420](../../../docs/BACKLOG.md).
  // ⛔ **It was absent for the reason [C-269](../../../docs/LANE_COORDINATION.md)
  // gave: no help, docs or support route existed.** ⚡ **The route exists now, so
  // the entry does** — and `reachability` refuses a route with no entrance, which
  // is how this arrived rather than being remembered.
  // ✅ **`Shortcuts`** — [TASK-1458](../../../docs/BACKLOG.md).
  // ⛔ **It OPENS rather than navigates**, which is what `meta: '?'` means in
  // the design: it is the thing the `?` key opens, reached a second way.
  { id: 'shortcuts', label: 'Shortcuts', opens: 'shortcuts', meta: '?', icon: KeyRound, depth: 1 },
  { id: 'help', label: 'Docs & support', href: '/help', icon: BookOpen, depth: 1 },
];

/** ⚡ Which role can grant a capability, so the lock explains rather than refuses. */
const GRANTED_BY: Readonly<Record<Capability, string>> = {
  'workspace:read': 'any member',
  'workspace:update': 'an owner',
  'member:add': 'an owner',
  'member:remove': 'an owner',
};

/**
 * ⚡ **Exported so the suite asserts the rail's own law against the real list**
 * rather than against a fixture — 📁 `railViolations` is the check and this is
 * what it checks.
 */
/**
 * ⚡ **Every rail entry that GOES somewhere** — read by the command palette's
 * *Navigate* group and by the phone bar.
 *
 * ⛔ **Links only, and both consumers need that for the same reason**: each
 * renders an anchor, and 📁 [TASK-1458](../../../docs/BACKLOG.md) added an entry
 * that opens an overlay instead. ⚠️ **An action leaking in here would arrive as
 * a nav item with no destination** — the defect the `RailEntry` union exists to
 * prevent, one consumer over.
 *
 * 🔴 **So `Shortcuts` is unreachable below 1024px** — 📁
 * [B-240](../../../docs/BUGS.md), **filed against this slice.**
 *
 * ⚠️ **This comment first justified that as a decision** — *"a keyboard
 * reference on a device with no keyboard cannot help anybody"* — ⛔ **and the
 * design does not support it.** 📁 The App Shell's `< 1024px` band reads *"rail
 * becomes a sheet from a top-bar button"*: **the whole rail, utilities
 * included.** ⛔ **The design nowhere says this entry is desktop-only**, and
 * writing a plausible reason for an accident is how a side effect becomes a
 * decision nobody took.
 *
 * ⚡ **The real cause is structural and it predates this row**: the phone
 * surface is a fixed bottom bar ([B-203](../../../docs/BUGS.md)), not the
 * design's sheet, **and a bottom bar renders anchors** — so an entry that opens
 * an overlay has nowhere to live in it. ✅ **The filter is right for what that
 * surface is; the surface is what disagrees with the design.**
 */
export const RAIL_DESTINATIONS = [...DESTINATIONS, ...UTILITIES.filter(goesSomewhere)];

/**
 * 🔴 **`[workspace]` filled from the active workspace, for EVERY renderer** —
 * [B-233](../../../docs/BUGS.md).
 *
 * ⛔ **An entry whose segment cannot be filled is DROPPED, not linked
 * half-built**: `/w/[workspace]/home` as a literal href is a `404` with a
 * plausible shape, and 📁 `workspaceHome` in
 * [`lib/entry/rules.ts`](../../lib/entry/rules.ts) is the authority for the
 * shape.
 *
 * ⚠️ **This was a function inside `Navigation` and the phone bar never
 * called it**, so the phone bar rendered the literal — **and a dynamic href in
 * a `<Link>` THROWS in the App Router**, taking the whole navigation region
 * down with it. 🔴 **At every width**, because the phone bar is hidden by CSS
 * and still mounted.
 *
 * ⚡ **This file already claimed *"one source, two renderings"* and meant the
 * LIST.** ✅ **The resolution is now shared too**, which is what that sentence
 * had to mean for it to be true.
 *
 * ⚠️ **The two renderings are gone** — [TASK-1461](../../../docs/BACKLOG.md)
 * deleted the second. ✅ **This function stays**, because the reason it exists
 * is that a `[workspace]` literal must never reach a `<Link>`, **and that is
 * true of one renderer as much as of two.**
 */
export function resolved(
  items: readonly RailItem[],
  workspaceId: string | null,
  workspaceKnown = true,
): readonly RailEntry[] {
  return items.flatMap<RailEntry>((item) => {
    if (!item.href.includes('[workspace]')) return [item];
    if (workspaceId !== null) return [{ ...item, href: workspaceHome(workspaceId) }];
    /**
     * 🔴 **§16 tier one, and [TASK-1471](../../../docs/BACKLOG.md)'s whole
     * finding** — 📁 *"Cold boot paints the shell chrome immediately and
     * skeletons only the content region — **the frame is never blank, because
     * the frame is the same on every route**."*
     *
     * ⛔ **`workspaceId === null` meant two opposite things and both dropped the
     * entry**: *this person has no organization* and *the list has not arrived
     * yet.* ⚡ **Home is the rail's FIRST destination**, so on every cold boot
     * the rail rendered without it and **everything below shifted down when the
     * read landed** — measured 6 → 7 → 8 links across one page load.
     *
     * ✅ **The distinction already exists one level up**: `authenticated-shell`
     * computes `workspaceKnown` for exactly this reason, and 📁
     * [B-306](../../../docs/BUGS.md) is the row that established it — *"`resolved`
     * alone conflates a workspace that is absent with one that has not
     * arrived."* **This is that lesson, one component along.**
     *
     * ⛔ **Pending renders the entry without a destination rather than with a
     * false one.** ⚠️ **A `[workspace]` literal in a `<Link>` THROWS in the App
     * Router** ([B-233](../../../docs/BUGS.md)) and a link to `/` would be a
     * different screen wearing Home's label — **so the row holds its place and
     * says it is not ready yet.**
     */
    if (workspaceKnown) return [];
    // ⚡ **The `href` is dropped rather than emptied** — 📁 the union refuses an
    // entry with a route it cannot honour, which is the whole reason
    // {@link RailPending} is a third member instead of an optional field.
    const { href, ...withoutRoute } = item;
    void href;
    return [{ ...withoutRoute, pending: true }];
  });
}

/**
 * ⚡ **The geometry every rail entry shares**, extracted on its second caller —
 * [TASK-1458](../../../docs/BACKLOG.md)'s action button.
 *
 * ⛔ **Extracted rather than copied.** 📁 The values are the design's, and two
 * copies would let the rail's link and its action drift apart by one padding
 * token — **a difference nobody would call a bug and everybody would see.**
 */
function railShape(depth: number, collapsed: boolean): string {
  return cn(
    // 📁 *"Item 32px tall, 8px radius, 10px icon-to-label gap."* ⛔ The values
    // are the design's; `gap-2.5` is 10px and `rounded-md` is the 8px token.
    'flex h-8 items-center gap-2.5 rounded-md px-2.5 text-sm transition-colors',
    // 📁 *"Second level indents to 30px and never nests further."*
    depth === 2 && !collapsed && 'pl-[30px]',
    collapsed && 'justify-center px-0',
    // 📁 *"Focus: 1px brand border plus a 3px tint halo — never the browser
    // ring."* ⛔ `outline-none` alone would be an accessibility defect; this
    // replaces the ring rather than removing it.
    'focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-accent',
    'focus-visible:ring-offset-[3px] focus-visible:ring-offset-accent-subtle',
  );
}

/**
 * ⚡ **A rail entry that opens an overlay** — [TASK-1458](../../../docs/BACKLOG.md).
 *
 * ⛔ **A `<button>`, and the distinction is not cosmetic**: 📁 it goes nowhere,
 * so an anchor would be the *control that lies about itself*
 * [§2](../../../CLAUDE.md) names — **and a screen reader would announce a link
 * that never changes the page.**
 *
 * ♿ **The `?` meta is NOT the only affordance**, which the row requires
 * explicitly: **the entry is a labelled button reachable by Tab**, and the glyph
 * is `aria-hidden` because *"?"* read aloud in the middle of a label is noise.
 *
 * ⛔ **Renders nothing when no provider is above it.** ⚠️ **A rail mounted
 * without the shell — a test, a story — would otherwise show an entry that does
 * nothing**, which is precisely the dead end
 * [C-269](../../../docs/LANE_COORDINATION.md) refuses.
 */
/**
 * 🔴 **A destination that is in the frame and not yet reachable** —
 * [TASK-1471](../../../docs/BACKLOG.md), §16 tier one.
 *
 * 📁 ***"Cold boot paints the shell chrome immediately and skeletons only the
 * content region — the frame is never blank, because the frame is the same on
 * every route."***
 *
 * ⚡ **It holds Home's place, its icon, its label and its exact geometry**, so
 * nothing below it moves when the workspace read lands. ⛔ **It is not a link
 * and not a button**: there is nowhere to go yet, and 📁 [§2](../../../CLAUDE.md)
 * calls a control that does nothing the worse kind — **one a person presses and
 * believes.**
 *
 * ♿ **`aria-busy` says what a sighted reader sees**: this row is resolving, not
 * disabled and not forbidden. ⛔ **`aria-disabled` would be wrong** — nothing
 * about this entry is refused, and a screen-reader user told *disabled* would
 * reasonably stop waiting for it.
 */
function RailPendingRow({ item, collapsed }: { item: RailPending; collapsed: boolean }) {
  const Icon = item.icon;

  return (
    <div
      data-pending="true"
      aria-busy="true"
      aria-label={item.label}
      className={cn(railShape(item.depth, collapsed), 'text-content-subtle')}
    >
      <Icon className="h-4 w-4 shrink-0 text-content-subtle" aria-hidden />
      {collapsed ? null : <span className="min-w-0 flex-1 truncate">{item.label}</span>}
    </div>
  );
}

function RailAction({ item, collapsed }: { item: RailAction; collapsed: boolean }) {
  const reference = useShortcutsReference();
  const copilot = useCopilot();
  const Icon = item.icon;

  /**
   * ⚡ **Both providers are read unconditionally**, because hooks are — ⛔ **and
   * the SELECTION is the branch**, which is what the union's `opens` exists to
   * make total. 📁 [§2](../../../CLAUDE.md): *types should make incorrect
   * architecture impossible* — **a third door gains a third case here and the
   * compiler names the file.**
   */
  const controls = item.opens === 'assistant' ? copilot : reference;

  // ⛔ **No provider means no door**, never a control that silently does
  // nothing — 📁 the rule `Copilot` and `ShortcutsReference` both already keep.
  if (controls === null) return null;

  /**
   * 📁 **The design tints the assistant row and nothing else in the group** —
   * `var(--ai-ink)` on `var(--ai-tint)`. ⚡ **The token, never a literal**
   * ([§20c](../../../CLAUDE.md)).
   */
  const assistant = item.opens === 'assistant';

  return (
    <button
      type="button"
      onClick={controls.open}
      aria-label={item.label}
      aria-haspopup="dialog"
      className={cn(
        railShape(item.depth, collapsed),
        'w-full',
        assistant
          ? 'bg-ai-subtle text-ai hover:bg-ai-subtle/80'
          : 'text-content-muted hover:bg-surface-sunken hover:text-content',
      )}
    >
      <Icon
        className={cn('h-4 w-4 shrink-0', assistant ? 'text-ai' : 'text-content-subtle')}
        aria-hidden
      />
      {collapsed ? null : (
        <>
          <span className="min-w-0 flex-1 truncate text-left">{item.label}</span>
          {/* 📁 **The design's `meta` slot** — `railUtility` gives this entry
              `'?'`. ⛔ **`aria-hidden`**: it is a reminder of the key, and read
              aloud inside the label it is noise rather than information. */}
          {item.meta === undefined ? null : (
            <span aria-hidden className="shrink-0 font-mono text-2xs text-content-subtle">
              {item.meta}
            </span>
          )}
        </>
      )}
    </button>
  );
}

function RailLink({
  roleKnown,
  item,
  role,
  collapsed,
}: {
  item: RailItem;
  role: WorkspaceRole | null;
  /**
   * 🔴 **Whether the role has ARRIVED**, which `role: null` cannot say —
   * [B-253](../../../docs/BUGS.md). ⛔ `null` meant both *has no role* and *has
   * not come back yet*, **and the rail could only read it as the first**.
   */
  roleKnown: boolean;
  collapsed: boolean;
}) {
  const pathname = usePathname();
  const [explaining, setExplaining] = useState(false);

  const guard = guardFor(item.href);
  /**
   * 🔴 **An unresolved role renders an ORDINARY row, never a locked one** —
   * [B-253](../../../docs/BUGS.md), released 2026-08-13, **and the design
   * decides it rather than this lane**:
   *
   * 📁 **App Shell §16 *Cold boot***: *"workspace name and rail appear before
   * data resolves."* ⚡ **So the rail is drawn before the role is known**, and
   * a row that locked meanwhile would be asserting a permission answer nobody
   * had yet.
   *
   * 📁 **Rail States**: *"restricted destinations stay visible at 45% with a
   * lock and explain on click"* — ⛔ **the RESOLVED-DENIED appearance, and the
   * only one that locks.**
   *
   * ⚠️ **What this cost while it was wrong**: an OWNER was told *"Settings —
   * restricted. Requires an owner."* on every cold boot, reproducibly, on the
   * most-looked-at surface in the product. ⛔ **A courtesy that fires on data
   * it does not have is not a courtesy — it is a false claim about
   * entitlement**, and [§20c](../../../CLAUDE.md) already said this check is
   * *"presentational… never enforcement"*, so being briefly generous costs a
   * refusal the server was always going to give.
   */
  const restricted = roleKnown && guard !== undefined && !can(role, guard.requires as Capability);
  const isActive = pathname === item.href;
  const Icon = item.icon;

  const body = (
    <>
      <Icon
        className={cn('h-4 w-4 shrink-0', isActive ? 'text-accent' : 'text-content-subtle')}
        aria-hidden
      />
      {/* ⛔ **Collapsed hides the LABEL, never the accessible name** — 📁
          *"collapsed items expose their label as an accessible name."* The
          `aria-label` on the control carries it either way. */}
      {collapsed ? null : (
        <>
          <span className="min-w-0 flex-1 truncate">{item.label}</span>
          {/* 📁 *"Counts are neutral"* — content colour, never brand or risk. */}
          {item.count !== undefined ? (
            <span className="shrink-0 text-2xs tabular-nums text-content-subtle">
              {item.count.toLocaleString()}
            </span>
          ) : null}
          {/* 📁 *"a dot means unread and only Signals uses it."* `railViolations`
              refuses it anywhere else. */}
          {item.unread ? (
            <span
              className="h-1.5 w-1.5 shrink-0 rounded-full bg-accent"
              aria-label="unread"
            />
          ) : null}
          {restricted ? <Lock className="h-3 w-3 shrink-0" aria-hidden /> : null}
        </>
      )}
    </>
  );

  const shape = railShape(item.depth, collapsed);

  if (restricted) {
    /**
     * 📁 *"Restricted destinations stay visible at 45% with a lock and
     * **explain on click**."* ⛔ **A `<button>`, not a `<Link>`** — the
     * destination is not reachable, and rendering an anchor that refuses to
     * navigate is the *control that does nothing* [§2](../../../CLAUDE.md)
     * names.
     */
    return (
      <div className="relative">
        <button
          type="button"
          onClick={() => setExplaining((was) => !was)}
          aria-expanded={explaining}
          aria-label={`${item.label} — restricted. ${
            guard ? `Requires ${GRANTED_BY[guard.requires as Capability]}.` : ''
          }`}
          // 📁 *"stay visible at 45%"* — the design's own number.
          className={cn(shape, 'w-full opacity-45', 'text-content-muted hover:bg-surface-sunken')}
        >
          {body}
        </button>
        {explaining && !collapsed ? (
          <p
            role="status"
            className="mt-1 rounded-md bg-surface-sunken px-2.5 py-2 text-2xs leading-5 text-content-muted"
          >
            {/* ⛔ **It names who can grant it rather than saying *no*.** 📁 The
                design's reason, in `rail.ts`: a person who is only refused
                *"asks for the wrong thing or asks nobody."* */}
            {item.label} is available to {guard ? GRANTED_BY[guard.requires as Capability] : 'an owner'}.
            Ask someone with that role to open it for you.
          </p>
        ) : null}
      </div>
    );
  }

  const link = (
    <Link
      href={item.href}
      aria-current={isActive ? 'page' : undefined}
      aria-label={collapsed ? item.label : undefined}
      className={cn(
        shape,
        isActive
          ? // 📁 *"Active: brand tint, 600 label, brand icon."*
            'bg-accent-subtle font-semibold text-accent'
          : // 📁 *"Hover: sunken tint."*
            'text-content-muted hover:bg-surface-sunken hover:text-content',
      )}
    >
      {body}
    </Link>
  );

  // 📁 *"Collapsed items expose their label as an accessible name and a 300ms
  // tooltip."* ⚡ **The `title` attribute was the honest thing to ship before
  // [TASK-1448](../../../docs/BACKLOG.md)** — ⛔ **but the browser's delay is
  // its own and varies between engines**, and a rule naming a duration needs
  // something that can hold one. ✅ **The accessible name stays on the link**,
  // so the tooltip describes rather than names.
  return collapsed ? <Tooltip content={item.label}>{link}</Tooltip> : link;
}

/**
 * The rail, on a screen wide enough for it.
 *
 * 📁 *"12px outer / 10px inner padding"*, and the utility group pinned to the
 * bottom — which is why this is a column with a spacer rather than one list.
 */
export function Navigation({
  roleKnown,
  role,
  collapsed = false,
}: {
  role: WorkspaceRole | null;
  /** 🔴 **Threaded rather than collapsed into `role`** — [B-253](../../../docs/BUGS.md). */
  roleKnown: boolean;
  collapsed?: boolean;
}) {
  const { activeWorkspace, workspaces, isLoading } = useWorkspaceContext();
  /**
   * ⚡ **The same question `authenticated-shell` asks, asked once more here** —
   * 📁 *"the question is answered when there is an active organization, or when
   * the list came back and there are none, and it is genuinely open in
   * between."* ⛔ **Not a second answer**: the shell's copy governs whether the
   * CONTENT is guarded, and this one governs whether a DESTINATION exists.
   */
  const workspaceKnown = !isLoading && (activeWorkspace !== null || workspaces.length === 0);
  const destinations = resolved(DESTINATIONS, activeWorkspace?.id ?? null, workspaceKnown);

  return (
    // 📁 **`nav[navigation]`, labelled "Primary"** — TASK-1444. ⛔ It said
    // "Main", which is not the design's word and, more importantly, is the
    // word a screen reader user hears when choosing between landmarks.
    <nav
      id={SKIP_TARGETS.navigation}
      aria-label="Primary"
      className="flex h-full flex-col gap-0.5 p-3"
    >
      {visibleDestinations(destinations).map((item) => {
        const entry = item as RailEntry;
        /* 🔴 **§16 tier one: the frame holds its shape while the workspace read
           is in flight** — [TASK-1471](../../../docs/BACKLOG.md). ⛔ **Not a
           link**, because it has no destination yet and a link to the wrong
           screen is worse than one that waits. */
        return isPendingEntry(entry) ? (
          <RailPendingRow key={entry.id} item={entry} collapsed={collapsed} />
        ) : goesSomewhere(entry) ? (
          <RailLink key={entry.id} item={entry} role={role} roleKnown={roleKnown} collapsed={collapsed} />
        ) : null;
      })}

      {/* 📁 *"Utilities and the assistant pin to the bottom above the fold."*
          ⚡ The spacer is what pins them, and it is why the rail is a flex
          column: a margin would put them below the fold on a short viewport. */}
      <div className="flex-1" />

      <div className="flex flex-col gap-0.5 border-t border-border pt-2">
        {visibleDestinations(UTILITIES).map((item) => {
          const entry = item as RailEntry;
          // ⛔ **The utilities are static and none carries a `[workspace]`
          // segment**, so a pending entry cannot occur here — ⚡ **and the
          // exhaustive branch says so rather than casting it away.**
          if (goesSomewhere(entry)) {
            return <RailLink key={entry.id} item={entry} role={role} roleKnown={roleKnown} collapsed={collapsed} />;
          }
          return isPendingEntry(entry) ? null : (
            <RailAction key={entry.id} item={entry} collapsed={collapsed} />
          );
        })}
      </div>
    </nav>
  );
}

/**
 * ⛔ **The phone's bottom navigation bar is DELETED** —
 * [TASK-1461](../../../docs/BACKLOG.md).
 *
 * 📁 **The design's `< 1024px` band gives the rail `railW: 0` and one
 * sentence** — *"Rail becomes a sheet from a top-bar button"* — **and its
 * landmark table names exactly one `nav[navigation]`: *"the rail, labelled
 * 'Primary'. Workspace switcher is its first child."***
 *
 * 🔴 **A fixed bottom bar is neither.** ⛔ **It was a SECOND `nav[aria-label="Primary"]`
 * mounted at every width** — `display:none` leaves the element in the DOM, so
 * the page carried two Primary landmarks at 390, 1024, 1280 and 1600, and 📁
 * [B-180](../../../docs/BUGS.md) is what that cost: QE's own overlap guard
 * resolved the region with `querySelector`, got the 0×0 one, and **could not
 * fail at any width on any page.**
 *
 * ⚠️ **Scrapped rather than restyled** ([D-229A](../../../docs/DECISION_REGISTER.md)):
 * a bottom bar and a sheet are different structures, and **restyling would
 * have kept two generations alive** — which is the defect the row exists to
 * remove, not a step towards removing it.
 *
 * ✅ **What replaced it is not a second renderer.** 📁 [`app-shell.tsx`](app-shell.tsx)
 * moves the ONE rail between two positions: **in flow at ≥1024, off-canvas
 * below it**, opened by the top bar's trigger. ⚡ **The band is
 * {@link deviceClassFor}'s, already shipped** — no component measures itself,
 * and the count of `nav[aria-label="Primary"]` is one at every width.
 */

/**
 * ⚡ **The rail checks its own law at module load, in development only.**
 *
 * ⛔ **`railViolations` had no caller before this row** — it was a rule nobody
 * ran. **The suite asserts it too**, and this makes a tenth destination or a
 * third level fail the moment somebody adds one rather than at the next test
 * run.
 */
if (process.env.NODE_ENV !== 'production') {
  const problems = railViolations(RAIL_DESTINATIONS);
  if (problems.length > 0) {
    throw new Error(`The rail breaks its own law:\n  ${problems.join('\n  ')}`);
  }
}
