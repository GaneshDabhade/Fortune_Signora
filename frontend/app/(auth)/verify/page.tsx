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
      title="Verify your email"
      description={
        email
          ? // ⚠️ **The design says *"Enter the 6-digit code we sent to…"*.**
            // This sends a link, and the sentence says the true thing rather
            // than the designed one — C-241. Same shape, same address in the
            // same place; only the instrument differs, and it differs because
            // `email-otp` is installed and unregistered.
            `We sent a link to ${email}. Follow it and you will be signed in.`
          : 'We sent you a link. Follow it and you will be signed in.'
      }
      // The design's own words under the control: *"Didn't get it?"*
      footer={
        <>
          Wrong address? <AuthLink href="/register">Use a different email</AuthLink>
        </>
      }
    >
      <ResendVerification email={email ?? null} />
    </AuthShell>
  );
}
