/**
 * RS256 signing-key management.
 *
 * The asymmetry is the point (ADR-0026): Next.js holds the private key and
 * is the only tier that can mint a token; FastAPI holds only the public half
 * and is cryptographically incapable of issuing one it would accept. A
 * read-only compromise of API configuration therefore cannot become identity
 * forgery.
 *
 * Keys are loaded from configuration, never from disk at runtime and never
 * generated on the fly — a key that regenerates on restart would invalidate
 * every live session and, worse, would mean no two instances agreed on
 * identity.
 */

import { importPKCS8, importSPKI, type KeyLike } from 'jose';

export const JWT_ALGORITHM = 'RS256' as const;

/** Minimum acceptable RSA modulus. 2048 is the floor for RS256 to be
 * meaningful; anything smaller is a configuration mistake worth failing on
 * rather than warning about. */
const MIN_KEY_BITS = 2048;

export class SigningKeyError extends Error {
  constructor(message: string) {
    super(message);
    this.name = 'SigningKeyError';
  }
}

/**
 * Normalises a PEM supplied through an environment variable.
 *
 * Multi-line PEMs are routinely flattened to `\n` escapes by secret managers
 * and CI systems. Handling that here rather than at each call site avoids a
 * confusing "invalid key" failure whose real cause is transport encoding.
 */
export function normalizePem(raw: string): string {
  return raw.includes('\\n') ? raw.replace(/\\n/g, '\n') : raw;
}

function assertPemShape(pem: string, marker: string, label: string): void {
  if (!pem.includes(`BEGIN ${marker}`)) {
    throw new SigningKeyError(
      `${label} is not a valid PEM: expected a "BEGIN ${marker}" block.`,
    );
  }
}

/**
 * Loads the private signing key.
 *
 * Server-only. Importing this into a client bundle would ship the private
 * key to every browser, so the guard below is a hard failure rather than a
 * warning.
 */
export async function loadPrivateKey(pem: string | undefined): Promise<KeyLike> {
  if (typeof window !== 'undefined') {
    throw new SigningKeyError(
      'The private signing key must never be loaded in a browser.',
    );
  }
  if (!pem) {
    throw new SigningKeyError(
      'SIGNORA_JWT_PRIVATE_KEY is not configured. Run `npm run keys:generate` for local development.',
    );
  }
  const normalized = normalizePem(pem);
  assertPemShape(normalized, 'PRIVATE KEY', 'SIGNORA_JWT_PRIVATE_KEY');
  try {
    return await importPKCS8(normalized, JWT_ALGORITHM);
  } catch {
    // The underlying parse error is deliberately not surfaced: jose's
    // messages can echo key material.
    throw new SigningKeyError(
      `SIGNORA_JWT_PRIVATE_KEY could not be parsed as ${JWT_ALGORITHM}.`,
    );
  }
}

export async function loadPublicKey(pem: string | undefined): Promise<KeyLike> {
  if (!pem) {
    throw new SigningKeyError('SIGNORA_JWT_PUBLIC_KEY is not configured.');
  }
  const normalized = normalizePem(pem);
  assertPemShape(normalized, 'PUBLIC KEY', 'SIGNORA_JWT_PUBLIC_KEY');
  try {
    return await importSPKI(normalized, JWT_ALGORITHM);
  } catch {
    throw new SigningKeyError(
      `SIGNORA_JWT_PUBLIC_KEY could not be parsed as ${JWT_ALGORITHM}.`,
    );
  }
}

export interface KeyHealth {
  privateKeyLoaded: boolean;
  publicKeyLoaded: boolean;
  keyPairMatches: boolean;
  error?: string;
}

/**
 * Verifies the configured key pair is usable *and* that the two halves match.
 *
 * A mismatched pair is the failure this exists to catch: both keys load
 * cleanly, every token mints successfully, and every request 401s at the API
 * with no obvious cause. Detecting it at startup turns a baffling outage into
 * a clear configuration error.
 *
 * Implemented as a sign-then-verify round trip rather than by comparing key
 * material, because that is the property that actually matters.
 */
export async function checkKeyHealth(
  privatePem: string | undefined,
  publicPem: string | undefined,
): Promise<KeyHealth> {
  const health: KeyHealth = {
    privateKeyLoaded: false,
    publicKeyLoaded: false,
    keyPairMatches: false,
  };

  let privateKey: KeyLike;
  let publicKey: KeyLike;

  try {
    privateKey = await loadPrivateKey(privatePem);
    health.privateKeyLoaded = true;
  } catch (error) {
    health.error = error instanceof Error ? error.message : 'private key unavailable';
    return health;
  }

  try {
    publicKey = await loadPublicKey(publicPem);
    health.publicKeyLoaded = true;
  } catch (error) {
    health.error = error instanceof Error ? error.message : 'public key unavailable';
    return health;
  }

  try {
    const { SignJWT, jwtVerify } = await import('jose');
    const probe = await new SignJWT({ probe: true })
      .setProtectedHeader({ alg: JWT_ALGORITHM })
      .setIssuedAt()
      .setExpirationTime('1m')
      .sign(privateKey);
    await jwtVerify(probe, publicKey, { algorithms: [JWT_ALGORITHM] });
    health.keyPairMatches = true;
  } catch {
    health.error =
      'The configured public key does not verify tokens signed by the configured private key.';
  }

  return health;
}

export { MIN_KEY_BITS };
