'use client';

import { WifiOff } from 'lucide-react';
import { useCallback, useEffect, useRef, useState } from 'react';

import { SystemState } from '@/components/ui/system-state';
import {
  describeLastConnected,
  lastConnected,
  probeConnection,
} from '@/lib/system-states/last-connected';

/**
 * **No internet, cold start** — [TASK-1436](../../../docs/BACKLOG.md).
 *
 * > 📁 **System States §04**: ***"Different problem, different screen. There is
 * > no cached session to fall back on, so the state is honest about having
 * > nothing: it distinguishes 'your network' from 'our service', offers a
 * > single retry that actually re-checks rather than reloading, and shows the
 * > last successful connection time."***
 *
 * ## ⚡ This is the ladder's PLATFORM scope, finding its first caller
 *
 * 📁 **`no-internet` has been legal at platform scope since
 * [TASK-1409](../../../docs/BACKLOG.md) and nothing had rendered it.** ⛔ **So
 * no new component**: `SystemState` already derives the assertive announcement
 * platform scope requires — 📁 `4.1.3`, *"only a state that ends the session
 * announces assertively"* — **and this state does end it.**
 *
 * ## ⛔ It is not [TASK-1435](../../../docs/BACKLOG.md)'s pill, and the design says so
 *
 * ⚠️ **The pill is for a session that is still working from cache with edits
 * queued.** **This is the cold start where there is nothing** — 📁 *"different
 * problem, different screen"* — **and conflating them would offer somebody a
 * queue that does not exist.**
 *
 * ## 🔴 Retry PROBES; it never reloads
 *
 * 📁 The row: ⛔ ***"a reload on a cold start with no network returns the
 * browser's own error page — the customer loses the product's designed state
 * and gets the browser's undesigned one, which is the one screen Signora
 * cannot style."*** ⚡ **`probeConnection()` asks Signora's service and returns
 * an answer.**
 */

/** 📁 *"retrying in 8s"* — the design's own interval. */
export const RETRY_SECONDS = 8;

export function NoConnection({ onRestored }: { onRestored?: () => void }) {
  const [seconds, setSeconds] = useState(RETRY_SECONDS);
  const [checking, setChecking] = useState(false);
  // ⛔ Read once, in an effect: `localStorage` during render disagrees with the
  // server's markup and loses the tree.
  const [since, setSince] = useState<string | null>(null);
  const restored = useRef(onRestored);
  restored.current = onRestored;

  useEffect(() => setSince(describeLastConnected(lastConnected())), []);

  const check = useCallback(async () => {
    setChecking(true);
    const back = await probeConnection();
    setChecking(false);
    setSeconds(RETRY_SECONDS);
    if (back) restored.current?.();
  }, []);

  // ⚡ **The countdown is the design's promise made observable.** 📁 *"retrying
  // in 8s"* is a commitment that something will happen without being asked,
  // and a number that ticks is how a person knows it still will.
  useEffect(() => {
    const tick = setInterval(() => {
      setSeconds((left) => {
        if (left > 1) return left - 1;
        void check();
        return RETRY_SECONDS;
      });
    }, 1000);
    return () => clearInterval(tick);
  }, [check]);

  return (
    <main className="flex min-h-screen items-center justify-center bg-canvas px-6">
      <div className="w-full max-w-md">
        <SystemState
          scope="platform"
          state="no-internet"
          glyph={WifiOff}
          // 📁 The design's own heading and its two sentences, unchanged.
          title="No connection"
          description="Your device reports no network. Signora's own service is reachable from other regions, so this is almost certainly local."
          primaryAction={
            <button
              type="button"
              onClick={() => void check()}
              disabled={checking}
              className="rounded border border-border-strong bg-surface px-3 py-1 text-sm font-medium text-content transition-colors hover:bg-surface-sunken focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent disabled:opacity-60"
            >
              {checking ? 'Checking…' : 'Check again'}
            </button>
          }
          secondaryAction={
            <a
              href="https://status.signora.app"
              className="rounded text-sm font-medium text-accent underline decoration-border underline-offset-4 transition-colors hover:decoration-accent focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent"
            >
              Status page
            </a>
          }
        />

        {/* 📁 ***"Last connected 3 minutes ago · retrying in 8s"*** — one line,
            two facts, exactly as the design writes it.

            ⛔ **The left half is omitted when this browser has never
            connected**, rather than saying *"just now"*. ⚡ **A first-ever
            visit with no network has nothing to report**, and the design asks
            this screen to be *"honest about having nothing"* — inventing a
            time here would be the one thing it is told not to do. */}
        <p className="mt-4 text-center text-xs text-content-subtle">
          {since === null ? `Retrying in ${seconds}s` : `${since} · retrying in ${seconds}s`}
        </p>
      </div>
    </main>
  );
}
