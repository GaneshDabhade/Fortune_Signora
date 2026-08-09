'use client';

import { Check, Loader2 } from 'lucide-react';
import { useEffect, useState } from 'react';

import { Button } from '@/components/ui';
import { cn } from '@/lib/design/cn';

/**
 * **Signing you in…** — design `15`.
 *
 * **TASK-467 · Workflow 1, milestone 4.**
 *
 * ### The two timings are the design's, and both are rules rather than polish
 *
 * | | |
 * |---|---|
 * | **800ms** | *"Named steps replace a bare spinner past 800ms."* ⚡ **Below it nothing appears at all** — a card that swaps itself out for a fast sign-in is a flash, and the button's own loading state already covers that case |
 * | **8s** | *"Past 8 seconds the card offers to cancel and try another method — **it never hangs silently**."* |
 *
 * ### ⛔ Two steps, not the design's three, and the third is not hidden
 *
 * The design names **verified your credentials · checking workspace membership
 * · loading your permissions**. ⚡ **Only the first two happen while this card
 * is on screen.** Permissions resolve in `authenticated-shell.tsx` *after* the
 * navigation, against a session that does not exist yet here — so a third step
 * would be this screen narrating work it cannot observe, which is the
 * fabricated-progress trap in its most convincing form.
 *
 * ⚡ **What is rendered is what is true**: the credential check is a real
 * request, and *preparing your organization* is the real `router.refresh()`
 * and navigation that follow a successful one.
 *
 * ### Cancelling actually cancels
 *
 * The escape aborts the in-flight request through an `AbortSignal`. **A button
 * that only stopped *showing* the attempt would let a session be established
 * for somebody who had just told the product to stop** — and on a shared
 * machine that is the whole of the risk.
 */
export type AuthStage = 'credentials' | 'organization';

const STEPS: [AuthStage, string][] = [
  ['credentials', 'Checking your credentials'],
  ['organization', 'Preparing your organization'],
];

export function Authenticating({
  stage,
  onCancel,
}: {
  stage: AuthStage;
  onCancel: () => void;
}) {
  // Two independent thresholds rather than one timer with two branches: they
  // answer different questions — *is this slow enough to explain* and *is this
  // slow enough to escape* — and a single elapsed counter re-rendering every
  // second to serve them would be work nobody sees.
  const [named, setNamed] = useState(false);
  const [stalled, setStalled] = useState(false);

  useEffect(() => {
    const explain = setTimeout(() => setNamed(true), 800);
    const escape = setTimeout(() => setStalled(true), 8000);
    return () => {
      clearTimeout(explain);
      clearTimeout(escape);
    };
  }, []);

  // ⛔ **Below 800ms this renders nothing at all.** The button it replaces is
  // already saying *Signing in…*, and swapping the whole card out for one
  // frame is a flash rather than feedback.
  if (!named) return null;

  const reached = STEPS.findIndex(([name]) => name === stage);

  return (
    <div className="flex flex-col gap-5" aria-live="polite">
      <div className="flex flex-col gap-1">
        <h2 className="text-xl font-bold tracking-tight text-content">Signing you in…</h2>
      </div>

      <ol className="flex flex-col gap-3">
        {STEPS.map(([name, label], index) => {
          const done = index < reached;
          const active = index === reached;
          return (
            <li key={name} className="flex items-center gap-2.5 text-sm">
              <span
                aria-hidden
                className={cn(
                  'flex h-5 w-5 flex-none items-center justify-center rounded-full',
                  done && 'bg-success text-accent-contrast',
                  active && 'text-accent',
                  !done && !active && 'border border-border-soft',
                )}
              >
                {done ? <Check className="h-3 w-3" /> : null}
                {active ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : null}
              </span>
              {/* 1.4.1 — the mark is decorative and the state is in the text,
                  so a step that is merely *pending* does not read as done to
                  somebody who cannot see the tick. */}
              <span className={done || active ? 'text-content' : 'text-content-subtle'}>
                {label}
                {done ? <span className="sr-only"> — done</span> : null}
                {active ? <span className="sr-only"> — in progress</span> : null}
              </span>
            </li>
          );
        })}
      </ol>

      {stalled ? (
        <div className="flex flex-col gap-3 rounded-lg bg-surface-sunken p-4">
          <p className="text-sm leading-6 text-content-muted">
            This is taking longer than usual. You can stop waiting and try another
            way to sign in.
          </p>
          <Button type="button" variant="secondary" onClick={onCancel}>
            Cancel and go back
          </Button>
        </div>
      ) : null}
    </div>
  );
}
