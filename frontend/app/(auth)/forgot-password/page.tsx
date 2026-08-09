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
 * (CLAUDE.md §20b), and the violation predates this change: `/signin` has
 * been static since M1.5.
 */
export const dynamic = 'force-dynamic';

export default function ForgotPasswordPage() {
  if (!loadAuthConfig().passwordEnabled) notFound();

  return (
    <AuthShell
      title="Reset your password"
      // The design's own sentence, verbatim. It carried one changed word until
      // C-243 was ruled; `resetPasswordTokenExpiresIn: 1800` is what makes the
      // thirty true, and the two are edited together or not at all.
      description="Enter your work email. If an account exists, you'll get a reset link that works once and expires in 30 minutes."
      footer={<AuthLink href="/signin">Back to sign in</AuthLink>}
    >
      <ForgotPasswordForm />
    </AuthShell>
  );
}
