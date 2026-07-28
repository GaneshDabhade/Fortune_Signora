/**
 * Better Auth server instance — the Authentication Authority (ADR-0026).
 *
 * Everything credential-shaped lives here and nowhere else: password
 * storage, OAuth authorization-code exchange, session lifecycle. The Python
 * tier is never given any of it, and adding a login route or a private key
 * there would violate the boundary this file exists to hold
 * (18-authentication.md).
 */

import { betterAuth } from 'better-auth';
import { Pool } from 'pg';

import { loadAuthConfig, type AuthConfig } from '@/lib/auth/config';
import { AUTH_EVENTS, emitAuthEvent } from '@/lib/auth/events';

let pool: Pool | null = null;

/**
 * Lazily-created connection pool.
 *
 * `search_path` pins Better Auth to its own schema, so its tables can never
 * be created alongside or confused with application tables.
 */
export function getAuthPool(config: AuthConfig = loadAuthConfig()): Pool {
  if (!pool) {
    pool = new Pool({
      connectionString: config.databaseUrl,
      options: `-c search_path=${config.authSchema}`,
      max: 10,
    });
  }
  return pool;
}

export function createAuth(config: AuthConfig = loadAuthConfig()) {
  return betterAuth({
    database: getAuthPool(config),
    baseURL: config.baseUrl,
    secret: config.betterAuthSecret,

    emailAndPassword: {
      // Deliberately off. Signora's ICP signs in with Google or Microsoft
      // (ADR-0010); enabling password auth would add credential storage,
      // reset flows, and breach exposure for no product benefit.
      enabled: false,
    },

    socialProviders: {
      ...(config.google ? { google: config.google } : {}),
      ...(config.microsoft ? { microsoft: config.microsoft } : {}),
    },

    session: {
      // The session outlives any single access token; the 15-minute access
      // token is refreshed from it rather than forcing re-authentication.
      expiresIn: 60 * 60 * 24 * 7,
      updateAge: 60 * 60 * 24,
    },

    advanced: {
      // Better Auth generates its own ids; we do not override them, so that
      // `sub` in the JWT is exactly Better Auth's user id and the two
      // systems never disagree about who a user is.
      useSecureCookies: process.env.NODE_ENV === 'production',
    },

    hooks: {
      // Observability only — this hook never alters the outcome of a
      // request. An auth hook that can fail a sign-in is a liability.
      after: async (ctx) => {
        // Better Auth's middleware context types `path` loosely across
        // versions; read it defensively rather than pinning to an internal
        // shape that may change. A miscategorised observability event is
        // acceptable; a type error that blocks sign-in is not.
        const path = String((ctx as { path?: unknown }).path ?? '');
        if (path.includes('/callback')) {
          emitAuthEvent(AUTH_EVENTS.OAUTH_CALLBACK);
        } else if (path.includes('/sign-out')) {
          emitAuthEvent(AUTH_EVENTS.LOGOUT);
        } else if (path.includes('/sign-in')) {
          emitAuthEvent(AUTH_EVENTS.LOGIN_SUCCESS);
        }
      },
    },
  });
}

export type AuthInstance = ReturnType<typeof createAuth>;

let instance: AuthInstance | null = null;

export function auth(): AuthInstance {
  if (!instance) {
    instance = createAuth();
  }
  return instance;
}
