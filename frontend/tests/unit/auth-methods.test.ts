/**
 * Authentication methods as configuration (ADR-0033).
 *
 * The method changes; the authenticated session does not. These assert the
 * two places that claim could quietly stop being true — what the product
 * reports as a usable sign-in method, and where a verification link goes.
 */
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

import {
  loadAuthConfig,
  oauthMethods,
  signInMethods,
  type AuthConfig,
} from '@/lib/auth/config';
import { checkAuthHealth } from '@/lib/auth/health';

const ORIGINAL = { ...process.env };

beforeEach(() => {
  vi.resetModules();
  // **The two values with no default** ([B-104](../../../docs/BUGS.md)). These
  // used to fall back — the database to the *shared* `signora`, the secret to a
  // string committed to this repository — and `loadAuthConfig()` now refuses
  // rather than guessing. This suite exercised those defaults without meaning
  // to; setting them explicitly is what it always intended.
  process.env.SIGNORA_AUTH_DATABASE_URL =
    'postgresql://signora_auth:x@localhost:5432/signora_test';
  process.env.BETTER_AUTH_SECRET = 'a-secret-this-suite-sets-explicitly';
});

afterEach(() => {
  process.env = { ...ORIGINAL };
  vi.unstubAllEnvs();
});

function config(overrides: Partial<AuthConfig> = {}): AuthConfig {
  return {
    databaseUrl: 'postgresql://signora_auth:x@localhost:5432/signora',
    authSchema: 'auth',
    baseUrl: 'http://localhost:3000',
    betterAuthSecret: 'secret',
    jwtIssuer: 'http://localhost:3000',
    jwtAudience: 'signora-api',
    jwtPrivateKey: undefined,
    jwtPublicKey: undefined,
    google: null,
    microsoft: null,
    apiBaseUrl: 'http://localhost:8000',
    passwordEnabled: true,
    emailTransport: 'console',
    resend: null,
    ...overrides,
  };
}

describe('what counts as a way to sign in', () => {
  it('reports the password method when it is enabled', () => {
    expect(signInMethods(config())).toEqual(['password']);
  });

  it('reports every configured method together', () => {
    const credentials = { clientId: 'id', clientSecret: 'secret' };

    expect(
      signInMethods(config({ google: credentials, microsoft: credentials })),
    ).toEqual(['password', 'google', 'microsoft']);
  });

  it('leads with password, because it is the one that always works', () => {
    // An OAuth button exists only when its credentials do. A page ordering
    // the other way would have a primary action that can be absent.
    const methods = signInMethods(
      config({ google: { clientId: 'id', clientSecret: 'secret' } }),
    );

    expect(methods[0]).toBe('password');
  });

  it('separates the redirect methods from the form', () => {
    // The sign-in page renders one as buttons and one as a form. Nothing
    // else needs to know the difference.
    const credentials = { clientId: 'id', clientSecret: 'secret' };

    expect(oauthMethods(config({ google: credentials }))).toEqual(['google']);
  });

  it('reports nothing when no method is available', () => {
    expect(signInMethods(config({ passwordEnabled: false }))).toEqual([]);
  });

  it('needs both halves of an OAuth credential', () => {
    // A half-configured provider renders a button that fails at the callback,
    // which is worse than not offering it.
    process.env.GOOGLE_CLIENT_ID = 'id-without-a-secret';
    delete process.env.GOOGLE_CLIENT_SECRET;

    expect(loadAuthConfig().google).toBeNull();
  });
});

describe('health answers "can anybody sign in", not "is OAuth configured"', () => {
  it('is healthy with password sign-in and no OAuth at all', async () => {
    // **The defect this replaced.** The old check counted social providers
    // and reported "sign-in is unavailable" — a false report about a healthy
    // install, which is worse than no check.
    const report = await checkAuthHealth(config());

    expect(report.checks.sign_in_methods.status).toBe('ok');
    expect(report.checks.sign_in_methods.detail).toContain('password');
  });

  it('is degraded when nothing at all is configured', async () => {
    // Degraded, not unavailable: the process is healthy and serving, and an
    // orchestrator must not restart it. An operator does need to know.
    const report = await checkAuthHealth(config({ passwordEnabled: false }));

    expect(report.checks.sign_in_methods.status).toBe('degraded');
  });

  it('names the methods rather than counting them', async () => {
    const report = await checkAuthHealth(
      config({ microsoft: { clientId: 'id', clientSecret: 'secret' } }),
    );

    expect(report.checks.sign_in_methods.detail).toContain('microsoft');
  });
});

describe('a link is never written to a production log', () => {
  it('refuses the console transport in a deployed environment', async () => {
    // **A startup failure, not a runtime check.** A password-reset link in a
    // production log is a credential in a log file, and the failure mode of
    // getting this wrong is silent — every flow appears to work and nobody
    // receives anything.
    //
    // Keyed to SIGNORA_ENVIRONMENT rather than NODE_ENV: `NODE_ENV=production`
    // means "an optimised build", which Next.js sets while compiling on a
    // laptop. The first version of this guard refused to build the artifact it
    // was protecting.
    vi.stubEnv('SIGNORA_ENVIRONMENT', 'production');
    const { loadAuthConfig: load } = await import('@/lib/auth/config');

    expect(() => load()).toThrow(/deployed environment/);
  });

  it('refuses a transport this build does not have', async () => {
    process.env.SIGNORA_AUTH_EMAIL_TRANSPORT = 'ses';
    const { loadAuthConfig: load } = await import('@/lib/auth/config');

    expect(() => load()).toThrow(/not a transport this build has/);
  });

  it('allows the console transport on a developer machine', () => {
    vi.stubEnv('SIGNORA_ENVIRONMENT', 'local');

    expect(loadAuthConfig().emailTransport).toBe('console');
  });
});

describe('the delivered link is never logged as an event', () => {
  it('records that a link was requested and not what it was', async () => {
    // A verification URL is a bearer credential for as long as it lives. The
    // event exists so a silent flow is observable; the link must not be in it.
    const { createEmailTransport } = await import('@/lib/auth/email');
    const emitted: string[] = [];
    const log = vi.spyOn(console, 'log').mockImplementation((line: string) => {
      emitted.push(String(line));
    });

    await createEmailTransport(config())({
      to: 'rep@customer.test',
      purpose: 'reset-password',
      url: 'http://localhost:3000/reset?token=SECRET_TOKEN_VALUE',
    });

    log.mockRestore();
    const events = emitted.filter((line) => line.startsWith('{'));
    expect(events).toHaveLength(1);
    expect(events[0]).toContain('AUTH_PASSWORD_RESET_REQUESTED');
    expect(events[0]).not.toContain('SECRET_TOKEN_VALUE');
    expect(events[0]).not.toContain('rep@customer.test');
  });

  it('still puts the link where a developer can use it', async () => {
    const { createEmailTransport } = await import('@/lib/auth/email');
    const emitted: string[] = [];
    const log = vi.spyOn(console, 'log').mockImplementation((line: string) => {
      emitted.push(String(line));
    });

    await createEmailTransport(config())({
      to: 'rep@customer.test',
      purpose: 'verify-email',
      url: 'http://localhost:3000/api/auth/verify?token=abc',
    });

    log.mockRestore();
    expect(emitted.join('\n')).toContain(
      'http://localhost:3000/api/auth/verify?token=abc',
    );
  });

  it('passes the url through untouched', async () => {
    // A transport that rewrote a link could invalidate it, and the failure
    // would look like an expired token.
    const { createEmailTransport } = await import('@/lib/auth/email');
    const url =
      'http://localhost:3000/api/auth/verify?token=a%2Bb%2Fc&callbackURL=%2F';
    const emitted: string[] = [];
    const log = vi.spyOn(console, 'log').mockImplementation((line: string) => {
      emitted.push(String(line));
    });

    await createEmailTransport(config())({
      to: 'x@y.test',
      purpose: 'verify-email',
      url,
    });

    log.mockRestore();
    expect(emitted.join('\n')).toContain(url);
  });
});

describe('the identifier Better Auth mints is one the other tier accepts', () => {
  /**
   * **The two tiers had never agreed on what a user is.**
   *
   * Better Auth's default id is a 32-character nanoid. `sub` carries it
   * verbatim; the Python verifier does `UUID(str(claims["sub"]))` and rejects
   * anything else — so every API request from a real signed-in user returned
   * 401, and the JWT boundary was violated by the identity provider itself.
   *
   * Invisible for three compounding reasons: no user existed until the auth
   * tables were created (R6-01); every test mints `sub` as a `uuid4()`, so the
   * test path and the production path differed in exactly the disputed field;
   * and the comment in `server.ts` asserted the opposite.
   *
   * Asserted against the configured instance rather than against a constant,
   * because the defect was in the *wiring* — the generator was never the
   * problem, its absence was.
   */
  const UUID_V4 =
    /^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;

  it('mints a UUID for every model it stores', async () => {
    const { createAuth } = await import('@/lib/auth/server');
    const generateId = createAuth(config()).options.advanced?.database?.generateId;

    expect(typeof generateId, 'no id generator is configured at all').toBe('function');

    for (const model of ['user', 'session', 'account', 'verification'] as const) {
      const id = (generateId as (o: { model: string }) => string)({ model });
      expect(id, `${model} id is not a UUID the Python tier will accept`).toMatch(
        UUID_V4,
      );
    }
  });

  it('does not delegate the id to a database column default', async () => {
    // `generateId: 'uuid'` resolves to a `gen_random_uuid()` column default,
    // which silently inserts null on any table created before the setting
    // existed. Generating in the process depends on no schema state.
    const { createAuth } = await import('@/lib/auth/server');

    expect(createAuth(config()).options.advanced?.database?.generateId).not.toBe('uuid');
  });
});
