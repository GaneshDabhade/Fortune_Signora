/**
 * What the acquisition framework needs to know about each system.
 *
 * **Configuration, not code.** Adding Google Calendar, Salesforce or Microsoft
 * 365 should be an entry here plus credentials in the environment — never a
 * change to the flow. If a future provider needs a branch in the route
 * handlers, this table is missing a field and that is the thing to fix.
 *
 * **Credentials are never in this file.** They arrive from the environment and
 * are read at request time, so a repository checkout carries no secret and a
 * misconfigured deployment fails honestly rather than silently using a stale
 * default.
 */

export interface ProviderConfig {
  /** The catalog slug. Must match the backend catalog exactly. */
  slug: string;
  /** What a customer calls it. */
  name: string;
  /** Where the customer is sent to approve access. */
  authorizeUrl: string;
  /** Where the authorization is exchanged for credentials. */
  tokenUrl: string;
  /**
   * What Signora asks permission to do.
   *
   * **Read-only, and that is a product promise rather than a default.** Every
   * Day One capability is an observation source; a write scope here would make
   * the connect screen's central sentence false.
   */
  scopes: string[];
  /** Environment variables holding this provider's credentials. */
  clientIdEnv: string;
  clientSecretEnv: string;
  /**
   * Whether the provider returns a per-account host that must be stored
   * alongside the connection. Salesforce does; HubSpot does not.
   */
  usesInstanceEndpoint: boolean;
}

export const PROVIDERS: Record<string, ProviderConfig> = {
  hubspot: {
    slug: 'hubspot',
    name: 'HubSpot',
    authorizeUrl: 'https://app.hubspot.com/oauth/authorize',
    tokenUrl: 'https://api.hubapi.com/oauth/v1/token',
    scopes: ['crm.objects.contacts.read', 'crm.objects.companies.read'],
    clientIdEnv: 'SIGNORA_HUBSPOT_CLIENT_ID',
    clientSecretEnv: 'SIGNORA_HUBSPOT_CLIENT_SECRET',
    usesInstanceEndpoint: false,
  },
  google_calendar: {
    slug: 'google_calendar',
    name: 'Google Calendar',
    authorizeUrl: 'https://accounts.google.com/o/oauth2/v2/auth',
    tokenUrl: 'https://oauth2.googleapis.com/token',
    scopes: ['https://www.googleapis.com/auth/calendar.events.readonly'],
    clientIdEnv: 'SIGNORA_GOOGLE_CLIENT_ID',
    clientSecretEnv: 'SIGNORA_GOOGLE_CLIENT_SECRET',
    usesInstanceEndpoint: false,
  },
};

export interface ProviderCredentials {
  clientId: string;
  clientSecret: string;
}

/**
 * Whether a provider is fully configured to be connected right now.
 *
 * **The honest source of `connectable`.** A provider listed in this file but
 * missing its credentials is understood and not offerable, and saying so is
 * better than a button that fails after the customer has committed.
 */
export function credentialsFor(
  config: ProviderConfig,
  env: Record<string, string | undefined>,
): ProviderCredentials | null {
  const clientId = env[config.clientIdEnv];
  const clientSecret = env[config.clientSecretEnv];
  if (!clientId || !clientSecret) return null;
  return { clientId, clientSecret };
}

export function providerFor(slug: string): ProviderConfig | null {
  return PROVIDERS[slug] ?? null;
}
