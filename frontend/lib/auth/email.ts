/**
 * How a verification or password-reset link leaves the process.
 *
 * **A port with one implementation, and it earns the shape rather than
 * anticipating one.** Two flows need to deliver a link today — email
 * verification and password reset — and neither can be built without an
 * answer. What arrives later is a vendor, which is a dependency decision and
 * its own ADR (ADR-0033); what must not arrive later is a second copy of
 * either flow, written around whatever the vendor turned out to want.
 *
 * **Nothing here is mocked.** Better Auth mints a real token with a real
 * expiry and builds a real URL; this decides where that URL goes. A test
 * mints a real JWT rather than skipping verification for the same reason —
 * the flow under review has to be the flow that ships.
 */

import { AUTH_EVENTS, emitAuthEvent } from '@/lib/auth/events';
import type { AuthConfig } from '@/lib/auth/config';

export interface AuthEmail {
  to: string;
  /** What the recipient is being asked to do. Also what the log line is
   * labelled with, so a developer scanning output can find the right link
   * when they have triggered two flows in a row. */
  purpose: 'verify-email' | 'reset-password';
  /** The URL Better Auth built, carrying its own token. Passed through
   * untouched — a transport that rewrote a link would be able to invalidate
   * it, and the failure would look like an expired token. */
  url: string;
}

export type AuthEmailTransport = (email: AuthEmail) => Promise<void>;

const PROMPT: Record<AuthEmail['purpose'], string> = {
  'verify-email': 'Verify this address to finish signing up',
  'reset-password': 'Set a new password',
};

/**
 * Writes the link to stdout, framed so it cannot be missed in a dev server's
 * output.
 *
 * **The only transport this build has**, and it refuses to exist in
 * production — enforced at configuration load, before a process starts, so a
 * misconfigured deployment stops rather than silently emailing nobody.
 */
const consoleTransport: AuthEmailTransport = async (email) => {
  const lines = [
    '',
    '  ┌────────────────────────────────────────────────────────────────',
    `  │  ${PROMPT[email.purpose]}`,
    `  │  ${email.to}`,
    '  │',
    `  │  ${email.url}`,
    '  └────────────────────────────────────────────────────────────────',
    '',
  ];
  // This transport *is* the console; the write is the delivery.
  console.log(lines.join('\n'));
};

/**
 * The transport this build will use.
 *
 * **No selection, because there is nothing to select between.**
 * `AuthEmailTransportName` has one member and `loadAuthConfig` refuses any
 * other value, so a `config.emailTransport === 'console' ? … : …` here would
 * be a branch that cannot fail — Decorative Logic, giving the impression of a
 * choice the build cannot make. The `config` parameter stays because the
 * *shape* is the point: adding a vendor adds a member to the union and a case
 * here, and every caller is already passing what that case will need.
 */
export function createEmailTransport(_config: AuthConfig): AuthEmailTransport {
  return async (email) => {
    // Recorded before delivery and without the URL. The event says an address
    // was asked to do something; the link is a credential and belongs in
    // neither an event nor a log line that outlives the request.
    emitAuthEvent(
      email.purpose === 'verify-email'
        ? AUTH_EVENTS.VERIFICATION_REQUESTED
        : AUTH_EVENTS.PASSWORD_RESET_REQUESTED,
    );
    await consoleTransport(email);
  };
}
