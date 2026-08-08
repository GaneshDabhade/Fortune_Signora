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
export type AuthEmailTransportName = 'console' | 'resend';

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
 * A value whose default is harmless and helps a first clone run.
 *
 * **Named separately so the distinction is visible at the call site.** A URL
 * pointing at the wrong port fails loudly and immediately; a database pointing
 * at the wrong schema fails silently and permanently.
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

  if (configured !== 'console' && configured !== 'resend') {
    throw new Error(
      `SIGNORA_AUTH_EMAIL_TRANSPORT='${configured}' is not a transport this build has. ` +
        "It offers 'console' and 'resend'. Adding a third is a dependency choice " +
        'and its own ADR, not a configuration value.',
    );
  }
  // **Resend needs no deployment check, and that is the point of the row.**
  // The guard below exists because the console transport writes a credential
  // to stdout; a real transport is what the guard has always been asking for.
  if (configured === 'resend') return 'resend';
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

/** Whether this process is serving people who are not the person who started it. */
function isDeployed(): boolean {
  return !['local', 'test', 'development'].includes(environmentName());
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
