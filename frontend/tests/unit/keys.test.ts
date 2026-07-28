/**
 * Signing-key management tests.
 *
 * The key-pair-mismatch case is the one worth having: both keys load, every
 * token mints successfully, and every API request 401s with no obvious
 * cause. Catching it at startup turns a baffling outage into a clear
 * configuration error.
 */

import { describe, expect, it } from 'vitest';
import { generateKeyPair, exportPKCS8, exportSPKI } from 'jose';

import {
  checkKeyHealth,
  loadPrivateKey,
  loadPublicKey,
  normalizePem,
  SigningKeyError,
} from '@/lib/auth/keys';

async function pemPair() {
  const { privateKey, publicKey } = await generateKeyPair('RS256', {
    modulusLength: 2048,
    extractable: true,
  });
  return {
    privatePem: await exportPKCS8(privateKey),
    publicPem: await exportSPKI(publicKey),
  };
}

describe('normalizePem', () => {
  it('restores newlines flattened by a secret manager', () => {
    // Secret managers and CI systems routinely flatten PEMs to \n escapes.
    const flattened = '-----BEGIN PUBLIC KEY-----\\nABC\\n-----END PUBLIC KEY-----';

    expect(normalizePem(flattened)).toContain('\n');
    expect(normalizePem(flattened)).not.toContain('\\n');
  });

  it('leaves an already-multiline PEM untouched', () => {
    const pem = '-----BEGIN PUBLIC KEY-----\nABC\n-----END PUBLIC KEY-----';

    expect(normalizePem(pem)).toBe(pem);
  });
});

describe('key loading', () => {
  it('loads a valid private key', async () => {
    const { privatePem } = await pemPair();

    await expect(loadPrivateKey(privatePem)).resolves.toBeDefined();
  });

  it('rejects a missing private key with actionable guidance', async () => {
    await expect(loadPrivateKey(undefined)).rejects.toThrow(SigningKeyError);
    await expect(loadPrivateKey(undefined)).rejects.toThrow(/keys:generate/);
  });

  it('rejects a public key supplied where a private key is expected', async () => {
    const { publicPem } = await pemPair();

    await expect(loadPrivateKey(publicPem)).rejects.toThrow(SigningKeyError);
  });

  it('rejects a private key supplied where a public key is expected', async () => {
    const { privatePem } = await pemPair();

    await expect(loadPublicKey(privatePem)).rejects.toThrow(SigningKeyError);
  });

  it('rejects garbage', async () => {
    await expect(loadPublicKey('not-a-key')).rejects.toThrow(SigningKeyError);
  });
});

describe('checkKeyHealth', () => {
  it('reports a matching pair as healthy', async () => {
    const { privatePem, publicPem } = await pemPair();

    const health = await checkKeyHealth(privatePem, publicPem);

    expect(health).toMatchObject({
      privateKeyLoaded: true,
      publicKeyLoaded: true,
      keyPairMatches: true,
    });
    expect(health.error).toBeUndefined();
  });

  it('detects a mismatched pair', async () => {
    const { privatePem } = await pemPair();
    const { publicPem: unrelatedPublic } = await pemPair();

    const health = await checkKeyHealth(privatePem, unrelatedPublic);

    expect(health.privateKeyLoaded).toBe(true);
    expect(health.publicKeyLoaded).toBe(true);
    expect(health.keyPairMatches).toBe(false);
    expect(health.error).toMatch(/does not verify/);
  });

  it('reports a missing private key without claiming the pair matches', async () => {
    const { publicPem } = await pemPair();

    const health = await checkKeyHealth(undefined, publicPem);

    expect(health.privateKeyLoaded).toBe(false);
    expect(health.keyPairMatches).toBe(false);
  });
});
