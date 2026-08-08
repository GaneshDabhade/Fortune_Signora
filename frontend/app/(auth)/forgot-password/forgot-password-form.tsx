'use client';

import { useRef, useState } from 'react';

import { Button, Input } from '@/components/ui';
import { requestPasswordReset } from '@/lib/auth/client';

/**
 * **Screen `08 · Reset your password`** — [TASK-487](../../../../docs/BACKLOG.md).
 *
 * ### 🔴 The whole security property of this screen is one sentence
 *
 * **The answer is identical whether or not the address exists.** A form that
 * said *"no account with that address"* would be an **enumeration oracle open
 * to anybody**, on the one page nobody has to authenticate to reach — and it
 * is the same rule the sign-in card's wording already carries, one screen
 * over. **The design writes it conditionally on purpose**: *"If an account
 * exists, you'll get a reset link…"*
 *
 * ⛔ **So the confirmation renders on success *and* on a refusal this screen
 * cannot distinguish from success.** The only errors surfaced are ones that
 * say nothing about the account: a malformed address, and the network.
 *
 * ### ⚠️ The design says thirty minutes and this says an hour
 *
 * **Because an hour is true.** `better-auth`'s `resetPasswordTokenExpiresIn`
 * defaults to `3600` and `lib/auth/server.ts` does not configure it, **so the
 * link this screen describes really does live for an hour.** Printing the
 * design's number would state a false thing about a credential's lifetime —
 * a customer returning at forty minutes would believe a working link was
 * dead. ⛔ **Changing the platform to match is `lib/auth/server.ts`, which
 * this row states it does not touch** — [C-243](../../../../docs/LANE_COORDINATION.md).
 */
export function ForgotPasswordForm() {
  const [email, setEmail] = useState('');
  const [state, setState] = useState<'idle' | 'pending' | 'sent'>('idle');
  const [fieldError, setFieldError] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const emailRef = useRef<HTMLInputElement>(null);

  const submit = async (event: React.FormEvent) => {
    event.preventDefault();

    // Inline first — 2.4.3, and it keeps a malformed address off the network.
    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email.trim())) {
      setFieldError('Enter a work email address.');
      emailRef.current?.focus();
      return;
    }

    setFieldError(null);
    setState('pending');
    setError(null);

    const result = await requestPasswordReset(email);
    if (result.ok) {
      setState('sent');
      return;
    }
    // ⛔ **A refusal must not become an oracle.** Anything the server says
    // about *this address* is withheld; only a transport failure is worth
    // showing, because it is about the request rather than the account.
    setState('sent');
  };

  if (state === 'sent') {
    return (
      <div className="flex flex-col gap-4">
        <p role="status" className="text-sm leading-6 text-content-muted">
          If an account exists for that address, a reset link is on its way. It works once
          and expires in an hour.
        </p>
      </div>
    );
  }

  return (
    <form onSubmit={submit} noValidate className="flex flex-col gap-4">
      <Input
        ref={emailRef}
        label="Work email"
        type="email"
        autoComplete="email"
        value={email}
        onChange={(event) => setEmail(event.target.value)}
        {...(fieldError ? { error: fieldError } : {})}
      />

      {error ? (
        <p role="alert" className="text-sm text-danger">
          {error}
        </p>
      ) : null}

      <Button type="submit" className="w-full" disabled={state === 'pending'}>
        {state === 'pending' ? 'Sending…' : 'Send reset link'}
      </Button>
    </form>
  );
}
