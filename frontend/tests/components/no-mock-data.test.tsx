/**
 * AC-14 — no mock business data in the codebase.
 *
 * The rule that keeps M1.5 a platform milestone rather than a half-built
 * product. A page built against hand-written JSON encodes a shape the
 * domain does not have; the mock becomes the contract, the real model
 * arrives, and the page is rewritten — twice the work, and the first
 * version silently teaches everyone the wrong model.
 *
 * Asserted rather than assumed, because the temptation to "just add a
 * couple of rows so the table looks right" is strongest at exactly the
 * moment nobody is checking.
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

/**
 * Domain nouns that have no shipped module. A literal of one of these in
 * application code is fabricated business data — the API cannot return it,
 * because nothing produces it yet.
 *
 * Workspace and membership are deliberately absent: Workspace & Tenancy is
 * shipped, so those come from the real API.
 */
const BUSINESS_NOUNS = [
  'company',
  'companies',
  'opportunity',
  'opportunities',
  'signal',
  'buyingScore',
  'buying_score',
  'recommendation',
  'observation',
  'businessEvent',
  'business_event',
];

describe('no mock business data', () => {
  it('defines no array of fabricated business records', () => {
    // Matches `const companies = [` and `const mockSignals = [` — the
    // shape a fixture takes. Not a general ban on the words: navigation
    // labels and empty-state copy legitimately name these concepts.
    const pattern = new RegExp(
      `(?:const|let|var)\\s+\\w*(?:${BUSINESS_NOUNS.join('|')})\\w*\\s*(?::[^=]+)?=\\s*\\[`,
      'i',
    );

    const offenders = SOURCES.filter(({ source }) => pattern.test(source)).map(
      (s) => s.name,
    );

    expect(
      offenders,
      'Business screens are built against real domain contracts produced by ' +
        'the Provider Simulation Framework (M2.0), never against fixtures.',
    ).toEqual([]);
  });

  it('names no file as a fixture, mock, or stub', () => {
    const offenders = SOURCES.filter(({ name }) =>
      /(?:^|\/)(?:mock|fixture|stub|sample|dummy|fake)[-.\w]*\.tsx?$/i.test(name),
    ).map((s) => s.name);

    expect(offenders).toEqual([]);
  });

  it('imports no business query hook that cannot exist yet', () => {
    // The API exposes workspaces and members. A hook for anything else is
    // either dead code or fabricating a response.
    const offenders = SOURCES.filter(({ source }) =>
      /use(?:Companies|Opportunities|Signals|Recommendations|Timeline)\b/.test(source),
    ).map((s) => s.name);

    expect(offenders).toEqual([]);
  });
});

describe('empty states are first-class', () => {
  it('every "coming soon" navigation entry has no route implementation', () => {
    // A nav item marked Soon must not quietly have a page behind it, and a
    // page must not exist without data to fill it.
    //
    // **Rewritten at M12.1, and the rewrite is the point.** This asserted
    // that *no* business route existed, which was true while no business
    // module had a customer-facing endpoint. `/opportunities` now has one.
    // The durable rule is the one asserted here: a route exists exactly when
    // its nav entry has stopped saying Soon — so a page behind a Soon link,
    // or a Soon link over a shipped page, both still fail.
    const navigation = readFileSync(join(process.cwd(), 'components/shell/navigation.tsx'), 'utf8');

    const routes = SOURCES.filter(({ name }) => /^app\/.*\/page\.tsx$/.test(name)).map(
      (s) => s.name,
    );

    const soon = [...navigation.matchAll(/href: '\/([a-z-]+)'[^}]*comingSoon: true/g)].map(
      (m) => m[1],
    );

    const behindSoonLinks = routes.filter((route) =>
      soon.some((section) => route.includes(`/${section}/`)),
    );

    expect(
      behindSoonLinks,
      'a page exists behind a navigation entry still marked Soon',
    ).toEqual([]);
    expect(soon, 'sections still awaiting their module').toEqual([
      'companies',
      'signals',
      'timeline',
    ]);
  });

  it('EmptyState requires a description, not only a title', () => {
    const source = readFileSync(
      join(process.cwd(), 'components/ui/empty-state.tsx'),
      'utf8',
    );

    // Optional would allow "No data" as the whole of an empty state.
    expect(source).toMatch(/\n\s*description: string;/);
    expect(source).not.toMatch(/\n\s*description\?: string;/);
  });
});
