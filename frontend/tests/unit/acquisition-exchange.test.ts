/**
 * The authorization-code exchange, and the hand-off that follows it.
 *
 * **Against a fake `fetch`, and that is the whole point.** No developer
 * application exists for any provider, so a live round trip is impossible —
 * but the exchange is RFC 6749 and the failure translation is Signora's, and
 * neither needs a vendor to be exercised. What a live handshake will confirm
 * is the one step no RFC covers, which is marked in `exchange.ts` and is
 * deliberately the only unverified thing here.
 *
 * **Nothing in these tests makes the product claim a connection.** Every
 * catalog entry stays `connectable: false` while credentials are absent, and a
 * backend test asserts that separately.
 */

import { describe, expect, it } from 'vitest';

import { exchangeAuthorizationCode, type Fetcher } from '@/lib/integrations/exchange';
import { providerFor, type ProviderConfig } from '@/lib/integrations/providers';
import { recordConnection } from '@/lib/integrations/record';

/**
 * **Narrowed rather than asserted.** `providerFor` returns `null` for a slug
 * the table does not hold, and a test that reached for `!` would fail with
 * *cannot read property of undefined* three assertions later instead of
 * saying which system went missing.
 */
function required(slug: string): ProviderConfig {
  const config = providerFor(slug);
  if (config === null) throw new Error(`${slug} is not in the provider table`);
  return config;
}

const HUBSPOT = required('hubspot');
const CREDENTIALS = { clientId: 'client-id', clientSecret: 'client-secret' };
const NOW = () => Date.parse('2026-08-04T12:00:00Z');

/**
 * The one call a test meant to inspect.
 *
 * `calls[0]` is possibly-undefined under `noUncheckedIndexedAccess`, and
 * silencing that with `!` would hide the case worth catching: a test asserting
 * a request that was never made passes vacuously.
 */
function only<T>(calls: T[]): T {
  expect(calls).toHaveLength(1);
  const first = calls[0];
  if (first === undefined) throw new Error('no request was made');
  return first;
}

function json(body: unknown, status = 200): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { 'content-type': 'application/json' },
  });
}

/** A fetcher that answers the token endpoint, then the identity endpoint. */
function replies(token: Response, identity: Response = json({ hub_id: 24601 })): {
  fetcher: Fetcher;
  calls: Array<{ url: string; init: RequestInit }>;
} {
  const calls: Array<{ url: string; init: RequestInit }> = [];
  const fetcher: Fetcher = async (url, init) => {
    calls.push({ url, init });
    return url.startsWith(HUBSPOT.tokenUrl) ? token : identity;
  };
  return { fetcher, calls };
}

async function exchange(
  token: Response,
  identity?: Response,
): Promise<ReturnType<typeof exchangeAuthorizationCode>> {
  const { fetcher } = replies(token, identity);
  return exchangeAuthorizationCode({
    provider: HUBSPOT,
    credentials: CREDENTIALS,
    code: 'the-code',
    redirectUri: 'https://signora.test/api/integrations/hubspot/callback',
    fetcher,
    now: NOW,
  });
}

describe('exchanging a customer’s consent for credentials', () => {
  it('sends exactly what RFC 6749 §4.1.3 requires', async () => {
    const { fetcher, calls } = replies(json({ access_token: 'at', expires_in: 1800 }));
    await exchangeAuthorizationCode({
      provider: HUBSPOT,
      credentials: CREDENTIALS,
      code: 'the-code',
      redirectUri: 'https://signora.test/api/integrations/hubspot/callback',
      fetcher,
      now: NOW,
    });

    const token = calls[0];
    if (token === undefined) throw new Error('the token endpoint was never called');
    const sent = new URLSearchParams(String(token.init.body));
    expect(token.url).toBe(HUBSPOT.tokenUrl);
    expect(token.init.method).toBe('POST');
    expect(Object.fromEntries(sent)).toEqual({
      grant_type: 'authorization_code',
      client_id: 'client-id',
      client_secret: 'client-secret',
      redirect_uri: 'https://signora.test/api/integrations/hubspot/callback',
      code: 'the-code',
    });
  });

  it('never lets a code exchange be served from a cache', async () => {
    const { fetcher, calls } = replies(json({ access_token: 'at' }));
    await exchangeAuthorizationCode({
      provider: HUBSPOT,
      credentials: CREDENTIALS,
      code: 'the-code',
      redirectUri: 'https://signora.test/cb',
      fetcher,
      now: NOW,
    });

    expect(calls.every((call) => call.init.cache === 'no-store')).toBe(true);
  });

  it('turns a token response into a grant in the domain’s words', async () => {
    const result = await exchange(
      json({
        access_token: 'the-access-token',
        refresh_token: 'the-refresh-token',
        expires_in: 1800,
        scope: 'crm.objects.companies.read crm.objects.contacts.read',
      }),
    );

    expect(result).toEqual({
      ok: true,
      grant: {
        accessToken: 'the-access-token',
        refreshToken: 'the-refresh-token',
        expiresAt: new Date('2026-08-04T12:30:00Z'),
        scopes: ['crm.objects.companies.read', 'crm.objects.contacts.read'],
        externalAccountId: '24601',
        endpoint: null,
      },
    });
  });

  it('treats a missing refresh token as a grant that cannot be renewed', async () => {
    // Not an error. An API key behaves the same way, and modelling it as an
    // exception would put OAuth's shape into every other mechanism.
    const result = await exchange(json({ access_token: 'at' }));

    expect(result.ok && result.grant.refreshToken).toBeNull();
    expect(result.ok && result.grant.expiresAt).toBeNull();
  });
});

describe('when the provider refuses', () => {
  it.each([
    ['access_denied', 'cancelled'],
    ['invalid_grant', 'authorization_expired'],
    ['invalid_scope', 'insufficient_permission'],
    ['unauthorized_client', 'insufficient_permission'],
    ['server_error', 'provider_unavailable'],
  ])('translates %s into %s', async (error, outcome) => {
    const result = await exchange(json({ error }, 400));
    expect(result).toEqual({ ok: false, outcome });
  });

  it('calls an unrecognised refusal a provider error rather than unknown', async () => {
    // The provider answered and refused. That is a different fact from Signora
    // being unable to tell what happened, and it sends an engineer somewhere
    // else.
    const result = await exchange(json({ error: 'something_new' }, 400));
    expect(result).toEqual({ ok: false, outcome: 'provider_error' });
  });

  it('reads a 5xx as theirs and worth retrying', async () => {
    const result = await exchange(new Response('<html>502</html>', { status: 502 }));
    expect(result).toEqual({ ok: false, outcome: 'provider_unavailable' });
  });

  it('survives a maintenance page where JSON was expected', async () => {
    const result = await exchange(new Response('<html>oops</html>', { status: 400 }));
    expect(result).toEqual({ ok: false, outcome: 'provider_error' });
  });

  it('reports an unreachable provider rather than throwing', async () => {
    const result = await exchangeAuthorizationCode({
      provider: HUBSPOT,
      credentials: CREDENTIALS,
      code: 'c',
      redirectUri: 'https://signora.test/cb',
      fetcher: async () => {
        throw new TypeError('fetch failed');
      },
      now: NOW,
    });

    expect(result).toEqual({ ok: false, outcome: 'provider_unavailable' });
  });

  it('refuses a 200 that carries no token', async () => {
    // The provider's contract broken, which is not the customer's mistake.
    const result = await exchange(json({ token_type: 'bearer' }));
    expect(result).toEqual({ ok: false, outcome: 'provider_error' });
  });
});

describe('a token Signora cannot attribute', () => {
  it('is refused rather than stored', async () => {
    // Every later question about a connection begins with *whose is it?*, so a
    // token with no account behind it is one the product must not keep.
    const result = await exchange(json({ access_token: 'at' }), json({}, 200));
    expect(result).toEqual({ ok: false, outcome: 'unsupported_account' });
  });

  it('is refused when the identity endpoint itself refuses', async () => {
    const result = await exchange(json({ access_token: 'at' }), json({}, 401));
    expect(result).toEqual({ ok: false, outcome: 'unsupported_account' });
  });

  it('asks the provider named in the table, never a hardcoded host', async () => {
    const { fetcher, calls } = replies(json({ access_token: 'the-token' }));
    await exchangeAuthorizationCode({
      provider: HUBSPOT,
      credentials: CREDENTIALS,
      code: 'c',
      redirectUri: 'https://signora.test/cb',
      fetcher,
      now: NOW,
    });

    const identity = calls[1];
    if (identity === undefined) throw new Error('the identity endpoint was never called');
    expect(identity.url).toBe(`${HUBSPOT.identityUrl}the-token`);
  });
});

describe('handing the grant to the tier that keeps it', () => {
  const GRANT = {
    accessToken: 'the-access-token',
    refreshToken: 'the-refresh-token',
    expiresAt: new Date('2026-08-04T12:30:00Z'),
    scopes: ['crm.objects.companies.read'],
    externalAccountId: '24601',
    endpoint: null,
  };

  function record(response: Response): {
    result: Promise<Awaited<ReturnType<typeof recordConnection>>>;
    calls: Array<{ url: string; init: RequestInit }>;
  } {
    const calls: Array<{ url: string; init: RequestInit }> = [];
    const result = recordConnection({
      apiBaseUrl: 'http://api.test',
      accessToken: 'signora-jwt',
      workspaceId: 'ws-1',
      integration: 'hubspot',
      label: 'HubSpot',
      grant: GRANT,
      fetcher: async (url, init) => {
        calls.push({ url, init });
        return response;
      },
    });
    return { result, calls };
  }

  it('posts what the API asks for, and names no OAuth', async () => {
    const { result, calls } = record(json({ id: 'c-1' }, 201));
    await result;

    const call = only(calls);
    expect(call.url).toBe('http://api.test/workspaces/ws-1/connections');
    expect(JSON.parse(String(call.init.body))).toEqual({
      integration: 'hubspot',
      external_account_id: '24601',
      label: 'HubSpot',
      endpoint: null,
      credential: {
        kind: 'oauth2',
        material: JSON.stringify({
          access_token: 'the-access-token',
          refresh_token: 'the-refresh-token',
        }),
      },
      scopes: ['crm.objects.companies.read'],
      expires_at: '2026-08-04T12:30:00.000Z',
      refreshable: true,
    });
  });

  it('carries the caller’s own token, never a shared one', async () => {
    const { result, calls } = record(json({ id: 'c-1' }, 201));
    await result;

    expect(only(calls).init.headers).toMatchObject({
      authorization: 'Bearer signora-jwt',
    });
  });

  it('reports an already-connected account as an answer rather than a fault', async () => {
    const { result } = record(
      json({ error: { code: 'integration_already_connected' } }, 409),
    );
    await expect(result).resolves.toEqual({ ok: false, outcome: 'already_connected' });
  });

  it('reports a refused permission as one', async () => {
    const { result } = record(json({ error: { code: 'forbidden' } }, 403));
    await expect(result).resolves.toEqual({ ok: false, outcome: 'insufficient_permission' });
  });

  it('does not blame the other system when Signora’s own API is unreachable', async () => {
    // `provider_unavailable` here would send a customer to check HubSpot's
    // status page for a problem that is entirely ours.
    const result = await recordConnection({
      apiBaseUrl: 'http://api.test',
      accessToken: 'signora-jwt',
      workspaceId: 'ws-1',
      integration: 'hubspot',
      label: 'HubSpot',
      grant: GRANT,
      fetcher: async () => {
        throw new TypeError('fetch failed');
      },
    });

    expect(result).toEqual({ ok: false, outcome: 'unknown' });
  });
});

describe('the refresh token is not thrown away', () => {
  /**
   * **The first version of `record.ts` discarded it while recording
   * `refreshable: true`** — a flag nothing could ever act on, and with
   * HubSpot's 1800-second access tokens it meant every connection died within
   * half an hour with no way back except reconnecting by hand.
   *
   * These pin the property rather than the encoding: what matters is that
   * material carrying a renewable grant can be renewed, and that a grant with
   * nothing to renew says so.
   */
  const BASE = {
    accessToken: 'the-access-token',
    expiresAt: null,
    scopes: [],
    externalAccountId: '24601',
    endpoint: null,
  };

  async function sent(refreshToken: string | null): Promise<Record<string, unknown>> {
    const calls: Array<{ url: string; init: RequestInit }> = [];
    await recordConnection({
      apiBaseUrl: 'http://api.test',
      accessToken: 'signora-jwt',
      workspaceId: 'ws-1',
      integration: 'hubspot',
      label: 'HubSpot',
      grant: { ...BASE, refreshToken },
      fetcher: async (url, init) => {
        calls.push({ url, init });
        return json({ id: 'c-1' }, 201);
      },
    });
    return JSON.parse(String(only(calls).init.body)) as Record<string, unknown>;
  }

  it('keeps it, so a renewable grant can actually be renewed', async () => {
    const body = await sent('the-refresh-token');
    const credential = body.credential as { kind: string; material: string };

    expect(body.refreshable).toBe(true);
    expect(JSON.parse(credential.material)).toMatchObject({
      access_token: 'the-access-token',
      refresh_token: 'the-refresh-token',
    });
  });

  it('says a grant with nothing to renew is not refreshable', async () => {
    const body = await sent(null);
    const credential = body.credential as { kind: string; material: string };

    expect(body.refreshable).toBe(false);
    expect(JSON.parse(credential.material).refresh_token).toBeNull();
  });

  it('never records refreshable without something to refresh with', async () => {
    // The invariant, stated once so neither half can drift from the other.
    for (const token of ['a-token', null]) {
      const body = await sent(token);
      const material = JSON.parse((body.credential as { material: string }).material);
      expect(body.refreshable).toBe(material.refresh_token !== null);
    }
  });
});
