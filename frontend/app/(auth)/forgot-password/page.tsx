import { notFound } from 'next/navigation';

import { loadAuthConfig } from '@/lib/auth/config';

import { AuthLink, AuthShell } from '../auth-shell';
import { ForgotPasswordForm } from './forgot-password-form';

/**
 * **Read at boot, never baked in.** This page's content depends on which
 * sign-in methods are configured, and Next.js would otherwise prerender it —
 * so an image built without OAuth credentials would keep showing no provider
 * buttons after being deployed *with* them, because the HTML was decided at
 * build time.
 *
 * That is the Infrastructure Contract's environment-based-configuration rule
 * (CLAUDE.md §20b), and the violation predates this change: `/sign-in` has
 * been static since M1.5.
 */
export const dynamic = 'force-dynamic';

export default function ForgotPasswordPage() {
  if (!loadAuthConfig().passwordEnabled) notFound();

  return (
    <AuthShell
      title="Reset your password"
      description="Give us the address on your account and we will send you a link."
      footer={<AuthLink href="/sign-in">Back to sign in</AuthLink>}
    >
      <ForgotPasswordForm />
    </AuthShell>
  );
}
