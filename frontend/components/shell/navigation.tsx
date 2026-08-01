'use client';

import { LineChart, Settings } from 'lucide-react';
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
 */
const ITEMS: readonly NavItem[] = [
  { href: '/', label: 'Attention', icon: LineChart },
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
