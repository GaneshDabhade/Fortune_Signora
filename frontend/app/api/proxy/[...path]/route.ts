/**
 * The browser's one hop to the Signora API.
 *
 * ## Why this file exists
 *
 * `lib/api/client.ts` has chosen `/api/proxy` as the browser's base URL since
 * M1.2, deliberately: the API is not internet-facing in the deployed topology
 * (ADR-0022), and keeping the browser one hop away from it is the same
 * reasoning that keeps the browser one hop away from the signing key.
 *
 * **The route it named was never built.** Every data request a browser has
 * ever made — on every screen, in every environment, since the authentication
 * boundary shipped — resolved to Next's not-found handler and returned HTML
 * with a 404. The product rendered its shell, its empty states and its error
 * states, and never once rendered a row of its own data. A signed-in owner of
 * a seeded organization was told *"You are not part of an organization yet"*,
 * because the request that would have said otherwise 404'd.
 *
 * Nothing caught it. The backend suite calls the API directly; the component
 * suite mocks the hooks; `make smoke` mints a real token and then calls the
 * API directly too. **Every component was proven and the composition between
 * them was never exercised** — the same shape as B-024, B-301 and B-302, one
 * layer further out.
 *
 * ## What it is, and what it deliberately is not
 *
 * A transport hop. It forwards the method, the path, the query and the body,
 * and it returns the API's response untouched — including the error envelope,
 * because `ApiError` parses the API's `code` and `correlation_id` and a
 * proxy that reshaped them would break the one thing that makes a failure
 * traceable (19-api-conventions.md).
 *
 * **It makes no authorization decision.** The caller's own Bearer token is
 * forwarded unchanged and the API verifies it, re-verifies workspace
 * membership and applies Casbin, exactly as it does for any other client. A
 * proxy that decided anything would be a second authorization surface, and
 * the architecture has one.
 *
 * **It requires a session, and that is not authorization either.** Without it
 * this is an open forwarder into a service that is not otherwise reachable
 * from the internet: anyone could aim it at the private API and let the API
 * reject them, which is a request they should never have been able to make.
 * The check answers *may you use this hop*, never *may you have this data*.
 *
 * **It forwards two headers and no others.** Notably not `Cookie`: the
 * session cookie belongs to the Next tier and the API has no use for it, so
 * forwarding it would hand a credential to a tier that never needs one.
 */

import { NextResponse, type NextRequest } from 'next/server';

import { loadAuthConfig } from '@/lib/auth/config';
import { auth } from '@/lib/auth/server';

/** Methods a screen actually performs. An unlisted method is refused rather
 * than forwarded — a proxy that accepts anything is a wider surface than the
 * product behind it. */
const FORWARDED = new Set(['GET', 'POST', 'PATCH', 'PUT', 'DELETE']);

const UNAUTHENTICATED = {
  error: { code: 'unauthenticated', message: 'No active session.', correlation_id: '' },
};

async function forward(request: NextRequest, path: string[]): Promise<NextResponse> {
  if (!FORWARDED.has(request.method)) {
    return NextResponse.json(
      {
        error: {
          code: 'method_not_allowed',
          message: `${request.method} is not forwarded.`,
          correlation_id: '',
        },
      },
      { status: 405 },
    );
  }

  const session = await auth().api.getSession({ headers: request.headers });
  if (!session?.user) return NextResponse.json(UNAUTHENTICATED, { status: 401 });

  // Rebuilt from the matched segments rather than taken from the URL, so a
  // caller cannot walk out of the API's namespace with `..` or an absolute
  // URL. `encodeURIComponent` on each segment keeps an identifier containing
  // a slash from becoming two path segments.
  const target = new URL(
    `${loadAuthConfig().apiBaseUrl}/${path.map(encodeURIComponent).join('/')}`,
  );
  target.search = request.nextUrl.search;

  const authorization = request.headers.get('authorization');
  const contentType = request.headers.get('content-type');
  const body = FORWARDED.has(request.method) && request.method !== 'GET'
    ? await request.text()
    : undefined;

  const response = await fetch(target, {
    method: request.method,
    headers: {
      ...(authorization ? { authorization } : {}),
      ...(contentType ? { 'content-type': contentType } : {}),
    },
    ...(body ? { body } : {}),
    // The API is a backing service attached by URL and this hop adds no
    // caching of its own; a cached 200 here would show one person another
    // person's answer.
    cache: 'no-store',
  });

  // 204 has no body and `NextResponse` must not be handed one.
  if (response.status === 204) return new NextResponse(null, { status: 204 });

  return new NextResponse(await response.text(), {
    status: response.status,
    headers: {
      'content-type': response.headers.get('content-type') ?? 'application/json',
    },
  });
}

type Context = { params: Promise<{ path: string[] }> };

export async function GET(request: NextRequest, context: Context): Promise<NextResponse> {
  return forward(request, (await context.params).path);
}

export async function POST(
  request: NextRequest,
  context: Context,
): Promise<NextResponse> {
  return forward(request, (await context.params).path);
}

export async function PATCH(
  request: NextRequest,
  context: Context,
): Promise<NextResponse> {
  return forward(request, (await context.params).path);
}

export async function PUT(request: NextRequest, context: Context): Promise<NextResponse> {
  return forward(request, (await context.params).path);
}

export async function DELETE(
  request: NextRequest,
  context: Context,
): Promise<NextResponse> {
  return forward(request, (await context.params).path);
}
