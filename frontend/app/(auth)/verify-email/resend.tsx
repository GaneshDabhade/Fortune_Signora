'use client';

import { useState } from 'react';

import { Button, Input } from '@/components/ui';
import { resendVerification } from '@/lib/auth/client';

/**
 * Send the link again.
 *
 * **The address is prefilled and still editable.** Somebody who mistyped it on
 * the previous screen is the single most likely person to be reading this, and
 * making them start over is how a sign-up gets abandoned at the last step.
 */
export function ResendVerification({ email }: { email: string | null }) {
  const [address, setAddress] = useState(email ?? '');
  const [state, setState] = useState<'idle' | 'pending' | 'sent'>('idle');
  const [error, setError] = useState<string | null>(null);

  const submit = async (event: React.FormEvent) => {
    event.preventDefault();
    setState('pending');
    setError(null);
    const result = await resendVerification(address);
    setState(result.ok ? 'sent' : 'idle');
    if (!result.ok) setError(result.error ?? null);
  };

  if (state === 'sent') {
    return (
      <p className="text-sm leading-6 text-content-muted">
        Sent again. If it does not arrive, check the address above.
      </p>
    );
  }

  return (
    <form onSubmit={submit} className="flex flex-col gap-4">
      <Input
        label="Email"
        type="email"
        autoComplete="email"
        required
        value={address}
        onChange={(event) => setAddress(event.target.value)}
        {...(error ? { error } : {})}
      />
      <Button type="submit" variant="secondary" disabled={state === 'pending'}>
        {state === 'pending' ? 'Sending…' : 'Send the link again'}
      </Button>
    </form>
  );
}
