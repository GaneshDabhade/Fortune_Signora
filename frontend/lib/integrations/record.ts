/**
 * Handing an acquired grant to the tier that keeps it.
 *
 * **The boundary `44-integrations.md` §5 draws, crossed in the one direction
 * it allows**: acquisition happens here, storage happens in Python, and this
 * is the sentence between them. Nothing about OAuth travels across — the API
 * receives a credential, a label and an account identifier, and an API key
 * would arrive through the same call.
 *
 * **It mints its own token rather than forwarding one.** A customer returning
 * from a provider's consent screen arrives on a redirect carrying cookies and
 * no `Authorization` header, so there is nothing to forward. The session is
 * exchanged for a short-lived access token exactly as `/api/token` does — the
 * same issuer, the same key, the same claims — because a second way to reach
 * the API would be a second authentication surface, and the architecture has
 * one.
 */

import type { ConnectOutcomeCode } from '@/lib/integrations/outcomes';
import type { AcquiredGrant } from '@/lib/integrations/exchange';

/** Just enough of `fetch` to be substitutable in a test without a network. */
export type Fetcher = (url: string, init: RequestInit) => Promise<Response>;

export interface RecordInput {
  apiBaseUrl: string;
  accessToken: string;
  workspaceId: string;
  integration: string;
  label: string;
  grant: AcquiredGrant;
  fetcher?: Fetcher;
}

/**
 * The API's refusals, in the customer's words.
 *
 * **`409` is the interesting one.** The account is already connected, which is
 * not a failure — it is an answer, and the outcome copy already directs
 * somebody who reached it to disconnect first if it is not working.
 */
const API_ERROR_OUTCOMES: Record<string, ConnectOutcomeCode> = {
  integration_already_connected: 'already_connected',
  unknown_integration: 'unsupported_account',
  forbidden: 'insufficient_permission',
};

export async function recordConnection(
  input: RecordInput,
): Promise<{ ok: true } | { ok: false; outcome: ConnectOutcomeCode }> {
  const fetcher = input.fetcher ?? ((url, init) => fetch(url, init));
  const { grant } = input;

  let response: Response;
  try {
    response = await fetcher(
      `${input.apiBaseUrl}/workspaces/${input.workspaceId}/connections`,
      {
        method: 'POST',
        headers: {
          authorization: `Bearer ${input.accessToken}`,
          'content-type': 'application/json',
        },
        body: JSON.stringify({
          integration: input.integration,
          external_account_id: grant.externalAccountId,
          label: input.label,
          endpoint: grant.endpoint,
          credential: { kind: 'bearer', material: grant.accessToken },
          scopes: grant.scopes,
          expires_at: grant.expiresAt ? grant.expiresAt.toISOString() : null,
          // **A property, not a special case.** A grant with no refresh token
          // is one that cannot be renewed without the customer, which is true
          // of an API key and of every provider that declines to issue one.
          refreshable: grant.refreshToken !== null,
        }),
        cache: 'no-store',
      },
    );
  } catch {
    // Signora's own API being unreachable is not the other system's fault, and
    // telling a customer it was would send them to check the wrong place.
    return { ok: false, outcome: 'unknown' };
  }

  if (response.ok) return { ok: true };

  let code: string | null = null;
  try {
    const body = (await response.json()) as { error?: { code?: unknown } };
    code = typeof body.error?.code === 'string' ? body.error.code : null;
  } catch {
    code = null;
  }

  return { ok: false, outcome: (code === null ? undefined : API_ERROR_OUTCOMES[code]) ?? 'unknown' };
}
