/**
 * Structured authentication events.
 *
 * Authentication is the one subsystem where the absence of a log is itself a
 * security finding: without these, a credential-stuffing attempt, a broken
 * OAuth callback, and a misconfigured signing key all look identical from the
 * outside — namely, silence.
 *
 * Emitted as single-line JSON matching the backend's format
 * (`signora_platform.observability.logging`), so both tiers land in one
 * queryable stream rather than two that have to be correlated by hand.
 *
 * **These events must never carry a token or PII.** A user id is an opaque
 * UUID and is safe; an email address is not. The redaction below is
 * structural rather than advisory, for the same reason it is on the Python
 * side: "remember not to log the token" holds until the one time it doesn't.
 */

export const AUTH_EVENTS = {
  LOGIN_SUCCESS: 'AUTH_LOGIN_SUCCESS',
  LOGIN_FAILURE: 'AUTH_LOGIN_FAILURE',
  TOKEN_ISSUED: 'AUTH_TOKEN_ISSUED',
  TOKEN_REFRESH: 'AUTH_TOKEN_REFRESH',
  TOKEN_REJECTED: 'AUTH_TOKEN_REJECTED',
  LOGOUT: 'AUTH_LOGOUT',
  OAUTH_CALLBACK: 'AUTH_OAUTH_CALLBACK',
  WORKSPACE_SWITCH: 'AUTH_WORKSPACE_SWITCH',
  // Both carry an address that was asked to prove something and **never the
  // link that was sent** — a verification or reset URL is a bearer credential
  // for the seconds it lives, and `sanitize` drops the field regardless.
  SIGN_UP: 'AUTH_SIGN_UP',
  VERIFICATION_REQUESTED: 'AUTH_VERIFICATION_REQUESTED',
  PASSWORD_RESET_REQUESTED: 'AUTH_PASSWORD_RESET_REQUESTED',
  PASSWORD_RESET_COMPLETED: 'AUTH_PASSWORD_RESET_COMPLETED',
} as const;

export type AuthEventName = (typeof AUTH_EVENTS)[keyof typeof AUTH_EVENTS];

/**
 * Fields an auth event may carry.
 *
 * The type is closed deliberately: an open `Record<string, unknown>` would
 * let an email address or a token be added to an event by a well-meaning
 * change, and nothing would catch it. Adding a field here is a reviewable
 * decision.
 */
export interface AuthEventContext {
  userId?: string;
  sessionId?: string;
  workspaceId?: string;
  /** How somebody signed in. **Provenance in the log and nowhere else** — it
   * is deliberately not a JWT claim, so no backend decision can ever depend
   * on it (ADR-0033). */
  provider?: 'google' | 'microsoft' | 'password';
  /** Coarse reason for a failure. Must stay coarse — a message echoing why
   * a credential was rejected helps an attacker enumerate. */
  reason?: string;
  correlationId?: string;
  tokenId?: string;
  outcome?: 'success' | 'failure';
}

/** Keys that must never appear in an auth event, regardless of how they got
 * there. Enforced at emit time rather than trusted to call sites. */
const FORBIDDEN_KEYS = /(token|password|secret|authorization|email|credential|key)/i;

const JWT_PATTERN = /\beyJ[A-Za-z0-9_-]{5,}\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+/g;

/**
 * Strips anything that must not be logged.
 *
 * `tokenId` (`jti`) is explicitly permitted — it is an opaque identifier, not
 * a credential, and it is what makes a token traceable to a revocation
 * decision later.
 */
export function sanitize(context: AuthEventContext): Record<string, unknown> {
  const safe: Record<string, unknown> = {};

  for (const [key, value] of Object.entries(context)) {
    if (value === undefined || value === null) continue;
    if (key !== 'tokenId' && FORBIDDEN_KEYS.test(key)) continue;

    safe[key] =
      typeof value === 'string' ? value.replace(JWT_PATTERN, '[REDACTED]') : value;
  }

  return safe;
}

export interface AuthEventSink {
  (line: string): void;
}

const defaultSink: AuthEventSink = (line) => {
  console.log(line);
};

/**
 * Emits an authentication event.
 *
 * `outcome` is derived from the event name rather than passed in, so a
 * failure can never be recorded as a success by a mistaken argument — the
 * kind of error that makes an audit trail actively misleading.
 */
export function emitAuthEvent(
  event: AuthEventName,
  context: AuthEventContext = {},
  sink: AuthEventSink = defaultSink,
): void {
  const isFailure =
    event === AUTH_EVENTS.LOGIN_FAILURE || event === AUTH_EVENTS.TOKEN_REJECTED;

  const payload = {
    timestamp: new Date().toISOString(),
    level: isFailure ? 'WARNING' : 'INFO',
    logger: 'signora.auth',
    message: event,
    auth_event: event,
    outcome: isFailure ? 'failure' : 'success',
    tier: 'frontend',
    ...sanitize(context),
  };

  sink(JSON.stringify(payload));
}
