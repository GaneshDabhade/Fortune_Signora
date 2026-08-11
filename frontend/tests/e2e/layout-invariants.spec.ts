import { expect, test, type Locator, type Page } from '@playwright/test';

/**
 * **Layout invariants — the assertions that fail when the rendered layout
 * breaks, rather than when a class string changes.**
 *
 * ⛔ **Every responsive assertion this repository had before this file was a
 * statement about markup**: a `phone:` prefix present, an element in the DOM, a
 * `hidden` class applied. **None of them could fail when the layout actually
 * broke** — [B-175](../../../docs/BUGS.md) is the same defect one level down,
 * and the suite carried it at *four* of twenty-five specs setting a viewport at
 * all.
 *
 * ⚠️ **And jsdom cannot help here.** Vitest renders without a layout engine, so
 * every width in it is zero and every overlap is undetectable. **A responsive
 * test that passes under jsdom has proven nothing about responsiveness** — it
 * has proven a class name is spelled correctly.
 *
 * **So these read geometry from a real engine and nothing else.** Each one
 * names the customer-visible failure it exists to catch, because an invariant
 * whose failure nobody can picture is the kind that gets weakened to make a
 * suite green.
 *
 * ⚡ **The breakpoints are the product's own** — `tailwind.config.ts` replaces
 * Tailwind's defaults with `phone` · `smalllaptop` · `laptop` · `desktop`, so
 * those four are what the design means and what these run at. They are supplied
 * by the project matrix in `playwright.config.ts`; this file never hard-codes a
 * width, because a viewport written in two places drifts.
 */

/** Everything a page must satisfy at every width, whatever it is showing. */
const SHELL_REGIONS = ['banner', 'navigation', 'main'] as const;

async function boxOf(locator: Locator): Promise<{ x: number; y: number; width: number; height: number } | null> {
  if ((await locator.count()) === 0) return null;
  if (!(await locator.first().isVisible())) return null;
  return locator.first().boundingBox();
}

/**
 * **Does anything spill sideways out of the viewport?**
 *
 * The customer-visible failure: a table, a toolbar or a card wider than the
 * window, so the whole page scrolls horizontally and the right-hand column is
 * unreachable without dragging. ⛔ **This is the single most common responsive
 * defect and the suite could not see it at any width.**
 */
async function expectNoHorizontalOverflow(page: Page): Promise<void> {
  const overflow = await page.evaluate(() => {
    const viewport = document.documentElement.clientWidth;
    const offenders: { tag: string; id: string; cls: string; right: number }[] = [];
    for (const element of Array.from(document.body.querySelectorAll<HTMLElement>('*'))) {
      const style = getComputedStyle(element);
      if (style.display === 'none' || style.visibility === 'hidden') continue;
      // An element that owns a scroller is allowed to be wider than the window
      // — that is what `overflow-x: auto` is for, and a wide table inside one
      // is correct rather than broken.
      if (style.overflowX === 'auto' || style.overflowX === 'scroll') continue;
      if (style.position === 'fixed') continue;
      const rect = element.getBoundingClientRect();
      if (rect.width === 0 || rect.height === 0) continue;
      // One pixel of tolerance: sub-pixel rounding at some widths puts a
      // correctly laid-out edge a fraction over, and a test that fails on that
      // gets disabled rather than fixed.
      if (rect.right > viewport + 1) {
        offenders.push({
          tag: element.tagName.toLowerCase(),
          id: element.id,
          cls: (element.className || '').toString().slice(0, 80),
          right: Math.round(rect.right),
        });
      }
    }
    return { viewport, offenders: offenders.slice(0, 5), total: offenders.length };
  });

  expect(
    overflow.total,
    `${overflow.total} element(s) extend past the ${overflow.viewport}px viewport, so the page scrolls sideways: ` +
      JSON.stringify(overflow.offenders),
  ).toBe(0);
}

/**
 * **Does the document itself scroll sideways?**
 *
 * The complement of the check above, and deliberately separate: the one above
 * names the offender, this one asks the question the customer actually
 * experiences. ⚡ **An element can be clipped by an ancestor and still not
 * produce a scrollbar; both answers are worth having.**
 */
async function expectNoDocumentScroll(page: Page): Promise<void> {
  const { scrollWidth, clientWidth } = await page.evaluate(() => ({
    scrollWidth: document.documentElement.scrollWidth,
    clientWidth: document.documentElement.clientWidth,
  }));
  expect(scrollWidth, `the document scrolls horizontally at ${clientWidth}px`).toBeLessThanOrEqual(clientWidth + 1);
}

/**
 * **Do two shell regions sit on top of each other?**
 *
 * The customer-visible failure: navigation drawn over content, or a banner
 * covering the top of the page, so a control is present, and visible to a test,
 * and *unclickable*. ⛔ **An `expect(button).toBeVisible()` passes while the
 * button sits underneath a sidebar** — which is exactly the class of defect
 * this file exists for.
 */
async function expectShellRegionsDoNotOverlap(page: Page): Promise<void> {
  const boxes: { role: string; box: NonNullable<Awaited<ReturnType<typeof boxOf>>> }[] = [];
  for (const role of SHELL_REGIONS) {
    const box = await boxOf(page.getByRole(role));
    if (box) boxes.push({ role, box });
  }

  for (let i = 0; i < boxes.length; i += 1) {
    for (let j = i + 1; j < boxes.length; j += 1) {
      const a = boxes[i];
      const b = boxes[j];
      const overlapX = Math.min(a.box.x + a.box.width, b.box.x + b.box.width) - Math.max(a.box.x, b.box.x);
      const overlapY = Math.min(a.box.y + a.box.height, b.box.y + b.box.height) - Math.max(a.box.y, b.box.y);
      const area = Math.max(0, overlapX) * Math.max(0, overlapY);
      // Tolerance is an area rather than a distance: a shared one-pixel border
      // between two adjacent regions is correct, a covered control is not.
      expect(
        area,
        `<${a.role}> and <${b.role}> overlap by ${Math.round(area)}px², so a control in one is drawn under the other`,
      ).toBeLessThan(64);
    }
  }
}

/**
 * **Is the primary navigation reachable?**
 *
 * The customer-visible failure: at a width nobody tested, the sidebar is hidden
 * by a breakpoint and no trigger replaces it, so the product has no navigation
 * at all. ⚡ **[B-233](../../../docs/BUGS.md) was this exact defect** — the rail
 * failed on every authenticated screen at every width while 2,696 unit tests
 * stayed green, because they asserted the component rendered rather than that a
 * customer could navigate.
 *
 * **Deliberately loose about *how*.** A rail, a drawer trigger, a menu button —
 * any of them satisfies it. The invariant is that *something* gets you out of
 * this page, not which shape the design chose at this width.
 */
async function expectNavigationReachable(page: Page): Promise<void> {
  const candidates = [
    page.getByRole('navigation'),
    page.getByRole('button', { name: /menu|navigation|open menu/i }),
  ];

  const reachable: string[] = [];
  for (const candidate of candidates) {
    const box = await boxOf(candidate);
    if (box && box.width > 0 && box.height > 0) reachable.push('found');
  }

  expect(
    reachable.length,
    'no visible navigation and no control that opens one — the product has no way out of this page at this width',
  ).toBeGreaterThan(0);
}

/**
 * **Is any visible text squeezed to nothing?**
 *
 * The customer-visible failure: a column collapses far enough that a label
 * renders one character per line, or a heading is clipped to a sliver. ⚡ **The
 * element is present, visible, and useless** — and every existence-based
 * assertion in the suite passes.
 */
async function expectNoCrushedText(page: Page): Promise<void> {
  const crushed = await page.evaluate(() => {
    const offenders: { text: string; width: number }[] = [];
    const headings = Array.from(document.querySelectorAll<HTMLElement>('h1, h2, h3, [role="heading"]'));
    for (const element of headings) {
      const style = getComputedStyle(element);
      if (style.display === 'none' || style.visibility === 'hidden') continue;
      const text = (element.textContent || '').trim();
      if (text.length < 4) continue;
      const rect = element.getBoundingClientRect();
      if (rect.width === 0 || rect.height === 0) continue;
      // A heading narrower than roughly two characters cannot be read at any
      // font size the design uses.
      if (rect.width < 24) offenders.push({ text: text.slice(0, 40), width: Math.round(rect.width) });
    }
    return offenders.slice(0, 5);
  });

  expect(crushed, `heading(s) rendered too narrow to read: ${JSON.stringify(crushed)}`).toEqual([]);
}

/**
 * **The routes every invariant runs against.**
 *
 * ⛔ **Deliberately the shell-bearing ones**, because the shell is what the
 * design defines responsively and what every screen inherits. A page that
 * breaks here breaks everywhere.
 */
const ROUTES: { path: string; name: string }[] = [
  { path: '/', name: 'Attention' },
  { path: '/accounts', name: 'Accounts' },
  { path: '/reports', name: 'Reports' },
  { path: '/settings/team', name: 'Team' },
];

for (const route of ROUTES) {
  test(`${route.name} holds its layout invariants`, async ({ page }, testInfo) => {
    await page.goto(route.path);
    // The invariants are about a settled layout, not about a frame mid-paint.
    await page.waitForLoadState('networkidle');

    const width = page.viewportSize()?.width ?? 0;
    await test.step(`no horizontal overflow at ${width}px`, () => expectNoHorizontalOverflow(page));
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
