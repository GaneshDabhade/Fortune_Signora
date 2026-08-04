/**
 * Turning a customer's consent into credentials Signora can hold.
 *
 * **The step `18-authentication.md` reserves to this tier**, and the only one
 * the acquisition flow was missing. Everything before it — the redirect, the
 * signed state, the returning nonce — has worked since M13; everything after
 * it is the Python tier's, which manages credentials and never acquires them.
 *
 * ## Standards, not a vendor
 *
 * The exchange is **RFC 6749 §4.1.3**: a form-encoded `POST` carrying
 * `grant_type=authorization_code`, the code, the redirect URI and the client's
 * credentials. The success shape is §5.1 and the failure shape is §5.2, error
 * codes included. HubSpot, Google, Salesforce and Microsoft all implement it
 * identically, which is why none of them is named below.
 *
 * **One step is not standardised, and it is marked where it happens.** No RFC
 * field says *whose* account a token belongs to, and Signora needs that: a
 * connection is keyed on the customer's own account identifier. Each provider
 * publishes its own endpoint for the question, so the endpoint and the field
 * are **configuration** in `providers.ts` rather than a branch here.
 *
 * ## What it never does
 *
 * **It does not decide.** It returns tokens or a `ConnectOutcomeCode`, and the
 * route decides what a customer sees. **It never logs a token, never returns
 * one in an error, and never retries** — a retried authorization code is a
 * code already spent, and the second attempt fails in a way that reads like
 * the first one's fault.
 */

import type { ConnectOutcomeCode } from '@/lib/integrations/outcomes';
import type { ProviderConfig, ProviderCredentials } from '@/lib/integrations/providers';

/** What a successful exchange yields, in the domain's words rather than OAuth's. */
export interface AcquiredGrant {
  /** The material itself. **Never logged, never rendered, never returned in an error.** */
  accessToken: string;
  /** Present when the provider issued one. Its absence is what makes a grant unrefreshable. */
  refreshToken: string | null;
  /** When the material stops working, or `null` when the provider did not say. */
  expiresAt: Date | null;
  /** What the customer actually permitted, when the provider reported it. */
  scopes: string[];
  /** The customer's own identifier for the account that granted access. */
  externalAccountId: string;
  /** Where to reach this account, for providers whose host moves. `null` otherwise. */
  endpoint: string | null;
}

export type ExchangeResult =
  | { ok: true; grant: AcquiredGrant }
  | { ok: false; outcome: ConnectOutcomeCode };

/** Just enough of `fetch` to be substitutable in a test without a network. */
export type Fetcher = (url: string, init: RequestInit) => Promise<Response>;

export interface ExchangeInput {
  provider: ProviderConfig;
  credentials: ProviderCredentials;
  code: string;
  redirectUri: string;
  fetcher?: Fetcher;
  now?: () => number;
}

/**
 * RFC 6749 §5.2 error codes, translated to what a customer is told.
 *
 * **The provider's word is never the customer's.** `invalid_scope` means an
 * administrator did not grant something; `unauthorized_client` means Signora
 * is not permitted on that account. Both are actionable and neither is
 * *"invalid scope"*.
 *
 * **An unlisted code becomes `provider_error`, not `unknown`.** The provider
 * answered and refused, which is a different fact from Signora being unable to
 * tell what happened, and it points an engineer at a different place.
 */
const OAUTH_ERROR_OUTCOMES: Record<string, ConnectOutcomeCode> = {
  access_denied: 'cancelled',
  invalid_grant: 'authorization_expired',
  invalid_scope: 'insufficient_permission',
  unauthorized_client: 'insufficient_permission',
  invalid_client: 'provider_unavailable',
  server_error: 'provider_unavailable',
  temporarily_unavailable: 'provider_unavailable',
};

interface TokenResponse {
  access_token?: unknown;
  refresh_token?: unknown;
  expires_in?: unknown;
  scope?: unknown;
  error?: unknown;
}

function outcomeForStatus(status: number): ConnectOutcomeCode {
  // 5xx is theirs and worth retrying; 4xx without a parseable OAuth error is a
  // refusal we cannot explain, which is `provider_error` rather than `unknown`
  // for the same reason as above.
  if (status >= 500) return 'provider_unavailable';
  return 'provider_error';
}

async function readJson(response: Response): Promise<Record<string, unknown> | null> {
  try {
    return (await response.json()) as Record<string, unknown>;
  } catch {
    // A provider that answers with HTML — a proxy error page, a maintenance
    // notice — is unavailable rather than malformed, and saying so keeps a
    // customer from checking their own settings for an hour.
    return null;
  }
}

export async function exchangeAuthorizationCode(
  input: ExchangeInput,
): Promise<ExchangeResult> {
  const { provider, credentials, code, redirectUri } = input;
  const fetcher = input.fetcher ?? ((url, init) => fetch(url, init));
  const now = input.now ?? Date.now;

  const body = new URLSearchParams({
    grant_type: 'authorization_code',
    client_id: credentials.clientId,
    client_secret: credentials.clientSecret,
    redirect_uri: redirectUri,
    code,
  });

  let response: Response;
  try {
    response = await fetcher(provider.tokenUrl, {
      method: 'POST',
      headers: { 'content-type': 'application/x-www-form-urlencoded' },
      body: body.toString(),
      // Nothing about a one-time code exchange may be served from a cache.
      cache: 'no-store',
    });
  } catch {
    // Refused connection, DNS failure, timeout. Their side, and recoverable.
    return { ok: false, outcome: 'provider_unavailable' };
  }

  const payload = (await readJson(response)) as TokenResponse | null;

  if (!response.ok) {
    const declared = typeof payload?.error === 'string' ? payload.error : null;
    return {
      ok: false,
      outcome: declared
        ? (OAUTH_ERROR_OUTCOMES[declared] ?? 'provider_error')
        : outcomeForStatus(response.status),
    };
  }

  const accessToken = payload?.access_token;
  if (payload === null || typeof accessToken !== 'string' || accessToken.length === 0) {
    // A 200 with no token is the provider's contract broken, not the
    // customer's mistake. Distinct from a refusal, because an engineer looks
    // in a different place for each.
    return { ok: false, outcome: 'provider_error' };
  }

  const identity = await accountIdentity(provider, accessToken, fetcher);
  if (identity === null) return { ok: false, outcome: 'unsupported_account' };

  return {
    ok: true,
    grant: {
      accessToken,
      refreshToken: typeof payload.refresh_token === 'string' ? payload.refresh_token : null,
      expiresAt: expiryFrom(payload.expires_in, now),
      scopes: typeof payload.scope === 'string' ? payload.scope.split(' ').filter(Boolean) : [],
      externalAccountId: identity.accountId,
      endpoint: provider.usesInstanceEndpoint ? identity.endpoint : null,
    },
  };
}

/**
 * `expires_in` is seconds from now (RFC 6749 §5.1), and absence means the
 * material does not expire — which is a real state, not a missing value: an
 * API key is a grant that never expires and cannot be refreshed.
 */
function expiryFrom(raw: unknown, now: () => number): Date | null {
  const seconds = typeof raw === 'number' ? raw : Number.parseInt(String(raw ?? ''), 10);
  if (!Number.isFinite(seconds) || seconds <= 0) return null;
  return new Date(now() + seconds * 1000);
}

/**
 * **The one step no RFC covers.**
 *
 * A connection is keyed on the customer's own account, and no standard field
 * carries it — so each provider's introspection endpoint and the field it uses
 * are configuration in `providers.ts`, read here rather than branched on.
 *
 * **Unverified against a live provider**, because no developer application
 * exists for any of them yet. The exchange above is a standard this cannot get
 * wrong; this is documented behaviour that a first real handshake will confirm
 * or correct. It is separated for exactly that reason.
 *
 * `null` means *the provider would not say whose account this is*, which
 * reaches the customer as `unsupported_account` — a token Signora cannot
 * attribute is a token it must not store, because every later question about
 * that connection begins with *whose is it?*
 */
async function accountIdentity(
  provider: ProviderConfig,
  accessToken: string,
  fetcher: Fetcher,
): Promise<{ accountId: string; endpoint: string | null } | null> {
  let response: Response;
  try {
    response = await fetcher(`${provider.identityUrl}${encodeURIComponent(accessToken)}`, {
      method: 'GET',
      headers: { accept: 'application/json' },
      cache: 'no-store',
    });
  } catch {
    return null;
  }
  if (!response.ok) return null;

  const payload = await readJson(response);
  const accountId = payload?.[provider.identityAccountField];
  if (accountId === undefined || accountId === null || String(accountId) === '') return null;

  const endpoint = provider.identityEndpointField
    ? payload?.[provider.identityEndpointField]
    : null;

  return {
    accountId: String(accountId),
    endpoint: typeof endpoint === 'string' && endpoint ? endpoint : null,
  };
}
