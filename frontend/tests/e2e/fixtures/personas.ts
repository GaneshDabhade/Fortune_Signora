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
  /**
   * Which part of the suite an account is set aside for, if any.
   *
   * **A suite concern, and the product models it no more than it models the
   * sales titles in `persona`.** Declared in the file rather than derived from
   * position here, because `find(role === 'owner')` made the ordinary owner a
   * function of array order — reorder the file and the whole suite quietly
   * signs in as somebody else.
   */
  reserved_for?: string;
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

/**
 * The journeys that permanently create organizations, and the account they own.
 *
 * **B-1017.** `organization-setup.spec.ts` and `onboarding-journey.spec.ts`
 * create an organization and leave it — correctly, because the product offers
 * no delete and a test asserting one would assert a path that does not exist.
 * Run on the ordinary owner, that growth reached every later spec: the persona
 * became a member of four organizations, `/` resolved to the chooser, and
 * **36 of 392 browser tests failed about nothing.**
 *
 * Measured: the environment rebuilt and the three worst-hit specs run alone —
 * **67 passed, 0 failed, one workspace row afterwards.** Ten of those failed in
 * the full run.
 */
const MUTATING = 'mutating-journeys';

function reserved(): Persona {
  const found = PERSONAS.find((user) => user.reserved_for === MUTATING);
  if (!found) {
    throw new Error(
      `infra/demo-users.json declares no account reserved for ${MUTATING}. ` +
        'The journeys that create organizations would fall back to the ordinary ' +
        'owner and contaminate every spec that runs after them (B-1017).',
    );
  }
  if (found.role !== 'owner') {
    throw new Error(
      `the ${MUTATING} account must be an owner. Signora refuses /settings to a ` +
        'member — the client guard redirects and the server refuses the write — ' +
        'so the screen under test would be unreachable.',
    );
  }
  return found;
}

function byRole(role: WorkspaceRole): Persona {
  const found = PERSONAS.find(
    (user) => user.role === role && user.reserved_for !== MUTATING,
  );
  if (!found) {
    throw new Error(
      `infra/demo-users.json declares no unreserved ${role}. The suite signs in as ` +
        'one of each, so a list without both cannot exercise the permission boundary.',
    );
  }
  return found;
}

/** Dana — Revenue Operations. Administers the organization. */
export const OWNER = byRole('owner');

/** Sam — Sales Development. Triages the list and administers nothing. */
export const MEMBER = byRole('member');

/** Quinn — the second owner, and the only account whose memberships may grow. */
export const MUTATOR = reserved();

/** Where each persona's signed-in browser state is kept between tests. */
export function storageStatePath(email: string): string {
  return join('tests', 'e2e', '.auth', `${email.replace(/[^a-z0-9]/gi, '-')}.json`);
}
