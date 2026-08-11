'use client';

import {
  BarChart3,
  BookOpen,
  Briefcase,
  Home,
  // 📁 The design's `navIcon('key')` for `Shortcuts`.
  KeyRound,
  LineChart,
  Lock,
  Radio,
  Settings as SettingsIcon,
} from 'lucide-react';
import Link from 'next/link';

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
  opens: 'shortcuts';
}

/**
 * ⛔ **A union, so a rail entry with NEITHER a route nor an action cannot be
 * written.** 📁 [§2](../../../CLAUDE.md): *"prefer a violation that is
 * unrepresentable over one that is merely discouraged."* ⚡ **The alternative —
 * an optional `href` — makes the dead entry ordinary code that happens to be
 * wrong**, which is exactly the shape [C-269](../../../docs/LANE_COORDINATION.md)
 * refuses.
 */
type RailEntry = RailItem | RailAction;

function goesSomewhere(entry: RailEntry): entry is RailItem {
  return 'href' in entry;
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
 * 🔴 **So `Shortcuts` is absent from the phone bar, and that is a decision
 * rather than a side effect.** ⛔ **A keyboard-shortcut reference on a device
 * with no keyboard is a control that cannot help anybody**, and the phone bar is
 * the most space-constrained surface in the product — 📁 five slots for what the
 * design gives eleven. ✅ **`?` and the rail entry both remain on every viewport
 * that has a keyboard.**
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
 * ⚠️ **This was a function inside `Navigation` and `MobileNavigation` never
 * called it**, so the phone bar rendered the literal — **and a dynamic href in
 * a `<Link>` THROWS in the App Router**, taking the whole navigation region
 * down with it. 🔴 **At every width**, because the phone bar is hidden by CSS
 * and still mounted.
 *
 * ⚡ **This file already claimed *"one source, two renderings"* and meant the
 * LIST.** ✅ **The resolution is now shared too**, which is what that sentence
 * had to mean for it to be true.
 */
export function resolved(
  items: readonly RailItem[],
  workspaceId: string | null,
): readonly RailItem[] {
  return items.flatMap((item) => {
    if (!item.href.includes('[workspace]')) return [item];
    if (workspaceId === null) return [];
    return [{ ...item, href: workspaceHome(workspaceId) }];
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
function RailAction({ item, collapsed }: { item: RailAction; collapsed: boolean }) {
  const reference = useShortcutsReference();
  const Icon = item.icon;

  if (reference === null) return null;

  return (
    <button
      type="button"
      onClick={reference.open}
      aria-label={item.label}
      aria-haspopup="dialog"
      className={cn(
        railShape(item.depth, collapsed),
        'w-full text-content-muted hover:bg-surface-sunken hover:text-content',
      )}
    >
      <Icon className="h-4 w-4 shrink-0 text-content-subtle" aria-hidden />
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
  item,
  role,
  collapsed,
}: {
  item: RailItem;
  role: WorkspaceRole | null;
  collapsed: boolean;
}) {
  const pathname = usePathname();
  const [explaining, setExplaining] = useState(false);

  const guard = guardFor(item.href);
  const restricted = guard !== undefined && !can(role, guard.requires as Capability);
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
  role,
  collapsed = false,
}: {
  role: WorkspaceRole | null;
  collapsed?: boolean;
}) {
  const { activeWorkspace } = useWorkspaceContext();
  const destinations = resolved(DESTINATIONS, activeWorkspace?.id ?? null);

  return (
    // 📁 **`nav[navigation]`, labelled "Primary"** — TASK-1444. ⛔ It said
    // "Main", which is not the design's word and, more importantly, is the
    // word a screen reader user hears when choosing between landmarks.
    <nav
      id={SKIP_TARGETS.navigation}
      aria-label="Primary"
      className="flex h-full flex-col gap-0.5 p-3"
    >
      {visibleDestinations(destinations).map((item) => (
        <RailLink key={item.id} item={item as RailItem} role={role} collapsed={collapsed} />
      ))}

      {/* 📁 *"Utilities and the assistant pin to the bottom above the fold."*
          ⚡ The spacer is what pins them, and it is why the rail is a flex
          column: a margin would put them below the fold on a short viewport. */}
      <div className="flex-1" />

      <div className="flex flex-col gap-0.5 border-t border-border pt-2">
        {visibleDestinations(UTILITIES).map((item) => {
          const entry = item as RailEntry;
          return goesSomewhere(entry) ? (
            <RailLink key={entry.id} item={entry} role={role} collapsed={collapsed} />
          ) : (
            <RailAction key={entry.id} item={entry} collapsed={collapsed} />
          );
        })}
      </div>
    </nav>
  );
}

/**
 * The same navigation, on a phone. **CX-07 · [B-203](../../../docs/BUGS.md).**
 *
 * ### It reads the same lists, and that is the point
 *
 * **One source, two renderings.** A second array would be a second answer to
 * *what can this person reach*, and the two would diverge the first time an
 * entry was added to one.
 *
 * ⚡ **The utilities are appended rather than pinned** — 📁 a bottom bar has no
 * *bottom* to pin to, and the design's reason for pinning (*"keep the funnel
 * order uninterrupted at the top"*) is satisfied by order alone here.
 *
 * ⛔ **A restricted entry is rendered restricted here too**, not dropped: the
 * rule is the design's, not the desktop's.
 */
export function MobileNavigation({ role }: { role: WorkspaceRole | null }) {
  const pathname = usePathname();
  const { activeWorkspace } = useWorkspaceContext();
  // 🔴 **[B-233](../../../docs/BUGS.md)** — this mapped `RAIL_DESTINATIONS`
  // raw, so `/w/[workspace]/home` reached a `<Link>` as a literal and the
  // App Router threw, blanking the navigation region on every screen.
  const destinations = resolved(RAIL_DESTINATIONS, activeWorkspace?.id ?? null);

  return (
    <nav
      aria-label="Primary"
      className={cn(
        // 📁 **The design's `< 1024px` band** — *"rail becomes a sheet from a
        // top-bar button"*. ⛔ **It was `md:hidden`, Tailwind's 768**, so the
        // rail vanished 256px earlier than the design says and the phone bar
        // appeared on a small laptop that should have had the collapsed rail.
        'fixed inset-x-0 bottom-0 z-10 flex border-t border-border bg-surface smalllaptop:hidden',
        // The safe area on a phone with a home indicator.
        'pb-[env(safe-area-inset-bottom)]',
      )}
    >
      {destinations.map((item) => {
        const guard = guardFor(item.href);
        const restricted = guard !== undefined && !can(role, guard.requires as Capability);
        const isActive = pathname === item.href;
        const Icon = item.icon;

        const content = (
          <>
            <Icon className="h-5 w-5 shrink-0" aria-hidden />
            <span className="max-w-full truncate px-1">{item.label}</span>
          </>
        );

        // **`min-h-11` is the touch target**, not decoration: a control smaller
        // than roughly 44px is one a thumb misses.
        const shape = cn(
          'flex min-h-11 flex-1 flex-col items-center justify-center gap-1 py-2 text-2xs',
          'transition-colors',
          'focus-visible:outline focus-visible:outline-2 focus-visible:-outline-offset-2',
          'focus-visible:outline-accent',
        );

        if (restricted) {
          return (
            <span
              key={item.id}
              className={cn(shape, 'opacity-45 text-content-muted')}
              aria-label={`${item.label} — restricted`}
            >
              {content}
            </span>
          );
        }

        return (
          <Link
            key={item.id}
            href={item.href}
            aria-current={isActive ? 'page' : undefined}
            className={cn(shape, isActive ? 'font-semibold text-accent' : 'text-content-muted')}
          >
            {content}
          </Link>
        );
      })}
    </nav>
  );
}

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
