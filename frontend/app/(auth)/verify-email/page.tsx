import { AuthLink, AuthShell } from '../auth-shell';
import { ResendVerification } from './resend';

/**
 * The step between signing up and signing in.
 *
 * **A real gate, not a courtesy screen.** `requireEmailVerification` is on, so
 * a session does not exist until the link is followed — which is what turns
 * `email_verified` from an assertion an identity provider made into a fact
 * Signora established (ADR-0033).
 *
 * In local development the link is written to the dev server's output rather
 * than sent. **The flow is not shortened** — real token, real expiry, real
 * Better Auth route — only the transport differs.
 */
export default async function VerifyEmailPage({
  searchParams,
}: {
  searchParams: Promise<{ email?: string }>;
}) {
  const { email } = await searchParams;

  return (
    <AuthShell
      title="Confirm your email"
      description={
        email
          ? `We sent a link to ${email}. Follow it and you will be signed in.`
          : 'We sent you a link. Follow it and you will be signed in.'
      }
      footer={<AuthLink href="/sign-in">Back to sign in</AuthLink>}
    >
      <ResendVerification email={email ?? null} />
    </AuthShell>
  );
}
