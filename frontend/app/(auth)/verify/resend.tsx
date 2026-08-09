'use client';

import { useState } from 'react';

import { Button, Input } from '@/components/ui';
import {
  ATTEMPTS_BEFORE_FILTER_HINT,
  formatRemaining,
  useResendTimer,
} from '@/components/ui/resend-timer';
import { resendVerification } from '@/lib/auth/client';

/**
 * **Screen `07`'s *"Didn't get it?"*** — [TASK-486](../../../../docs/BACKLOG.md).
 *
 * ⚡ **The design's timer, exactly as stated**: *"the resend timer starts at
 * 45s and doubles; the third resend suggests checking spam and the corporate
 * filter."* **The remaining time is printed rather than the control merely
 * being disabled** — the design's own accessibility note asks for that of
 * *"resend counters, lock countdowns, redirect timers"*.
 *
 * ⛔ **What this screen sends is a link, not a code, and it says so.** The
 * design draws six digit boxes; **`lib/auth/server.ts:73` sends `{ user, url }`
 * and there is no endpoint that would accept a typed code** — raised as
 * [C-241](../../../../docs/LANE_COORDINATION.md). **Six boxes wired to nothing
 * would be the false affordance this lane already refused at `/join`'s
 * *Request access* and `/sso`'s domain field.**
 *
 * **The address stays prefilled and editable.** Somebody who mistyped it on
 * the previous screen is the most likely person reading this, and making them
 * start over is how a sign-up is abandoned at the last step.
 */
export function ResendVerification({ email }: { email: string | null }) {
  const [address, setAddress] = useState(email ?? '');
  const [state, setState] = useState<'idle' | 'pending'>('idle');
  const [error, setError] = useState<string | null>(null);
  const { remaining, attempts, sent } = useResendTimer();

  const submit = async (event: React.FormEvent) => {
    event.preventDefault();
    setState('pending');
    setError(null);

    const result = await resendVerification(address);
    setState('idle');
    if (!result.ok) {
      setError(result.error ?? null);
      return;
    }
    // Only a successful send starts the next wait. A failure that began a
    // 45-second countdown would punish somebody for the product's own error.
    sent();
  };

  const waiting = remaining > 0;

  return (
    <form onSubmit={submit} className="flex flex-col gap-4">
      <Input
        label="Work email"
        type="email"
        autoComplete="email"
        required
        value={address}
        onChange={(event) => setAddress(event.target.value)}
        {...(error ? { error } : {})}
      />

      <Button type="submit" variant="secondary" disabled={state === 'pending' || waiting}>
        {state === 'pending' ? 'Sending…' : waiting ? `Resend in ${formatRemaining(remaining)}` : 'Resend'}
      </Button>

      {/* ⚡ **Announced, because the count changes every second.** Polite, not
          an alert — an interruption per second is not feedback. */}
      <p aria-live="polite" className="sr-only">
        {waiting ? `You can send again in ${remaining} seconds.` : ''}
      </p>

      {attempts > 0 ? (
        <p className="text-sm leading-6 text-content-muted">
          {attempts >= ATTEMPTS_BEFORE_FILTER_HINT
            ? // The design's third-attempt wording. By now the likely cause is
              // not a slow queue, and saying so is more use than sending again.
              'Sent again. If it still has not arrived, check your spam folder and ask whether your corporate filter is holding mail from us.'
            : 'Sent again. If it does not arrive, check the address above.'}
        </p>
      ) : null}
    </form>
  );
}
