/**
 * Better Auth's route handler — sign-in, OAuth callbacks, sessions, sign-out.
 *
 * Every credential-handling path in the system terminates here. Nothing
 * equivalent exists, or may exist, in the Python tier (ADR-0026).
 */

import { toNextJsHandler } from 'better-auth/next-js';

import { auth } from '@/lib/auth/server';

/**
 * **Never evaluated at build time.** Constructing the handler reads secrets,
 * opens a database pool and validates authentication configuration; doing any
 * of that while compiling means a build either fails on a laptop that has no
 * production configuration, or — worse — bakes configuration into an artifact
 * that should read it at boot (§20b: environment-based configuration).
 */
export const dynamic = 'force-dynamic';

export const { GET, POST } = toNextJsHandler(auth());
