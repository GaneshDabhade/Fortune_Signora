/**
 * Environment configuration for the authentication tier.
 *
 * Read and validated once at module load so a misconfiguration fails at
 * startup rather than on a user's first sign-in attempt. Authentication
 * config that is wrong is not something to discover in production traffic.
 */

export type AuthEmailTransportName = 'console';

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
  /** How verification and reset links leave the process. One implementation
   * today; see `lib/auth/email.ts` for why it is a port anyway. */
  emailTransport: AuthEmailTransportName;
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

function required(name: string, fallback?: string): string {
  const value = process.env[name] ?? fallback;
  if (!value) {
    throw new Error(`${name} is required but not configured.`);
  }
  return value;
}

export function loadAuthConfig(): AuthConfig {
  return {
    // Connects as `signora_auth`, never as the database owner. Migration
    // 0005 revokes `signora_app` from the auth schema; that isolation only
    // holds if this tier's credential is equally narrow. The owner role
    // would read every application table and bypass Row-Level Security.
    databaseUrl: required(
      'SIGNORA_AUTH_DATABASE_URL',
      'postgresql://signora_auth:signora_auth_local_dev@localhost:5432/signora',
    ),
    // Better Auth's tables live in their own schema so they can never
    // collide with application tables and so a rollback of one cannot
    // affect the other (approved decision, M1.2).
    authSchema: process.env.SIGNORA_AUTH_SCHEMA ?? 'auth',
    baseUrl: required('SIGNORA_APP_URL', 'http://localhost:3000'),
    betterAuthSecret: required('BETTER_AUTH_SECRET', 'local-dev-secret-change-me'),
    jwtIssuer: required('SIGNORA_JWT_ISSUER', 'http://localhost:3000'),
    jwtAudience: required('SIGNORA_JWT_AUDIENCE', 'signora-api'),
    jwtPrivateKey: process.env.SIGNORA_JWT_PRIVATE_KEY,
    jwtPublicKey: process.env.SIGNORA_JWT_PUBLIC_KEY,
    google: optionalProvider('GOOGLE_CLIENT_ID', 'GOOGLE_CLIENT_SECRET'),
    microsoft: optionalProvider('MICROSOFT_CLIENT_ID', 'MICROSOFT_CLIENT_SECRET'),
    apiBaseUrl: required('SIGNORA_API_URL', 'http://localhost:8000'),
    // On by default. An address and a password is the method that works
    // without an external service, and a product whose only sign-in requires
    // a Google account has assumed something about its customers.
    passwordEnabled: process.env.SIGNORA_AUTH_PASSWORD_ENABLED !== 'false',
    emailTransport: resolveEmailTransport(),
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

  if (configured !== 'console') {
    throw new Error(
      `SIGNORA_AUTH_EMAIL_TRANSPORT='${configured}' is not a transport this build has. ` +
        "Only 'console' ships today; a production provider is an outstanding decision " +
        '(ADR-0033) and adding one is a dependency choice, not a configuration value.',
    );
  }
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
