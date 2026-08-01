/**
 * Create the Playground's sign-in accounts.
 *
 *     npm run demo:users
 *
 * ## This is not a bypass, and the shape is what proves it
 *
 * Every account is created by **`auth.api.signUpEmail`** — the same handler the
 * browser's sign-up form reaches — with a password Better Auth hashes and a
 * verification token **Better Auth mints**. The account is then verified
 * through `auth.api.verifyEmail`, which is the route the emailed link resolves
 * to. Nothing about the authentication pipeline differs from a real customer's.
 * The accounts simply already exist.
 *
 * The alternative that was rejected: writing rows into `auth.user` with a
 * hash we computed. That is authentication logic Signora would then own, in
 * the one subsystem where a vendor was bought precisely so it would not
 * (ADR-0010).
 *
 * ## Why it needs no running server
 *
 * `auth.api.*` is Better Auth's server-side surface — the same code the HTTP
 * route delegates to. Going over HTTP would work and would make seeding
 * require a dev server, for no additional fidelity.
 *
 * ## Why it refuses outside a developer's machine
 *
 * It creates accounts with a published password. On the same terms as the
 * console email transport: **a startup failure, not a runtime check**, because
 * the failure mode of getting it wrong is silent.
 */

import { readFileSync } from 'node:fs';
import { join } from 'node:path';

import { createEmailVerificationToken } from 'better-auth/api';

import { environmentName, loadAuthConfig } from '@/lib/auth/config';
import { createAuth, getAuthPool } from '@/lib/auth/server';

interface DemoUser {
  email: string;
  name: string;
  persona: string;
  role: string;
}

interface DemoUsers {
  password: string;
  users: DemoUser[];
}

/** One list, read by this script and by the backend seeder that enrols them.
 * Two lists would disagree about who exists the first time either changed. */
function demoUsers(): DemoUsers {
  const path = join(process.cwd(), '..', 'infra', 'demo-users.json');
  return JSON.parse(readFileSync(path, 'utf8')) as DemoUsers;
}

async function main(): Promise<void> {
  const environment = environmentName();
  if (!['local', 'test', 'development'].includes(environment)) {
    throw new Error(
      `Refusing to create demo accounts: SIGNORA_ENVIRONMENT='${environment}' is a deployed ` +
        'environment, and these accounts share a password published in RUNNING.md.',
    );
  }

  const config = loadAuthConfig();
  const auth = createAuth(config);
  const { password, users } = demoUsers();

  for (const user of users) {
    try {
      await auth.api.signUpEmail({
        body: { name: user.name, email: user.email, password },
      });
    } catch (error) {
      // Already there. Re-running seeding must not fail, and must not reset a
      // password somebody may have deliberately changed while reviewing.
      const message = error instanceof Error ? error.message : String(error);
      if (!/exist/i.test(message)) throw error;
      console.log(`  ${user.email.padEnd(32)} already exists`);
      continue;
    }

    // Better Auth mints the token; Better Auth verifies it. The emailed link
    // resolves to exactly this call, so the account reaches the same state a
    // person reaches by clicking it — rather than a state only a seeder knows
    // how to produce.
    const token = await createEmailVerificationToken(config.betterAuthSecret, user.email);
    await auth.api.verifyEmail({ query: { token } });

    console.log(`  ${user.email.padEnd(32)} created and verified · ${user.role}`);
  }

  console.log(`\n  password for all of them: ${password}`);
  console.log('  run `make demo-seed` to enrol them in the Playground workspace.\n');

  await getAuthPool(config).end();
}

main().catch((error: unknown) => {
  console.error(error instanceof Error ? error.message : error);
  process.exitCode = 1;
});
