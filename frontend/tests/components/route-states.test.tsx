import { existsSync, readFileSync, readdirSync, statSync } from 'node:fs';
import { join } from 'node:path';
import { describe, expect, it } from 'vitest';

/**
 * **The loading and error states every route owes** —
 * [TASK-1447](../../../docs/BACKLOG.md), 📁 Design System v2 §13 *States*.
 *
 * ## 🔴 The ratio was the defect, not the counts
 *
 * ⚠️ **Measured before this row**: `loading.tsx` on **0 of 26** route
 * directories · a designed ERROR state on **2** · a designed EMPTY state on
 * **7**. ⛔ **Three and a half times more screens could tell a customer *there
 * is nothing here* than could tell them *we could not read it*.**
 *
 * 📁 **[P-A](../../../docs/DOMAIN_DISCOVERY_REGISTER.md): *a failed read must
 * never render as an empty result*.** ⚡ **[C-226](../../../docs/LANE_COORDINATION.md)
 * found exactly that six times on ONE screen and it was fixed there** — this
 * is the same defect at platform scale, and these tests are what stop the
 * ratio drifting back.
 */

const APP = join(process.cwd(), 'app');

/** Every directory that renders a route. */
function routeDirectories(root = APP, acc: string[] = []): string[] {
  for (const entry of readdirSync(root)) {
    const path = join(root, entry);
    if (!statSync(path).isDirectory()) continue;
    if (entry === 'node_modules') continue;
    if (existsSync(join(path, 'page.tsx'))) acc.push(path);
    routeDirectories(path, acc);
  }
  return acc;
}

/**
 * ⚡ **A route READS if its own tree imports a query hook.**
 *
 * ⛔ **Not just `page.tsx`** — `/signals` and `/profile` delegate to
 * components, and a check that looked only at the page file measured the wrong
 * file. **That mistake was made while writing this row**, which is why the
 * helper walks the directory.
 *
 * ⚠️ **And the first version was too broad the other way**: `use[A-Z]\w*\(`
 * matched `useState`, so **every auth form counted as a read** and the sign-in
 * screen was told it owed a loading state for data it never fetches.
 * ✅ **An IMPORT from the query layer is the honest signal** — it is what
 * actually distinguishes a screen that waits on a server from one that does
 * not.
 */
function readsData(dir: string): boolean {
  const files = readdirSync(dir).filter((f) => f.endsWith('.tsx') || f.endsWith('.ts'));
  return files.some((f) =>
    /from '@\/lib\/query\/hooks|useQuery\(/.test(readFileSync(join(dir, f), 'utf8')),
  );
}

const ROUTES = routeDirectories();
const READING = ROUTES.filter(readsData);

describe('📁 §13 — a route that reads owes a loading state', () => {
  it('⚡ the sweep found routes to check, so nothing below is vacuous', () => {
    // ⛔ **Vacuity guard first.** If the walk returned nothing, every
    // assertion here would pass over a repository with no routes at all.
    expect(ROUTES.length).toBeGreaterThan(10);
    expect(READING.length).toBeGreaterThan(5);
  });

  it.each(READING.map((d) => [d.replace(APP, '') || '/', d]))(
    '✅ %s has a loading.tsx',
    (_label, dir) => {
      /**
       * ⚡ **Next renders this while the route segment resolves**, so a
       * navigation shows the shape of what is coming rather than a blank
       * frame. ⛔ **It was 0 of 26.**
       */
      expect(existsSync(join(dir as string, 'loading.tsx'))).toBe(true);
    },
  );
});

describe('🔴 P-A — a failed read must never render as an empty result', () => {
  /**
   * ⚡ **The rule this asserts is one-directional and that is the point.** A
   * route may render an empty state without an error state only if it never
   * reads — ⛔ **but a route that renders an EMPTY state for data it READ owes
   * an error path**, because otherwise the failure and the emptiness are the
   * same pixels.
   */
  const offenders = READING.filter((dir) => {
    const files = readdirSync(dir).filter((f) => f.endsWith('.tsx'));
    const source = files.map((f) => readFileSync(join(dir, f), 'utf8')).join('\n');
    const rendersEmpty = /<EmptyState|StatedAbsence/.test(source);
    const rendersError = /<ErrorState|<SystemState|isError|\berror\b/.test(source);
    return rendersEmpty && !rendersError;
  });

  it('⛔ no route renders an empty state for data it read without an error path', () => {
    expect(
      offenders.map((d) => d.replace(APP, '')),
      'these routes tell a customer their data is empty when the read may simply have failed',
    ).toEqual([]);
  });
});

describe('⛔ a skeleton is not an empty state', () => {
  it.each(READING.map((d) => [d.replace(APP, '') || '/', d]))(
    '✅ %s\'s loading.tsx renders a skeleton and claims nothing',
    (_label, dir) => {
      /**
       * 🔴 **A `loading.tsx` that rendered *"Nothing here yet"* would be
       * [P-A](../../../docs/DOMAIN_DISCOVERY_REGISTER.md) in its worst form**:
       * a screen asserting emptiness before the read has even returned.
       * ⚡ **A skeleton claims nothing**, which is why it is the only correct
       * thing to render at this moment.
       */
      const source = readFileSync(join(dir as string, 'loading.tsx'), 'utf8');
      expect(source).toMatch(/Skeleton/);
      expect(source).not.toMatch(/<EmptyState|Nothing here|No results/);
    },
  );
});
