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

/**
 * ⛔ **The population of DIRECTORIES is under test, not a constant somebody
 * maintains** — 📁 [B-1089](../../../docs/BUGS.md).
 *
 * ⚠️ **`lib` was missing until 2026-08-28**, and four customer-read strings in
 * `lib/settings/sections.ts` reached `/settings` carrying the platform word
 * while this guard was green.
 *
 * ⚡ **That is this file's own `subject` scar one level up.** The comment on
 * `humanReadable` below records a population of PROPS that was too narrow and
 * shipped *"Signora could not load your workspaces"*; **this was a population
 * of ROOTS that was too narrow and shipped four labels on Settings.** ⛔ **Both
 * fail SILENTLY, which is the worst way for a guard to be wrong.**
 */
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

/**
 * ⛔ **An exception carries the id of the decision that ends it, or it is
 * permanent by accident.**
 *
 * ⚠️ **`lib/research/capability.ts` labels a capability `Knowledge graph`, and
 * every one of its eight siblings is a customer phrase** — *"Ask a question"*,
 * *"The answer, with its sources"*, *"Share and export"*. **It is the odd one
 * out and the guard is right to find it.**
 *
 * ⛔ **But choosing its replacement is a word choice with no design statement
 * behind it, and neither a feature lane nor QE may make one.** 📁 **Raised as
 * [C-1579](../../../docs/LANE_COORDINATION.md).** ⚡ **Latent rather than live:
 * nothing renders this module — only a unit test imports it.**
 *
 * ✅ **The second test below is what stops this becoming permanent**: an
 * exception whose offender has gone is removed, loudly, rather than sitting
 * here forgiving nothing.
 */
const AWAITING_A_PRODUCT_DECISION: readonly (readonly [string, string])[] = [
  ['lib/research/capability.ts', 'C-1579'],
];

function offendersIn(sources: typeof SOURCES): string[] {
  const pattern = new RegExp(`\\b(?:${INTERNAL_TERMS.join('|')})s?\\b`, 'i');
  return sources.flatMap(({ name, source }) =>
    humanReadable(source)
      .filter((line) => pattern.test(line))
      .map((line) => `${name}: "${line.trim()}"`),
  );
}

const EXCUSED = new Set(AWAITING_A_PRODUCT_DECISION.map(([file]) => file));

describe('the platform vocabulary never reaches a customer', () => {
  /**
   * ⛔ **The population itself is under test.** ⚡ **`ROOTS` was
   * `['app','components']` until 2026-08-28**, and a guard that walks the wrong
   * directories is green for the same reason an empty one is.
   *
   * ✅ **Asserting that a `lib/` file with human-readable strings was actually
   * READ** — not that the constant contains the string `'lib'`, which would be
   * the constant asserting itself.
   */
  it('⚡ reads lib — the population is under test, not a constant somebody maintains', () => {
    expect(
      SOURCES.some((f) => f.name.startsWith('lib/settings/')),
      'ROOTS must include lib: four customer-read strings on /settings carried ' +
        'the platform word while this guard was green (B-1089)',
    ).toBe(true);
  });

  it('uses no internal term in a string a human reads', () => {
    const offenders = offendersIn(SOURCES).filter(
      (entry) => ![...EXCUSED].some((file) => entry.startsWith(`${file}:`)),
    );

    expect(
      offenders,
      'ADR-0034: a customer says "organization", the platform says "workspace". ' +
        'Internal vocabulary belongs in code, schema and docs/architecture — never in ' +
        'a sentence somebody reads.',
    ).toEqual([]);
  });

  /**
   * ⛔ **An exception list that outlives its cause is how a guard quietly stops
   * guarding.** ⚡ **So every excused file must STILL have an offender**: when
   * the word is finally chosen, this fails and the entry is deleted rather than
   * left behind forgiving something that no longer happens.
   */
  it('⚡ and every excused file is still excusing something — no stale forgiveness', () => {
    for (const [file, item] of AWAITING_A_PRODUCT_DECISION) {
      const still = offendersIn(SOURCES.filter((f) => f.name === file));
      expect(
        still,
        `${file} is excused pending ${item} and no longer has an offender — ` +
          'remove the exception rather than leaving one that forgives nothing',
      ).not.toEqual([]);
    }
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
  const asRendered = (path: string) =>
    path
      .replace(/\$\{[^}]*\}/g, '*')
      // ⚡ **A Next dynamic segment is a placeholder, not text.** 🔴 Widening
      // the matcher above surfaced `components/shell/navigation.tsx`'s
      // `href: '/w/[workspace]/home'` — ⛔ **and no customer ever sees that
      // string.** 📁 `resolved()` substitutes the id before the rail renders
      // it ([B-1060](../../../docs/BUGS.md)), so the address bar reads
      // `/w/<uuid>/home`. **The same collapse the interpolation already gets,
      // for the same reason.**
      .replace(/\[[^\]]*\]/g, '*');

  /**
   * 🔴 **A shipped ROUTE whose name is under decision, and it is not this
   * lane's to rename** — 📁 [C-1517](../../../docs/LANE_COORDINATION.md).
   *
   * ⚠️ **The route assertion's original reason is half spent.** It read:
   * *"`/workspaces` was a redirect target for three slices and never a route —
   * the vocabulary leak and a dead link were the same defect."* ⛔ **The dead
   * link is gone**: `app/workspaces/page.tsx` draws WS-B, and four entry rules
   * plus the Workspace Chooser's rule 7 all land on it.
   *
   * ⚡ **What remains is a genuine conflict between two ratified things.**
   * 📁 [ADR-0034](../../../docs/architecture/adr/0034-ubiquitous-language.md)
   * exempts identifiers — *"no table, column, **API path**, JWT claim, module,
   * type or architecture document is renamed"* — and this guard's own premise
   * is that **an address bar is text somebody reads.** ⛔ **Both are
   * defensible and a lane may not choose**, so the path is excused by id and
   * the question is recorded rather than settled by whoever wrote the last
   * link.
   *
   * ⛔ **Renaming the route is 🔴 Routing** and would move four entry rules, a
   * page, a layout and a gate action.
   */
  const ROUTE_AWAITING_A_PRODUCT_DECISION: readonly (readonly [string, string])[] = [
    ['/workspaces', 'C-1517'],
  ];

  function routeOffenders(sources: typeof SOURCES): string[] {
    return sources.flatMap(({ name, source }) =>
      [
        ...prose(source).matchAll(
          // ⚡ **`:` is in the class, and it was not.** 🔴 `href="/x"` was
          // caught and `href: '/x'` was not — 📁 `lib/entry/gates.ts:111`
          // carries `action: { label: …, href: '/workspaces' }`, and this
          // guard has never seen it. ⛔ **One character wider is the
          // difference between a rule about JSX and a rule about routing.**
          /(?:href|router\.(?:push|replace))[=(:\s]+["'`](\/[^"'`]*)/g,
        ),
      ]
        .map((match) => asRendered(match[1] ?? ''))
        .filter((path) =>
          new RegExp(`\\b(?:${INTERNAL_TERMS.join('|')})`, 'i').test(path),
        )
        .map((path) => `${name}: ${path}`),
    );
  }

  const EXCUSED_ROUTES = new Set(ROUTE_AWAITING_A_PRODUCT_DECISION.map(([path]) => path));

  it('routes a customer to no path named after a platform concept', () => {
    // The address bar is user-visible text.
    const offenders = routeOffenders(SOURCES).filter(
      (entry) => ![...EXCUSED_ROUTES].some((path) => entry.endsWith(`: ${path}`)),
    );

    expect(offenders).toEqual([]);
  });

  /**
   * ⛔ **The same discipline the prose exceptions carry**: an excused path that
   * nothing routes to any more is forgiveness with no subject, and it would sit
   * here quietly permitting a term after the decision that allowed it had been
   * taken.
   */
  it('⚡ and every excused ROUTE is still excusing something', () => {
    const all = routeOffenders(SOURCES);
    for (const [path, item] of ROUTE_AWAITING_A_PRODUCT_DECISION) {
      expect(
        all.filter((entry) => entry.endsWith(`: ${path}`)),
        `${path} is excused pending ${item} and nothing routes there any more — ` +
          'remove the exception rather than leaving one that forgives nothing',
      ).not.toEqual([]);
    }
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
