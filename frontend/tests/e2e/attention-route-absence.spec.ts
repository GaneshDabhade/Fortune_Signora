/**
 * The standalone Attention surface is obsolete, and nothing may quietly reach it.
 *
 * ## What this proves, and what it deliberately does not
 *
 * The **`AccountAttention` domain concept is not obsolete.** Accounts are ranked
 * by an attention score, `GET /workspaces/{id}/accounts` returns
 * `CursorPage[AccountAttentionResponse]`, and Account 360 and Triage both render
 * it. Deleting anything named *Attention* would strip a live capability.
 *
 * What is obsolete is a **standalone `/attention` product surface** — a route of
 * its own, reachable from navigation, fetched by ordinary flows. This file
 * asserts its absence, at the three levels absence can hide:
 *
 * | | |
 * |---|---|
 * | **No flow requests it** | every network request on the ordinary journeys |
 * | **No route serves it** | a direct navigation does not land on a working page |
 * | **No navigation offers it** | the rail and the palette do not name it |
 *
 * ## Why an absence test rather than a deletion
 *
 * A capability removed without a guard comes back — a component re-imported, a
 * nav entry restored, a helpful redirect added — and nothing notices, because
 * everything still passes. `CLAUDE.md` §2: prefer a violation that is
 * *unrepresentable* over one that is merely discouraged. This is the nearest a
 * test can get, and it fails loudly when the surface returns.
 *
 * ⛔ **It must not be weakened to make a suite green.** If it starts failing
 * because the product legitimately reintroduces the route, that is a product
 * decision and this file is the place the decision becomes visible.
 */

import { expect, test } from '@playwright/test';

/** The obsolete surface, as it would appear in a URL path. */
const OBSOLETE = /\/attention(\/|\?|$)/;

/** The ordinary journeys — where an accidental request would actually happen. */
const FLOWS = ['/', '/business', '/signals', '/settings', '/settings/team'];

test('@regression no ordinary flow requests the obsolete /attention endpoint', async ({
  page,
}) => {
  const requested: string[] = [];
  page.on('request', (request) => {
    const { pathname } = new URL(request.url());
    if (OBSOLETE.test(pathname)) requested.push(`${request.method()} ${pathname}`);
  });

  for (const flow of FLOWS) {
    await page.goto(flow);
    await page.waitForLoadState('networkidle');
  }

  expect(
    requested,
    'An ordinary flow requested the obsolete /attention surface. The attention ' +
      'LIST is served by /workspaces/{id}/accounts; a request to /attention means ' +
      'the removed standalone surface has been reintroduced.',
  ).toEqual([]);
});

test('@regression the obsolete /attention route does not serve a page', async ({ page }) => {
  const response = await page.goto('/attention');

  // A 404, a redirect away, or a rendered "not found" are all acceptable
  // absences. What is not acceptable is a working Attention screen.
  const landed = new URL(page.url()).pathname;
  const servedItself = response !== null && response.ok() && OBSOLETE.test(landed);

  expect(
    servedItself,
    `Navigating to /attention landed on ${landed} with a successful response, so ` +
      'the obsolete standalone surface is reachable again.',
  ).toBe(false);
});

test('@regression navigation does not offer Attention as a destination', async ({ page }) => {
  await page.goto('/');
  await page.waitForLoadState('networkidle');

  const rail = page.getByRole('navigation', { name: 'Primary' });
  await expect(
    rail.getByRole('link', { name: 'Attention', exact: true }),
    'The primary rail offers Attention as a destination. TASK-1482 removed that ' +
      'entry under D-240; a rail that offers it again has regressed.',
  ).toHaveCount(0);

  const anywhere = page.locator('a[href="/attention"]');
  await expect(
    anywhere,
    'A link points at /attention. The obsolete surface has no route, so this is a ' +
      'dead link as well as a reintroduction.',
  ).toHaveCount(0);
});
