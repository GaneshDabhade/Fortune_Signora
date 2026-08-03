/**
 * Better Auth's route handler — sign-in, OAuth callbacks, sessions, sign-out.
 *
 * Every credential-handling path in the system terminates here. Nothing
 * equivalent exists, or may exist, in the Python tier (ADR-0026).
 */

import { toNextJsHandler } from 'better-auth/next-js';

import { auth } from '@/lib/auth/server';

/**
 * **Never evaluated at build time**, and until [B-104](../../../../../docs/BUGS.md)
 * that sentence was false.
 *
 * Constructing the handler reads secrets, opens a database pool and validates
 * authentication configuration. Doing any of that while compiling means a build
 * either fails on a machine with no production configuration, or — worse —
 * bakes configuration into an artifact that should read it at boot (§20b).
 *
 * **`force-dynamic` does not prevent it.** It governs *rendering*; Next.js
 * still imports every route module during *Collecting page data* to read its
 * exports. `toNextJsHandler(auth())` at module scope therefore ran at build
 * time, exactly as the comment above promised it would not — the Decorative
 * Logic §2 names, with a false claim sitting beside it.
 *
 * **It was invisible only because the configuration had fallbacks.** The build
 * quietly succeeded against the shared database and a secret committed to this
 * repository. Making those refuse turned a silent defect into a failed build,
 * which is how it was found.
 *
 * **The handler is now built on first request**, memoized thereafter.
 */
export const dynamic = 'force-dynamic';

let handlers: ReturnType<typeof toNextJsHandler> | null = null;

function route(): ReturnType<typeof toNextJsHandler> {
  if (!handlers) {
    handlers = toNextJsHandler(auth());
  }
  return handlers;
}

export function GET(request: Request): Promise<Response> {
  return route().GET(request);
}

export function POST(request: Request): Promise<Response> {
  return route().POST(request);
}
