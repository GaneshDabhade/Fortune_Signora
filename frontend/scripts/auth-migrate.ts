/**
 * Create or update Better Auth's own tables.
 *
 * ## Why this exists
 *
 * **Nothing in the repository has ever created them.** The `auth` schema is
 * created by backend migration `0005`, and the tables inside it are Better
 * Auth's — owned by the vendor, versioned with the vendor, and reshaped by a
 * vendor upgrade. Alembic must not own them: Signora would then be maintaining
 * a hand-written copy of another system's schema, and the two would disagree
 * on the first upgrade.
 *
 * So there was a gap: a fresh clone had a schema with no tables in it, and
 * **sign-in could not work by any method.** Nobody noticed because the only
 * offered methods were OAuth, and no OAuth credentials were configured either
 * — the first failure hid the second.
 *
 * ## Why it is a script rather than the vendor's CLI
 *
 * `@better-auth/cli` would do this and is a dependency this repository does
 * not have. `better-auth/db` exposes the same migrations programmatically, so
 * the already-approved dependency (ADR-0010) is sufficient and the setup step
 * is a committed, reviewable file rather than a command in a README.
 *
 * ## What it does not do
 *
 * It does not run automatically, and no service runs it at boot. Schema
 * changes execute as a discrete step under a credential that may perform DDL
 * — the same rule the Python tier follows, for the same reason.
 *
 *     npm run auth:migrate
 */

import { getMigrations } from 'better-auth/db/migration';

import { createAuth, getAuthPool } from '@/lib/auth/server';
import { loadAuthConfig } from '@/lib/auth/config';

async function main(): Promise<void> {
  const config = loadAuthConfig();
  // `createAuth` returns the configured instance; `getMigrations` wants the
  // options that produced it, which the instance carries.
  const auth = createAuth(config);
  const { toBeCreated, toBeAdded, runMigrations } = await getMigrations(auth.options);

  const creating = toBeCreated.map((t) => t.table);
  const altering = toBeAdded.map((t) => t.table);

  if (creating.length === 0 && altering.length === 0) {
    console.log(`auth schema "${config.authSchema}" is already up to date.`);
    await getAuthPool(config).end();
    return;
  }

  if (creating.length > 0) console.log(`creating: ${creating.join(', ')}`);
  if (altering.length > 0) console.log(`altering: ${altering.join(', ')}`);

  await runMigrations();
  console.log(`auth schema "${config.authSchema}" is ready. Sign-in will work now.`);
  await getAuthPool(config).end();
}

main().catch((error: unknown) => {
  console.error(error instanceof Error ? error.message : error);
  process.exitCode = 1;
});
