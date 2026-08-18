'use client';

import { useEffect, useState } from 'react';

/**
 * 📁 **Home's two timed loading rules** — `Fortune Signora Home.dc.html` §09.
 *
 * > | | |
 * > |---|---|
 * > | **Under 300ms** | *"**No skeleton at all.** A placeholder shown and removed inside 300ms reads as a flicker."* |
 * > | **Over 8 seconds** | *"The card **converts to its error state with a retry**. Skeletons do not shimmer indefinitely."* |
 *
 * ## ⚡ One hook rather than a rule per card
 *
 * 📁 §09's other four rules are already structural — the greeting is never
 * skeletonised, the scope count is silent rather than `0`, each skeleton uses its
 * declared footprint, and **no card waits for a sibling**. ⛔ **These two are
 * about TIME**, which nothing in a render can observe, so they need a clock.
 *
 * ⚠️ **Per card, deliberately.** 📁 *"Independence: one slow card holds its own
 * skeleton."* ⛔ A single page-level timer would make every card's skeleton appear
 * and expire together, which is the coupling that rule forbids.
 *
 * ## 🔴 The timeout is a state, not a cancellation
 *
 * ⛔ **The query is not aborted.** ⚡ **The card stops waiting; the read does
 * not** — so a response that arrives at nine seconds still renders, and the card
 * heals itself without anybody pressing anything. 📁 *"Skeletons do not shimmer
 * indefinitely"* is a statement about what a person sees, not about the network.
 */
export type CardPhase =
  /** The read has settled — render the card. */
  | 'settled'
  /** 📁 *"No skeleton at all"* — under 300ms, the frame holds its footprint empty. */
  | 'quiet'
  /** 📁 The declared skeleton, at the card's declared height. */
  | 'skeleton'
  /** 📁 *"The card converts to its error state with a retry."* */
  | 'timeout';

/** 📁 ***"A placeholder shown and removed inside 300ms reads as a flicker."*** */
export const SKELETON_AFTER_MS = 300;
/** 📁 ***"Over 8 seconds… skeletons do not shimmer indefinitely."*** */
export const GIVE_UP_AFTER_MS = 8_000;

export function useCardPhase(pending: boolean): CardPhase {
  const [phase, setPhase] = useState<CardPhase>('quiet');

  useEffect(() => {
    if (!pending) {
      setPhase('settled');
      return;
    }
    // ⚡ **Reset on every new wait.** A refetch after a timeout starts its own
    // 300ms of quiet rather than inheriting the last attempt's verdict.
    setPhase('quiet');
    const skeleton = setTimeout(() => setPhase('skeleton'), SKELETON_AFTER_MS);
    const timeout = setTimeout(() => setPhase('timeout'), GIVE_UP_AFTER_MS);
    return () => {
      clearTimeout(skeleton);
      clearTimeout(timeout);
    };
  }, [pending]);

  return phase;
}
