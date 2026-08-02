/**
 * Begins connecting a system.
 *
 * **The authorization flow lives here and only here.** `18-authentication.md`
 * reserves OAuth flows, callback handlers and authorization-code exchange to
 * this tier; the Python tier manages credentials and never acquires them.
 *
 * **A separate OAuth client from Better Auth's**, per `CLAUDE.md` §13 — a
 * different registration, different scopes, a different secret. A sign-in grant
 * and an integration grant are different permissions from the same vendor, and
 * conflating them would let one imply the other.
 *
 * **Nothing here is HubSpot-specific.** Everything the flow needs comes from
 * the provider table; adding a system is an entry there and two environment
 * variables.
 */

import { NextResponse } from 'next/server';

import { acquisitionCookie } from '@/lib/integrations/callback';
import { credentialsFor, providerFor } from '@/lib/integrations/providers';
import { STATE_TTL_MS, issueState } from '@/lib/integrations/state';

export const runtime = 'nodejs';

/** Where a returning customer lands, and where the outcome is shown. */
function connectionsUrl(origin: string, outcome: string, slug: string): string {
  return `${origin}/settings/connections?system=${slug}&outcome=${outcome}`;
}

export async function GET(
  request: Request,
  { params }: { params: Promise<{ slug: string }> },
): Promise<NextResponse> {
  const { slug } = await params;
  const origin = new URL(request.url).origin;

  const provider = providerFor(slug);
  if (!provider) {
    return NextResponse.redirect(connectionsUrl(origin, 'unknown', slug));
  }

  const credentials = credentialsFor(provider, process.env);
  if (!credentials) {
    // A configuration mistake, surfaced as a customer-readable outcome rather
    // than a stack trace. The catalog should already have prevented the button
    // existing; this is the second line of defence, not the first.
    return NextResponse.redirect(connectionsUrl(origin, 'provider_unavailable', slug));
  }

  const workspaceId = new URL(request.url).searchParams.get('workspace');
  if (!workspaceId) {
    return NextResponse.redirect(connectionsUrl(origin, 'unknown', slug));
  }

  const secret = process.env.SIGNORA_INTEGRATIONS_STATE_SECRET;
  if (!secret) {
    return NextResponse.redirect(connectionsUrl(origin, 'provider_unavailable', slug));
  }

  const { value, nonce } = issueState(slug, workspaceId, secret);
  const redirectUri = `${origin}/api/integrations/${slug}/callback`;

  const authorize = new URL(provider.authorizeUrl);
  authorize.searchParams.set('client_id', credentials.clientId);
  authorize.searchParams.set('redirect_uri', redirectUri);
  authorize.searchParams.set('scope', provider.scopes.join(' '));
  authorize.searchParams.set('response_type', 'code');
  authorize.searchParams.set('state', value);

  const response = NextResponse.redirect(authorize.toString());
  response.cookies.set(acquisitionCookie(slug), nonce, {
    httpOnly: true,
    sameSite: 'lax',
    secure: process.env.NODE_ENV === 'production',
    path: '/',
    maxAge: STATE_TTL_MS / 1000,
  });
  return response;
}
