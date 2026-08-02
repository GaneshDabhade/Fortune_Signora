/**
 * Translating what a provider says into what a customer reads.
 *
 * **Separate from the route handler on purpose.** A route module's job is to
 * answer an HTTP request; these are pure decisions about wording and cookies,
 * and they are the part worth testing exhaustively. Keeping them here means the
 * tests exercise the logic rather than a framework.
 */

/**
 * What each provider error means to a customer.
 *
 * Deliberately small and shared: OAuth's error codes are standardised, and a
 * per-provider table would be five copies of one mapping waiting to disagree.
 */
export const PROVIDER_ERROR_OUTCOME: Record<string, string> = {
  access_denied: 'cancelled',
  consent_required: 'cancelled',
  invalid_scope: 'insufficient_permission',
  insufficient_scope: 'insufficient_permission',
  unauthorized_client: 'provider_unavailable',
  invalid_client: 'provider_unavailable',
  server_error: 'provider_unavailable',
  temporarily_unavailable: 'provider_unavailable',
};

/** `null` when the provider reported no error at all. */
export function outcomeForProviderError(error: string | null): string | null {
  if (!error) return null;
  return PROVIDER_ERROR_OUTCOME[error] ?? 'provider_error';
}

/** The nonce cookie for a system. Absent is what a replayed callback looks like. */
export function readCookie(header: string, name: string): string | null {
  for (const part of header.split(';')) {
    const [key, ...rest] = part.trim().split('=');
    if (key === name) return rest.join('=') || null;
  }
  return null;
}

export function acquisitionCookie(slug: string): string {
  return `signora_acq_${slug}`;
}
