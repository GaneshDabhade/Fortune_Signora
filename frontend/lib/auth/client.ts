'use client';

/**
 * Browser-side auth client.
 *
 * Only ever talks to our own Next.js routes — never directly to the API and
 * never to an OAuth provider. Keeping the browser one hop away from both is
 * what stops credentials and the signing key reaching it.
 *
 * **Every function here ends in the same place: a Better Auth session.** An
 * address and a password, a Google redirect, a Microsoft redirect — the method
 * differs and the session does not, and the JWT minted from it carries no
 * record of which was used (ADR-0033). Nothing downstream can tell them apart,
 * which is what makes the next method free.
 */

import { createAuthClient } from 'better-auth/react';

export const authClient = createAuthClient();

/**
 * Where a person lands once they are signed in: the attention list, which is
 * a seller's morning.
 *
 * **It said `/workspaces` and no such route has ever existed.** The comment
 * here argued for workspace selection over the product — a reasonable
 * argument about a page nobody built, and the address it named returned
 * *"That address does not lead anywhere"* to every person who ever signed in.
 *
 * D38 recorded exactly this and fixed only half of it: the password form
 * calls `router.push('/')` after a successful sign-in, which reads like the
 * defect was closed. It is not — Better Auth performs its own navigation to
 * `callbackURL`, and it wins. **A fix that cannot change the outcome is a
 * comment claiming a correctness property the code does not have**, and it
 * survived because no test has ever signed in.
 *
 * A brand-new account with no organization is answered by the attention list
 * itself, which says so and offers to create one — so the destination this
 * constant used to argue for is a screen the product already has.
 */
const AFTER_SIGN_IN = '/';

export async function signIn(provider: string): Promise<void> {
  await authClient.signIn.social({ provider, callbackURL: AFTER_SIGN_IN });
}

/**
 * The failure a caller can show a person.
 *
 * **Deliberately not the vendor's message.** Better Auth distinguishes *no
 * such user* from *wrong password*, and surfacing that distinction turns the
 * sign-in form into an address-enumeration oracle. One sentence covers both.
 */
export interface AuthResult {
  ok: boolean;
  error?: string;
}

function failed(message: string): AuthResult {
  return { ok: false, error: message };
}

export async function signInWithPassword(
  email: string,
  password: string,
): Promise<AuthResult> {
  const { error } = await authClient.signIn.email({
    email,
    password,
    callbackURL: AFTER_SIGN_IN,
  });

  if (!error) return { ok: true };
  // 403 is Better Auth's "verify your address first", which is the one
  // failure a person can act on and the one that is not a credential hint.
  if (error.status === 403) {
    return failed('Verify your email address before signing in.');
  }
  return failed('That email and password do not match an account.');
}

export async function signUpWithPassword(
  name: string,
  email: string,
  password: string,
): Promise<AuthResult> {
  const { error } = await authClient.signUp.email({ name, email, password });

  if (!error) return { ok: true };
  // Better Auth reports an existing address here, and unlike sign-in this is
  // not an enumeration leak worth closing: a sign-up form that accepted a
  // duplicate silently would leave somebody waiting for an email that is
  // never coming. The honest message is the usable one.
  if (error.status === 422) {
    return failed('An account already exists for that address. Try signing in.');
  }
  return failed(error.message ?? 'That account could not be created.');
}

export async function requestPasswordReset(email: string): Promise<AuthResult> {
  const { error } = await authClient.requestPasswordReset({
    email,
    redirectTo: '/reset-password',
  });

  // **The same answer either way, on purpose.** A response that differed for
  // an unknown address would make this form the enumeration oracle the
  // sign-in form refuses to be.
  return error ? failed('That request could not be sent. Try again.') : { ok: true };
}

export async function resetPassword(
  token: string,
  password: string,
): Promise<AuthResult> {
  const { error } = await authClient.resetPassword({ token, newPassword: password });

  if (!error) return { ok: true };
  return failed('That reset link has expired or has already been used.');
}

export async function resendVerification(email: string): Promise<AuthResult> {
  const { error } = await authClient.sendVerificationEmail({
    email,
    callbackURL: AFTER_SIGN_IN,
  });

  return error ? failed('That could not be sent. Try again.') : { ok: true };
}

export async function signOut(): Promise<void> {
  await authClient.signOut();
  window.location.href = '/sign-in';
}

export const useSession = authClient.useSession;
