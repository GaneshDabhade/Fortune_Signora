/**
 * Semantic visual assertions — the value of screenshot testing without its cost.
 *
 * ## Why not snapshots
 *
 * A pixel snapshot of a screen whose content is computed from *today's* dates
 * fails daily and is re-baselined until it asserts nothing. That is not a
 * hypothesis: the Playground is deliberately anchored to the current day so
 * evidence ages realistically, so every score, trend and evidence state moves
 * on its own.
 *
 * ## What is asserted instead
 *
 * **Properties a customer would notice and a designer would call a bug**, none
 * of which depends on a pixel:
 *
 *   the page never scrolls sideways · nothing is clipped · no text is
 *   invisible · no image is broken · the layout does not jump after it loads ·
 *   a dialog does not leave the page scrolling underneath it · focus is never
 *   lost to `<body>`
 *
 * Each of these fails on a real regression and survives a spacing change. That
 * is the trade snapshots get backwards.
 */

import { expect, test } from './fixtures/signora';

const SCREENS = [
  ['the accounts list', '/accounts'],
  ['your business', '/settings/products'],
  ['settings', '/settings'],
  ['connections', '/settings/connections'],
] as const;

/** Wait for a screen to have settled, rather than for a duration. Every screen
 * here has a heading, and the heading is the last thing to arrive on none of
 * them — so the content behind it is what we wait on. */
async function settled(page: import('@playwright/test').Page): Promise<void> {
  await expect(page.getByRole('heading', { level: 1 })).toBeVisible({ timeout: 20_000 });
  await page.waitForLoadState('networkidle');
}

test.describe('the page fits the window', () => {
  for (const [name, path] of SCREENS) {
    test(`@regression ${name} never scrolls sideways`, async ({ page }) => {
      await page.goto(path);
      await settled(page);

      // A horizontal scrollbar on a desktop layout is the most visible symptom
      // of a width that escaped its container, and it is invisible to every
      // component test because a component has no window.
      const overflow = await page.evaluate(() => ({
        scrollWidth: document.documentElement.scrollWidth,
        clientWidth: document.documentElement.clientWidth,
      }));
      expect(
        overflow.scrollWidth,
        `${name} is ${overflow.scrollWidth - overflow.clientWidth}px wider than the window`,
      ).toBeLessThanOrEqual(overflow.clientWidth + 1);
    });

    test(`@regression ${name} clips no text`, async ({ page }) => {
      await page.goto(path);
      await settled(page);

      // An element whose content is wider than itself *and* which hides the
      // overflow is a truncated sentence a customer cannot read. Ellipsis is
      // deliberate and allowed; silent clipping is not.
      const clipped = await page.evaluate(() =>
        [...document.querySelectorAll('main *')]
          .filter((element) => {
            const style = getComputedStyle(element);
            if (style.overflow === 'visible' && style.overflowX === 'visible') return false;
            if (style.textOverflow === 'ellipsis') return false;
            if (!element.textContent?.trim()) return false;
            return element.scrollWidth > element.clientWidth + 2;
          })
          .slice(0, 5)
          .map((element) => (element.textContent ?? '').trim().slice(0, 60)),
      );
      expect(clipped, `clipped text on ${name}`).toEqual([]);
    });

    test(`@regression ${name} has no invisible text and no broken image`, async ({
      page,
    }) => {
      await page.goto(path);
      await settled(page);

      const problems = await page.evaluate(() => {
        const found: string[] = [];
        for (const image of document.querySelectorAll('img')) {
          if (image.complete && image.naturalWidth === 0) {
            found.push(`broken image: ${image.getAttribute('src') ?? '(no src)'}`);
          }
        }
        for (const element of document.querySelectorAll('main *')) {
          const text = element.textContent?.trim();
          if (!text || element.children.length > 0) continue;
          const style = getComputedStyle(element);
          // `sr-only` text is deliberately off-screen and is not invisible —
          // it is the accessible half of a visual element.
          if (style.position === 'absolute' && style.clip !== 'auto') continue;
          if (style.opacity === '0' || style.color === 'rgba(0, 0, 0, 0)') {
            found.push(`invisible text: ${text.slice(0, 40)}`);
          }
        }
        return found.slice(0, 5);
      });
      expect(problems, `on ${name}`).toEqual([]);
    });
  }
});

test.describe('the layout settles', () => {
  test('@regression the accounts list does not jump once it has loaded', async ({
    page,
  }) => {
    // ⚠️ **`/accounts`, and it used to be `/`.** `/` is the shell's entry
    // resolver now, so this measured a redirect into Home while calling itself
    // *"the accounts list"*.
    await page.goto('/accounts');
    // Measure from the first paint, which is when a customer starts reading.
    await page.evaluate(() => {
      (window as unknown as { __shift: number }).__shift = 0;
      new PerformanceObserver((list) => {
        for (const entry of list.getEntries()) {
          const shift = entry as PerformanceEntry & {
            value: number;
            hadRecentInput: boolean;
          };
          if (!shift.hadRecentInput) {
            (window as unknown as { __shift: number }).__shift += shift.value;
          }
        }
      }).observe({ type: 'layout-shift', buffered: true });
    });
    await expect(page.locator('main a[href^="/accounts/"]').first()).toBeVisible({
      timeout: 20_000,
    });
    await page.waitForLoadState('networkidle');

    const shift = await page.evaluate(
      () => (window as unknown as { __shift: number }).__shift,
    );
    /**
     * 🔴 **KNOWN RED — [B-283](../../../docs/BUGS.md), filed 2026-08-18.**
     * ⛔ **The assertion is NOT relaxed.** Measured on this branch:
     * **Companies `0.277`, Home `0.153`**, against a boundary of `0.1` — and
     * the retired Attention screen settled under it, which is why the number
     * only became visible when the journeys moved.
     *
     * **A list that reflows under the cursor makes a customer click the wrong
     * row.** 0.1 is the web's own "good" boundary; the number is recorded so a
     * regression is visible even when it passes.
     */
    test.info().annotations.push({ type: 'cumulative-layout-shift', description: `${shift}` });
    expect(shift, `cumulative layout shift on the accounts list`).toBeLessThan(0.1);
  });
});

test.describe('dialogs behave like dialogs', () => {
  test('@regression an open dialog does not leave the page scrolling behind it', async ({
    home,
    brief,
    page,
  }) => {
    // ⚡ **Home's ranked card** — 📁 `B-1022`: an unscored brief has no
    // citations, so there is no dialog to hold the page still behind.
    await home.open();
    await home.openFirstRankedAccount();
    await brief.waitForScore();
    await brief.openFirstCitation();

    // **Skip rather than pass when the page cannot scroll.** A short brief has
    // nowhere to scroll to, so the assertion would hold for a dialog that locks
    // nothing — and it did, on the first account this test happened to open.
    // A test that can pass vacuously is documentation pretending to be code.
    const scrollable = await page.evaluate(
      () => document.documentElement.scrollHeight > window.innerHeight + 100,
    );
    if (!scrollable) test.skip(true, 'this brief is shorter than the window');

    // Scrolling the page while reading a modal is the most common way a dialog
    // feels unfinished — the content moves behind it and the reader loses
    // their place on the page they will return to.
    const before = await page.evaluate(() => window.scrollY);
    await page.mouse.wheel(0, 600);
    const after = await page.evaluate(() => window.scrollY);
    expect(after, 'the page scrolled underneath an open dialog').toBe(before);

    await page.keyboard.press('Escape');
  });

  test('@regression only one dialog is ever open', async ({
    home,
    brief,
    page,
  }) => {
    // ⚡ **Home's ranked card** — 📁 `B-1022`: an unscored brief has no
    // citations, so there is no dialog to hold the page still behind.
    await home.open();
    await home.openFirstRankedAccount();
    await brief.waitForScore();

    // Two citations in quick succession — a customer comparing two lines.
    const citations = brief.citations;
    if ((await citations.count()) < 2) test.skip(true, 'only one citation on this account');
    await citations.nth(0).click();
    await expect(page.getByRole('dialog')).toHaveCount(1);
    await page.keyboard.press('Escape');
    await citations.nth(1).click();
    await expect(page.getByRole('dialog')).toHaveCount(1);
    await page.keyboard.press('Escape');
  });
});

test.describe('focus is never lost', () => {
  test('@a11y navigating with the keyboard never drops focus to the body', async ({
    page,
    accounts,
  }) => {
    await accounts.open();
    // **Wait for the rows, not the heading.** The shell has seven controls and
    // the list adds twelve; tabbing before the rows arrive walks off the end of
    // a shorter page, which is the browser behaving correctly and the test
    // asking the wrong question.
    await accounts.names();

    for (let step = 0; step < 12; step += 1) {
      await page.keyboard.press('Tab');
      const tag = await page.evaluate(() => document.activeElement?.tagName ?? 'NONE');
      // Landing on `<body>` mid-sequence means a control removed itself from
      // under the keyboard, and the reader has to start again from the top.
      expect(tag, `focus fell to ${tag} after ${step + 1} tabs`).not.toBe('BODY');
    }
  });
});
