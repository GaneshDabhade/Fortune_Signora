import type { HTMLAttributes } from 'react';

import { cn } from '@/lib/design/cn';

/**
 * A loading placeholder occupying the same space as the content it stands
 * in for.
 *
 * `aria-hidden` with a sibling live region rather than announcing itself:
 * a screen reader repeating "loading" for each of twelve skeleton rows is
 * worse than silence. The single status message belongs to the container.
 */
export function Skeleton({ className, ...props }: HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      aria-hidden
      className={cn('animate-pulse rounded bg-surface-sunken', className)}
      {...props}
    />
  );
}

export interface SkeletonTextProps extends HTMLAttributes<HTMLDivElement> {
  lines?: number;
}

export function SkeletonText({ lines = 3, className, ...props }: SkeletonTextProps) {
  return (
    <div className={cn('flex flex-col gap-2', className)} {...props}>
      {Array.from({ length: lines }, (_, index) => (
        <Skeleton
          key={index}
          className={cn('h-4', index === lines - 1 ? 'w-2/3' : 'w-full')}
        />
      ))}
    </div>
  );
}
