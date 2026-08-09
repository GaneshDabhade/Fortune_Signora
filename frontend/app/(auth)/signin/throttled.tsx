'use client';

import { Clock } from 'lucide-react';
import { useEffect, useState } from 'react';

import { Button } from '@/components/ui';

/**
 * **Too many attempts** — design `12`.
 *
 * **TASK-467 · Workflow 1, milestone 3.**
 *
 * ### ⚡ Every number on this screen is the vendor's, not this screen's
 *
 * Better Auth rate-limits `/signin` at **three attempts per ten seconds**,
 * keyed on **`ip + path`** (`api/rate-limiter`), and answers `429` with
 * `X-Retry-After`. **So the design's own footnote is literally true of this
 * implementation** — *"throttling is per device and IP, not per account, so an
 * attacker cannot lock a colleague out by guessing at their address"* — and it
 * is printed because it is true, not because the design printed it.
 *
 * ### ⛔ One line of the design is deliberately not rendered
 *
 * *"Doubles with each further attempt."* **Better Auth's window does not
 * double** — it is a fixed rolling ten seconds. Printing it would tell a
 * customer their next attempt costs twenty seconds when it costs ten, which is
 * a false claim about a security control ([§2](../../../../CLAUDE.md)).
 * **Reported to the product owner rather than quietly rendered.**
 *
 * ### The countdown is absent rather than invented when the header is
 *
 * A `429` with no `X-Retry-After` is possible — a proxy may strip it. ⚡ **Then
 * the panel states the pause and offers no timer**, because a countdown made
 * up to fill the space is a promise about when sign-in resumes that nothing
 * supports ([P-A](../../../../docs/DOMAIN_DISCOVERY_REGISTER.md)).
 */
export function Throttled({
  retryAfterSeconds,
  onExpire,
}: {
  retryAfterSeconds?: number;
  onExpire: () => void;
}) {
  const [remaining, setRemaining] = useState(retryAfterSeconds ?? 0);

  useEffect(() => {
    if (retryAfterSeconds === undefined) return;
    setRemaining(retryAfterSeconds);

    const timer = setInterval(() => {
      setRemaining((seconds) => Math.max(0, seconds - 1));
    }, 1000);

    return () => clearInterval(timer);
  }, [retryAfterSeconds]);

  // ⚠️ **Reaching zero is its own effect, deliberately.** Calling `onExpire`
  // from inside the `setRemaining` updater would work and is a trap: an
  // updater runs during the render phase, so it would be updating the parent
  // while this component renders — the shape React warns about, and one that
  // survives review because the countdown still looks right.
  useEffect(() => {
    if (retryAfterSeconds === undefined || remaining > 0) return;
    onExpire();
  }, [remaining, retryAfterSeconds, onExpire]);

  return (
    <div className="flex flex-col gap-4">
      <div
        aria-hidden
        className="flex h-9 w-9 items-center justify-center rounded-lg border border-warning bg-warning-subtle text-warning"
      >
        <Clock className="h-4 w-4" />
      </div>

      <div className="flex flex-col gap-2">
        {/* An `h2` under the shell's `h1`: the heading names the screen, this
            names the state it is in. 4.1.3 — announced politely, because it
            replaces the form the person was just using rather than
            interrupting them mid-keystroke. */}
        <h2 className="text-xl font-bold tracking-tight text-content" aria-live="polite">
          Too many attempts
        </h2>
        <p className="text-sm leading-6 text-content-muted">
          For your protection, sign-in is paused for this device.
          {retryAfterSeconds === undefined ? ' Try again shortly.' : ' Try again in:'}
        </p>
      </div>

      {retryAfterSeconds === undefined ? null : (
        <div className="rounded-lg bg-surface-sunken p-4 text-center">
          {/* `tabular-nums` so the digits do not shift the card width as they
              count down — the same reasoning as the design's fixed-width
              loading button. */}
          <div className="text-display font-bold tabular-nums tracking-tight text-content">
            {format(remaining)}
          </div>
        </div>
      )}

      <Button type="button" variant="secondary" className="w-full" onClick={onExpire}>
        Sign in
      </Button>

      <p className="text-xs leading-5 text-content-subtle">
        Throttling is per device and IP, not per account, so an attacker cannot
        lock a colleague out by guessing at their address.
      </p>
    </div>
  );
}

function format(seconds: number): string {
  const minutes = Math.floor(seconds / 60);
  return `${minutes}:${String(seconds % 60).padStart(2, '0')}`;
}
