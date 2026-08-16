import { expect, type Page } from '@playwright/test';

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

/**
 * **Does anything spill sideways out of the viewport?**
 *
 * The customer-visible failure: a table, a toolbar or a card wider than the
 * window, so the whole page scrolls horizontally and the right-hand column is
 * unreachable without dragging. ⛔ **This is the single most common responsive
 * defect and the suite could not see it at any width.**
 */
export async function expectNoHorizontalOverflow(page: Page): Promise<void> {
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
 * **Is anything inside a fixed region pushed below the fold, where nothing can
 * scroll it into view?**
 *
 * The customer-visible failure: a control is in the DOM, Playwright reports it
 * **visible**, and a customer cannot press it. ⛔ **`expect(button).toBeVisible()`
 * passes; a click times out.**
 *
 * ⚡ **[B-241](../../../docs/BUGS.md) is exactly this, and QE's matrix could not
 * see it.** The rail's `nav` was `h-full` while starting 106px below the
 * wordmark, so its pinned utilities sat at **y=872 on an 844px viewport**. **It
 * overflowed at every width for several cycles** — a scrollbar absorbed it
 * until a `fixed` sheet had nowhere to scroll to. **Lane A found it because a
 * journey timed out, not because anything asserted it.**
 *
 * ⛔ **The reason this file missed it is one word**: `expectNoHorizontalOverflow`
 * reads `rect.right` and **nothing read `rect.bottom`.** A whole axis was
 * unasserted, and the axis that carries the shell's own furniture.
 *
 * **Fixed subtrees only, and that is the discriminating property.** Ordinary
 * content below the fold is *reachable by scrolling* and is not a defect. **A
 * descendant of a `position: fixed` element cannot be scrolled into view by
 * anybody**, so its bottom edge is a promise the layout has to keep.
 */
export async function expectNothingFixedBelowTheFold(page: Page): Promise<void> {
  // ⛔ **The sheet is CLOSED by default, and a closed sheet measures nothing.**
  // Below 1024 the rail is a `fixed` overlay carrying `invisible
  // -translate-x-full`, so every element inside it is skipped as hidden — and
  // this check passed cleanly on a tree with B-241 deliberately reintroduced.
  //
  // ⚡ **B-241 was found by a journey that OPENED the navigation**, which is the
  // only state where the sheet's contents are reachable at all. **So the check
  // opens it too**, and where there is no such control the rail is already in
  // flow and there is nothing to open.
  const opener = page.getByRole('button', { name: /open navigation/i });
  if (await opener.count()) {
    await opener.first().click();
    await page.waitForTimeout(300);
  }

  const offenders = await page.evaluate(() => {
    const viewportHeight = window.innerHeight;
    const found: { tag: string; text: string; bottom: number; overflow: number }[] = [];

    const fixedRoots = Array.from(document.body.querySelectorAll<HTMLElement>('*')).filter(
      (element) => getComputedStyle(element).position === 'fixed',
    );

    for (const root of fixedRoots) {
      const rootStyle = getComputedStyle(root);
      if (rootStyle.display === 'none' || rootStyle.visibility === 'hidden') continue;
      // A fixed panel that scrolls internally CAN bring its own children into
      // view, so only the panel's own edge is a promise.
      const scrolls = ['auto', 'scroll'].includes(rootStyle.overflowY);
      const candidates = scrolls ? [root] : [root, ...Array.from(root.querySelectorAll<HTMLElement>('*'))];

      for (const element of candidates) {
        const style = getComputedStyle(element);
        if (style.display === 'none' || style.visibility === 'hidden') continue;
        const rect = element.getBoundingClientRect();
        if (rect.width === 0 || rect.height === 0) continue;
        // Leaf elements only for the descendants: a container reported alongside
        // every child it holds is noise, and noise is what gets a gate ignored.
        if (element !== root && element.children.length > 0) continue;
        if (rect.bottom > viewportHeight + 1) {
          found.push({
            tag: element.tagName.toLowerCase(),
            text: (element.textContent || '').trim().slice(0, 40),
            bottom: Math.round(rect.bottom),
            overflow: Math.round(rect.bottom - viewportHeight),
          });
        }
      }
    }
    return { viewportHeight, offenders: found.slice(0, 5), total: found.length };
  });

  // ⛔ **Put the sheet back, and this is not tidiness.** An open overlay
  // legitimately covers `main`, so leaving it open made the *overlap* check
  // fail on a correct layout — a check breaking the check after it, which is
  // the worst kind of false positive because the error names the wrong
  // assertion entirely.
  const closer = page.getByRole('button', { name: /close navigation/i });
  if (await closer.count()) {
    await closer.first().click();
    await page.waitForTimeout(250);
  }

  expect(
    offenders.total,
    `${offenders.total} element(s) inside a fixed region sit below the ${offenders.viewportHeight}px fold, ` +
      `where nothing can scroll them into view — a customer cannot press them: ${JSON.stringify(offenders.offenders)}`,
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
export async function expectNoDocumentScroll(page: Page): Promise<void> {
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
 *
 * ⚠️ **Measured against the CONTENT box when a fixed overlay is involved, and
 * that correction came from a false positive on the first real run.** At 640px
 * every screen reported `<navigation>` and `<main>` overlapping by 15,680px².
 * **The layout was correct**: `main` runs to y=867 with `padding-bottom: 24px`,
 * the fixed bottom bar starts at y=843, and **the padding covers the overlap
 * exactly**. Nothing was ever under the bar.
 *
 * ⛔ **A guard that fires on correct behaviour gets switched off, and then it
 * protects nothing** — so the border box was the wrong thing to measure. **The
 * property that matters is content clearance**, and this now fails if that
 * `padding-bottom` is removed while passing when it is there.
 */
export async function expectShellRegionsDoNotOverlap(page: Page): Promise<void> {
  // ⚠️ **Scrolled to the bottom first, and that is the whole check.** A fixed
  // bottom bar covers content only once the page is scrolled down to it — at
  // scroll 0 the last element is far above and every measurement is clean.
  //
  // ⛔ **Found by trying to make this fail and failing.** Removing the
  // compensating `padding-bottom` left the suite green twice, because `main`'s
  // height is content *plus* padding: take the padding away and the box shrinks
  // by exactly as much, so the overlap never appears. **The assertion was
  // measuring a position where the defect cannot occur** — decorative, in §2's
  // sense, and it passed on the real product for the wrong reason.
  // ⛔ **Scrolled until the page STOPS GROWING, not once.** A single
  // `scrollTo(bottom)` lands mid-page while a list is still rendering, and the
  // content that then sits below the bar is not hidden — it is simply further
  // down, reachable by scrolling. **Asserting there reports a defect that does
  // not exist**, which it did on the Team screen: 34,040px², consistently, on a
  // correct product.
  //
  // ⚡ **The property is only meaningful at a settled bottom**, so this waits
  // for `scrollHeight` to stop changing and confirms it actually reached it.
  await page.evaluate(async () => {
    let previous = -1;
    for (let attempt = 0; attempt < 20 && previous !== document.documentElement.scrollHeight; attempt += 1) {
      previous = document.documentElement.scrollHeight;
      window.scrollTo(0, previous);
      await new Promise((resolve) => setTimeout(resolve, 150));
    }
  });
  const atBottom = await page.evaluate(
    () => window.scrollY + window.innerHeight >= document.documentElement.scrollHeight - 2,
  );
  expect(atBottom, 'the page never settled at its bottom, so clearance cannot be judged').toBe(true);

  const overlaps = await page.evaluate(() => {
    const roles = ['banner', 'navigation', 'main'];
    const found: { a: string; b: string; area: number }[] = [];
    const boxes: { role: string; el: HTMLElement; r: DOMRect; fixed: boolean; content: DOMRect }[] = [];

    for (const role of roles) {
      // ⛔ **`querySelectorAll`, and this is the correction that made the whole
      // check real.** It was `querySelector`, which returns the FIRST match —
      // and the shell mounts TWO `nav[aria-label="Primary"]` elements, the
      // first collapsed to 0×0. That one was skipped as zero-size, so the
      // fixed bottom bar was never measured and **this assertion could not
      // fail at any width, on any page, for any layout.**
      //
      // ⚡ **Three mutations passed before the vacuity was found**, which is
      // why a green check is not evidence until something has made it red.
      const els = Array.from(
        document.querySelectorAll<HTMLElement>(
          role === 'main' ? 'main' : role === 'banner' ? 'header, [role="banner"]' : 'nav, [role="navigation"]',
        ),
      );
      for (const el of els) {
      const style = getComputedStyle(el);
      if (style.display === 'none' || style.visibility === 'hidden') continue;
      const r = el.getBoundingClientRect();
      if (r.width === 0 || r.height === 0) continue;
      // **The content box, not the border box** — see the note below.
      const content = new DOMRect(
        r.x + parseFloat(style.paddingLeft),
        r.y + parseFloat(style.paddingTop),
        r.width - parseFloat(style.paddingLeft) - parseFloat(style.paddingRight),
        r.height - parseFloat(style.paddingTop) - parseFloat(style.paddingBottom),
      );
      boxes.push({ role, el, r, fixed: style.position === 'fixed', content });
      }
    }

    for (let i = 0; i < boxes.length; i += 1) {
      for (let j = i + 1; j < boxes.length; j += 1) {
        const a = boxes[i];
        const b = boxes[j];
        // ⛔ **Containment is not collision.** A `<header>` inside `<main>` is a
        // section heading, not a banner drawn over the content, and it overlaps
        // by 100% by construction. **`querySelectorAll` made that visible the
        // moment it stopped looking only at the first match** — 22 of 26 failed
        // on a correct product, which is the false-positive shape that gets a
        // gate switched off.
        if (a.el.contains(b.el) || b.el.contains(a.el)) continue;
        // A fixed overlay is *supposed* to sit above the flow. What matters is
        // whether the other region's CONTENT reaches under it — which is what
        // its padding exists to prevent.
        const ra = a.fixed || b.fixed ? a.content : a.r;
        const rb = a.fixed || b.fixed ? b.content : b.r;
        const ox = Math.min(ra.x + ra.width, rb.x + rb.width) - Math.max(ra.x, rb.x);
        const oy = Math.min(ra.y + ra.height, rb.y + rb.height) - Math.max(ra.y, rb.y);
        const depth = Math.min(Math.max(0, ox), Math.max(0, oy));
        const area = Math.max(0, ox) * Math.max(0, oy);
        // ⚠️ **Tolerance on DEPTH, not area** — the same 1px reasoning the
        // overflow check uses, and for the same measured reason. A full-width
        // region overlapping by half a pixel of rounding is 296px², which is
        // large as an area and invisible as a defect. **A bar actually covering
        // content overlaps by tens of pixels**, so nothing real is masked.
        if (depth > 1) found.push({ a: a.role, b: b.role, area: Math.round(area) });
      }
    }
    return found;
  });

  expect(
    overlaps,
    `shell regions overlap so a control in one is drawn under the other: ${JSON.stringify(overlaps)}`,
  ).toEqual([]);
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
export async function expectNavigationReachable(page: Page): Promise<void> {
  // ⛔ **This matched on WORDS and not on capability, and it passed with the
  // primary navigation deleted.** The old predicate accepted any control named
  // `/menu|navigation|open menu/`, and at 1280 that is satisfied by **"Collapse
  // navigation"** and **"Account menu"** — measured, both visible, **neither
  // of which navigates anywhere.**
  //
  // ⚡ **Criterion 6 of B-428, failed by QE's own check**: it passed by asking
  // something *broader* than the design requires. **A `display: none` on the
  // rail left it green.**
  //
  // **The property is a link a customer can follow, or a control that opens
  // one.** `Collapse` and `Account menu` do neither, so they are named out.
  // ⛔ **The PRIMARY landmark by name, not any `role="navigation"`.** Two
  // tightenings were needed and each was forced by a measurement:
  //
  // **First** the predicate matched control NAMES — `/menu|navigation/` — and
  // at 1280 that is satisfied by **"Collapse navigation"** and **"Account
  // menu"**, neither of which navigates anywhere.
  //
  // **Then** it matched any navigation LANDMARK, and with the rail deleted the
  // page still offered two: **"Whose work"** and **"How the list is
  // arranged"** — content filters inside `main`. **A filter is not a way out
  // of the page.**
  //
  // ⚡ **Both were criterion 6 of [B-428](../../../docs/BUGS.md) failing inside
  // the check written to satisfy it**: passing by asking something broader than
  // the design requires. **A `display: none` on the rail left it green twice.**
  const primary = page.getByRole('navigation', { name: /^Primary$/i });
  const opener = page.getByRole('button', { name: /^(open navigation|open menu|main menu)$/i });

  let reachable = 0;
  for (const candidate of [primary, opener]) {
    const count = await candidate.count();
    for (let index = 0; index < count; index += 1) {
      const element = candidate.nth(index);
      if (!(await element.isVisible())) continue;
      const box = await element.boundingBox();
      if (box && box.width > 0 && box.height > 0) reachable += 1;
    }
  }

  // A navigation landmark with no links in it is furniture, not navigation.
  if (reachable > 0 && (await primary.count())) {
    const links = await primary.first().getByRole('link').count();
    expect(links, 'the navigation landmark contains no links — it cannot take anybody anywhere').toBeGreaterThan(0);
  }

  expect(
    reachable,
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
export async function expectNoCrushedText(page: Page): Promise<void> {
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
export const ROUTES: { path: string; name: string }[] = [
  // ⚠️ **`/` still renders and still bears the shell** — [TASK-1482](../../../docs/BACKLOG.md)
  // removed its RAIL ENTRY on [D-240](../../../docs/DECISION_REGISTER.md), not
  // the route. ⛔ **It is dropped from this list because the list is what a
  // customer can REACH from the shell**, and nothing links here any more.
  // ⚡ **Whether `/` is retired is a separate question the ruling did not
  // answer**, and this file does not decide it by omission.
  //
  // ⛔ **Removed rather than replaced with `/business`, which was already
  // below** — a duplicate here would have run every responsive invariant
  // twice against one route and reported it as wider coverage.
  { path: '/signals', name: 'Signals' },
  { path: '/reports', name: 'Reports' },
  { path: '/settings/team', name: 'Team' },
  { path: '/settings/products', name: 'Products' },
  { path: '/business', name: 'Business' },
];

/**
 * ⛔ **A route that 404s is a defect in this list, not in the layout** — and it
 * has to say so, because the 404 page legitimately has no navigation and would
 * otherwise fail `expectNavigationReachable` with a message about the shell.
 *
 * ⚠️ **Found on the first real run.** The list opened with `/accounts`, which
 * does not exist — only `/accounts/[accountId]` does. The invariant reported
 * *"the product has no way out of this page"*, which was **true of the page it
 * was given and false about the product.** That is the same shape this file was
 * written to catch, one level up: a correct assertion answering a question
 * nobody meant to ask.
 */
export async function expectRouteExists(page: Page, path: string): Promise<void> {
  const notFound = page.getByRole('heading', { name: /does not lead anywhere/i });
  expect(
    await notFound.count(),
    `${path} 404s — fix the route list in this file, not the shell`,
  ).toBe(0);
}
