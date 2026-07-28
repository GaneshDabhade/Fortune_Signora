'use client';

/**
 * Browser-side auth client.
 *
 * Only ever talks to our own Next.js routes — never directly to the API and
 * never to an OAuth provider. Keeping the browser one hop away from both is
 * what stops credentials and the signing key reaching it.
 */

import { createAuthClient } from 'better-auth/react';

export const authClient = createAuthClient();

export async function signIn(provider: string): Promise<void> {
  await authClient.signIn.social({ provider, callbackURL: '/workspaces' });
}

export async function signOut(): Promise<void> {
  await authClient.signOut();
  window.location.href = '/sign-in';
}

export const useSession = authClient.useSession;
