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
import { createAuthMiddleware } from 'better-auth/api';
import { Pool } from 'pg';

import { loadAuthConfig, type AuthConfig } from '@/lib/auth/config';
import { createEmailTransport } from '@/lib/auth/email';
import { AUTH_EVENTS, emitAuthEvent } from '@/lib/auth/events';
import { MINIMUM_PASSWORD_LENGTH } from '@/lib/auth/password';

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
  const deliver = createEmailTransport(config);

  return betterAuth({
    database: getAuthPool(config),
    baseURL: config.baseUrl,
    secret: config.betterAuthSecret,

    // **A method, not a fallback** (ADR-0033). It produces the same session,
    // the same claims and the same authorization as an OAuth sign-in, because
    // the token carries no record of how anybody signed in. Signora writes no
    // hashing, no comparison and no token minting here — that surface is the
    // reason a vendor was bought.
    emailAndPassword: {
      enabled: config.passwordEnabled,
      minPasswordLength: MINIMUM_PASSWORD_LENGTH,
      // `email_verified` has been a JWT claim since M1.2 and has never meant
      // anything, because an identity provider always asserts it. Requiring
      // verification is what turns it into a fact.
      requireEmailVerification: true,
      sendResetPassword: async ({ user, url }) => {
        await deliver({ to: user.email, purpose: 'reset-password', url });
      },
      onPasswordReset: async () => {
        emitAuthEvent(AUTH_EVENTS.PASSWORD_RESET_COMPLETED);
      },
    },

    emailVerification: {
      sendOnSignUp: true,
      // Straight into the product after verifying. The alternative is asking
      // somebody to type a password they set ninety seconds ago, which is how
      // a sign-up gets abandoned at the last step.
      autoSignInAfterVerification: true,
      sendVerificationEmail: async ({ user, url }) => {
        await deliver({ to: user.email, purpose: 'verify-email', url });
      },
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
      useSecureCookies: process.env.NODE_ENV === 'production',
      database: {
        // **UUIDs, because the other tier requires them.**
        //
        // Better Auth's default id is a 32-character nanoid. `sub` carries it
        // verbatim, and the Python verifier does `UUID(str(claims["sub"]))`
        // and rejects anything else — so **every API request from a real
        // signed-in user returned 401**, and the two tiers had never once
        // agreed on what a user is.
        //
        // Invisible for three reasons at once: no user existed until the auth
        // tables were created (R6-01); every test mints `sub` as a `uuid4()`,
        // so the test path and the production path differed in exactly the
        // field under dispute; and the comment that used to sit here asserted
        // the opposite — *"we do not override them, so the two systems never
        // disagree"* — which was written on the assumption that Better Auth's
        // ids were UUIDs.
        //
        // `generateId` is Better Auth's own hook, so nothing is
        // reimplemented and the vendor still owns identity — this only says
        // *which* generator. The alternative — widening `user_id` to text
        // across the schema, RLS, `app.user_id` and the principal — would
        // trade a type for a defect nobody would find again.
        //
        // The function form rather than `'uuid'`: that setting resolves to a
        // `gen_random_uuid()` **column default**, so it silently inserts null
        // on any table created before it was set. Generating in the process
        // depends on no schema state and works the same on every adapter.
        generateId: () => crypto.randomUUID(),
      },
    },

    hooks: {
      // Observability only — this hook never alters the outcome of a
      // request. An auth hook that can fail a sign-in is a liability.
      //
      // **It must be a `createAuthMiddleware`, not a bare async function.**
      // A plain function runs and then leaves Better Auth to continue with a
      // context it did not build, which throws *after* the side effects have
      // happened — a sign-up that creates the user, sends the email, and
      // returns 500. Invisible until now because no authentication request
      // had ever completed: the auth tables did not exist.
      after: createAuthMiddleware(async (ctx) => {
        // Better Auth's middleware context types `path` loosely across
        // versions; read it defensively rather than pinning to an internal
        // shape that may change. A miscategorised observability event is
        // acceptable; a type error that blocks sign-in is not.
        const path = String((ctx as { path?: unknown }).path ?? '');
        if (path.includes('/callback')) {
          emitAuthEvent(AUTH_EVENTS.OAUTH_CALLBACK);
        } else if (path.includes('/sign-out')) {
          emitAuthEvent(AUTH_EVENTS.LOGOUT);
        } else if (path.includes('/sign-up')) {
          emitAuthEvent(AUTH_EVENTS.SIGN_UP);
        } else if (path.includes('/sign-in')) {
          emitAuthEvent(AUTH_EVENTS.LOGIN_SUCCESS);
        }
      }),
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
