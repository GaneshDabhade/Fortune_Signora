/**
 * Where a customer lands after approving — or declining — access.
 *
 * **Every path ends at the same screen with an outcome the customer can read.**
 * A callback that rendered a JSON error, or a blank page, would strand somebody
 * at the exact moment they were trusting the product with their CRM.
 *
 * **The provider's own error codes are translated here and never shown.**
 * `access_denied` is not a customer's word for *"I changed my mind"*.
 */

import { NextResponse } from 'next/server';

import {
  acquisitionCookie,
  outcomeForProviderError,
  readCookie,
} from '@/lib/integrations/callback';
import { providerFor } from '@/lib/integrations/providers';
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

  // **The one step that needs a real provider**, and the only one. Everything
  // above is exercised without credentials; the exchange and the hand-off to
  // the backend acquisition endpoint are what a HubSpot developer app unlocks.
  // Deliberately not stubbed: a fake exchange would let this route report
  // success it never achieved.
  return done(origin, slug, 'provider_unavailable');
}
