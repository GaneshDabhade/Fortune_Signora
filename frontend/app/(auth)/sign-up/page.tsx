import { notFound } from 'next/navigation';

import { loadAuthConfig } from '@/lib/auth/config';

import { AuthLink, AuthShell } from '../auth-shell';
import { SignUpForm } from './sign-up-form';

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

/**
 * Create an account.
 *
 * **404 when password sign-in is off**, rather than a page explaining that
 * registration is unavailable. A route that exists to say it does not work is
 * a dead end somebody can bookmark; with OAuth alone, an account is created by
 * signing in and there is nothing here to do.
 */
export default function SignUpPage() {
  if (!loadAuthConfig().passwordEnabled) notFound();

  return (
    <AuthShell
      title="Create your account"
      description="You will be asked to confirm your email address before signing in."
      footer={
        <>
          Already have an account? <AuthLink href="/sign-in">Sign in</AuthLink>
        </>
      }
    >
      <SignUpForm />
    </AuthShell>
  );
}
