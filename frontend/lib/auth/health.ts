/**
 * Authentication subsystem health.
 *
 * Authentication fails in ways that are invisible until a user tries to sign
 * in: a mismatched key pair, an unreachable auth database, an OAuth provider
 * configured with only half its credentials. Each of those produces a
 * perfectly healthy-looking process that cannot authenticate anyone.
 *
 * These checks make those states observable before a user finds them.
 */

import { loadAuthConfig, signInMethods, type AuthConfig } from '@/lib/auth/config';
import { checkKeyHealth } from '@/lib/auth/keys';
import { getAuthPool } from '@/lib/auth/server';

export type CheckStatus = 'ok' | 'degraded' | 'unavailable';

export interface SubsystemCheck {
  status: CheckStatus;
  detail?: string;
}

export interface AuthHealthReport {
  status: CheckStatus;
  checks: {
    database: SubsystemCheck;
    signing_keys: SubsystemCheck;
    jwt_configuration: SubsystemCheck;
    sign_in_methods: SubsystemCheck;
  };
}

async function checkDatabase(config: AuthConfig): Promise<SubsystemCheck> {
  try {
    const result = await getAuthPool(config).query(
      'SELECT 1 FROM information_schema.schemata WHERE schema_name = $1',
      [config.authSchema],
    );
    if (result.rowCount === 0) {
      return {
        status: 'unavailable',
        detail: `The "${config.authSchema}" schema does not exist. Run backend migrations.`,
      };
    }
    return { status: 'ok' };
  } catch {
    // The error text is withheld: connection errors routinely embed the
    // connection string, which contains a password.
    return { status: 'unavailable', detail: 'Auth database is unreachable.' };
  }
}

async function checkSigningKeys(config: AuthConfig): Promise<SubsystemCheck> {
  const health = await checkKeyHealth(config.jwtPrivateKey, config.jwtPublicKey);

  if (!health.privateKeyLoaded) {
    return { status: 'unavailable', detail: 'Private signing key is unavailable.' };
  }
  if (!health.publicKeyLoaded) {
    return { status: 'degraded', detail: 'Public key unavailable; cannot self-verify.' };
  }
  if (!health.keyPairMatches) {
    // The failure worth catching: both keys load, every token mints, and
    // every API request 401s with no obvious cause.
    return {
      status: 'unavailable',
      detail: 'Public and private keys do not form a matching pair.',
    };
  }
  return { status: 'ok' };
}

function checkJwtConfiguration(config: AuthConfig): SubsystemCheck {
  const missing = [
    !config.jwtIssuer && 'issuer',
    !config.jwtAudience && 'audience',
  ].filter(Boolean);

  if (missing.length > 0) {
    return {
      status: 'unavailable',
      detail: `JWT ${missing.join(' and ')} not configured.`,
    };
  }
  return { status: 'ok' };
}

/**
 * Whether anybody can actually sign in.
 *
 * **The question is about methods, not about OAuth** (ADR-0033). This check
 * previously counted social providers and reported *"sign-in is unavailable"*
 * when there were none — which became a **false report about a healthy
 * install** the moment password sign-in existed, and a health check that lies
 * about a working system is worse than one that is absent.
 */
function checkSignInMethods(config: AuthConfig): SubsystemCheck {
  const methods = signInMethods(config);

  if (methods.length === 0) {
    // Degraded rather than unavailable: the process is healthy and can serve
    // traffic, but no human can sign in. Distinguishing the two matters —
    // an orchestrator should not restart this process, but an operator does
    // need to know.
    return {
      status: 'degraded',
      detail: 'No sign-in method is configured; nobody can sign in.',
    };
  }
  return { status: 'ok', detail: `Available: ${methods.join(', ')}.` };
}

function worst(statuses: CheckStatus[]): CheckStatus {
  if (statuses.includes('unavailable')) return 'unavailable';
  if (statuses.includes('degraded')) return 'degraded';
  return 'ok';
}

export async function checkAuthHealth(
  config: AuthConfig = loadAuthConfig(),
): Promise<AuthHealthReport> {
  const [database, signingKeys] = await Promise.all([
    checkDatabase(config),
    checkSigningKeys(config),
  ]);
  const checks = {
    database,
    signing_keys: signingKeys,
    jwt_configuration: checkJwtConfiguration(config),
    sign_in_methods: checkSignInMethods(config),
  };

  return {
    status: worst(Object.values(checks).map((check) => check.status)),
    checks,
  };
}
