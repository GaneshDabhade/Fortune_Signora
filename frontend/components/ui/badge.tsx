import type { HTMLAttributes } from 'react';

import { cn } from '@/lib/design/cn';

export type BadgeTone =
  | 'neutral'
  | 'accent'
  | 'success'
  | 'warning'
  | 'danger'
  | 'info'
  /** §14's reserved hue — *"a machine produced this"*, and nothing else in
   * the product may use the pairing. Deliberately not `info`: a notice and a
   * generated claim are different things to a reader deciding whether to
   * trust what they are looking at. */
  | 'ai';

const TONES: Record<BadgeTone, string> = {
  neutral: 'bg-surface-sunken text-content-muted',
  accent: 'bg-accent-subtle text-accent',
  success: 'bg-success-subtle text-success',
  warning: 'bg-warning-subtle text-warning',
  danger: 'bg-danger-subtle text-danger',
  info: 'bg-info-subtle text-info',
  ai: 'bg-ai-subtle text-ai',
};

export interface BadgeProps extends HTMLAttributes<HTMLSpanElement> {
  tone?: BadgeTone;
}

export function Badge({ className, tone = 'neutral', ...props }: BadgeProps) {
  return (
    <span
      className={cn(
        'inline-flex items-center rounded-sm px-2 py-0.5 text-xs font-medium',
        TONES[tone],
        className,
      )}
      {...props}
    />
  );
}
