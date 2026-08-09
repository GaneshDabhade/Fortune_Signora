/**
 * **The port selects by configuration, not by branch** — [TASK-494](../../../docs/BACKLOG.md)'s
 * own stated unit test.
 *
 * ⚡ **Why that is the assertion and not "does Resend send an email".** The row
 * does not re-decide the vendor; [`09-build-vs-buy.md`](../../../docs/architecture/09-build-vs-buy.md)
 * ratified Resend and [ADR-0015](../../../docs/architecture/adr/0015-communication-email-and-calendar-integrations.md)
 * approved it. **What this slice can get wrong is the seam**: a transport
 * chosen by `NODE_ENV`, or by whether a key happens to be present, is a build
 * whose behaviour nobody can state from its configuration.
 *
 * ⛔ **Nothing here reaches `api.resend.com`.** The vendor's client is
 * substituted, which is [D-167](../../../docs/DECISION_REGISTER.md) ①'s
 * permitted substitution — **an infrastructure boundary, not a business
 * rule.** A test that sent real mail would be a test nobody could run twice.
 */
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

const send = vi.hoisted(() => vi.fn());
vi.mock('resend', () => ({
  Resend: class {
    readonly emails = { send };
    constructor(readonly apiKey: string) {
      constructedWith.push(apiKey);
    }
  },
}));
const constructedWith = vi.hoisted(() => [] as string[]);

vi.mock('@/lib/auth/events', () => ({
  AUTH_EVENTS: { VERIFICATION_REQUESTED: 'v', PASSWORD_RESET_REQUESTED: 'r' },
  emitAuthEvent: vi.fn(),
}));

import { createEmailTransport } from '@/lib/auth/email';
import type { AuthConfig, ResendConfig } from '@/lib/auth/config';

const RESEND: ResendConfig = { apiKey: 're_test_key', from: 'Signora <no-reply@signora.test>' };

function config(overrides: Partial<AuthConfig>): AuthConfig {
  return {
    databaseUrl: 'postgresql://x@localhost:5432/signora',
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

const LINK = {
  to: 'm.reinhardt@northwind.com',
  purpose: 'verify-email',
  url: 'http://localhost:3000/verify?token=a-real-token',
} as const;

beforeEach(() => {
  vi.clearAllMocks();
  constructedWith.length = 0;
  send.mockResolvedValue({ data: { id: 'sent' }, error: null });
});

afterEach(() => vi.restoreAllMocks());

describe('the transport is chosen by configuration', () => {
  it('console when the configuration says console', async () => {
    const log = vi.spyOn(console, 'log').mockImplementation(() => {});

    await createEmailTransport(config({ emailTransport: 'console' }))(LINK);

    expect(send).not.toHaveBeenCalled();
    expect(log).toHaveBeenCalled();
  });

  it('Resend when the configuration says resend', async () => {
    await createEmailTransport(config({ emailTransport: 'resend', resend: RESEND }))(LINK);

    expect(send).toHaveBeenCalledOnce();
    expect(constructedWith).toEqual(['re_test_key']);
  });

  it('⛔ never decides from the environment', async () => {
    /**
     * **The failure this asserts against.** A transport picked from
     * `NODE_ENV`, or from whether a key happens to be exported, is a build
     * whose delivery behaviour cannot be stated from its configuration —
     * and `config.ts` already learned that lesson once, keying its deployment
     * guard to `SIGNORA_ENVIRONMENT` rather than `NODE_ENV` because
     * **`NODE_ENV=production` means "an optimised build", not "deployed"**.
     */
    vi.stubEnv('NODE_ENV', 'production');
    vi.stubEnv('RESEND_API_KEY', 're_a_key_that_is_present');
    const log = vi.spyOn(console, 'log').mockImplementation(() => {});

    await createEmailTransport(config({ emailTransport: 'console' }))(LINK);

    expect(send).not.toHaveBeenCalled();
    expect(log).toHaveBeenCalled();
    vi.unstubAllEnvs();
  });
});

describe('what the vendor is handed, and what it is not', () => {
  it('passes the link through untouched', async () => {
    // The port's oldest rule: *"a transport that rewrote a link would be able
    // to invalidate it, and the failure would look like an expired token."*
    await createEmailTransport(config({ emailTransport: 'resend', resend: RESEND }))(LINK);

    expect(send.mock.calls[0]?.[0].text).toContain(LINK.url);
  });

  it('sends from the configured address, never a default', async () => {
    await createEmailTransport(config({ emailTransport: 'resend', resend: RESEND }))(LINK);

    expect(send.mock.calls[0]?.[0]).toMatchObject({ from: RESEND.from, to: LINK.to });
  });

  it('labels the two purposes differently', async () => {
    const deliver = createEmailTransport(config({ emailTransport: 'resend', resend: RESEND }));

    await deliver(LINK);
    await deliver({ ...LINK, purpose: 'reset-password' });

    const [first, second] = send.mock.calls.map((call) => call[0].subject);
    expect(first).not.toEqual(second);
  });
});

describe('a refused delivery is raised, never swallowed', () => {
  it('throws so Better Auth does not report success', async () => {
    /**
     * ⛔ **The silent failure this exists to prevent.** Better Auth awaits the
     * transport. If a rejected send resolved quietly, the customer would be
     * told to check an inbox nothing was sent to — the same failure the
     * console-in-production guard was written for, arriving via the vendor.
     */
    send.mockResolvedValue({ data: null, error: { message: 'domain is not verified' } });

    await expect(
      createEmailTransport(config({ emailTransport: 'resend', resend: RESEND }))(LINK),
    ).rejects.toThrow(/domain is not verified/);
  });

  it('refuses to fall back to the console when the credential is missing', async () => {
    // A silent fallback would make a misconfigured deployment look healthy
    // while writing customer credentials to stdout — both failures at once.
    expect(() => createEmailTransport(config({ emailTransport: 'resend', resend: null }))).toThrow(
      /no Resend configuration was resolved/,
    );
  });
});
