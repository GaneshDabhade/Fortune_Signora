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
import { Resend } from 'resend';

import type { AuthConfig, ResendConfig } from '@/lib/auth/config';

export interface AuthEmail {
  to: string;
  /** What the recipient is being asked to do. Also what the log line is
   * labelled with, so a developer scanning output can find the right link
   * when they have triggered two flows in a row. */
  purpose: 'verify-email' | 'reset-password';
  /** The URL Better Auth built, carrying its own token. Passed through
   * untouched — a transport that rewrote a link would be able to invalidate
   * it, and the failure would look like an expired token. */
  url?: string;
  /**
   * A six-digit code, when the flow is `email-otp` rather than a link.
   *
   * ⚡ **A variant on the port rather than a second port** — [TASK-498](../../../docs/BACKLOG.md).
   * **An OTP is not a URL**, and this file's oldest rule is that what arrives
   * later must not be *"a second copy of either flow, written around whatever
   * the vendor turned out to want."* **One of `url` or `code` is present,
   * never both**, and the transport prints whichever it was given.
   */
  code?: string;
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
    `  │  ${email.code ?? email.url}`,
    '  └────────────────────────────────────────────────────────────────',
    '',
  ];
  // This transport *is* the console; the write is the delivery.
  console.log(lines.join('\n'));
};

/**
 * Delivers through **Resend**, the vendor [`09-build-vs-buy.md`](../../../docs/architecture/09-build-vs-buy.md)
 * ratified and [ADR-0015](../../../docs/architecture/adr/0015-communication-email-and-calendar-integrations.md)
 * approved — [TASK-494](../../../docs/BACKLOG.md).
 *
 * ⚡ **The URL is passed through untouched**, which this file has required
 * since it was written: *"a transport that rewrote a link would be able to
 * invalidate it, and the failure would look like an expired token."* **So the
 * link is not wrapped in click tracking**, and that is a deliberate vendor
 * setting rather than an omission — Resend rewrites URLs when tracking is on,
 * and a rewritten verification link is a broken one.
 *
 * ⛔ **A failure is raised, never swallowed.** Better Auth is awaiting this;
 * if it resolves quietly on a rejected send, the customer is told to check an
 * inbox nothing was sent to — **the silent failure the console guard exists
 * to prevent, arriving through the vendor instead.**
 */
function createResendTransport(config: ResendConfig): AuthEmailTransport {
  // Constructed once, outside the returned closure: the client is a thin
  // wrapper over `fetch` and rebuilding it per send would be work per email
  // for no isolation.
  const client = new Resend(config.apiKey);

  return async (email) => {
    const { error } = await client.emails.send({
      from: config.from,
      to: email.to,
      subject: PROMPT[email.purpose],
      // **Plain text, and this is the honest limit of this row.** The design
      // snapshot has no email template — screen `07` draws the *code entry*,
      // not the message — and inventing a branded HTML email would be
      // designing a customer-visible surface nobody approved (§21).
      // ⚡ **The link is what the flow needs and it is here in full.**
      // The code stands alone; the link needs no prose either. Whichever
      // arrived is what the recipient needs, and nothing else is invented.
      text: `${PROMPT[email.purpose]}:\n\n${email.code ?? email.url}\n`,
    });

    if (error) {
      // The vendor's own words. A second phrasing here would be the message
      // nobody maintains, and this one reaches a log rather than a customer.
      throw new Error(`Resend refused to deliver a ${email.purpose} email: ${error.message}`);
    }
  };
}

/**
 * The transport this build will use.
 *
 * ⚡ **Now a real selection, and it reads the resolved configuration rather
 * than the environment.** This function used to document why it did *not*
 * branch — *"a branch that cannot fail is Decorative Logic"* — and predicted
 * exactly this change: *"adding a vendor adds a member to the union and a
 * case here, and every caller is already passing what that case will need."*
 * **Every caller was; none of them changed.**
 *
 * ⛔ **`config.resend` is non-null whenever the name is `resend`**, because
 * `loadAuthConfig` resolves the credential at startup. The throw below is
 * therefore unreachable through `loadAuthConfig` and exists for the one
 * caller that constructs an `AuthConfig` by hand — a test — where a silent
 * fallback to the console would make a suite pass while asserting the wrong
 * transport.
 */
export function createEmailTransport(config: AuthConfig): AuthEmailTransport {
  const deliver =
    config.emailTransport === 'resend'
      ? createResendTransport(
          config.resend ??
            (() => {
              throw new Error(
                "emailTransport is 'resend' and no Resend configuration was resolved.",
              );
            })(),
        )
      : consoleTransport;

  return async (email) => {
    // Recorded before delivery and without the URL. The event says an address
    // was asked to do something; the link is a credential and belongs in
    // neither an event nor a log line that outlives the request.
    emitAuthEvent(
      email.purpose === 'verify-email'
        ? AUTH_EVENTS.VERIFICATION_REQUESTED
        : AUTH_EVENTS.PASSWORD_RESET_REQUESTED,
    );
    await deliver(email);
  };
}
