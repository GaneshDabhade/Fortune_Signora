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
import { emailOTP, haveIBeenPwned } from 'better-auth/plugins';
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

    /**
     * ⚡ **Three controls, none of them a decision made here** — [TASK-498](../../../docs/BACKLOG.md).
     *
     * **Every authentication workflow needed one line in this file, every row
     * correctly forbade it, and the screens shipped without the controls.**
     * [C-434](../../../docs/LANE_COORDINATION.md) was Workflow 1's,
     * [C-240](../../../docs/LANE_COORDINATION.md) Workflow 2's and
     * [C-241](../../../docs/LANE_COORDINATION.md) Workflow 3's. **This row is
     * the one that may touch it.**
     */
    plugins: [
      /**
       * ⚡ **[C-240](../../../docs/LANE_COORDINATION.md) ① — ruled by the
       * product owner, 2026-08-08.** Restores the design's fourth password
       * rule on screen `06`.
       *
       * **k-anonymity, so the password never leaves the process**: it sends
       * the first five hex characters of a SHA-1 to `api.pwnedpasswords.com`
       * and matches the suffix locally.
       *
       * ⚠️ **The cost was named when this was raised and is accepted with the
       * ruling**: the plugin raises on an unreachable range API, **so an
       * outage there becomes an inability to register.** ⛔ **Not softened
       * here** — softening it would be this file deciding a semantic the
       * ruling did not.
       */
      haveIBeenPwned(),

      /**
       * 🔴 **[C-241](../../../docs/LANE_COORDINATION.md) — the control screen
       * `07` was built without**, because nothing accepted a typed code.
       *
       * ⛔ **`otpLength: 6` is a *read*, not a choice.** The design says it in
       * terms — *"Enter the 6-digit code"* — and [D-138](../../../docs/DECISION_REGISTER.md)
       * makes the snapshot the implementation authority. ⚠️ **This item first
       * called it "a security parameter nobody has chosen" and that was
       * wrong**; the framing mattered more than the number, because an open
       * parameter justifies waiting and a value the design carries does not.
       */
      emailOTP({
        otpLength: 6,
        async sendVerificationOTP({ email, otp }) {
          await deliver({ to: email, purpose: 'verify-email', code: otp });
        },
      }),
    ],

    /**
     * ⚡ **[C-240](../../../docs/LANE_COORDINATION.md) ② — ruled twice**: by the
     * product owner 2026-08-08, and before that by [D-170](../../../docs/DECISION_REGISTER.md)
     * §3 ③ — *"rate limiting is enabled in development wherever practical;
     * development should behave as close to production as reasonably
     * possible."*
     *
     * ⛔ **Better Auth defaults this to production only**, so the throttled
     * screen Workflow 1 built against the real `429` and the real
     * `X-Retry-After` **could not be reached at any review.** ✅ **The window,
     * the limit and the `/signin` special case are the vendor's own and are
     * not restated here** — restating them would be the second copy this
     * codebase keeps refusing.
     */
    rateLimit: { enabled: true },

    /**
     * ✅ **[C-243](../../../docs/LANE_COORDINATION.md) — ruled [D-185](../../../docs/DECISION_REGISTER.md)
     * §1, product owner, 2026-08-08: thirty minutes.**
     *
     * ⚡ **The ruling's sentence is standing guidance and is quoted rather than
     * paraphrased: *"the framework should implement the product, not define
     * it."*** **`better-auth` defaults to `3600`; the design says thirty; so
     * the configuration moves and the design does not.**
     *
     * 🔴 **This line and screen `08`'s copy ship together, and the pairing is
     * load-bearing.** ⛔ **The config alone leaves the screen understating a
     * credential's life; the copy alone restores exactly the lie the forgot-
     * password screen refused to print.** ⚠️ **Whoever changes one number
     * changes both** — `forgot-password-form.tsx` and its `page.tsx`
     * description carry the sentence a customer reads.
     */
    resetPasswordTokenExpiresIn: 1800,
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
      /**
       * 🔴 **The link is built here rather than passed through** —
       * [TASK-499](../../../docs/BACKLOG.md),
       * [D-185](../../../docs/DECISION_REGISTER.md) §2's `/reset/:token`.
       *
       * ⛔ **`better-auth` hands us a `url` it composed from its own default
       * path and a `?token=` query string.** ⚡ **The product's route is
       * `/reset/:token` — a path segment — so passing that `url` through
       * would email every customer a link to a route that no longer exists.**
       *
       * 📁 **This is [C-243](../../../docs/LANE_COORDINATION.md)'s rule in a
       * second place**: *"configure the framework to match the product… the
       * framework should implement the product, not define it."* ✅ **The
       * token is supplied to this callback, so the URL is ours to compose and
       * there is nothing to infer.**
       */
      sendResetPassword: async ({ user, token }) => {
        const url = `${config.baseUrl}/reset/${token}`;
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
      /**
       * 🔴 **Step-up authentication, and it is BOUGHT rather than built** —
       * [TASK-1410](../../../docs/BACKLOG.md).
       *
       * 📁 **Security Center §02**: ***"Step-up lasts 10 minutes, then expires
       * — long enough to finish a task, short enough that an unlocked laptop
       * is not a standing authorisation."*** ⚡ **600 is the design's number,
       * read rather than chosen**, exactly as `otpLength: 6` was
       * ([C-241](../../../docs/LANE_COORDINATION.md)).
       *
       * ⛔ **`better-auth`'s default is `3600 * 24`** — a day — **which would
       * make an unlocked laptop precisely the standing authorisation the
       * design refuses.**
       *
       * ## ⚡ This is the SERVER-SIDE half, and it is the half that matters
       *
       * 📁 **The row's Security Invariant: *"the challenge is enforced
       * SERVER-SIDE — a client check is a courtesy, and a step-up that only
       * guards the dialog guards nothing."*** ⛔ **`freshAge` is enforced by
       * Better Auth inside the session route, which raises `SESSION_NOT_FRESH`
       * — so a caller that skips the dialog entirely is refused by the server
       * rather than by the screen it did not open.**
       *
       * ⚠️ **[§13](../../../CLAUDE.md) forbids a bespoke authentication
       * mechanism by name, and this row is where somebody would write one.**
       * ✅ **Nothing here implements a challenge; it configures how long the
       * framework's own freshness lasts.**
       */
      freshAge: 600,
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
        } else if (path.includes('/register')) {
          emitAuthEvent(AUTH_EVENTS.SIGN_UP);
        } else if (path.includes('/signin')) {
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
