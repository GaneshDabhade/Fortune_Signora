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
