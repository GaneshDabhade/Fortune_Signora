import { notFound } from 'next/navigation';

import { loadAuthConfig } from '@/lib/auth/config';

import { AuthLink, AuthShell } from '../auth-shell';
import { ResetPasswordForm } from './reset-password-form';

/**
 * **Reads runtime configuration, so it must never be prerendered** — the same
 * rule `/sign-in`, `/sign-up` and `/forgot-password` already follow (§20b,
 * environment-based configuration).
 *
 * This page and `/verify-email` were the two that did not, and the gap was
 * invisible: `loadAuthConfig()` had fallbacks, so prerendering silently
 * succeeded against a database and a secret belonging to no environment in
 * particular ([B-104](../../../../docs/BUGS.md)).
 */
export const dynamic = 'force-dynamic';

/**
 * Set a new password.
 *
 * Reached from the emailed link, which carries the token as a query
 * parameter. **A visit with no token is a dead link**, and the screen says so
 * rather than rendering a form that cannot succeed — the same rule as an
 * OAuth button for an unconfigured provider.
 */
export default async function ResetPasswordPage({
  searchParams,
}: {
  searchParams: Promise<{ token?: string; error?: string }>;
}) {
  if (!loadAuthConfig().passwordEnabled) notFound();
  const { token, error } = await searchParams;

  if (!token || error) {
    return (
      <AuthShell
        title="That link has expired"
        description="Reset links last an hour and can be used once. Ask for another and it will work."
        footer={<AuthLink href="/sign-in">Back to sign in</AuthLink>}
      >
        <p className="text-sm leading-6 text-content-muted">
          <AuthLink href="/forgot-password">Send me a new link</AuthLink>
        </p>
      </AuthShell>
    );
  }

  return (
    <AuthShell
      title="Set a new password"
      footer={<AuthLink href="/sign-in">Back to sign in</AuthLink>}
    >
      <ResetPasswordForm token={token} />
    </AuthShell>
  );
}
