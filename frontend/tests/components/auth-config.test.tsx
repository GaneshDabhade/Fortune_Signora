/**
 * Two auth values have no safe default, and the config must refuse rather than guess.
 *
 * **This is [B-104](../../../docs/BUGS.md), asserted.** `required(name, fallback)`
 * was a lie: with a fallback supplied it could never throw. Two of the six
 * values that used it were dangerous.
 *
 * * **The auth database** silently became the *shared* `signora`, so an
 *   environment that had not set the variable wrote Better Auth users into
 *   whatever else was using that database. **That happened.**
 * * **The signing secret** silently became a string committed to this
 *   repository, so any clone that had not set it minted JWTs every other clone
 *   could forge.
 *
 * **A URL with a wrong default fails loudly and immediately; a database with a
 * wrong default fails silently and permanently.** That asymmetry is why two
 * values refuse and the rest keep a development default.
 */

import { afterEach, beforeEach, describe, expect, it } from 'vitest';

import { loadAuthConfig } from '@/lib/auth/config';

const REQUIRED = {
  SIGNORA_AUTH_DATABASE_URL: 'postgresql://signora_auth:pw@localhost:5432/signora_review',
  BETTER_AUTH_SECRET: 'a-secret-this-environment-actually-set',
};

let saved: NodeJS.ProcessEnv;

beforeEach(() => {
  saved = { ...process.env };
  for (const [name, value] of Object.entries(REQUIRED)) process.env[name] = value;
});

afterEach(() => {
  process.env = saved;
});

describe('values with no safe default', () => {
  it('refuses to load without an auth database', () => {
    delete process.env.SIGNORA_AUTH_DATABASE_URL;

    expect(() => loadAuthConfig()).toThrow(/SIGNORA_AUTH_DATABASE_URL is required/);
  });

  it('refuses to load without a signing secret', () => {
    delete process.env.BETTER_AUTH_SECRET;

    expect(() => loadAuthConfig()).toThrow(/BETTER_AUTH_SECRET is required/);
  });

  it('never falls back to the shared database', () => {
    // The exact string that caused the incident. If it ever reappears as a
    // default, this fails — regardless of how the fallback is spelled.
    delete process.env.SIGNORA_AUTH_DATABASE_URL;

    expect(() => loadAuthConfig()).toThrow();
    expect(() => loadAuthConfig()).not.toThrow(/signora_review/);
  });

  it('says where to find the right value, rather than only that it is missing', () => {
    delete process.env.BETTER_AUTH_SECRET;

    // An operator told only "missing" goes hunting. B-022's lesson, applied.
    expect(() => loadAuthConfig()).toThrow(/RUNNING\.md/);
  });

  it('loads when both are provided', () => {
    const config = loadAuthConfig();

    expect(config.databaseUrl).toBe(REQUIRED.SIGNORA_AUTH_DATABASE_URL);
    expect(config.betterAuthSecret).toBe(REQUIRED.BETTER_AUTH_SECRET);
  });
});

describe('values whose default is harmless', () => {
  it('a first clone still runs without every URL configured', () => {
    delete process.env.SIGNORA_APP_URL;
    delete process.env.SIGNORA_API_URL;
    delete process.env.SIGNORA_JWT_ISSUER;

    const config = loadAuthConfig();

    expect(config.baseUrl).toBe('http://localhost:3000');
    expect(config.apiBaseUrl).toBe('http://localhost:8000');
  });

  it('an explicit value always wins over the development default', () => {
    process.env.SIGNORA_APP_URL = 'http://localhost:3400';

    expect(loadAuthConfig().baseUrl).toBe('http://localhost:3400');
  });
});
