/**
 * Where a customer lands after approving — or declining — access.
 *
 * **Every path ends at the same screen with an outcome the customer can read.**
 * A callback that rendered a JSON error, or a blank page, would strand somebody
 * at the exact moment they were trusting the product with their CRM.
 *
 * **The provider's own error codes are translated here and never shown.**
 * `access_denied` is not a customer's word for *"I changed my mind"*.
 *
 * **The exchange landed 2026-08-04 and this route is now complete.** It had
 * stopped one line short of it since M13 — verifying the state and then
 * returning `provider_unavailable` — because no developer application existed
 * to test against. It still does not, and `credentialsFor()` still returns
 * `null` without one, so **every catalog entry stays `connectable: false` and
 * no customer can reach this path.** What changed is that the path exists and
 * is exercised: the exchange is RFC 6749 and testable against a fake, and the
 * only unverified step is the one no RFC covers, marked where it happens.
 */

import { NextResponse } from 'next/server';

import {
  acquisitionCookie,
  outcomeForProviderError,
  readCookie,
} from '@/lib/integrations/callback';
import { loadAuthConfig } from '@/lib/auth/config';
import { issueAccessToken } from '@/lib/auth/jwt';
import { loadPrivateKey } from '@/lib/auth/keys';
import { auth } from '@/lib/auth/server';
import { exchangeAuthorizationCode } from '@/lib/integrations/exchange';
import { credentialsFor, providerFor } from '@/lib/integrations/providers';
import { recordConnection } from '@/lib/integrations/record';
import { STATE_FAILURE_OUTCOME, verifyState } from '@/lib/integrations/state';

export const runtime = 'nodejs';

function done(origin: string, slug: string, outcome: string): NextResponse {
  const response = NextResponse.redirect(
    `${origin}/settings/connections?system=${slug}&outcome=${outcome}`,
  );
  // Cleared on every path, success or not. That is what makes the nonce
  // single-use, and therefore what makes a replayed callback detectable.
  response.cookies.delete(acquisitionCookie(slug));
  return response;
}

export async function GET(
  request: Request,
  { params }: { params: Promise<{ slug: string }> },
): Promise<NextResponse> {
  const { slug } = await params;
  const url = new URL(request.url);
  const origin = url.origin;

  const provider = providerFor(slug);
  if (!provider) return done(origin, slug, 'unknown');

  // The provider's own refusal is read before anything else: a customer who
  // pressed Cancel has no code and no reason to see a signature failure.
  const declined = outcomeForProviderError(url.searchParams.get('error'));
  if (declined) return done(origin, slug, declined);

  const secret = process.env.SIGNORA_INTEGRATIONS_STATE_SECRET;
  if (!secret) return done(origin, slug, 'provider_unavailable');

  const cookieHeader = request.headers.get('cookie') ?? '';
  const nonce = readCookie(cookieHeader, acquisitionCookie(slug));
  const verified = verifyState(url.searchParams.get('state'), nonce, secret);
  if (!verified.ok) {
    return done(origin, slug, STATE_FAILURE_OUTCOME[verified.failure]);
  }

  const code = url.searchParams.get('code');
  if (!code) return done(origin, slug, 'unknown');

  // **Read after the state is verified, not before.** An unconfigured provider
  // and a forged callback are both refusals, and answering the cheaper one
  // first would let an unauthenticated caller learn which systems Signora
  // holds credentials for.
  const credentials = credentialsFor(provider, process.env);
  if (!credentials) return done(origin, slug, 'provider_unavailable');

  // The session, not a forwarded token: a customer returning from a consent
  // screen arrives on a redirect carrying cookies and no `Authorization`
  // header. Exchanged for a short-lived access token exactly as `/api/token`
  // does — same issuer, same key, same claims.
  const session = await auth().api.getSession({ headers: request.headers });
  if (!session?.user) return done(origin, slug, 'unknown');

  const exchanged = await exchangeAuthorizationCode({
    provider,
    credentials,
    code,
    redirectUri: `${origin}/api/integrations/${slug}/callback`,
  });
  if (!exchanged.ok) return done(origin, slug, exchanged.outcome);

  const config = loadAuthConfig();
  const accessToken = await issueAccessToken(
    {
      userId: session.user.id,
      sessionId: session.session.id,
      email: session.user.email,
      emailVerified: session.user.emailVerified ?? false,
      activeWorkspaceId: verified.state.workspaceId,
    },
    {
      issuer: config.jwtIssuer,
      audience: config.jwtAudience,
      privateKey: await loadPrivateKey(config.jwtPrivateKey),
    },
  );

  const recorded = await recordConnection({
    apiBaseUrl: config.apiBaseUrl,
    accessToken,
    // **From the signed state, never from the query string.** The workspace a
    // connection lands in is decided when the flow starts and travels inside
    // something the customer cannot edit; the API re-verifies membership
    // regardless, which is what makes this a hint rather than a grant.
    workspaceId: verified.state.workspaceId,
    integration: slug,
    label: provider.name,
    grant: exchanged.grant,
  });

  return done(origin, slug, recorded.ok ? 'connected' : recorded.outcome);
}
