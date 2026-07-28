/**
 * Better Auth's route handler — sign-in, OAuth callbacks, sessions, sign-out.
 *
 * Every credential-handling path in the system terminates here. Nothing
 * equivalent exists, or may exist, in the Python tier (ADR-0026).
 */

import { toNextJsHandler } from 'better-auth/next-js';

import { auth } from '@/lib/auth/server';

export const { GET, POST } = toNextJsHandler(auth());
