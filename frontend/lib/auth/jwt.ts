/**
 * RS256 JWT issuance — the Next.js half of the boundary in ADR-0026.
 *
 * The claim set here is a contract, not an implementation detail. The Python
 * verifier requires every claim marked required in 18-authentication.md and
 * rejects the token outright if one is missing, so a change on this side that
 * is not mirrored there produces a total authentication outage rather than a
 * degraded experience.
 *
 * `tests/unit/jwt-contract.test.ts` asserts the shape; the cross-tier
 * contract test in CI mints a token here and verifies it with the real Python
 * verifier, which is the only check that actually proves the two agree.
 */

import { SignJWT, type KeyLike } from 'jose';

import { JWT_ALGORITHM } from '@/lib/auth/keys';

/**
 * Access-token lifetime.
 *
 * Short by design: the JWT boundary trades immediate revocation for stateless
 * verification, and 15 minutes bounds that exposure. `sid` and `jti` are
 * carried so a revocation list can be added later without a contract change
 * (ADR-0026, Tradeoffs).
 */
export const ACCESS_TOKEN_TTL_SECONDS = 15 * 60;

export interface TokenSubject {
  userId: string;
  sessionId: string;
  email: string;
  emailVerified: boolean;
  /**
   * The workspace the user has selected, if any.
   *
   * **A routing hint, never a grant.** The API re-verifies membership against
   * Workspace & Tenancy on every request, so a stale or forged value here
   * grants nothing. Null immediately after sign-in, before a workspace is
   * chosen or created.
   */
  activeWorkspaceId: string | null;
}

export interface IssuerConfig {
  issuer: string;
  audience: string;
  privateKey: KeyLike;
}

/** The exact claim set the Python verifier expects. Field names are the wire
 * contract — they are snake_case because that is what 19-api-conventions.md
 * specifies, not because of any JS convention. */
export interface SignoraClaims {
  sub: string;
  sid: string;
  email: string;
  email_verified: boolean;
  active_workspace_id?: string;
  jti: string;
}

export function buildClaims(subject: TokenSubject): SignoraClaims {
  const claims: SignoraClaims = {
    sub: subject.userId,
    sid: subject.sessionId,
    email: subject.email,
    email_verified: subject.emailVerified,
    jti: crypto.randomUUID(),
  };

  // Omitted rather than sent as null when absent: the verifier treats the
  // claim as optional, and an explicit null would need special-casing on
  // both sides for no benefit.
  if (subject.activeWorkspaceId) {
    claims.active_workspace_id = subject.activeWorkspaceId;
  }

  return claims;
}

/**
 * Mints an access token for a subject.
 *
 * Deliberately carries no permission or capability claims. Casbin is the
 * single source of authorization truth (ADR-0010), and embedding permissions
 * would fork that logic across two systems while delaying every policy change
 * until tokens expire.
 *
 * Deliberately carries no workspace *membership list* either — only the
 * single active workspace. A list would be unbounded, would grow staler the
 * longer it is, and could never be authoritative anyway, since the API
 * re-verifies membership server-side regardless.
 */
export async function issueAccessToken(
  subject: TokenSubject,
  config: IssuerConfig,
  now: Date = new Date(),
): Promise<string> {
  const issuedAt = Math.floor(now.getTime() / 1000);

  return new SignJWT({ ...buildClaims(subject) })
    .setProtectedHeader({ alg: JWT_ALGORITHM, typ: 'JWT' })
    .setIssuer(config.issuer)
    .setAudience(config.audience)
    .setIssuedAt(issuedAt)
    .setExpirationTime(issuedAt + ACCESS_TOKEN_TTL_SECONDS)
    .sign(config.privateKey);
}
