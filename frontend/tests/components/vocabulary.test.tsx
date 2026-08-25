/**
 * ADR-0034 — the customer's vocabulary and the platform's are separate.
 *
 * Signora has two ubiquitous languages and both are correct. A customer says
 * *organization*, *account*, *opportunity*, *evidence*. The platform says
 * *workspace*, *tenant*, *provider*, *entity*, *business event*. This asserts
 * that the second never reaches a screen.
 *
 * ### Why a test rather than a glossary
 *
 * Every string this would have caught was written deliberately, by an engineer
 * who had read the architecture, in a codebase whose constitution already
 * demands a consistent ubiquitous language. They were not carelessness — they
 * are what happens when **the only vocabulary written down is the internal
 * one**, and an engineer reaching for the right word finds `Workspace` because
 * it is the only word the repository has.
 *
 * The worst of them was not copy at all: a password sign-in redirected to
 * `/workspaces`, a route that has never existed, because the code was
 * reasoning about a tenancy concept while the product needed a destination.
 *
 * *A guard that cannot fail is documentation pretending to be code*, and a
 * glossary nobody can violate is the same thing.
 *
 * ### What it deliberately does not check
 *
 * Identifiers, imports, types, hooks, query keys, API paths and comments —
 * all of which **should** say `workspace`, because ADR-0034 forbids the rename
 * travelling inward. The same file may legitimately contain `workspaceId`
 * fifteen times and must never contain the word in a sentence. That asymmetry
 * is the whole point.
 */
import { readFileSync, readdirSync, statSync } from 'node:fs';
import { extname, join } from 'node:path';

import { describe, expect, it } from 'vitest';

const ROOTS = ['app', 'components'];

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
 * Platform vocabulary. Correct, load-bearing, and never on a screen.
 *
 * `provider` is deliberately absent: it is legitimate customer-facing
 * *evidence* — *"reported by CoreSignal and Apollo"* — which ADR-0034 permits
 * and the product owner's ruling explicitly preserves. What is forbidden is
 * provider *configuration*, and no screen offers any.
 */
const INTERNAL_TERMS = [
  'workspace',
  'tenant',
  'tenancy',
  'knowledge graph',
  'business event',
  'buying score',
  'signal catalog',
  'signal profile',
  'scoring model',
  'evidence set',
  'prompt registry',
  'outbox',
  'event bus',
  'pipeline stage',
  'composition root',
];

/**
 * Strip everything a customer never reads, leaving only prose.
 *
 * Comments go first and matter most: this file, every ADR reference, and every
 * explanation of *why* a screen says `organization` all contain the word
 * `workspace`, and a scan that flagged them would be unusable within a week —
 * which is how a well-meant lint rule gets deleted.
 */
function prose(source: string): string {
  return source.replace(/\/\*[\s\S]*?\*\//g, ' ').replace(/(^|[^:])\/\/.*$/gm, '$1 ');
}

/**
 * Prose, or a fragment of TSX that merely sat between a `>` and a `<`.
 *
 * TSX is full of both — `) : workspaces.length === 0 ? (` lives between two
 * angle brackets in every conditional render, and a scan that reported it
 * would be reporting an identifier, which this test exists *not* to do.
 * A sentence a customer reads starts with a word and contains no syntax.
 */
function isSentence(candidate: string): boolean {
  // `\s` rather than a literal space: JSX prose is wrapped by the formatter,
  // so most real sentences span lines. Requiring a single line rejected the
  // one genuine finding this test first produced — a false negative is worse
  // than a false positive here, because nobody investigates a passing test.
  return /^[A-Za-z][A-Za-z0-9\s,.'’“”"—–…:;!?%&()/-]*$/.test(candidate.trim());
}

/**
 * Every string a human reads: JSX text, and the props that render as words.
 *
 * `aria-label` is included on purpose. A screen-reader user hearing *"active
 * workspace"* would be the only customer ever told the internal term, which is
 * the worst possible place for one to survive.
 */
function humanReadable(source: string): string[] {
  // **`${…}` is stripped first.** `` `Created ${workspace.name}` `` renders as
  // *"Created Acme Revenue"* — the identifier is code, and the customer never
  // sees the word.
  const text = prose(source).replace(/\$\{[^}]*\}/g, ' ');
  const found: string[] = [];

  // `title="…"`, `description="…"`, `label="…"`, `placeholder="…"`,
  // `message: '…'`, `aria-label="…"` — the props that reach a reader.
  //
  // 🔴 **`subject` was missing and it is the sharpest of them.** ⛔ It is not
  // decoration: `StatedAbsence` composes it into a sentence — *"Signora could
  // not load ${subject}."* — **so its whole purpose is to be read.** ⚡ **A
  // customer was told *"Signora could not load your workspaces"*** on the audit
  // screen, and this guard could not see it because the population named eight
  // props and not the ninth.
  //
  // ⚠️ **The population was too NARROW, which fails silently** — the guard was
  // green throughout, which is the worst way for a guard to be wrong.
  const props =
    /(?:title|description|label|placeholder|message|detail|hint|heading|subject|aria-label)\s*[=:]\s*["'`]([^"'`]+)["'`]/gi;
  for (const match of text.matchAll(props)) found.push(match[1] ?? '');

  // JSX text nodes: `>Some words<`, with expressions and tags excluded.
  for (const match of text.matchAll(/>([^<>{}]{3,})</g)) {
    const candidate = match[1] ?? '';
    if (isSentence(candidate)) found.push(candidate);
  }

  return found.filter((s) => /[a-z]{3}/i.test(s));
}

describe('the platform vocabulary never reaches a customer', () => {
  it('uses no internal term in a string a human reads', () => {
    const pattern = new RegExp(`\\b(?:${INTERNAL_TERMS.join('|')})s?\\b`, 'i');

    const offenders = SOURCES.flatMap(({ name, source }) =>
      humanReadable(source)
        .filter((line) => pattern.test(line))
        .map((line) => `${name}: "${line.trim()}"`),
    );

    expect(
      offenders,
      'ADR-0034: a customer says "organization", the platform says "workspace". ' +
        'Internal vocabulary belongs in code, schema and docs/architecture — never in ' +
        'a sentence somebody reads.',
    ).toEqual([]);
  });

  /**
   * 🔴 **What a customer's address bar shows, not what the source says.**
   *
   * ⚠️ **A template literal names its variable, and the variable is engineering's
   * word.** `router.push(`/w/${workspaceId}/home`)` renders `/w/<uuid>/home` — ⛔
   * **which contains no platform term** — but the source text contains
   * `workspaceId`, and both assertions below read source text.
   *
   * ⚡ **So an interpolation collapses to `*` before either check**, which is
   * exactly what the route-existence check already does to `[workspaceId]` on the
   * filesystem side. ✅ **The term check still bites on the LITERAL segments**:
   * `/workspace/${id}` normalises to `/workspace/*` and is still caught.
   */
  const asRendered = (path: string) => path.replace(/\$\{[^}]*\}/g, '*');

  it('routes a customer to no path named after a platform concept', () => {
    // The address bar is user-visible text. `/workspaces` was a redirect
    // target for three slices and never a route — the vocabulary leak and a
    // dead link were the same defect.
    const offenders = SOURCES.flatMap(({ name, source }) =>
      [
        ...prose(source).matchAll(
          /(?:href|router\.(?:push|replace))[=(\s]+["'`](\/[^"'`]*)/g,
        ),
      ]
        .map((match) => asRendered(match[1] ?? ''))
        .filter((path) =>
          new RegExp(`\\b(?:${INTERNAL_TERMS.join('|')})`, 'i').test(path),
        )
        .map((path) => `${name}: ${path}`),
    );

    expect(offenders).toEqual([]);
  });

  it('sends a customer only to routes that exist', () => {
    // The rule the dead redirect actually broke. A destination nobody can
    // reach is worse than a missing link: it looks like the product failing.
    const routes = new Set(
      walk(join(process.cwd(), 'app'))
        .filter((path) => /\/page\.tsx$/.test(path))
        .map((path) =>
          path
            .replace(`${join(process.cwd(), 'app')}`, '')
            .replace(/\/page\.tsx$/, '')
            // Route groups — `(app)`, `(auth)` — are organisational and do
            // not appear in a URL.
            .replace(/\/\([^)]+\)/g, '')
            .replace(/\/\[[^\]]+\]/g, '/*'),
        )
        .map((route) => (route === '' ? '/' : route)),
    );

    const offenders = SOURCES.flatMap(({ name, source }) =>
      [...prose(source).matchAll(/router\.(?:push|replace)\(\s*["'`](\/[^"'`?#]*)/g)]
        .map((match) => asRendered(match[1] ?? '').replace(/\/$/, '') || '/')
        .filter(
          (path) => !routes.has(path) && !routes.has(path.replace(/\/[^/]+$/, '/*')),
        )
        .map((path) => `${name}: router.push("${path}")`),
    );

    expect(
      offenders,
      `Navigates somewhere with no page. Routes that exist: ${[...routes].sort().join(', ')}`,
    ).toEqual([]);
  });
});

describe('the customer vocabulary is the one on screen', () => {
  it('offers an organization where it used to offer a workspace', () => {
    // A positive control. The two tests above pass trivially if the strings
    // are simply deleted, so this asserts the replacement is present and the
    // screens still say something.
    const settings = SOURCES.find(({ name }) => name.endsWith('settings/page.tsx'));
    const empty = SOURCES.find(({ name }) => name.endsWith('no-workspace.tsx'));

    expect(settings?.source).toMatch(/New organization/);
    expect(empty?.source).toMatch(/organization/i);
  });
});
