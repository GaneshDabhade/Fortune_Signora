/**
 * Environment configuration for the authentication tier.
 *
 * Read and validated once at module load so a misconfiguration fails at
 * startup rather than on a user's first sign-in attempt. Authentication
 * config that is wrong is not something to discover in production traffic.
 */

/**
 * ⚡ **A union with two members, and that is the change** — [TASK-494](../../../docs/BACKLOG.md).
 *
 * **`resend` is not a new decision.** [`09-build-vs-buy.md`](../../../docs/architecture/09-build-vs-buy.md)
 * ratified it — *"transactional delivery/deliverability reputation is a
 * solved, specialized problem"* — and [ADR-0015](../../../docs/architecture/adr/0015-communication-email-and-calendar-integrations.md)
 * is the approval. **[D-179](../../../docs/DECISION_REGISTER.md) is why it is
 * being built now rather than rediscovered later:** *"no architectural
 * decision should remain only as documentation."*
 */
export type AuthEmailTransportName = 'console' | 'resend' | 'mailbox';

export interface AuthConfig {
  databaseUrl: string;
  authSchema: string;
  baseUrl: string;
  betterAuthSecret: string;
  jwtIssuer: string;
  jwtAudience: string;
  jwtPrivateKey: string | undefined;
  jwtPublicKey: string | undefined;
  google: OAuthProviderConfig | null;
  microsoft: OAuthProviderConfig | null;
  apiBaseUrl: string;
  /** Whether a person may sign in with an address and a password.
   *
   * A **method**, not a fallback and not a development affordance (ADR-0033).
   * It produces the same session, the same claims and the same authorization
   * as an OAuth sign-in, because the token carries no record of how anybody
   * signed in. */
  passwordEnabled: boolean;
  /** How verification and reset links leave the process. Two implementations
   * now; see `lib/auth/email.ts` for why it was a port before there were. */
  emailTransport: AuthEmailTransportName;
  /** The Resend credential, present only when `emailTransport` is `resend`.
   *
   * ⛔ **Read here rather than inside the adapter**, so a missing key is a
   * startup failure like every other authentication misconfiguration —
   * **not a delivery that silently does nothing on a customer's first
   * sign-up.** */
  resend: ResendConfig | null;
}

export interface ResendConfig {
  apiKey: string;
  /** The envelope sender. **Resend refuses any address on an unverified
   * domain**, so this is a real deployment decision and has no default: a
   * fallback would be a value that works in this file and fails at the API. */
  from: string;
}

export interface OAuthProviderConfig {
  clientId: string;
  clientSecret: string;
}

function optionalProvider(idVar: string, secretVar: string): OAuthProviderConfig | null {
  const clientId = process.env[idVar];
  const clientSecret = process.env[secretVar];

  // Both or neither. A half-configured provider would render a sign-in
  // button that fails at the callback, which is worse than not offering it.
  if (!clientId || !clientSecret) return null;
  return { clientId, clientSecret };
}

/**
 * A value with no safe default. **Refuses rather than guessing.**
 *
 * This used to accept a `fallback`, which made the name a lie: with one
 * supplied it could never throw. Two of the six values that used it were
 * dangerous ([B-104](../../../docs/BUGS.md)) — the auth database silently
 * became the *shared* `signora`, and the JWT signing secret silently became a
 * string committed to this repository.
 *
 * **Refusing to start is the correct failure.** A process that will not boot is
 * diagnosed in seconds; one that boots against the wrong database is diagnosed
 * after somebody notices users in it.
 */
function required(name: string): string {
  const value = process.env[name];
  if (!value) {
    throw new Error(
      `${name} is required and is not set. It has no default: guessing one ` +
        `would connect this tier to somebody else's environment. See ` +
        `docs/RUNNING.md for the value your environment should use.`,
    );
  }
  return value;
}

/**
 * A value whose default helps a first clone run.
 *
 * **Named separately so the distinction is visible at the call site.**
 *
 * ## 🔴 B-257 — this said the default *"fails loudly and immediately"*, and it does not
 *
 * ⛔ **Measured on a lane at 3200**, by QE, in the session that found it:
 *
 * ```
 * [Better Auth]: Invalid origin: http://localhost:3200   → 403
 * symptom: waitForURL: Timeout 20000ms exceeded
 * ```
 *
 * ⚡ **It fails as a sign-in that submits and never navigates** — 📁 **the
 * identical symptom of a missing Better Auth schema and of missing demo
 * accounts.** **Three causes, one appearance**, and QE hit all three in one
 * session.
 *
 * ⚠️ **And the defaults below are not merely *a wrong port*.** 📁
 * [`RUNNING.md`](../../../docs/RUNNING.md): *"3000 and 8000 belong to human
 * review on `main`, and to no lane."* ⛔ **An unset variable aims a lane's auth
 * tier at the one environment every lane is told to stay off.**
 *
 * 🔴 **The values are unchanged here on purpose.** **The honest repair needs
 * this tier to know which environment it is in** — a default for a first
 * clone, an error for a lane — **and it cannot**: 📁
 * [B-223](../../../docs/BUGS.md) / [C-298](../../../docs/LANE_COORDINATION.md),
 * where the auth tier's environment names and the registry's share an empty
 * intersection. **One root, two rows.**
 */
function developmentDefault(name: string, fallback: string): string {
  return process.env[name] ?? fallback;
}

export function loadAuthConfig(): AuthConfig {
  // Resolved once, and both fields read it. **Selection happens here and the
  // adapter is handed the answer** — `createEmailTransport` switches on this
  // value rather than re-reading the environment, which is what makes the
  // choice testable without setting process-wide state.
  const transport = resolveEmailTransport();

  return {
    // Connects as `signora_auth`, never as the database owner. Migration
    // 0005 revokes `signora_app` from the auth schema; that isolation only
    // holds if this tier's credential is equally narrow. The owner role
    // would read every application table and bypass Row-Level Security.
    //
    // **No default, and evaluated on access rather than on load.** Every
    // environment — each lane, QE, human review — has its own database, and an
    // unset variable used to send all of them to the shared one.
    //
    // A getter because **a build legitimately has no environment**: Next.js
    // prerenders pages that read `passwordEnabled`, and demanding a database
    // URL to answer a boolean fails a build that was never going to connect to
    // anything. **The value is required where it is *used*** — `getAuthPool()`
    // — not where the struct is assembled.
    get databaseUrl() {
      return required('SIGNORA_AUTH_DATABASE_URL');
    },
    // Better Auth's tables live in their own schema so they can never
    // collide with application tables and so a rollback of one cannot
    // affect the other (approved decision, M1.2).
    authSchema: process.env.SIGNORA_AUTH_SCHEMA ?? 'auth',
    baseUrl: developmentDefault('SIGNORA_APP_URL', 'http://localhost:3000'),
    // **No default, and this one is a security property.** The previous
    // fallback was a signing secret committed to the repository, so any clone
    // that had not set it minted tokens every other clone could forge (§13:
    // no credential is ever hardcoded or committed).
    //
    // A getter for the same reason as `databaseUrl`: required where it signs,
    // not where it is read.
    get betterAuthSecret() {
      return required('BETTER_AUTH_SECRET');
    },
    jwtIssuer: developmentDefault('SIGNORA_JWT_ISSUER', 'http://localhost:3000'),
    jwtAudience: developmentDefault('SIGNORA_JWT_AUDIENCE', 'signora-api'),
    jwtPrivateKey: process.env.SIGNORA_JWT_PRIVATE_KEY,
    jwtPublicKey: process.env.SIGNORA_JWT_PUBLIC_KEY,
    google: optionalProvider('GOOGLE_CLIENT_ID', 'GOOGLE_CLIENT_SECRET'),
    microsoft: optionalProvider('MICROSOFT_CLIENT_ID', 'MICROSOFT_CLIENT_SECRET'),
    apiBaseUrl: developmentDefault('SIGNORA_API_URL', 'http://localhost:8000'),
    // On by default. An address and a password is the method that works
    // without an external service, and a product whose only sign-in requires
    // a Google account has assumed something about its customers.
    passwordEnabled: process.env.SIGNORA_AUTH_PASSWORD_ENABLED !== 'false',
    emailTransport: transport,
    resend: transport === 'resend' ? resolveResend() : null,
  };
}

/**
 * How verification and reset links leave the process.
 *
 * **The console transport cannot be selected in a deployed environment, and
 * the check is a startup failure rather than a runtime one.** A password-reset
 * link written to a production log is a credential sitting in a log file, and
 * the failure mode of getting this wrong is silent: every flow appears to work
 * and nobody receives anything.
 *
 * ### Why this reads `SIGNORA_ENVIRONMENT` and not `NODE_ENV`
 *
 * Found by the build failing. **`NODE_ENV=production` means "an optimised
 * build", not "deployed to production"** — Next.js sets it while compiling on
 * a developer's laptop, so a guard keyed to it refused to build the very
 * artifact it was protecting.
 *
 * They are genuinely different questions, and the backend has always modelled
 * them separately (`Settings.environment`). This mirrors it: one variable
 * naming the *deployment*, owned by Signora rather than by the framework.
 */
function resolveEmailTransport(): AuthEmailTransportName {
  const configured = process.env.SIGNORA_AUTH_EMAIL_TRANSPORT ?? 'console';

  if (configured !== 'console' && configured !== 'resend' && configured !== 'mailbox') {
    throw new Error(
      `SIGNORA_AUTH_EMAIL_TRANSPORT='${configured}' is not a transport this build has. ` +
        "It offers 'console', 'resend' and 'mailbox'. Adding a fourth is a " +
        'dependency choice and its own ADR, not a configuration value.',
    );
  }
  // **Resend needs no deployment check, and that is the point of the row.**
  // The guard below exists because the console transport writes a credential
  // to stdout; a real transport is what the guard has always been asking for.
  if (configured === 'resend') return 'resend';

  // ⛔ **The mailbox carries the console's refusal, for a stronger reason.**
  // The console writes one credential to stdout; the mailbox *keeps a
  // history* of them and offers a surface to read it. **A delivery history is
  // a record of credentials being issued** — TASK-474 states the bound and
  // this is where it is enforced, at startup rather than at a request, so a
  // misconfigured deployment stops instead of serving it.
  if (configured === 'mailbox' && isDeployed()) {
    throw new Error(
      'The development mailbox keeps every verification and password-reset link this ' +
        `process has sent, which is a record of credentials. SIGNORA_ENVIRONMENT='${environmentName()}' ` +
        'is a deployed environment. Configure a real transport (ADR-0406 §3).',
    );
  }
  if (configured === 'mailbox') return 'mailbox';

  if (isDeployed()) {
    throw new Error(
      'The console email transport writes verification and password-reset links to stdout, ' +
        `which puts a credential in a log file. SIGNORA_ENVIRONMENT='${environmentName()}' is a ` +
        'deployed environment. Configure a real transport before deploying a build that offers ' +
        'password sign-in (ADR-0033).',
    );
  }
  return 'console';
}

/** Signora's own deployment environment, mirroring the backend's `Settings.environment`.
 * Defaults to `local` for the same reason the backend does: a developer who has
 * configured nothing is, definitionally, local. */
export function environmentName(): string {
  return process.env.SIGNORA_ENVIRONMENT ?? 'local';
}

/**
 * Whether this process is serving people who are not the person who started it.
 *
 * ### ⚠️ `development` is gone, and removing it is the point
 *
 * 📁 **[ADR-0412](../../../docs/architecture/adr/0412-environment-and-secret-safe-logging.md)
 * §2, ratified as [C-298](../../../docs/LANE_COORDINATION.md)**: *"frontend and
 * backend semantics are identical — a value that means production in one tier
 * and something else in the other is the same defect with a longer fuse."*
 *
 * 🔴 **This list had three members and the AI Platform's had one.** They were
 * never compared, so `SIGNORA_ENVIRONMENT=development` was **local here and
 * deployed there** — the deterministic mock refused while this tier happily
 * wrote verification links to stdout. ⛔ **`development` and `local` were two
 * spellings of one environment**, which is how a guard comes to be written
 * against whichever spelling somebody happened to use.
 *
 * ✅ **The vocabulary is now closed and lives in
 * `backend/signora_platform/environment.py`**, and a Security Invariant reads
 * both this list and the AI Platform's guard and fails if they diverge — 📁
 * ADR-0412 §4: *"two tiers disagreeing about a name is invisible until the day
 * it matters."*
 *
 * ⛔ **A value outside the vocabulary is DEPLOYED**, not development. An
 * allow-list makes an unknown name restrictive by default; a deny-list would
 * make it permissive, and the safe direction for a name nobody has thought
 * about yet is the one that refuses.
 */
function isDeployed(): boolean {
  return !['local', 'test'].includes(environmentName());
}

/**
 * **The three authentication execution modes** —
 * [TASK-473](../../../docs/BACKLOG.md), on
 * [ADR-0406](../../../docs/architecture/adr/0406-authentication-execution-modes.md) §2.
 *
 * > 📁 **[D-131](../../../docs/DECISION_REGISTER.md): *"These modes must be
 * > explicit and never silently imitate production behavior. A user or
 * > developer should always know which mode is active."***
 *
 * ⛔ **Today nothing reports it**, and the failure that costs is a review of
 * the wrong product: **a reviewer walking the first hour cannot tell whether
 * they signed in as a seeded demo account or created one.** ⚠️ **Those are two
 * different products, and a review of the wrong one is worse than no review,
 * because it is reported as a review** — 📁 [C-320](../../../docs/LANE_COORDINATION.md)
 * measured exactly that going unnoticed for three days.
 */
export type AuthMode = 'production' | 'development' | 'demo';

/**
 * ⛔ **This DERIVES; it does not decide.** 📁 **The row is explicit:
 * *"`lib/auth/config.ts` already resolves the mode; nothing new is computed.
 * This row SURFACES a value that exists — it must not introduce a second
 * resolution"*** ([§2](../../../CLAUDE.md), *behaviour exists exactly once*).
 * **Both inputs are the ones the transport guard above already uses.**
 *
 * ## 🔴 Nothing in an authentication path may branch on this
 *
 * 📁 **ADR-0406 §5: *"No code path changes. Only configuration changes… an
 * `if (mode === …)` in an authentication path is the defect this ADR exists to
 * prevent."*** ⚡ **So this is an OBSERVABLE, and the distinction is exact: it
 * is read by things that DISPLAY, never by things that DECIDE.** ⛔ **The
 * Python tier still has no concept of a mode at all** (§1), **which is what
 * makes the guarantee structural rather than disciplinary.**
 *
 * ## ⚡ Why `demo` is recognised by name and nothing is invented
 *
 * 📁 **`demo` is already a row in [`infra/environments.py`](../../../infra/environments.py)'s
 * registry** — *"Seeded demonstration of shipped capability"*, slot 7, its own
 * database and compose project. ✅ **Reading it is reading existing
 * configuration**; ⛔ **a new variable to mean the same thing would be the
 * second representation §2 forbids.**
 *
 * ## ⚠️ A gap this function makes visible and deliberately does not close
 *
 * ⛔ **`isDeployed()` above is a DENYLIST of three names — `local`, `test`,
 * `development` — and the environment registry contains none of them.** **It
 * holds `review`, `lane-qe`, `lane-a`…`lane-e` and `demo`.** ⚡ **So a lane
 * that exported `SIGNORA_ENVIRONMENT=lane-a`, which is what the registry calls
 * it, would be classified as DEPLOYED and its auth tier would refuse to
 * start.** ✅ **Latent rather than live** — nothing sets the variable for the
 * frontend today, so `environmentName()` returns `local`.
 *
 * ⛔ **Not fixed here, and the reason is [§13](../../../CLAUDE.md).** **Widening
 * that list would make the console transport — which writes a credential to
 * stdout — permissible in more environments.** ⚠️ **That is a weakened guard
 * however it is dressed, and this row's budget says *"no weakened guard"* by
 * name.** ✅ **Reported as [B-223](../../../docs/BUGS.md).**
 */
export function authMode(): AuthMode {
  // Order matters and it is the safe one: `demo` is a deployed name under
  // `isDeployed()`, and a demonstration reported as production would hide the
  // one fact a reviewer needs.
  if (environmentName() === 'demo') return 'demo';
  return isDeployed() ? 'production' : 'development';
}

/**
 * The ways a person can actually sign in.
 *
 * **The unit is a sign-in *method*, not an OAuth provider** (ADR-0033). The
 * previous `configuredProviders` answered *"which social providers have
 * credentials?"* and was used to answer *"can anyone sign in?"* — two
 * questions that were the same only while OAuth was the only method. The
 * moment password sign-in works, a health check built on the first answer
 * reports a healthy install as broken.
 *
 * Password first: it is the method that always works, so a page rendering
 * these in order leads with the one that needs no external service.
 */
export function signInMethods(config: AuthConfig): string[] {
  return [
    ...(config.passwordEnabled ? ['password'] : []),
    ...(config.google ? ['google'] : []),
    ...(config.microsoft ? ['microsoft'] : []),
  ];
}

/** The subset that redirects to an external identity provider. The sign-in
 * page renders these as buttons and `password` as a form; nothing else needs
 * to know the difference. */
export function oauthMethods(config: AuthConfig): string[] {
  return signInMethods(config).filter((method) => method !== 'password');
}

/**
 * The Resend credential, read at startup because a missing one must stop a
 * process rather than a customer.
 *
 * ⛔ **No defaults, either of them.** An API key has no safe fallback for the
 * reason `required` already documents. **And `from` has none because Resend
 * refuses any address on a domain the account has not verified** — a default
 * like `noreply@signora.app` would typecheck, boot, and fail at the vendor on
 * the first customer's sign-up, which is exactly the silent failure the
 * console-in-production guard was written to prevent.
 */
function resolveResend(): ResendConfig {
  return {
    apiKey: required('RESEND_API_KEY'),
    from: required('SIGNORA_AUTH_EMAIL_FROM'),
  };
}
