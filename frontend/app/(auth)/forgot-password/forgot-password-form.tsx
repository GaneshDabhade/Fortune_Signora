'use client';

import { useState } from 'react';

import { Button, Input } from '@/components/ui';
import { requestPasswordReset } from '@/lib/auth/client';

/**
 * Ask for a reset link.
 *
 * **The answer is the same whether or not the address exists**, and that is
 * the whole security property of this screen. A form that said *"no account
 * with that address"* would be an enumeration oracle open to anybody, on the
 * one page nobody has to authenticate to reach.
 *
 * The confirmation is therefore worded to be true either way — *if there is an
 * account* — rather than implying something was sent.
 */
export function ForgotPasswordForm() {
  const [email, setEmail] = useState('');
  const [state, setState] = useState<'idle' | 'pending' | 'sent'>('idle');
  const [error, setError] = useState<string | null>(null);

  const submit = async (event: React.FormEvent) => {
    event.preventDefault();
    setState('pending');
    setError(null);
    const result = await requestPasswordReset(email);
    setState(result.ok ? 'sent' : 'idle');
    if (!result.ok) setError(result.error ?? null);
  };

  if (state === 'sent') {
    return (
      <p className="text-sm leading-6 text-content-muted">
        If there is an account for that address, a reset link is on its way. The link
        expires in an hour.
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
        value={email}
        onChange={(event) => setEmail(event.target.value)}
        {...(error ? { error } : {})}
      />
      <Button type="submit" disabled={state === 'pending'}>
        {state === 'pending' ? 'Sending…' : 'Send the link'}
      </Button>
    </form>
  );
}
