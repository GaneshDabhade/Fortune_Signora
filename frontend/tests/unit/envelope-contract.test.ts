import { readFileSync, readdirSync } from 'node:fs';
import { join } from 'node:path';
import { describe, expect, it } from 'vitest';

/**
 * **A hook's declared shape against the endpoint's actual one** —
 * [B-420](../../../docs/BUGS.md).
 *
 * ## 🔴 The defect this exists for was silent in every gate
 *
 * ⛔ **`GET /workspaces/{id}/history` returns `CursorPage[...]` — `{ items,
 * next_cursor }` — and its hook declared `HistoryEntry[]`.** ⚡ **The product
 * owner opened the page and it threw**: `entries is not iterable`.
 *
 * **Nothing caught it, and each reason is worth stating:**
 *
 * ⛔ **`apiRequest<T>` is a CLAIM about the wire, not a check of it.**
 * TypeScript believed the claim, so `tsc` was clean.
 *
 * ⛔ **The component's empty-state guard HID it**: `entries.length === 0`
 * evaluates `undefined === 0` → `false`, so the envelope passed straight
 * through to the `for…of` rather than being caught by the guard standing right
 * in front of it.
 *
 * ⛔ **And the component's tests pass an array fixture directly**, so they
 * never exercised the real envelope — 🔴 **a test that cannot see the real
 * shape is asserting the wrong thing**, which is this lane's own finding from
 * the rail slice, turned around on it.
 *
 * ## ⚡ So the guard is static, and it is a cross-reference
 *
 * ⛔ **A runtime check inside `apiRequest` cannot work**: it does not know what
 * `T` is, and a generic has no presence at runtime to compare against.
 * ✅ **But the two declarations CAN be compared to each other** — the backend
 * says `response_model=CursorPage[...]`, the frontend says
 * `apiRequest<Thing[]>`, and **a path appearing on both sides with those two
 * shapes is the defect, statically.**
 *
 * ⚠️ **This is the answer to the judgement Lane C left open** — *whether the
 * guard belongs in `apiRequest` rather than in the caller.* **Neither: it
 * belongs in a test that reads both sides**, because that is the only place
 * the two claims meet.
 */

const BACKEND = join(process.cwd(), '..', 'backend', 'modules');
const HOOKS = join(process.cwd(), 'lib', 'query', 'hooks');

/** Every route the backend returns a `CursorPage` from, as a path template. */
function cursorPageRoutes(): string[] {
  const routes: string[] = [];
  const walk = (dir: string) => {
    for (const entry of readdirSync(dir, { withFileTypes: true })) {
      const path = join(dir, entry.name);
      if (entry.isDirectory()) {
        if (entry.name === '__pycache__') continue;
        walk(path);
        continue;
      }
      if (!entry.name.endsWith('.py')) continue;
      const source = readFileSync(path, 'utf8');
      // `@router.get( "/path", response_model=CursorPage[...] )` — the path and
      // the model are on separate lines, so the decorator block is matched.
      for (const block of source.matchAll(/@router\.\w+\(([\s\S]{0,400}?)\)\n/g)) {
        const body = block[1] ?? '';
        if (!body.includes('CursorPage[')) continue;
        const path = body.match(/["'](\/[^"']+)["']/)?.[1];
        if (path !== undefined) routes.push(path);
      }
    }
  };
  walk(BACKEND);
  return routes;
}

/** Every `apiRequest<…>(…)` in the hook layer, as (declared type, path). */
function hookCalls(): { type: string; path: string; file: string }[] {
  const calls: { type: string; path: string; file: string }[] = [];
  for (const file of readdirSync(HOOKS)) {
    if (!file.endsWith('.ts')) continue;
    const source = readFileSync(join(HOOKS, file), 'utf8');
    for (const call of source.matchAll(/apiRequest<([^>]+(?:<[^>]*>)?[^>]*)>\(\s*`([^`]+)`/g)) {
      calls.push({ type: call[1] ?? '', path: call[2] ?? '', file });
    }
  }
  return calls;
}

/** `/workspaces/${workspaceId}/history` → `/workspaces/{id}/history`. */
function normalise(path: string): string {
  return path.replace(/\$\{[^}]+\}/g, '{}').replace(/\{[^}]*\}/g, '{}').split('?')[0] ?? path;
}

const ROUTES = cursorPageRoutes().map(normalise);
const CALLS = hookCalls();

describe('🔴 B-420 — a hook may not declare a bare array for a CursorPage endpoint', () => {
  it('⚡ both sides were actually read, so nothing below is vacuous', () => {
    // ⛔ **The guard's whole value is the cross-reference.** If either side
    // came back empty every assertion would pass over a comparison that never
    // happened — which is the shape of the defect it exists to catch.
    expect(ROUTES.length, 'no CursorPage routes found in the backend').toBeGreaterThan(5);
    expect(CALLS.length, 'no apiRequest calls found in the hook layer').toBeGreaterThan(10);
  });

  it('⛔ no hook asks for an array where the endpoint sends an envelope', () => {
    const offenders = CALLS.filter(({ type, path }) => {
      const declaresArray = /\[\s*\]\s*$/.test(type.trim());
      return declaresArray && ROUTES.includes(normalise(path));
    }).map(({ type, path, file }) => `${file}: apiRequest<${type}>(${path})`);

    expect(
      offenders,
      'these declare a bare array for an endpoint that returns { items, next_cursor } — the shape that threw for the product owner',
    ).toEqual([]);
  });

  it('✅ and the four hooks that DO declare arrays are reading genuine list endpoints', () => {
    /**
     * ⚠️ **Measured before trusting the rule.** 📁 Five hooks declare a bare
     * array: `/integrations`, `/invitations`, `/ownership`, `/account-search`
     * and — before this fix — `/history`. **The first four are genuinely
     * `response_model=list[...]`**, so the rule above is not merely unfired,
     * it is discriminating.
     */
    const arrayHooks = CALLS.filter(({ type }) => /\[\s*\]\s*$/.test(type.trim()));
    expect(arrayHooks.length, 'array-declaring hooks vanished — the pattern stopped matching').toBeGreaterThan(2);
    for (const hook of arrayHooks) {
      expect(ROUTES, `${hook.file} → ${hook.path}`).not.toContain(normalise(hook.path));
    }
  });
});
