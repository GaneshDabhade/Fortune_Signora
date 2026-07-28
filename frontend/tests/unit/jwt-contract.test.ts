/**
 * JWT contract tests.
 *
 * These assert the claim set matches 18-authentication.md exactly. A drift
 * here is not a degraded experience — the Python verifier requires every
 * mandatory claim and rejects the token outright, so a missing field is a
 * total authentication outage.
 *
 * The definitive check is `tests/contract/` in CI, which mints a token here
 * and verifies it with the real Python verifier. These tests catch drift
 * earlier and more precisely.
 */

import { describe, expect, it } from 'vitest';
import { generateKeyPair, decodeJwt, decodeProtectedHeader, jwtVerify } from 'jose';

import { buildClaims, issueAccessToken, ACCESS_TOKEN_TTL_SECONDS } from '@/lib/auth/jwt';

const ISSUER = 'https://auth.signora.test';
const AUDIENCE = 'signora-api-test';

async function keys() {
  return generateKeyPair('RS256', { modulusLength: 2048, extractable: true });
}

const subject = {
  userId: '3f6c8a1e-0000-4000-8000-000000000001',
  sessionId: 'sess_abc123',
  email: 'rep@customer.test',
  emailVerified: true,
  activeWorkspaceId: '8b0f2c4d-0000-4000-8000-000000000002',
};

describe('claim contract', () => {
  it('emits every required claim with the documented names', () => {
    const claims = buildClaims(subject);

    expect(claims.sub).toBe(subject.userId);
    expect(claims.sid).toBe(subject.sessionId);
    expect(claims.email).toBe(subject.email);
    expect(claims.email_verified).toBe(true);
    expect(claims.active_workspace_id).toBe(subject.activeWorkspaceId);
    expect(claims.jti).toMatch(/^[0-9a-f-]{36}$/);
  });

  it('omits active_workspace_id when no workspace is selected', () => {
    // Absent immediately after sign-in. Omitted rather than null so neither
    // side needs to special-case it.
    const claims = buildClaims({ ...subject, activeWorkspaceId: null });

    expect(claims).not.toHaveProperty('active_workspace_id');
  });

  it('carries no permissions or capabilities', () => {
    // Casbin is the single source of authorization truth (ADR-0010).
    // Embedding permissions would fork that logic and delay every policy
    // change until tokens expire.
    const claims = buildClaims(subject) as unknown as Record<string, unknown>;

    for (const forbidden of [
      'permissions',
      'roles',
      'scopes',
      'capabilities',
      'policy',
    ]) {
      expect(claims).not.toHaveProperty(forbidden);
    }
  });

  it('carries no workspace membership list', () => {
    // A list would be unbounded, would grow staler the longer it is, and
    // could never be authoritative — the API re-verifies membership anyway.
    const claims = buildClaims(subject) as unknown as Record<string, unknown>;

    expect(claims).not.toHaveProperty('workspaces');
    expect(claims).not.toHaveProperty('workspace_memberships');
    expect(claims).not.toHaveProperty('memberships');
  });

  it('generates a unique jti per token', () => {
    expect(buildClaims(subject).jti).not.toBe(buildClaims(subject).jti);
  });
});

describe('token issuance', () => {
  it('signs with RS256 and pins the header', async () => {
    const { privateKey } = await keys();

    const token = await issueAccessToken(subject, {
      issuer: ISSUER,
      audience: AUDIENCE,
      privateKey,
    });

    expect(decodeProtectedHeader(token).alg).toBe('RS256');
    expect(decodeProtectedHeader(token).typ).toBe('JWT');
  });

  it('sets issuer, audience, iat and a 15-minute exp', async () => {
    const { privateKey } = await keys();
    const now = new Date('2026-07-28T12:00:00Z');

    const token = await issueAccessToken(
      subject,
      { issuer: ISSUER, audience: AUDIENCE, privateKey },
      now,
    );

    const claims = decodeJwt(token);
    const issuedAt = Math.floor(now.getTime() / 1000);
    expect(claims.iss).toBe(ISSUER);
    expect(claims.aud).toBe(AUDIENCE);
    expect(claims.iat).toBe(issuedAt);
    expect(claims.exp).toBe(issuedAt + ACCESS_TOKEN_TTL_SECONDS);
    expect(ACCESS_TOKEN_TTL_SECONDS).toBe(900);
  });

  it('produces a token its own public key verifies', async () => {
    const { privateKey, publicKey } = await keys();

    const token = await issueAccessToken(subject, {
      issuer: ISSUER,
      audience: AUDIENCE,
      privateKey,
    });

    const { payload } = await jwtVerify(token, publicKey, {
      issuer: ISSUER,
      audience: AUDIENCE,
      algorithms: ['RS256'],
    });
    expect(payload.sub).toBe(subject.userId);
  });

  it('is rejected by a different public key', async () => {
    const { privateKey } = await keys();
    const { publicKey: otherPublic } = await keys();

    const token = await issueAccessToken(subject, {
      issuer: ISSUER,
      audience: AUDIENCE,
      privateKey,
    });

    await expect(
      jwtVerify(token, otherPublic, { algorithms: ['RS256'] }),
    ).rejects.toThrow();
  });
});
