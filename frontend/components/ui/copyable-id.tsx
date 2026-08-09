'use client';

import { useState } from 'react';

import { cn } from '@/lib/design/cn';

/**
 * **A correlation id, copyable** — [TASK-1409](../../../docs/BACKLOG.md).
 *
 * > 📁 ***"Identifiers are copyable. Every failure carries a correlation ID
 * > in monospace with a copy affordance. It is the single thing that makes a
 * > support conversation short."***
 *
 * ## ⚡ Why this is extracted rather than written a fourth time
 *
 * ⚠️ **Three surfaces rendered a correlation id, three different ways**:
 * [`error-state.tsx`](./error-state.tsx) copied it, `app/error.tsx` printed
 * *"Reference: …"*, and `components/feedback/error-boundary.tsx` printed
 * *"Reference: …"* in a different size with no copy at all. ⛔ **§2 —
 * *behaviour exists exactly once*** — and the one that could not copy is the
 * one a customer would have had to retype.
 *
 * ## ⛔ The clipboard write is reported, never swallowed
 *
 * **It can fail** — permissions, a non-secure context. ⚡ **A silent failure
 * produces somebody who pastes their previous clipboard into a support
 * ticket**, so the outcome is stated and the id stays selectable either way.
 */
export function CopyableId({ value, className }: { value: string; className?: string }) {
  const [copied, setCopied] = useState<'idle' | 'done' | 'failed'>('idle');

  const copy = async () => {
    try {
      await navigator.clipboard.writeText(value);
      setCopied('done');
    } catch {
      setCopied('failed');
    }
  };

  return (
    <button
      type="button"
      onClick={copy}
      // ♿ `2.1.1` — reachable by keyboard, in visual order.
      className={cn(
        'mt-1 rounded px-2 py-1 font-mono text-2xs text-content-subtle transition-colors',
        'hover:bg-surface-sunken hover:text-content-muted',
        'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent',
        className,
      )}
    >
      {value}
      <span className="ml-2 font-sans">
        {copied === 'done' ? 'Copied' : copied === 'failed' ? 'Copy failed' : 'Copy'}
      </span>
    </button>
  );
}
