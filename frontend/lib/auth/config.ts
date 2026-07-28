/**
 * Environment configuration for the authentication tier.
 *
 * Read and validated once at module load so a misconfiguration fails at
 * startup rather than on a user's first sign-in attempt. Authentication
 * config that is wrong is not something to discover in production traffic.
 */

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
  };
}

/** Providers that are actually usable, for rendering sign-in options and for
 * the health endpoint. */
export function configuredProviders(config: AuthConfig): string[] {
  return [
    ...(config.google ? ['google'] : []),
    ...(config.microsoft ? ['microsoft'] : []),
  ];
}
