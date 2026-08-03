'use client';

import { useRouter } from 'next/navigation';
import { useState } from 'react';

import { Button, Input } from '@/components/ui';
import { signIn, signInWithPassword } from '@/lib/auth/client';

const OAUTH_LABELS: Record<string, string> = {
  google: 'Continue with Google',
  microsoft: 'Continue with Microsoft',
};

/**
 * Every way into Signora, on one screen.
 *
 * **The password form leads and the providers follow**, because the password
 * method is the one that always works — an OAuth button is only present when
 * its credentials are configured, and a screen whose primary action can be
 * absent has no reliable primary action.
 *
 * The two paths end in the same place. Better Auth issues one session shape,
 * `/api/token` mints one claim set from it, and the API cannot tell which
 * route a caller took because nothing in the token says (ADR-0033).
 */
export function SignInForm({
  passwordEnabled,
  oauthMethods,
}: {
  passwordEnabled: boolean;
  oauthMethods: string[];
}) {
  const router = useRouter();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [pending, setPending] = useState<string | null>(null);

  const submit = async (event: React.FormEvent) => {
    event.preventDefault();
    setPending('password');
    setError(null);
    const result = await signInWithPassword(email, password);
    if (result.ok) {
      // `router.refresh()` first: the session cookie was just set, and a
      // client-side navigation alone would render the destination against a
      // server component tree that still believes nobody is signed in.
      router.refresh();
      // **`/workspaces` for three slices, and no such route has ever
      // existed** — a password sign-in landed on the not-found page. Found by
      // the ADR-0034 vocabulary audit rather than by a test, because the code
      // was reasoning about a tenancy concept while the product needed a
      // destination. `/` is the attention list: a seller's morning (D38).
      //
      // **This line never fixed it, and that is the more useful lesson.**
      // Better Auth navigates to its own `callbackURL` and beats this push,
      // so the destination stayed `/workspaces` and the 404 stayed with it
      // for three further slices — invisible because the constant read as
      // corrected. Fixed at its source in `lib/auth/client.ts`; kept here
      // because it is still the right destination when the vendor does not
      // navigate, and it is now the same one.
      router.push('/');
      return;
    }
    setError(result.error ?? null);
    setPending(null);
  };

  if (!passwordEnabled && oauthMethods.length === 0) {
    return (
      <p className="rounded border border-warning bg-surface-raised p-3 text-sm text-content">
        No sign-in method is configured, so nobody can sign in. Enable password sign-in or
        set OAuth credentials.
      </p>
    );
  }

  return (
    <div className="flex flex-col gap-5">
      {passwordEnabled ? (
        <form onSubmit={submit} className="flex flex-col gap-4">
          <Input
            label="Email"
            type="email"
            autoComplete="email"
            required
            value={email}
            onChange={(event) => setEmail(event.target.value)}
          />
          <Input
            label="Password"
            type="password"
            autoComplete="current-password"
            required
            value={password}
            onChange={(event) => setPassword(event.target.value)}
            {...(error ? { error } : {})}
          />
          <Button type="submit" disabled={pending !== null}>
            {pending === 'password' ? 'Signing in…' : 'Sign in'}
          </Button>
        </form>
      ) : null}

      {passwordEnabled && oauthMethods.length > 0 ? (
        <div className="flex items-center gap-3">
          <span className="h-px flex-1 bg-border" />
          <span className="text-xs uppercase tracking-wide text-content-subtle">or</span>
          <span className="h-px flex-1 bg-border" />
        </div>
      ) : null}

      {oauthMethods.map((method) => (
        <Button
          key={method}
          variant="secondary"
          disabled={pending !== null}
          onClick={() => {
            setPending(method);
            void signIn(method);
          }}
        >
          {pending === method ? 'Redirecting…' : (OAUTH_LABELS[method] ?? method)}
        </Button>
      ))}
    </div>
  );
}
