import type { ComponentType, ReactNode } from 'react';

import { cn } from '@/lib/design/cn';

export interface EmptyStateProps {
  /** A lucide-react icon, or any component taking `className`. */
  icon?: ComponentType<{ className?: string }>;
  title: string;
  /** What the user can do about it. Required, because an empty state that
   * only reports emptiness leaves the user with no next step. */
  description: string;
  action?: ReactNode;
  className?: string;
}

/**
 * A first-class, permanent UX element — not a placeholder.
 *
 * Every screen in this product spends its first minutes empty for every
 * new customer, and some stay empty for accounts with no signal. An empty
 * state designed at the end is an apology; designed now, it is the
 * onboarding path.
 *
 * `title` and `description` are separate required props rather than one
 * blob, so "No data" cannot be the whole of it.
 */
export function EmptyState({
  icon: Icon,
  title,
  description,
  action,
  className,
}: EmptyStateProps) {
  return (
    <div
      className={cn(
        'flex flex-col items-center justify-center gap-3 rounded-lg',
        'border border-dashed border-border-strong bg-surface px-6 py-12 text-center',
        className,
      )}
    >
      {Icon ? <Icon className="h-8 w-8 text-content-subtle" /> : null}
      <div className="flex flex-col gap-1">
        <p className="text-sm font-semibold text-content">{title}</p>
        <p className="mx-auto max-w-sm text-sm text-content-muted">{description}</p>
      </div>
      {action ? <div className="mt-1">{action}</div> : null}
    </div>
  );
}
