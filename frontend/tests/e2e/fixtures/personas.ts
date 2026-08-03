/**
 * Who the suite signs in as.
 *
 * **Read from `infra/demo-users.json`, which already exists** and is already
 * read by the Next tier's `demo:users` script and by the backend's Playground
 * seeder. A fourth list of the same four people would disagree with the other
 * three the first time any of them changed, and the disagreement would look
 * like a permissions bug (CLAUDE.md §2 — one authoritative representation).
 *
 * These accounts are not a test fixture in the usual sense. Every one was
 * created through Better Auth's own sign-up route and verified through its own
 * verification route, and every one is enrolled in the seeded organization by
 * the seeder. **The suite signs in exactly as a customer does**, with an
 * address and a password, against the real authentication tier.
 */

import { readFileSync } from 'node:fs';
import { join } from 'node:path';

export type WorkspaceRole = 'owner' | 'member';

export interface Persona {
  email: string;
  name: string;
  persona: string;
  role: WorkspaceRole;
}

interface DemoUsers {
  password: string;
  users: Persona[];
}

function load(): DemoUsers {
  // `tests/e2e/fixtures` → `frontend` → repository root.
  const path = join(process.cwd(), '..', 'infra', 'demo-users.json');
  return JSON.parse(readFileSync(path, 'utf8')) as DemoUsers;
}

const declared = load();

export const PASSWORD = declared.password;

/** Everyone the Playground knows about, in the order the file declares. */
export const PERSONAS: readonly Persona[] = declared.users;

function byRole(role: WorkspaceRole): Persona {
  const found = PERSONAS.find((user) => user.role === role);
  if (!found) {
    throw new Error(
      `infra/demo-users.json declares no ${role}. The suite signs in as one of each, ` +
        'so a list without both cannot exercise the permission boundary.',
    );
  }
  return found;
}

/** Dana — Revenue Operations. Administers the organization. */
export const OWNER = byRole('owner');

/** Sam — Sales Development. Triages the list and administers nothing. */
export const MEMBER = byRole('member');

/** Where each persona's signed-in browser state is kept between tests. */
export function storageStatePath(email: string): string {
  return join('tests', 'e2e', '.auth', `${email.replace(/[^a-z0-9]/gi, '-')}.json`);
}
