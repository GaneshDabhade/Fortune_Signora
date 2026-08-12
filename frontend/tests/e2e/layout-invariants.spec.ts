import { test } from '@playwright/test';

import {
  ROUTES,
  expectNoCrushedText,
  expectNoDocumentScroll,
  expectNoHorizontalOverflow,
  expectNothingFixedBelowTheFold,
  expectNavigationReachable,
  expectRouteExists,
  expectShellRegionsDoNotOverlap,
} from './fixtures/layout-invariants';

/**
 * **Layout invariants — the assertions that fail when the rendered layout
 * breaks, rather than when a class string changes.**
 *
 * ⚡ **The seven checks live in `fixtures/layout-invariants.ts`**, and their
 * reasoning lives with them. **They were moved there so that
 * `layout-invariants.firetest.spec.ts` can prove each one is capable of
 * failing — against the same implementation this file runs, never a copy.**
 *
 * ⛔ **A fire-test against a duplicated check proves the duplicate works.** That
 * is why the extraction happened rather than the obvious copy-paste, and it is
 * the same argument as [B-238](../../../docs/BUGS.md): the defect was never in
 * the function, it was in which object the guard asked about.
 *
 * **This file is now only the matrix**: seven invariants × six shell-bearing
 * routes × the five viewport projects in `playwright.config.ts`.
 */

for (const route of ROUTES) {
  test(`${route.name} holds its layout invariants`, async ({ page }, testInfo) => {
    await page.goto(route.path);
    // The invariants are about a settled layout, not about a frame mid-paint.
    await page.waitForLoadState('networkidle');

    const width = page.viewportSize()?.width ?? 0;
    await test.step(`${route.path} is a real route`, () => expectRouteExists(page, route.path));
    await test.step(`no horizontal overflow at ${width}px`, () => expectNoHorizontalOverflow(page));
    await test.step(`nothing fixed below the fold at ${width}px`, () => expectNothingFixedBelowTheFold(page));
    await test.step(`document does not scroll sideways at ${width}px`, () => expectNoDocumentScroll(page));
    await test.step(`shell regions do not overlap at ${width}px`, () => expectShellRegionsDoNotOverlap(page));
    await test.step(`navigation is reachable at ${width}px`, () => expectNavigationReachable(page));
    await test.step(`no crushed text at ${width}px`, () => expectNoCrushedText(page));

    // **Evidence that corresponds to what the gate claims to validate.** A
    // screenshot of the width that failed is the difference between "responsive
    // test failed" and a defect somebody can see.
    if (testInfo.status !== testInfo.expectedStatus) {
      await testInfo.attach(`${route.name}-${width}px`, {
        body: await page.screenshot({ fullPage: true }),
        contentType: 'image/png',
      });
    }
  });
}
