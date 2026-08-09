import { ServiceStatus } from '@/components/auth/service-status';
import { loadAuthConfig, oauthMethods } from '@/lib/auth/config';

import { AuthLink, AuthShell } from '../auth-shell';
import { SignInForm } from './signin-form';

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
    // ⚠️ **No subline.** The design's is *"to Northwind Global"* — the
    // **organization**, which nothing knows before the person authenticates.
    // Substituting the product name would have kept the shape and thrown away
    // the meaning, so the line is omitted rather than filled (P-A).
    <AuthShell
      title="Sign in"
      footer={
        <>
          New here? <AuthLink href="/register">Create an account</AuthLink>
        </>
      }
      region={<ServiceStatus />}
    >
      <SignInForm
        passwordEnabled={config.passwordEnabled}
        oauthMethods={oauthMethods(config)}
      />
      {/* 🔴 **The second recovery link is gone.** Milestone 2 put *Forgot
          password?* beside the password field where the design has it, and
          left this one below the button — **two links to one destination,
          nine lines apart.** The design has exactly one. */}
    </AuthShell>
  );
}
