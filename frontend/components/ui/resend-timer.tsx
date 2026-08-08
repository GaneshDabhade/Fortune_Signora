'use client';

import { useCallback, useEffect, useRef, useState } from 'react';

/** The design's first interval. **45 seconds, then doubling.** */
export const FIRST_RESEND_DELAY_SECONDS = 45;

/** After this many sends the design adds the spam and corporate-filter hint. */
export const ATTEMPTS_BEFORE_FILTER_HINT = 3;

/** `0:42` — the design prints the remaining time, never a bare disabled button. */
export function formatRemaining(seconds: number): string {
  const minutes = Math.floor(seconds / 60);
  return `${minutes}:${String(seconds % 60).padStart(2, '0')}`;
}

export interface ResendTimer {
  /** Seconds left before another send is offered; `0` when it is. */
  readonly remaining: number;
  /** How many sends have happened. Drives the design's third-attempt hint. */
  readonly attempts: number;
  /** Call after a *successful* send. Starts the next, longer interval. */
  readonly sent: () => void;
}

/**
 * The resend cooldown from screen `07`, and from `08`/`09` after it.
 *
 * **The design states it exactly**: *"The resend timer starts at 45s and
 * doubles; the third resend suggests checking spam and the corporate
 * filter."* — 45, 90, 180, and so on.
 *
 * ### ⚠️ Why a doubling timer is honest here and was not on the sign-in card
 *
 * **Workflow 1 deliberately omitted the same phrase.** `sign-in/throttled.tsx`
 * refused to print *"doubles with each further attempt"* because **Better
 * Auth's sign-in window is a fixed rolling ten seconds** — the screen would
 * have been describing a server rule the server does not have.
 *
 * ⚡ **This one claims nothing about the server.** It is a **client-side
 * courtesy cooldown** on a button, and it says only *when this screen will
 * offer the control again*. **Nothing here rate-limits anything**, and the
 * component's name says so.
 *
 * ⛔ **It starts on a *successful* send, not on the click.** A failed request
 * that started a 45-second wait would punish somebody for the product's own
 * error, and they would have no way to retry.
 */
export function useResendTimer(): ResendTimer {
  const [remaining, setRemaining] = useState(0);
  const [attempts, setAttempts] = useState(0);
  // The next interval, doubling. Held in a ref because the countdown effect
  // must not restart when it changes.
  const delay = useRef(FIRST_RESEND_DELAY_SECONDS);

  useEffect(() => {
    if (remaining <= 0) return;
    const timer = setInterval(() => setRemaining((left) => Math.max(0, left - 1)), 1000);
    return () => clearInterval(timer);
  }, [remaining]);

  const sent = useCallback(() => {
    setAttempts((count) => count + 1);
    setRemaining(delay.current);
    delay.current *= 2;
  }, []);

  return { remaining, attempts, sent };
}
