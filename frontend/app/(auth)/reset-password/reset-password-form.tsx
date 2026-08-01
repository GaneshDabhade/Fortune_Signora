'use client';

import { useRouter } from 'next/navigation';
import { useState } from 'react';

import { Button, Input } from '@/components/ui';
import { MINIMUM_PASSWORD_LENGTH } from '@/lib/auth/password';
import { resetPassword } from '@/lib/auth/client';

/**
 * The last step of a reset.
 *
 * **No "current password" field**, because the person here is the one who
 * could not supply it; the emailed token is what stands in its place. Changing
 * a password while signed in is a different flow with a different proof, and
 * merging the two would weaken whichever one it borrowed from.
 */
export function ResetPasswordForm({ token }: { token: string }) {
  const router = useRouter();
  const [password, setPassword] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [pending, setPending] = useState(false);

  const submit = async (event: React.FormEvent) => {
    event.preventDefault();
    setPending(true);
    setError(null);
    const result = await resetPassword(token, password);
    if (result.ok) {
      // Deliberately not signed in automatically. A reset is the one moment
      // it is worth proving the new password works while the person still
      // remembers typing it.
      router.push('/sign-in');
      return;
    }
    setError(result.error ?? null);
    setPending(false);
  };

  return (
    <form onSubmit={submit} className="flex flex-col gap-4">
      <Input
        label="New password"
        type="password"
        autoComplete="new-password"
        required
        minLength={MINIMUM_PASSWORD_LENGTH}
        value={password}
        onChange={(event) => setPassword(event.target.value)}
        hint={`At least ${MINIMUM_PASSWORD_LENGTH} characters.`}
        {...(error ? { error } : {})}
      />
      <Button type="submit" disabled={pending}>
        {pending ? 'Saving…' : 'Save and sign in'}
      </Button>
    </form>
  );
}
