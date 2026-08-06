/**
 * *"Never a second search box"* — the App Shell's invariant, made enforceable.
 *
 * **The approved shell states a rule about the whole product and nothing in
 * the repository could enforce it** ([450 §5](../../../docs/architecture/450-global-search-traceability-audit.md)):
 * *"a structural test that refuses a second search input outside the shell.
 * Cheap, and it is the fourth instance of a pattern the frontend already uses
 * three times."* **The three are `vocabulary.test.tsx`, `design-tokens.test.tsx`
 * and `no-mock-data.test.tsx`**, and this is written to their shape
 * deliberately — a rule kept by discipline is documentation pretending to be
 * code (§2).
 *
 * ### What it forbids, and the reading behind it
 *
 * ⚠️ **All three precedents forbid a *practice*, never an element.** Vocabulary
 * forbids engineering words reaching a screen; design tokens forbid literal
 * colours; no-mock-data forbids fabricated records. **So this forbids a second
 * *implementation* of search, not a second input.**
 *
 * **The narrower reading — no `<input>` anywhere but the shell — was rejected
 * on the specification's own evidence**: [410](../../../docs/architecture/410-approved-ui-specification.md)
 * approves a *Search by name* on Companies **and** the shell's global search,
 * so a test forbidding the second would refuse an approved screen. **What the
 * invariant protects is that there is one search: one request path, one cache
 * identity, one global entry.** A screen may *use* it — reuse is the point —
 * and may not build another.
 *
 * ⛔ **If the product owner meant the literal reading, this test is where that
 * ruling lands**, and it is one line stricter rather than a redesign.
 *
 * ### Why now, when nothing violates it
 *
 * **Because nothing violates it yet.** The guard is being written at the only
 * moment it costs nothing, and the pressure is already real: TASK-440's
 * Companies screen wants a search, and the cheap way to give it one is a
 * second `apiRequest` beside the first.
 */
import { readFileSync, readdirSync, statSync } from 'node:fs';
import { extname, join } from 'node:path';

import { describe, expect, it } from 'vitest';

const ROOTS = ['app', 'components', 'lib'];

function walk(dir: string): string[] {
  return readdirSync(dir).flatMap((entry) => {
    const full = join(dir, entry);
    if (statSync(full).isDirectory()) return walk(full);
    return ['.ts', '.tsx'].includes(extname(full)) ? [full] : [];
  });
}

const SOURCES = ROOTS.flatMap((root) => walk(join(process.cwd(), root))).map((path) => ({
  name: path.replace(`${process.cwd()}/`, ''),
  source: readFileSync(path, 'utf8'),
}));

/** The one file allowed to reach the search endpoint. */
const THE_REQUEST = 'lib/query/hooks/search.ts';

/** The one file allowed to build the search cache key. */
const THE_KEY = 'lib/query/keys.ts';

/** The one component that is the global search, and the one place it mounts. */
const THE_BOX = 'components/intelligence/account-search.tsx';
const THE_SHELL = 'components/shell/';

describe('there is one search', () => {
  it('reaches the search endpoint from exactly one file', () => {
    // **A second request path is a second contract.** B-208 is what that costs
    // even when there is only one: the client and the server disagreed about
    // the response shape for a whole milestone, and a second caller would have
    // had to learn the correction separately.
    const offenders = SOURCES.filter(
      ({ name, source }) => name !== THE_REQUEST && source.includes('/account-search?'),
    ).map(({ name }) => name);

    expect(offenders).toEqual([]);
  });

  it('builds the search cache key in exactly one file', () => {
    // Two constructions of one key are two cache identities for one question,
    // and the second one is stale the first time the first one invalidates.
    const offenders = SOURCES.filter(
      ({ name, source }) =>
        name !== THE_KEY && name !== THE_REQUEST && /accountSearch\s*[:(]/.test(source),
    ).map(({ name }) => name);

    expect(offenders).toEqual([]);
  });

  it('mounts the global search only in the shell', () => {
    // **Search is a verb, not a place** (A1) — it belongs to the frame, and a
    // second mount would make it a place on one screen and a verb everywhere
    // else.
    const offenders = SOURCES.filter(
      ({ name, source }) =>
        !name.startsWith(THE_SHELL) && name !== THE_BOX && source.includes('<AccountSearch'),
    ).map(({ name }) => name);

    expect(offenders).toEqual([]);
  });

  it('leaves the shell able to mount it, so the guard cannot pass vacuously', () => {
    // **A guard that cannot fail is documentation pretending to be code** (§2).
    // If the shell ever stops mounting search, the three checks above go on
    // passing over a product that has no search at all.
    const shell = SOURCES.find(({ name }) => name === 'components/shell/app-shell.tsx');

    expect(shell?.source).toContain('<AccountSearch />');
  });
});
