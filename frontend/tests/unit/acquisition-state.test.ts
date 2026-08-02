/**
 * The security of the acquisition flow.
 *
 * A callback is an unauthenticated request arriving from a third party with a
 * code in the query string. Everything that stops it creating a connection in
 * somebody else's organization is in `state.ts`, so it is tested against the
 * attacks rather than against the happy path.
 */

import { describe, expect, it } from 'vitest';

import {
  STATE_FAILURE_OUTCOME,
  STATE_TTL_MS,
  type StateFailure,
  issueState,
  verifyState,
} from '@/lib/integrations/state';
import {
  PROVIDER_ERROR_OUTCOME,
  outcomeForProviderError,
  readCookie,
} from '@/lib/integrations/callback';
import { CONNECT_OUTCOMES, type ConnectOutcomeCode } from '@/lib/integrations/outcomes';
import { PROVIDERS, credentialsFor, providerFor } from '@/lib/integrations/providers';

const SECRET = 'a-test-signing-secret';
const NOW = 1_800_000_000_000;

describe('a state Signora issued verifies', () => {
  it('round-trips the slug and the organization it was issued for', () => {
    const { value, nonce } = issueState('hubspot', 'ws-1', SECRET, NOW);
    const result = verifyState(value, nonce, SECRET, NOW);
    expect(result.ok).toBe(true);
    if (result.ok) {
      expect(result.state.slug).toBe('hubspot');
      expect(result.state.workspaceId).toBe('ws-1');
    }
  });

  it('issues a different nonce every time', () => {
    // Two customers connecting at once must not share a value, and a repeated
    // nonce would make one of them replayable by the other.
    const first = issueState('hubspot', 'ws-1', SECRET, NOW);
    const second = issueState('hubspot', 'ws-1', SECRET, NOW);
    expect(first.nonce).not.toBe(second.nonce);
    expect(first.value).not.toBe(second.value);
  });
});

describe('a state Signora did not issue is refused', () => {
  it('refuses a forged value', () => {
    const forged = `${Buffer.from(
      JSON.stringify({ slug: 'hubspot', workspaceId: 'someone-else', nonce: 'n', issuedAt: NOW }),
    ).toString('base64url')}.notasignature`;
    expect(verifyState(forged, 'n', SECRET, NOW)).toEqual({
      ok: false,
      failure: 'bad_signature',
    });
  });

  it('refuses a value signed with a different secret', () => {
    const { value, nonce } = issueState('hubspot', 'ws-1', 'other-secret', NOW);
    expect(verifyState(value, nonce, SECRET, NOW)).toEqual({
      ok: false,
      failure: 'bad_signature',
    });
  });

  it('refuses a tampered organization', () => {
    // **The attack the signature exists for.** Without it, editing one field
    // would create a connection in somebody else's organization.
    const { value, nonce } = issueState('hubspot', 'ws-1', SECRET, NOW);
    const [encoded, signature] = value.split('.');
    const decoded = JSON.parse(Buffer.from(encoded as string, 'base64url').toString());
    decoded.workspaceId = 'ws-victim';
    const tampered = `${Buffer.from(JSON.stringify(decoded)).toString('base64url')}.${signature}`;
    expect(verifyState(tampered, nonce, SECRET, NOW)).toEqual({
      ok: false,
      failure: 'bad_signature',
    });
  });

  it.each(['', 'nodot', 'a.b.c.d'])('refuses a malformed value: %s', (value) => {
    expect(verifyState(value, 'n', SECRET, NOW).ok).toBe(false);
  });

  it('refuses a missing value', () => {
    expect(verifyState(null, 'n', SECRET, NOW)).toEqual({ ok: false, failure: 'malformed' });
  });
});

describe('interruptions a real customer causes', () => {
  it('refuses a state older than the window', () => {
    // Somebody left a tab open overnight. They start again rather than
    // completing a flow nobody remembers beginning.
    const { value, nonce } = issueState('hubspot', 'ws-1', SECRET, NOW);
    const late = NOW + STATE_TTL_MS + 1;
    expect(verifyState(value, nonce, SECRET, late)).toEqual({ ok: false, failure: 'expired' });
  });

  it('accepts one arriving just inside the window', () => {
    const { value, nonce } = issueState('hubspot', 'ws-1', SECRET, NOW);
    expect(verifyState(value, nonce, SECRET, NOW + STATE_TTL_MS - 1).ok).toBe(true);
  });

  it('refuses a replayed callback', () => {
    // **A refresh or a double-click, usually.** The cookie is cleared on first
    // use, so the second arrival finds no nonce.
    const { value } = issueState('hubspot', 'ws-1', SECRET, NOW);
    expect(verifyState(value, null, SECRET, NOW)).toEqual({ ok: false, failure: 'replayed' });
  });

  it('refuses a state that does not match the cookie it was issued with', () => {
    const { value } = issueState('hubspot', 'ws-1', SECRET, NOW);
    const other = issueState('hubspot', 'ws-1', SECRET, NOW);
    expect(verifyState(value, other.nonce, SECRET, NOW)).toEqual({
      ok: false,
      failure: 'mismatched',
    });
  });

  it('reads an expired tab as expired rather than as an attack', () => {
    // Order matters: expiry is checked before the cookie, so somebody whose
    // window timed out is told to start again rather than told they replayed.
    const { value } = issueState('hubspot', 'ws-1', SECRET, NOW);
    expect(verifyState(value, null, SECRET, NOW + STATE_TTL_MS + 1)).toEqual({
      ok: false,
      failure: 'expired',
    });
  });
});

describe('every failure reaches a customer as something readable', () => {
  const failures: StateFailure[] = [
    'malformed',
    'bad_signature',
    'expired',
    'replayed',
    'mismatched',
  ];

  it.each(failures)('%s maps to an outcome that explains itself', (failure) => {
    const code = STATE_FAILURE_OUTCOME[failure] as ConnectOutcomeCode;
    const outcome = CONNECT_OUTCOMES[code];
    expect(outcome).toBeDefined();
    expect(outcome.what).toBeTruthy();
    expect(outcome.next).toBeTruthy();
  });

  it('never shows a customer the word signature', () => {
    // A raw `bad_signature` would tell somebody they had been attacked when
    // the likeliest cause is a bookmarked URL.
    for (const failure of failures) {
      const code = STATE_FAILURE_OUTCOME[failure] as ConnectOutcomeCode;
      const outcome = CONNECT_OUTCOMES[code];
      expect(`${outcome.what} ${outcome.why} ${outcome.next}`).not.toMatch(
        /signature|nonce|state|token/i,
      );
    }
  });
});

describe("the provider's own errors are translated", () => {
  it('reads a decline as a change of mind rather than a failure', () => {
    expect(outcomeForProviderError('access_denied')).toBe('cancelled');
  });

  it('reads a scope refusal as a permissions problem', () => {
    expect(outcomeForProviderError('invalid_scope')).toBe('insufficient_permission');
  });

  it('reads an unknown provider error as something still explainable', () => {
    expect(outcomeForProviderError('something_new')).toBe('provider_error');
  });

  it('returns nothing when the provider reported no error', () => {
    expect(outcomeForProviderError(null)).toBeNull();
  });

  it.each(Object.values(PROVIDER_ERROR_OUTCOME))('%s is a defined outcome', (code) => {
    expect(CONNECT_OUTCOMES[code as ConnectOutcomeCode]).toBeDefined();
  });
});

describe('providers are configuration rather than code', () => {
  it('reports a provider unconfigurable when its credentials are absent', () => {
    // **The honest source of `connectable`.** Understood but not offerable is
    // better than a button that fails after the customer has committed.
    const hubspot = PROVIDERS.hubspot;
    expect(hubspot).toBeDefined();
    expect(credentialsFor(hubspot as never, {})).toBeNull();
  });

  it('reports it configurable when both halves are present', () => {
    const hubspot = PROVIDERS.hubspot;
    expect(hubspot).toBeDefined();
    const credentials = credentialsFor(hubspot as never, {
      SIGNORA_HUBSPOT_CLIENT_ID: 'id',
      SIGNORA_HUBSPOT_CLIENT_SECRET: 'secret',
    });
    expect(credentials).toEqual({ clientId: 'id', clientSecret: 'secret' });
  });

  it('refuses a half-configured provider rather than trying', () => {
    const hubspot = PROVIDERS.hubspot;
    expect(credentialsFor(hubspot as never, { SIGNORA_HUBSPOT_CLIENT_ID: 'id' })).toBeNull();
  });

  it('every provider asks only for read access', () => {
    // The connect screen's central promise. A write scope here would make it
    // false, and nothing else would catch that.
    for (const provider of Object.values(PROVIDERS)) {
      for (const scope of provider.scopes) {
        expect(scope).toMatch(/read|readonly/);
      }
    }
  });

  it('knows nothing about a system outside the table', () => {
    expect(providerFor('netsuite')).toBeNull();
  });
});

describe('cookie reading', () => {
  it('finds the value it was given', () => {
    expect(readCookie('a=1; signora_acq_hubspot=abc; b=2', 'signora_acq_hubspot')).toBe('abc');
  });

  it('returns nothing when absent, which is what a replay looks like', () => {
    expect(readCookie('a=1', 'signora_acq_hubspot')).toBeNull();
  });

  it('is not confused by a name that merely contains the one it wants', () => {
    expect(readCookie('xsignora_acq_hubspot=no', 'signora_acq_hubspot')).toBeNull();
  });
});
