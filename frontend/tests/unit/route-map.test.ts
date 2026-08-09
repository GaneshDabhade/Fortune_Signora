/**
 * **The route map is the product's** — [TASK-499](../../../docs/BACKLOG.md),
 * implementing [D-185](../../../docs/DECISION_REGISTER.md) §2.
 *
 * > 📁 ***"`/` becomes the Signora Welcome experience, with `/signin`
 * > `/register` `/verify` `/forgot-password` `/reset/:token`."***
 *
 * 🔴 **The row asks for this specific assertion**: *"no route in the product
 * links to a path that no longer exists — **asserted by a test over the route
 * table, not by review**."* ⚡ **A rename is exactly the change where a review
 * misses one link and a customer finds it.**
 *
 * ⚠️ **Two of the six changes are NOT here and their absence is deliberate** —
 * 📁 [C-263](../../../docs/LANE_COORDINATION.md): `/` still serves the
 * authenticated home because the home's destination is `/w/:ws/home` and no
 * `/w/` tree exists. **This file asserts what shipped, never what was
 * intended.**
 */
import { readdirSync, readFileSync, statSync } from 'node:fs';
import { join, relative } from 'node:path';

import { describe, expect, it } from 'vitest';

const APP = join(process.cwd(), 'app');

/** Every `page.tsx`, as the URL Next.js will serve it at. */
function routes(): string[] {
  const found: string[] = [];
  const walk = (dir: string): void => {
    for (const entry of readdirSync(dir)) {
      const full = join(dir, entry);
      if (statSync(full).isDirectory()) {
        walk(full);
        continue;
      }
      if (entry !== 'page.tsx') continue;
      const url = relative(APP, full)
        .replace(/\/page\.tsx$/, '')
        .replace(/\\/g, '/')
        // Route groups are organisational and never appear in a URL.
        .replace(/\([^)]+\)\/?/g, '');
      found.push('/' + url);
    }
  };
  walk(APP);
  return found.map((r) => (r === '/' ? r : r.replace(/\/$/, '')));
}

/** Every internal href/redirect the product actually contains. */
function internalLinks(): { file: string; path: string }[] {
  const out: { file: string; path: string }[] = [];
  const walk = (dir: string): void => {
    for (const entry of readdirSync(dir)) {
      const full = join(dir, entry);
      if (statSync(full).isDirectory()) {
        if (entry === 'node_modules' || entry === '.next') continue;
        walk(full);
        continue;
      }
      if (!/\.tsx?$/.test(entry)) continue;
      const src = readFileSync(full, 'utf8');
      // href="/x", redirect('/x'), router.push('/x') — internal only, so a
      // leading slash and never a scheme.
      for (const m of src.matchAll(/(?:href=|redirect\(|push\(|replace\()["'`](\/[a-z0-9\-/[\]:.]*)["'`]/gi)) {
        out.push({ file: relative(process.cwd(), full), path: m[1] as string });
      }
    }
  };
  for (const root of ['app', 'components', 'lib']) walk(join(process.cwd(), root));
  return out;
}

/** `/accounts/[accountId]` matches `/accounts/anything`. */
function matches(route: string, path: string): boolean {
  const pattern = new RegExp(
    '^' + route.replace(/\[[^\]]+\]/g, '[^/]+').replace(/\//g, '\\/') + '$',
  );
  return pattern.test(path);
}

describe('📁 D-185 §2 — the renamed paths exist', () => {
  it.each(['/signin', '/register', '/verify', '/forgot-password'])('%s is a route', (path) => {
    expect(routes()).toContain(path);
  });

  it('⚡ /reset/:token is a PATH parameter, not a query string', () => {
    // 🔴 The reshape, not just the rename. A query parameter says the token
    // modifies a page that exists without it, and this page does not.
    expect(routes()).toContain('/reset/[token]');
  });

  it('⛔ and the names they replaced are gone', () => {
    const all = routes();
    for (const dead of ['/sign-in', '/sign-up', '/verify-email', '/reset-password']) {
      expect(all).not.toContain(dead);
    }
  });
});

describe('🔴 no route in the product links to a path that no longer exists', () => {
  it('⚡ every internal link resolves to a real route', () => {
    /**
     * ⛔ **This is the assertion the row names**, and it is over the route
     * table rather than a grep for the old names: **a link to `/signinn`
     * would pass a grep for `/sign-in` and fail here.**
     */
    const all = routes();
    const dangling = internalLinks().filter(
      ({ path }) =>
        // Anchors, API routes and the static fallbacks are not app routes.
        !path.startsWith('/api/') &&
        !path.endsWith('.html') &&
        !all.some((route) => matches(route, path)),
    );
    expect(dangling).toEqual([]);
  });

  it('⛔ and the scan can fire — it is not an empty list congratulating itself', () => {
    // B-162's lesson: a guard proved only by passing is a guard nobody has
    // seen work. Both halves.
    expect(internalLinks().length).toBeGreaterThan(10);
    expect(matches('/reset/[token]', '/reset/abc123')).toBe(true);
    expect(matches('/reset/[token]', '/reset-password?token=abc')).toBe(false);
  });
});

describe('⚠️ what C-263 blocked, asserted as it actually is', () => {
  it('⛔ `/` still serves the authenticated home, and that is recorded not hidden', () => {
    /**
     * 📁 [C-263](../../../docs/LANE_COORDINATION.md): the home's destination
     * is `/w/:ws/home` — 📁 `lib/entry/rules.ts`, §04 *Home is a slot* — and
     * no `/w/` tree exists. ⛔ **Inventing `/home` would be a second answer to
     * *where is home* on a customer-visible URL.**
     *
     * ⚡ **This test will FAIL when the front door moves**, which is the point:
     * it states today's truth so the day it stops being true is loud.
     */
    expect(routes()).toContain('/');
    expect(routes()).not.toContain('/w/[workspaceId]/home');
  });
});
