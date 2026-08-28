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
        /**
         * 🔴 **The 24px floor is STATED, not inherited** — 📁 `Workspace Setup`
         * `2.5.8`: *"Row actions and **copy buttons** are ≥ 24px with 8px
         * separation."*
         *
         * ⛔ **It was `px-2 py-1 text-2xs` and nothing else**, so the height was
         * `8px + whatever line-height this button happened to inherit`.
         * ⚡ **`--text-2xs` is 11px and the config sets it size-only** — the
         * paired leading belongs to the tuple roles, not this one — **so a
         * parent with `leading-none` would render a 19px target and a parent
         * with `leading-6` a 32px one, from identical markup.**
         *
         * ⚠️ **A target whose size depends on where it is placed is not a
         * target size**, which is the lesson 📁
         * [`icon-button.tsx`](./icon-button.tsx) already records: *"`px-1`
         * around a `›` is padding round a narrow glyph, not a target."*
         *
         * ✅ **`inline-flex` is what makes `min-h` bite** and centres the text
         * inside it; **`coarse:min-h-11` is the repository's own touch floor**,
         * the same one `Button` and the accounts toolbar use.
         */
        'inline-flex min-h-6 items-center coarse:min-h-11',
        'mt-1 rounded px-2 py-1 font-mono text-2xs text-content-subtle transition-colors',
        'hover:bg-surface-sunken hover:text-content-muted',
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
