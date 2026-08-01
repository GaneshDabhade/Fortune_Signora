import { notFound } from 'next/navigation';

import { loadAuthConfig } from '@/lib/auth/config';

import { AuthLink, AuthShell } from '../auth-shell';
import { ResetPasswordForm } from './reset-password-form';

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
