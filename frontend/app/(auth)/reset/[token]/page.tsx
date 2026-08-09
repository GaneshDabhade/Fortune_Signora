import { notFound } from 'next/navigation';

import { loadAuthConfig } from '@/lib/auth/config';

import { AuthLink, AuthShell } from '../../auth-shell';
import { ResetPasswordForm } from './reset-password-form';

/**
 * **Reads runtime configuration, so it must never be prerendered** — the same
 * rule `/signin`, `/register` and `/forgot-password` already follow (§20b,
 * environment-based configuration).
 *
 * This page and `/verify` were the two that did not, and the gap was
 * invisible: `loadAuthConfig()` had fallbacks, so prerendering silently
 * succeeded against a database and a secret belonging to no environment in
 * particular ([B-104](../../../../docs/BUGS.md)).
 */
export const dynamic = 'force-dynamic';

/**
 * Set a new password.
 *
 * Reached from the emailed link. **The token is a PATH segment, not a query
 * parameter** — [TASK-499](../../../../docs/BACKLOG.md), on
 * [D-185](../../../../docs/DECISION_REGISTER.md) §2's `/reset/:token`.
 *
 * ### ⚡ Why the shape changed and not only the name
 *
 * ⛔ **A query parameter is the framework's habit, not the product's.** 📁 D-185
 * §2: *"do not optimize around today's implementation convenience. Optimize for
 * the long-term product experience."* **A path says the token identifies the
 * thing being reset; a query string says it modifies a page that exists
 * without it** — and this page does not.
 *
 * ⚠️ **`better-auth` emits the link, so the callback URL moved with it**
 * ([`lib/auth/server.ts`](../../../../lib/auth/server.ts)). **A rename that
 * left the emitter behind would send every customer to a dead link**, which
 * is the one failure this row could plausibly ship.
 *
 * **A visit with no token is a dead link** and the screen says so rather than
 * rendering a form that cannot succeed — ⚡ **and with the token in the path,
 * `/reset` with nothing after it no longer matches this route at all**, so the
 * empty case is now the router's rather than a branch here. **The branch stays
 * for `error`**, which `better-auth` still returns as a query parameter.
 */
export default async function ResetPasswordPage({
  params,
  searchParams,
}: {
  params: Promise<{ token: string }>;
  searchParams: Promise<{ error?: string; email?: string }>;
}) {
  if (!loadAuthConfig().passwordEnabled) notFound();
  const { token } = await params;
  const { error, email } = await searchParams;

  if (!token || error) {
    return (
      <AuthShell
        title="That link has expired"
        // The third place the expiry is stated to a customer, and the one
        // easiest to miss — C-243's ruling moves all three or none.
        description="Reset links last 30 minutes and can be used once. Ask for another and it will work."
        footer={<AuthLink href="/signin">Back to sign in</AuthLink>}
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
      footer={<AuthLink href="/signin">Back to sign in</AuthLink>}
    >
      <ResetPasswordForm token={token} email={email ?? null} />
    </AuthShell>
  );
}
