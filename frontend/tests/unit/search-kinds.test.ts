/**
 * **The search's kinds, against the enum they mirror** — 🔴 [B-288](../../../docs/BUGS.md).
 *
 * ## ⛔ Why this test exists at all
 *
 * `SearchResultType` is a hand-written copy of `EntityKind` in
 * `backend/modules/knowledge_graph/domain/identity.py`, and 📁 §2 is explicit
 * about what that is: *"truth has exactly one authoritative representation;
 * everything else derives from it… duplicated truth eventually becomes
 * contradictory truth."*
 *
 * ⚠️ **It did.** `PERSON` was added to the enum on 2026-08-06 for the `people`
 * context. The search endpoint returns **one group per kind**, so from that day
 * every search returned a `person` group, `KIND_LABEL['person']` was
 * `undefined`, and `.toLowerCase()` threw — ⛔ **taking down the whole search
 * region**, not one row. A seller typing an account name got *"Signora could not
 * load account search"* and lost the search box until they reloaded.
 *
 * ⚡ **`Record<SearchResultType, string>` would have caught the missing label** —
 * it is exactly the *"types should make incorrect architecture impossible"*
 * shape. ⛔ **But the union was missing the member too**, so the map was total
 * over a set that had itself gone stale, and nothing refused.
 *
 * ## ⚡ So the assertion is against the source of truth, not against a copy
 *
 * **Reading the Python is the point.** 📁 The precedent is
 * `envelope-contract.test.ts` and `breadcrumb.test.ts`, which read the hooks and
 * the design snapshot rather than restating them.
 */
import { readFileSync } from 'node:fs';
import { join } from 'node:path';

import { describe, expect, it } from 'vitest';

const IDENTITY = join(
  process.cwd(),
  '..',
  'backend',
  'modules',
  'knowledge_graph',
  'domain',
  'identity.py',
);

/** The `EntityKind` members, read from the enum itself. */
function entityKinds(): string[] {
  const source = readFileSync(IDENTITY, 'utf8');
  const start = source.indexOf('class EntityKind(StrEnum):');
  expect(start, 'EntityKind is not where this test expects it').toBeGreaterThan(-1);
  // ⛔ **Bounded to this class**, so a later enum in the same file cannot leak
  // members in and make the assertion pass for the wrong reason.
  const next = source.indexOf('\nclass ', start + 1);
  const body = source.slice(start, next === -1 ? undefined : next);
  return [...body.matchAll(/^\s{4}([A-Z_]+)\s*=\s*"([a-z_]+)"/gm)].map((m) => m[2]!);
}

/**
 * The union's members, read from the type rather than imported — ⚡ **a
 * TypeScript union does not exist at runtime**, so there is nothing to import.
 */
function searchResultTypes(): string[] {
  const source = readFileSync(join(process.cwd(), 'lib', 'api', 'types.ts'), 'utf8');
  const match = source.match(/export type SearchResultType =([^;]+);/);
  expect(match, 'SearchResultType is not where this test expects it').not.toBeNull();
  return [...match![1]!.matchAll(/'([a-z_]+)'/g)].map((m) => m[1]!);
}

describe('🔴 the search kinds mirror the graph exactly', () => {
  it('the enum is read, and it has more than one member', () => {
    // ⚠️ **A regex that matched nothing would make every assertion below
    // vacuously true**, which is the failure this whole file exists to catch.
    expect(entityKinds().length).toBeGreaterThan(1);
    expect(entityKinds()).toContain('person');
  });

  it('⛔ every kind the graph knows about has a name the product can render', () => {
    // 📁 The endpoint returns one group per kind, so a kind absent here is a
    // crash rather than a gap.
    expect(searchResultTypes().sort()).toEqual(entityKinds().sort());
  });

  it('⛔ and the union invents nothing the graph does not have', () => {
    // ⚡ The other direction matters too: a member here that the backend never
    // sends is a label for a group that cannot arrive, which reads as coverage
    // the product does not have.
    for (const kind of searchResultTypes()) {
      expect(entityKinds(), `${kind} is not an EntityKind`).toContain(kind);
    }
  });
});
