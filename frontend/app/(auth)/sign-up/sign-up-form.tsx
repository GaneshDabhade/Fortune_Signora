'use client';

import { useRouter } from 'next/navigation';
import { useState } from 'react';

import { Button, Input } from '@/components/ui';
import { MINIMUM_PASSWORD_LENGTH } from '@/lib/auth/password';
import { signUpWithPassword } from '@/lib/auth/client';

/**
 * Registration.
 *
 * **The minimum length is stated before it is enforced.** A rule a person
 * discovers by breaking it is a rule that costs them a round trip, and the
 * number here is imported from the same constant Better Auth is configured
 * with — not typed twice.
 */
export function SignUpForm() {
  const router = useRouter();
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [pending, setPending] = useState(false);

  const submit = async (event: React.FormEvent) => {
    event.preventDefault();
    setPending(true);
    setError(null);
    const result = await signUpWithPassword(name, email, password);
    if (result.ok) {
      router.push(`/verify-email?email=${encodeURIComponent(email)}`);
      return;
    }
    setError(result.error ?? null);
    setPending(false);
  };

  return (
    <form onSubmit={submit} className="flex flex-col gap-4">
      <Input
        label="Name"
        autoComplete="name"
        required
        value={name}
        onChange={(event) => setName(event.target.value)}
      />
      <Input
        label="Email"
        type="email"
        autoComplete="email"
        required
        value={email}
        onChange={(event) => setEmail(event.target.value)}
        {...(error ? { error } : {})}
      />
      <Input
        label="Password"
        type="password"
        autoComplete="new-password"
        required
        minLength={MINIMUM_PASSWORD_LENGTH}
        value={password}
        onChange={(event) => setPassword(event.target.value)}
        hint={`At least ${MINIMUM_PASSWORD_LENGTH} characters. Length is the only rule.`}
      />
      <Button type="submit" disabled={pending}>
        {pending ? 'Creating your account…' : 'Create account'}
      </Button>
    </form>
  );
}
