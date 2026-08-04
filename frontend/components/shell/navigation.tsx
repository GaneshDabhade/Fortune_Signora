'use client';

import { Briefcase, LineChart, Settings } from 'lucide-react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';

import { cn } from '@/lib/design/cn';
import {
  can,
  guardFor,
  type Capability,
  type WorkspaceRole,
} from '@/lib/state/permissions';

interface NavItem {
  href: string;
  label: string;
  icon: typeof Settings;
}

/**
 * **Two entries, reviewed from first principles at M12.3** (D38).
 *
 * It was six: Overview, Companies, Signals, Timeline, Opportunities, Settings
 * — four of the thirteen pipeline modules with a menu item each, which is a
 * data model rendered as navigation. That was defensible at M1.5, when the
 * point was to settle the information architecture *before* pages were written
 * into it. The pages have since been written and they disagree with it.
 *
 * **None of the six customer journeys is *show me all the signals* or *show me
 * all the companies*.** A signal is what explains an account; a company is what
 * an account is. Both are already on the brief, because that is where they
 * answer something. Timeline is journey J6 and is explicitly *per-account* —
 * when M7 ships it belongs beside the workflow history on the brief, not here.
 *
 * And an entry that leads nowhere advertises absence: three of six said
 * *coming soon* on the screen a customer sees first.
 *
 * `Attention` rather than `Opportunities` because *Opportunity* is Signora's
 * own word for **the workflow object a human commits to**, and most rows on
 * this list are not that yet. *Attention* is the domain's word too — the score
 * measures commercial attention, the ledger splits it by posture, the query is
 * `attention_list` — so the vocabulary is now the same from the database to
 * the sidebar.
 *
 * ---
 *
 * ### Three entries from CX-05, and the third had to earn it
 *
 * **D38 reduced this to two on purpose, so adding one back is a claim that
 * needs defending.** *Your business* earns it on a fact that was not measured
 * until 2026-08-03: **a `member` saw a sidebar with one item in it.** `Settings`
 * is guarded and correctly not rendered for them, so of the two entries, a
 * salesperson — the person Signora is built for — saw one. **A navigation of
 * one is not navigation; it is a label.**
 *
 * **It is the only door, not a second one.** Every test D38 applied still
 * holds: this is not a pipeline module with a menu item, it is not *show me all
 * the X*, and it does not lead to a *coming soon*. `/settings/products` remains
 * the authoring screen for owners; **for a member there is no other route to
 * five declarations `policy.csv` explicitly grants them** ([C-008](../../../docs/LANE_COORDINATION.md)).
 *
 * **Unguarded, deliberately.** `guardFor` is a deny-list, so leaving `/business`
 * out of `GUARDED_ROUTES` is what makes it member-reachable — the property that
 * chose option C over option A and kept `permissions.ts` untouched (§20c).
 */
const ITEMS: readonly NavItem[] = [
  { href: '/', label: 'Attention', icon: LineChart },
  { href: '/business', label: 'Your business', icon: Briefcase },
  { href: '/settings', label: 'Settings', icon: Settings },
];

export function Navigation({ role }: { role: WorkspaceRole | null }) {
  const pathname = usePathname();

  return (
    <nav aria-label="Main" className="flex flex-col gap-0.5 p-3">
      {ITEMS.map((item) => {
        const guard = guardFor(item.href);
        // A link the caller cannot follow is not rendered. Rendering it
        // disabled would advertise a capability they do not have; the
        // server enforces the same rule regardless.
        if (guard && !can(role, guard.requires as Capability)) return null;

        const isActive = pathname === item.href;
        const Icon = item.icon;

        return (
          <Link
            key={item.href}
            href={item.href}
            aria-current={isActive ? 'page' : undefined}
            className={cn(
              'flex items-center gap-2.5 rounded px-3 py-2 text-sm transition-colors',
              isActive
                ? 'bg-accent-subtle font-medium text-accent'
                : 'text-content-muted hover:bg-surface-sunken hover:text-content',
            )}
          >
            <Icon className="h-4 w-4 shrink-0" />
            <span className="flex-1">{item.label}</span>
          </Link>
        );
      })}
    </nav>
  );
}

/**
 * The same navigation, on a phone. **CX-07 · [B-203](../../../docs/BUGS.md).**
 *
 * **Below `768px` the product had no navigation at all.** `app-shell.tsx` hides
 * the sidebar and nothing replaced it, so a signed-in customer on a phone could
 * reach the screen they landed on and nothing else. That was 🟠 and
 * *undecided* — *"whether it is a defect or a non-goal depends on a product
 * decision nobody has made"* — until [C-205](../../../docs/LANE_COORDINATION.md)
 * was ruled on 2026-08-03: **a phone is in scope.** It is now a defect, and
 * §20c names this exact class — *an unreachable control* — as one the frozen
 * foundation is changed for.
 *
 * ### A bar, not a drawer
 *
 * **Three entries do not earn a drawer.** A drawer buys room for many
 * destinations and costs open/close state, a focus trap, an escape handler, a
 * scrim, and one tap before a customer can go anywhere. **Signora has two or
 * three destinations** (D38, and CX-05's third), so the room is worth nothing
 * and the cost is real.
 *
 * **A bar is one tap, always visible, and holds no state that can be wrong.**
 * It also sits where a thumb already is, which the sidebar's position never
 * could.
 *
 * ### It reads `ITEMS`, and that is the point
 *
 * **One list, two renderings.** A second array would be a second answer to
 * *what can this person reach*, and the two would diverge the first time an
 * entry was added to one — which is exactly what CX-05 just did to the
 * sidebar. The guard is applied identically, so **a control the server would
 * refuse is absent here too** rather than absent in one place and offered in
 * the other.
 */
export function MobileNavigation({ role }: { role: WorkspaceRole | null }) {
  const pathname = usePathname();

  return (
    <nav
      aria-label="Main"
      // **Fixed to the bottom, and only below `md`.** Above it the sidebar is
      // the navigation and a second one would be a second answer.
      className={cn(
        'fixed inset-x-0 bottom-0 z-10 flex border-t border-border bg-surface md:hidden',
        // The safe area on a phone with a home indicator. Without it the last
        // few pixels of the bar sit under the system gesture strip.
        'pb-[env(safe-area-inset-bottom)]',
      )}
    >
      {ITEMS.map((item) => {
        const guard = guardFor(item.href);
        if (guard && !can(role, guard.requires as Capability)) return null;

        const isActive = pathname === item.href;
        const Icon = item.icon;

        return (
          <Link
            key={item.href}
            href={item.href}
            aria-current={isActive ? 'page' : undefined}
            className={cn(
              // **`min-h-11` is the touch target**, not decoration: a control
              // smaller than roughly 44px is one a thumb misses, and missing a
              // navigation control is how a customer decides the product does
              // not work on their phone.
              'flex min-h-11 flex-1 flex-col items-center justify-center gap-1 py-2 text-xs',
              'transition-colors',
              'focus-visible:outline focus-visible:outline-2 focus-visible:-outline-offset-2',
              'focus-visible:outline-accent',
              isActive ? 'font-medium text-accent' : 'text-content-muted',
            )}
          >
            <Icon className="h-5 w-5 shrink-0" aria-hidden />
            {/* **The label stays.** An icon-only bar asks a first-time customer
                to guess what a briefcase means, and *Your business* is not a
                word an icon carries. */}
            <span className="max-w-full truncate px-1">{item.label}</span>
          </Link>
        );
      })}
    </nav>
  );
}
