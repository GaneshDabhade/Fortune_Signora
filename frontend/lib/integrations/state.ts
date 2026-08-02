/**
 * The value that makes a returning customer provably the one who left.
 *
 * **This is the security of the acquisition flow.** A callback is an
 * unauthenticated request arriving from a third party with a code in the query
 * string; without a state that Signora issued and can verify, anybody able to
 * make a browser hit that URL could cause a connection to be created in
 * somebody else's organization.
 *
 * Four properties, and each exists because of a specific failure:
 *
 * **Signed** — so a value cannot be forged. The signature covers every field,
 * so a tampered workspace or slug fails verification rather than quietly
 * connecting the wrong thing.
 *
 * **Expiring** — because a customer who left a tab open for a day and returned
 * should start again rather than complete a flow nobody remembers beginning.
 *
 * **Bound to a nonce** — so a replayed callback is detectable. The nonce is
 * held in a single-use cookie; the second arrival of one callback finds no
 * cookie and is refused.
 *
 * **Opaque to the provider** — it carries no secret, only identifiers the
 * customer already has, so a provider logging the state parameter leaks
 * nothing.
 */

import { createHmac, randomBytes, timingSafeEqual } from 'node:crypto';

/** How long a customer has to finish. Long enough to read a consent screen,
 * short enough that an abandoned tab cannot be completed later. */
export const STATE_TTL_MS = 10 * 60 * 1000;

export interface AcquisitionState {
  slug: string;
  workspaceId: string;
  nonce: string;
  issuedAt: number;
}

export type StateFailure =
  | 'malformed'
  | 'bad_signature'
  | 'expired'
  | 'replayed'
  | 'mismatched';

export type StateResult =
  | { ok: true; state: AcquisitionState }
  | { ok: false; failure: StateFailure };

function sign(payload: string, secret: string): string {
  return createHmac('sha256', secret).update(payload).digest('base64url');
}

export function issueState(
  slug: string,
  workspaceId: string,
  secret: string,
  now: number = Date.now(),
): { value: string; nonce: string } {
  const nonce = randomBytes(16).toString('base64url');
  const payload = JSON.stringify({ slug, workspaceId, nonce, issuedAt: now });
  const encoded = Buffer.from(payload).toString('base64url');
  return { value: `${encoded}.${sign(encoded, secret)}`, nonce };
}

/**
 * Verify a returning state against the nonce Signora stored when it issued one.
 *
 * `expectedNonce` is `null` when the cookie is absent — which is what a
 * replayed callback looks like, because the cookie is cleared on first use.
 */
export function verifyState(
  value: string | null,
  expectedNonce: string | null,
  secret: string,
  now: number = Date.now(),
): StateResult {
  if (!value) return { ok: false, failure: 'malformed' };

  const [encoded, signature] = value.split('.');
  if (!encoded || !signature) return { ok: false, failure: 'malformed' };

  const expected = sign(encoded, secret);
  // Constant-time, because a byte-by-byte comparison of a signature is a
  // timing oracle — and the whole point of signing is that forging is hard.
  const given = Buffer.from(signature);
  const want = Buffer.from(expected);
  if (given.length !== want.length || !timingSafeEqual(given, want)) {
    return { ok: false, failure: 'bad_signature' };
  }

  let parsed: AcquisitionState;
  try {
    parsed = JSON.parse(Buffer.from(encoded, 'base64url').toString()) as AcquisitionState;
  } catch {
    return { ok: false, failure: 'malformed' };
  }
  if (
    typeof parsed.slug !== 'string' ||
    typeof parsed.workspaceId !== 'string' ||
    typeof parsed.nonce !== 'string' ||
    typeof parsed.issuedAt !== 'number'
  ) {
    return { ok: false, failure: 'malformed' };
  }

  if (now - parsed.issuedAt > STATE_TTL_MS) return { ok: false, failure: 'expired' };

  // Checked after the signature so a forged value never reaches the cookie
  // comparison, and after expiry so an old tab reads as expired rather than as
  // an attack — the customer gets the message that matches what they did.
  if (expectedNonce === null) return { ok: false, failure: 'replayed' };
  if (expectedNonce !== parsed.nonce) return { ok: false, failure: 'mismatched' };

  return { ok: true, state: parsed };
}

/**
 * What a customer is told when the state does not verify.
 *
 * **Every one maps to an outcome that explains itself.** A raw
 * `bad_signature` on a screen would tell somebody they had been attacked when
 * the likeliest cause is a bookmarked URL.
 */
export const STATE_FAILURE_OUTCOME: Record<StateFailure, string> = {
  malformed: 'unknown',
  bad_signature: 'unknown',
  expired: 'authorization_expired',
  // A second arrival of one callback is almost always a refresh or a
  // double-click, not an attack — and the connection it describes already
  // exists, which is what the customer needs to know.
  replayed: 'already_connected',
  mismatched: 'authorization_expired',
};
