import { expect, test } from '@playwright/test';

import {
  expectNoCrushedText,
  expectNoDocumentScroll,
  expectNoHorizontalOverflow,
  expectNothingFixedBelowTheFold,
  expectNavigationReachable,
  expectRouteExists,
  expectShellRegionsDoNotOverlap,
} from './fixtures/layout-invariants';

/**
 * **Can each layout invariant actually fail?**
 *
 * ⛔ **A guard that cannot fail is not protection — it is documentation
 * pretending to be code** (`CLAUDE.md` §2). **This file is the only evidence
 * that the seven checks in `fixtures/layout-invariants.ts` are guards at all.**
 *
 * ⚠️ **It exists because one of them was not.** `expectShellRegionsDoNotOverlap`
 * used `querySelector` where it needed `querySelectorAll`; the shell mounts two
 * `nav[aria-label="Primary"]` elements and the first is collapsed to 0×0, so the
 * only one ever measured was skipped as zero-size. **The assertion could not
 * fail at any width, on any page, for any layout** — and **three mutations
 * passed before anybody noticed** ([B-180](../../../docs/BUGS.md)).
 *
 * ## Two-sided, and both sides are the point
 *
 * | | |
 * |---|---|
 * | **The good product** | the check **passes** — otherwise it is a false positive, and a gate that cries on correct behaviour gets switched off |
 * | **A deliberately broken layout** | the check **fails** — otherwise it is decorative |
 *
 * ⚡ **Neither half is sufficient alone.** A green run proves nothing until
 * something has made it red, and a red run proves nothing if the same check is
 * red on a correct product.
 *
 * ## It runs against the real implementation, never a copy
 *
 * ⛔ **This is why the checks were extracted to `fixtures/` rather than
 * duplicated here.** A fire-test against a copied check proves the copy works
 * and says nothing about what the suite runs — **the same defect as
 * [B-238](../../../docs/BUGS.md), where the guard asked the right question about
 * the wrong object.**
 *
 * ## The mutations are injected, not committed
 *
 * Each breakage is applied to a live page with `page.evaluate` and dies with the
 * page. ⛔ **Nothing here edits product source**, so this file cannot leave the
 * repository in a broken state to prove a point.
 */

/** The check must throw. If it returns, it is incapable of reporting the defect. */
async function expectCheckToFail(what: string, run: () => Promise<void>): Promise<void> {
  let threw = false;
  try {
    await run();
  } catch {
    threw = true;
  }
  expect(
    threw,
    `${what} PASSED on a deliberately broken layout. ` +
      'It cannot fail, so it protects nothing and every green run of it has been worthless.',
  ).toBe(true);
}

const ROUTE = '/';

test.describe('@regression the layout invariants are capable of failing', () => {
  test('horizontal overflow is detected when something spills sideways', async ({ page }) => {
    await page.goto(ROUTE);
    await page.waitForLoadState('networkidle');
    await expectNoHorizontalOverflow(page);

    await page.evaluate(() => {
      const spill = document.createElement('div');
      // Absolute rather than fixed: the check deliberately skips `fixed`,
      // because a fixed overlay is allowed to sit outside the flow.
      spill.setAttribute('style', 'position:absolute;left:0;top:0;width:200vw;height:20px;background:red');
      spill.id = 'qe-firetest-spill';
      document.body.appendChild(spill);
    });

    await expectCheckToFail('expectNoHorizontalOverflow', () => expectNoHorizontalOverflow(page));
  });

  test('a fixed element below the fold is detected', async ({ page }) => {
    await page.goto(ROUTE);
    await page.waitForLoadState('networkidle');
    await expectNothingFixedBelowTheFold(page);

    await page.evaluate(() => {
      const stranded = document.createElement('div');
      // Fixed, visible, non-zero, and reaching well past the fold — where
      // nothing can scroll it into view, so a customer cannot press it.
      stranded.setAttribute('style', 'position:fixed;left:0;top:0;width:50px;height:250vh;background:red');
      stranded.id = 'qe-firetest-stranded';
      document.body.appendChild(stranded);
    });

    await expectCheckToFail('expectNothingFixedBelowTheFold', () => expectNothingFixedBelowTheFold(page));
  });

  test('a document that scrolls sideways is detected', async ({ page }) => {
    await page.goto(ROUTE);
    await page.waitForLoadState('networkidle');
    await expectNoDocumentScroll(page);

    await page.evaluate(() => {
      const wide = document.createElement('div');
      wide.setAttribute('style', 'position:absolute;left:0;top:0;width:200vw;height:20px');
      wide.id = 'qe-firetest-wide';
      document.body.appendChild(wide);
    });

    await expectCheckToFail('expectNoDocumentScroll', () => expectNoDocumentScroll(page));
  });

  test('two shell regions drawn on top of each other are detected', async ({ page }) => {
    await page.goto(ROUTE);
    await page.waitForLoadState('networkidle');
    await expectShellRegionsDoNotOverlap(page);

    await page.evaluate(() => {
      const over = document.createElement('nav');
      over.setAttribute('role', 'navigation');
      // ⚡ Appended to `body`, so it neither contains nor is contained by
      // `main` — containment is deliberately not collision, and a mutation
      // that landed inside `main` would be skipped as a section heading.
      //
      // `fixed`, so it survives the check's own scroll-to-bottom and is
      // compared on CONTENT boxes, which is the comparison that matters.
      over.setAttribute('style', 'position:fixed;left:0;top:0;width:100%;height:100%;background:rgba(255,0,0,.2)');
      over.id = 'qe-firetest-overlay';
      document.body.appendChild(over);
    });

    await expectCheckToFail('expectShellRegionsDoNotOverlap', () => expectShellRegionsDoNotOverlap(page));
  });

  test('navigation that has become unreachable is detected', async ({ page }) => {
    await page.goto(ROUTE);
    await page.waitForLoadState('networkidle');
    await expectNavigationReachable(page);

    await page.evaluate(() => {
      // ⛔ The predicate accepts a rail OR a drawer trigger, so a fire-test
      // that removed only one would pass for the wrong reason. Both go.
      for (const nav of Array.from(document.querySelectorAll<HTMLElement>('nav, [role="navigation"]'))) {
        nav.style.display = 'none';
      }
      for (const button of Array.from(document.querySelectorAll<HTMLElement>('button'))) {
        const name = (button.getAttribute('aria-label') || button.textContent || '').trim().toLowerCase();
        if (/open navigation|open menu|main menu/.test(name)) button.style.display = 'none';
      }
    });

    await expectCheckToFail('expectNavigationReachable', () => expectNavigationReachable(page));
  });

  test('a heading crushed too narrow to read is detected', async ({ page }) => {
    await page.goto(ROUTE);
    await page.waitForLoadState('networkidle');
    await expectNoCrushedText(page);

    await page.evaluate(() => {
      const crushed = document.createElement('h2');
      // Four characters minimum, and narrower than the ~24px the check calls
      // unreadable — the element is present, visible, and useless.
      crushed.textContent = 'Crushed heading nobody can read';
      crushed.setAttribute('style', 'width:10px;overflow:hidden;position:absolute;left:0;top:0');
      crushed.id = 'qe-firetest-crushed';
      document.body.appendChild(crushed);
    });

    await expectCheckToFail('expectNoCrushedText', () => expectNoCrushedText(page));
  });

  test('a route that does not exist is reported as a list defect, not a shell defect', async ({ page }) => {
    await page.goto(ROUTE);
    await page.waitForLoadState('networkidle');
    await expectRouteExists(page, ROUTE);

    // ⚡ No injection here: the mutation is navigating somewhere real that the
    // product does not serve. This is the check that stopped
    // `expectNavigationReachable` reporting "the product has no way out of this
    // page" about a 404 — true of the page it was given, false about the product.
    await page.goto('/qe-firetest-no-such-route');
    await page.waitForLoadState('networkidle');

    await expectCheckToFail('expectRouteExists', () => expectRouteExists(page, '/qe-firetest-no-such-route'));
  });
});
