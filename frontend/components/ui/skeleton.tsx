'use client';

/**
 * ⛔ **`'use client'`, because `LoadingRegion` and `SkeletonText` hold state.**
 *
 * ⚠️ **Added after the browser refused to build, not after a test failed** —
 * 🔴 **the whole 4,000-test suite passed** while `next dev` returned 500 on
 * every route: **Vitest renders everything as a client component**, so a
 * missing directive is invisible to it. ⚡ **Sixteen route-level `loading.tsx`
 * files are Server Components importing this**, which is the shape that turned
 * one missing line into every page.
 */
import { useEffect, useRef, useState, type HTMLAttributes, type ReactNode } from 'react';

import { cn } from '@/lib/design/cn';

/**
 * A loading placeholder occupying the same space as the content it stands
 * in for.
 *
 * `aria-hidden` with a sibling live region rather than announcing itself:
 * a screen reader repeating "loading" for each of twelve skeleton rows is
 * worse than silence. The single status message belongs to the container.
 *
 * ## 🔴 [B-1057](../../../docs/BUGS.md) — the sibling live region did not exist
 *
 * ⛔ **The paragraph above described a design nobody had built**, which is
 * [§2](../../../CLAUDE.md)'s false claim in a docstring. ⚡ **QE held a read
 * open for 12 seconds and sampled mid-flight**: three skeletons, correctly
 * `aria-hidden`, **`aria-busy` nowhere in the document, both `aria-live`
 * regions empty, and the word *loading* absent.**
 *
 * ✅ **`aria-hidden` stays** — 📁 the row is explicit that exposing the
 * skeletons is not the fix, because *three pulsing rectangles are not a status
 * message*. 📁 **WCAG 2.2 SC 4.1.3** wants a programmatically determinable
 * status, and 📁 `LoadingRegion` below is it.
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

/**
 * ♿ **A live region must be in the document BEFORE its text changes**, or a
 * screen reader has nothing to notice. ⛔ **Rendering the message with the
 * region on the same paint is the classic way to publish a status nobody
 * hears** — so the region mounts empty and the text arrives one effect later.
 */
function useAnnouncedAfterMount(text: string): string {
  const [announced, setAnnounced] = useState('');
  useEffect(() => {
    setAnnounced(text);
  }, [text]);
  return announced;
}

export interface SkeletonTextProps extends HTMLAttributes<HTMLDivElement> {
  lines?: number;
  /**
   * ⚡ **What is loading, in the customer's words** — it completes
   * *"Loading …"*. ⛔ **Optional, and its absence gives the generic sentence
   * rather than silence**: 📁 WCAG 2.2 SC 4.1.3's own example is *"Content is
   * loading"*, and an unlabelled wait is still a wait.
   */
  label?: string;
}

/**
 * 🔴 **[B-1057](../../../docs/BUGS.md) — this is where the announcement had to
 * go, because this is what every waiting screen already renders.**
 *
 * 📁 **Sixteen of the product's seventeen route-level `loading.tsx` files are a
 * single `<SkeletonText/>`**, and roughly twenty card-level reads are too. ⚡
 * **Putting the region here makes the omission unrepresentable** rather than
 * something thirty-seven call sites each have to remember.
 *
 * ⚠️ **A route fallback announces entry only, and that is correct.** ⛔ **It
 * unmounts the moment the read settles**, so it could not speak then even if it
 * wanted to — ✅ **and 📁 `route-announcer.tsx` already announces the arriving
 * page, which IS the settle.** ⚡ **Where a region survives the transition, 📁
 * `LoadingRegion` announces both halves.**
 */
export function SkeletonText({ lines = 3, label, className, ...props }: SkeletonTextProps) {
  const announced = useAnnouncedAfterMount(label === undefined ? 'Loading…' : `Loading ${label}…`);
  return (
    <div aria-busy className={cn('flex flex-col gap-2', className)} {...props}>
      {/* ♿ **`<output>` is `role="status"` with an implicit polite live
          region** — 📁 the same element `route-announcer.tsx` uses. */}
      <output aria-live="polite" className="sr-only">
        {announced}
      </output>
      {Array.from({ length: lines }, (_, index) => (
        <Skeleton
          key={index}
          className={cn('h-4', index === lines - 1 ? 'w-2/3' : 'w-full')}
        />
      ))}
    </div>
  );
}

/**
 * ♿ **The status message the skeletons cannot be** — 📁
 * [B-1057](../../../docs/BUGS.md), 📁 **WCAG 2.2 SC 4.1.3 *Status Messages***.
 *
 * ⛔ **It wraps BOTH states, not the skeletons.** ⚡ **A region that unmounted
 * with the placeholders could never announce the settle** — the element
 * carrying the message would be gone at the moment there was something to say.
 *
 * ⚠️ **Twice, and only twice**: once on entry, once on settle. 📁 The row is
 * explicit — ⛔ *"not on every re-render"* — so the settle line is published
 * only if this region actually announced a wait, and a read that resolves from
 * cache says nothing at all.
 *
 * ⚡ **`aria-busy` is `undefined` rather than `"false"` when settled**, so a
 * settled page carries no attribute rather than an attribute saying nothing.
 */
export function LoadingRegion({
  label,
  busy,
  className,
  children,
}: {
  /** ⚡ **In the customer's words**, and it completes *"Loading …"*. */
  label: string;
  busy: boolean;
  className?: string;
  children: ReactNode;
}) {
  const waited = useRef(false);
  const [message, setMessage] = useState('');

  // ⚡ **Set in an effect, never during render** — see `useAnnouncedAfterMount`.
  useEffect(() => {
    if (busy) {
      waited.current = true;
      setMessage(`Loading ${label}…`);
      return;
    }
    // ⛔ **Nothing to settle if nothing waited.** A read served from cache
    // renders once, already settled, and owes no announcement.
    if (!waited.current) return;
    waited.current = false;
    setMessage(`${label} loaded.`);
  }, [busy, label]);

  return (
    <div aria-busy={busy ? true : undefined} className={className}>
      {/* ♿ **`<output>` is `role="status"` with an implicit polite live
          region** — the same element 📁 `route-announcer.tsx` uses, rather than
          a second spelling of the same idea. */}
      <output aria-live="polite" className="sr-only">
        {message}
      </output>
      {children}
    </div>
  );
}
