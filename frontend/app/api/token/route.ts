/**
 * Exchanges a Better Auth session for a short-lived API access token.
 *
 * This is the seam between the two tiers: the browser holds a session
 * cookie, the API accepts only a Bearer JWT, and this route converts one to
 * the other. Keeping the exchange server-side means the private signing key
 * is never exposed to the browser.
 */

import { NextResponse, type NextRequest } from 'next/server';

import { loadAuthConfig } from '@/lib/auth/config';
import { AUTH_EVENTS, emitAuthEvent } from '@/lib/auth/events';
import { issueAccessToken, ACCESS_TOKEN_TTL_SECONDS } from '@/lib/auth/jwt';
import { loadPrivateKey } from '@/lib/auth/keys';
import { auth } from '@/lib/auth/server';

export async function POST(request: NextRequest): Promise<NextResponse> {
  const config = loadAuthConfig();
  const session = await auth().api.getSession({ headers: request.headers });

  if (!session?.user) {
    // Coarse on purpose: a message distinguishing "no session" from
    // "expired session" tells an attacker which of the two they achieved.
    emitAuthEvent(AUTH_EVENTS.TOKEN_REJECTED, { reason: 'no_active_session' });
    return NextResponse.json(
      { error: { code: 'unauthenticated', message: 'No active session.' } },
      { status: 401 },
    );
  }

  const requestedWorkspace = request.nextUrl.searchParams.get('workspace_id');

  try {
    const token = await issueAccessToken(
      {
        userId: session.user.id,
        sessionId: session.session.id,
        email: session.user.email,
        emailVerified: session.user.emailVerified ?? false,
        // Passed through as a hint only. The API re-verifies membership
        // server-side, so an unauthorised value here grants nothing.
        activeWorkspaceId: requestedWorkspace,
      },
      {
        issuer: config.jwtIssuer,
        audience: config.jwtAudience,
        privateKey: await loadPrivateKey(config.jwtPrivateKey),
      },
    );

    emitAuthEvent(AUTH_EVENTS.TOKEN_ISSUED, {
      userId: session.user.id,
      sessionId: session.session.id,
      ...(requestedWorkspace ? { workspaceId: requestedWorkspace } : {}),
    });

    return NextResponse.json({
      access_token: token,
      token_type: 'Bearer',
      expires_in: ACCESS_TOKEN_TTL_SECONDS,
    });
  } catch {
    // A signing failure is an operational fault, not a client error: the
    // caller's session was valid.
    emitAuthEvent(AUTH_EVENTS.TOKEN_REJECTED, {
      userId: session.user.id,
      reason: 'signing_failed',
    });
    return NextResponse.json(
      { error: { code: 'token_issuance_failed', message: 'Could not issue a token.' } },
      { status: 500 },
    );
  }
}
