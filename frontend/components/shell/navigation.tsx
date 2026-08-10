'use client';

import { BookOpen, Briefcase, LineChart, Lock, Radio, Settings as SettingsIcon } from 'lucide-react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { useState } from 'react';

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

interface RailItem extends RailDestination {
  href: string;
  icon: typeof SettingsIcon;
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
  { id: 'attention', label: 'Attention', href: '/', icon: LineChart, depth: 1 },
  { id: 'business', label: 'Your business', href: '/business', icon: Briefcase, depth: 1 },
  // 📁 *"Counts are neutral; a dot means unread and only Signals uses it."*
  // ⛔ **No count is passed** — nothing publishes one, and a rail that invents
  // a number is worse than a rail without one.
  { id: 'signals', label: 'Signals', href: '/signals', icon: Radio, depth: 1 },
];

/**
 * 📁 **The pinned utility group** — *"Utilities and the assistant pin to the
 * bottom above the fold"*, and *"utilities at the bottom keep the funnel order
 * uninterrupted at the top."*
 *
 * 📁 **The design names three: Settings, Shortcuts, Docs & support.**
 * ✅ **Two have a route now** — [TASK-1420](../../../docs/BACKLOG.md) built
 * `/help`, which is the destination [C-269](../../../docs/LANE_COORDINATION.md)
 * recorded as missing. ⛔ **`Shortcuts` still has none and stays absent rather
 * than rendered as a dead end.**
 */
const UTILITIES: readonly RailItem[] = [
  { id: 'settings', label: 'Settings', href: '/settings', icon: SettingsIcon, depth: 1 },
  // ✅ **`Docs & support` gains its route** — [TASK-1420](../../../docs/BACKLOG.md).
  // ⛔ **It was absent for the reason [C-269](../../../docs/LANE_COORDINATION.md)
  // gave: no help, docs or support route existed.** ⚡ **The route exists now, so
  // the entry does** — and `reachability` refuses a route with no entrance, which
  // is how this arrived rather than being remembered.
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
export const RAIL_DESTINATIONS = [...DESTINATIONS, ...UTILITIES];

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

  const shape = cn(
    // 📁 *"Item 32px tall, 8px radius, 10px icon-to-label gap."* ⛔ The values
    // are the design's; `gap-2.5` is 10px and `rounded-md` is the 8px token.
    'flex h-8 items-center gap-2.5 rounded-md px-2.5 text-sm transition-colors',
    // 📁 *"Second level indents to 30px and never nests further."*
    item.depth === 2 && !collapsed && 'pl-[30px]',
    collapsed && 'justify-center px-0',
    // 📁 *"Focus: 1px brand border plus a 3px tint halo — never the browser
    // ring."* ⛔ `outline-none` alone would be an accessibility defect; this
    // replaces the ring rather than removing it.
    'focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-accent',
    'focus-visible:ring-offset-[3px] focus-visible:ring-offset-accent-subtle',
  );

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
  return (
    <nav aria-label="Main" className="flex h-full flex-col gap-0.5 p-3">
      {visibleDestinations(DESTINATIONS).map((item) => (
        <RailLink key={item.id} item={item as RailItem} role={role} collapsed={collapsed} />
      ))}

      {/* 📁 *"Utilities and the assistant pin to the bottom above the fold."*
          ⚡ The spacer is what pins them, and it is why the rail is a flex
          column: a margin would put them below the fold on a short viewport. */}
      <div className="flex-1" />

      <div className="flex flex-col gap-0.5 border-t border-border pt-2">
        {visibleDestinations(UTILITIES).map((item) => (
          <RailLink key={item.id} item={item as RailItem} role={role} collapsed={collapsed} />
        ))}
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

  return (
    <nav
      aria-label="Main"
      className={cn(
        'fixed inset-x-0 bottom-0 z-10 flex border-t border-border bg-surface md:hidden',
        // The safe area on a phone with a home indicator.
        'pb-[env(safe-area-inset-bottom)]',
      )}
    >
      {RAIL_DESTINATIONS.map((item) => {
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
