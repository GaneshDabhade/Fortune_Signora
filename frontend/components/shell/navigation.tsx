'use client';

import { Building2, Home, LineChart, Lightbulb, Settings, Clock } from 'lucide-react';
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
  icon: typeof Home;
  /** Sections whose pages arrive with the modules that produce their data.
   * Listed now so the shell's information architecture is settled before
   * pages are written into it, rather than growing one link at a time. */
  comingSoon?: boolean;
}

const ITEMS: readonly NavItem[] = [
  { href: '/', label: 'Overview', icon: Home },
  { href: '/companies', label: 'Companies', icon: Building2, comingSoon: true },
  { href: '/opportunities', label: 'Opportunities', icon: LineChart },
  { href: '/signals', label: 'Signals', icon: Lightbulb, comingSoon: true },
  { href: '/timeline', label: 'Timeline', icon: Clock, comingSoon: true },
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
            {item.comingSoon ? (
              <span className="text-xs text-content-subtle">Soon</span>
            ) : null}
          </Link>
        );
      })}
    </nav>
  );
}
