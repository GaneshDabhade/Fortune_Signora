'use client';

import { useEffect, useState } from 'react';

/**
 * 🔴 **Whether the DEVICE is reducing motion**, read at runtime.
 *
 * ⛔ **Not the `reduce_motion` preference**, and the distinction is the whole
 * reason this exists. 📁 [`preferences.ts`](../api/preferences.ts) states the
 * contract: *"this is **on regardless of what the device says**, and `false`
 * leaves the media query in charge"* — **so the preference alone misses every
 * person who set it in their operating system and never opened Signora's
 * settings.**
 *
 * ## ⚠️ Lifted here from one caller, because a second one arrived
 *
 * ⚡ **[`workspace-strip.tsx`](../../components/home/workspace-strip.tsx) wrote
 * it first and correctly**, for the half CSS cannot do: *cancelling a timer
 * rather than shortening an animation.* ✅ **It is unchanged** — 📁
 * [§20c](../../CLAUDE.md), *"add to the library rather than around it"*, and a
 * second copy is how the two would eventually disagree about what *reduced*
 * means.
 *
 * ## ⛔ It returns `false` on the first render, and that is deliberate
 *
 * **`matchMedia` does not exist during server rendering**, so the initial state
 * cannot be the real answer. ⚡ **Reporting *not reduced* until the effect runs
 * is the safe direction for both callers**: the strip's timer starts and is
 * cancelled, and the panel below shows one fewer sentence for one frame.
 * ⛔ **The opposite default would flash a claim about the reader's device that
 * might be untrue.**
 */
export function useReducedMotion(): boolean {
  const [reduced, setReduced] = useState(false);

  useEffect(() => {
    const media = window.matchMedia('(prefers-reduced-motion: reduce)');
    setReduced(media.matches);
    const listen = (event: MediaQueryListEvent) => setReduced(event.matches);
    media.addEventListener('change', listen);
    return () => media.removeEventListener('change', listen);
  }, []);

  return reduced;
}
