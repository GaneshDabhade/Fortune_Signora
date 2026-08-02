/**
 * What a customer is told when connecting a system, in every outcome.
 *
 * **Every failure answers three questions**: what happened, why it happened,
 * and what to do next. A message answering fewer is a message that leaves
 * somebody stuck with a screenshot and a support ticket.
 *
 * **No OAuth terminology reaches any of these strings.** A customer did not
 * fail an authorization-code exchange; they closed a window, or they lack an
 * admin's permission, or HubSpot is having a bad afternoon. The mechanics are
 * the adapter's business and the domain deliberately does not name them
 * ([ADR-0034](../../docs/architecture/adr/0034-ubiquitous-language.md)).
 *
 * **The `recoverable` flag is what the screen acts on**, not the code. A
 * customer who can simply try again should see one button; one who needs
 * somebody else's permission should not be invited to press it repeatedly.
 */

export type ConnectOutcomeCode =
  | 'connected'
  | 'cancelled'
  | 'insufficient_permission'
  | 'authorization_expired'
  | 'already_connected'
  | 'unsupported_account'
  | 'provider_unavailable'
  | 'provider_error'
  | 'unknown';

export interface ConnectOutcome {
  /** What happened, in one line a customer reads first. */
  what: string;
  /** Why it happened. Absent for success — nothing to explain. */
  why?: string;
  /** What to do next. **Always present on a failure.** */
  next?: string;
  /** Whether trying again could plausibly work. Drives the button, not the copy. */
  recoverable: boolean;
}

export const CONNECT_OUTCOMES: Record<ConnectOutcomeCode, ConnectOutcome> = {
  connected: {
    what: 'Connected.',
    recoverable: false,
  },

  cancelled: {
    what: 'Connecting was cancelled.',
    // Not framed as an error. The commonest reason for landing here is that
    // somebody changed their mind, and telling them something went wrong when
    // they made a choice is the product misreading them.
    why: 'The window closed before you finished, or you chose not to continue.',
    next: 'You can start again whenever you are ready. Nothing was changed.',
    recoverable: true,
  },

  insufficient_permission: {
    what: 'Your account does not have permission to connect this.',
    why: 'Connecting requires an administrator on the other system, and this account is not one.',
    // The specific fix, because "contact your administrator" without saying
    // what to ask for makes the customer relay a problem they do not
    // understand.
    next: 'Ask an administrator to connect it, or to give your account permission to.',
    recoverable: false,
  },

  authorization_expired: {
    what: 'That took too long and had to be restarted.',
    why: 'For your security, the other system only allows a few minutes to finish connecting.',
    next: 'Start again. It usually takes under a minute.',
    recoverable: true,
  },

  already_connected: {
    what: 'That account is already connected.',
    why: 'Signora is already receiving information from it.',
    // Directs somewhere useful rather than merely refusing. A customer who
    // reached this screen was trying to achieve something.
    next: 'If it is not working, disconnect it and connect it again.',
    recoverable: false,
  },

  unsupported_account: {
    what: 'That kind of account cannot be connected.',
    why: 'Signora needs an account that can read the information it works from, and this one cannot.',
    next: 'Try a different account, or ask an administrator which one to use.',
    recoverable: false,
  },

  provider_unavailable: {
    what: 'The other system is not responding.',
    // Deliberately explicit that this is not the customer's fault. The
    // alternative is somebody spending an afternoon checking their own
    // settings.
    why: 'This is a problem on their side, not with your account or with Signora.',
    next: 'Try again in a few minutes. Nothing was changed.',
    recoverable: true,
  },

  provider_error: {
    what: 'The other system refused the connection.',
    why: 'It did not say why. This is usually temporary.',
    next: 'Try again. If it keeps happening, an administrator on that system can check whether Signora is allowed.',
    recoverable: true,
  },

  unknown: {
    // The catch-all still answers all three questions. A generic "something
    // went wrong" is the failure this whole file exists to avoid.
    what: 'Connecting did not finish.',
    why: 'Something went wrong that Signora could not identify.',
    next: 'Try again. If it keeps happening, tell us and we will look.',
    recoverable: true,
  },
};

/** The outcome for a code, falling back to one that still explains itself. */
export function outcomeFor(code: string): ConnectOutcome {
  return CONNECT_OUTCOMES[code as ConnectOutcomeCode] ?? CONNECT_OUTCOMES.unknown;
}
