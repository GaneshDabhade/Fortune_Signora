import { loadAuthConfig, oauthMethods } from '@/lib/auth/config';

import { AuthLink, AuthShell } from '../auth-shell';
import { SignInForm } from './sign-in-form';

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
 * Sign in.
 *
 * **Methods are configuration** (ADR-0033). Password sign-in is on unless
 * switched off; an OAuth button appears only when both halves of its
 * credentials are present, because a half-configured provider renders a button
 * that fails at the callback — worse than not offering it.
 */
export default function SignInPage() {
  const config = loadAuthConfig();

  return (
    <AuthShell
      title="Sign in to Signora"
      description="AI Revenue Intelligence"
      footer={
        <>
          New here? <AuthLink href="/sign-up">Create an account</AuthLink>
        </>
      }
    >
      <SignInForm
        passwordEnabled={config.passwordEnabled}
        oauthMethods={oauthMethods(config)}
      />
      {config.passwordEnabled ? (
        <p className="text-sm text-content-muted">
          <AuthLink href="/forgot-password">Forgot your password?</AuthLink>
        </p>
      ) : null}
    </AuthShell>
  );
}
