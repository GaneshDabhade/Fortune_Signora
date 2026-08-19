/**
 * **The four responsive regimes, as behaviour** — against 📁
 * `Fortune Signora App Shell.dc.html` **§20**
 * ([D-138](../../../docs/DECISION_REGISTER.md)).
 *
 * > | 📁 Band | 📁 What the design says |
 * > |---|---|
 * > | **≥1600** | rail 232px, utility panel 360px, both can remain open |
 * > | **1280–1599** | the reference layout — rail 232px, panel 300px |
 * > | **1024–1279** | *"Rail collapses to 56px icons with tooltips"* · *"panel closes to a 28px tab rail"* · *"Filter strip stays; chips scroll horizontally"* |
 * > | **<1024** | *"Rail becomes a sheet from a top-bar button"* · *"Filter strip collapses to one 'Scope' button with a count"* · *"Tables become row cards"* |
 *
 * ## ⛔ What this file deliberately does NOT assert
 *
 * **Geometry that happens to be true.** ⚠️ **A test reading `left === 217px`
 * freezes an accident**; these read the things the design states — **which
 * regime is in force, whether the rail is in flow, whether one row of controls
 * became one control** — and the two numbers the design names by name.
 */
import { expect, test } from './fixtures/signora';

/**
 * ⚡ **Sixteen widths, not five.** ⛔ **The five documented viewports cannot
 * distinguish a layout that responds from one hard-coded to five sizes** —
 * which is the failure this file exists to catch.
 */
const WIDTHS = [320, 360, 390, 430, 600, 768, 820, 900, 1024, 1100, 1200, 1280, 1366, 1440, 1600, 1920];

interface Frame {
  client: number;
  hScroll: boolean;
  railWidth: number | null;
  railInFlow: boolean;
  contentStartsAt: number;
  railRowWidths: number[];
  iconOffCentre: (number | null)[];
  panelWidth: number | null;
  scope: boolean;
  table: boolean;
  cards: boolean;
  clipped: string[];
}

async function frame(page: import('@playwright/test').Page): Promise<Frame> {
  return page.evaluate(() => {
    const de = document.documentElement;
    const railBox = document.querySelector('[data-collapsed]') as HTMLElement | null;
    const rb = railBox?.getBoundingClientRect() ?? null;
    const rows = Array.from(document.querySelectorAll('#shell-navigation a, #shell-navigation button'));
    const panel = document.querySelector('#shell-utility-panel');

    const clipped: string[] = [];
    for (const el of Array.from(document.querySelectorAll('button, a[href], input, summary'))) {
      const r = el.getBoundingClientRect();
      if (r.width === 0 && r.height === 0) continue;
      const cs = getComputedStyle(el);
      if (cs.visibility === 'hidden' || cs.display === 'none') continue;
      // ⛔ **The closed navigation sheet is off-canvas BY DESIGN**, not clipped.
      const sheet = (el as HTMLElement).closest('[data-sheet-open]');
      if (sheet !== null && sheet.getAttribute('data-sheet-open') !== 'true') continue;
      // 📁 **Design System v2 §17 `1.4.10` — *"only tables retain horizontal
      // scroll."*** A control inside a scrollable region is reachable.
      let scroller: HTMLElement | null = el as HTMLElement;
      let inScroller = false;
      while (scroller !== null && scroller !== document.body) {
        if (scroller.scrollWidth > scroller.clientWidth + 1) { inScroller = true; break; }
        scroller = scroller.parentElement;
      }
      if (inScroller) continue;
      if (r.right > de.clientWidth + 1 || r.left < -1) {
        clipped.push(`${(el.textContent ?? el.getAttribute('aria-label') ?? '').trim().slice(0, 20)}`);
      }
    }

    return {
      client: de.clientWidth,
      hScroll: de.scrollWidth > de.clientWidth,
      railWidth: rb === null ? null : Math.round(rb.width),
      railInFlow: railBox === null ? false : getComputedStyle(railBox).position !== 'fixed',
      contentStartsAt: Math.round(document.querySelector('main#shell-content')!.getBoundingClientRect().x),
      railRowWidths: [...new Set(rows.map((el) => Math.round(el.getBoundingClientRect().width)))],
      iconOffCentre: [...new Set(rows.map((el) => {
        const ir = el.querySelector('svg')?.getBoundingClientRect();
        if (ir === undefined || rb === null) return null;
        return Math.round(ir.x + ir.width / 2 - (rb.x + rb.width / 2));
      }))],
      panelWidth: panel === null ? null : Math.round(panel.getBoundingClientRect().width),
      scope: document.querySelector('[data-testid="scope-control"]') !== null,
      table: document.querySelector('main table') !== null,
      cards: document.querySelector('[data-testid="accounts-cards"]') !== null,
      clipped: clipped.slice(0, 4),
    };
  });
}

/** ⚡ **Every rule the design states, checked against one measurement.** */
function breaches(w: number, f: Frame): string[] {
  const out: string[] = [];
  if (f.hScroll) out.push(`${w}: the page scrolls horizontally`);
  if (f.clipped.length > 0) out.push(`${w}: clipped ${f.clipped.join(', ')}`);

  if (w < 1024) {
    // 📁 *"Rail becomes a sheet from a top-bar button."* ⛔ **Not a narrower
    // rail, and not an invisible reservation underneath the content.**
    if (f.railInFlow) out.push(`${w}: the rail is still in flow`);
    if (f.contentStartsAt !== 0) out.push(`${w}: content starts at ${f.contentStartsAt}, not 0`);
    if (f.panelWidth !== null) out.push(`${w}: the utility panel exists below 1024`);
    // 📁 *"Filter strip collapses to one 'Scope' button with a count."*
    if (!f.scope) out.push(`${w}: no Scope control`);
    // 📁 *"Tables become row cards."*
    if (f.table) out.push(`${w}: a table below 1024`);
    if (!f.cards) out.push(`${w}: no row cards below 1024`);
  } else {
    if (!f.railInFlow) out.push(`${w}: the rail is out of flow at or above 1024`);
    if (f.scope) out.push(`${w}: the Scope control appears at or above 1024`);
    if (!f.table) out.push(`${w}: no table at or above 1024`);
    // ⛔ **One geometry for every row, in either state** — the collapsed-rail
    // defect was rows of 16px and 31px in a 56px rail.
    if (f.railRowWidths.length !== 1) {
      out.push(`${w}: the rail's rows have ${f.railRowWidths.length} widths ${JSON.stringify(f.railRowWidths)}`);
    }
  }

  // 📁 The two rail widths the design names.
  if (w >= 1024 && w < 1280) {
    if (f.railWidth !== 56) out.push(`${w}: rail ${f.railWidth}px, and the design says 56`);
    if (f.panelWidth !== 28) out.push(`${w}: panel ${f.panelWidth}px, and the design says 28`);
    // ⛔ **Centred, because a 56px icon rail is the one place it can be wrong
    // without looking wrong** — the icons sat 8px left of centre.
    if (f.iconOffCentre.some((o) => o !== null && o !== 0)) {
      out.push(`${w}: icons off the rail's centre by ${JSON.stringify(f.iconOffCentre)}`);
    }
  }
  if (w >= 1280 && f.railWidth !== 232) out.push(`${w}: rail ${f.railWidth}px, and the design says 232`);

  return out;
}

test.describe('§20 · the shell responds by regime, at every width between them', () => {
  test('@a11y @journey 1920 → 320 and back, with no regime it only works inside', async ({
    page,
  }) => {
    await page.setViewportSize({ width: 1600, height: 900 });
    await page.goto('/accounts');
    await expect(page.getByRole('heading', { name: 'Companies', level: 1 })).toBeVisible({
      timeout: 30_000,
    });

    const found: string[] = [];
    // ⚡ **Down and back up on ONE page**, because the question is whether the
    // layout recovers — ⛔ a fresh load at each width would never ask it.
    for (const w of [...WIDTHS].reverse().concat(WIDTHS)) {
      await page.setViewportSize({ width: w, height: 900 });
      // ⚡ The band hook measures on `resize`; this is one frame, not a guess.
      await page.waitForTimeout(400);
      found.push(...breaches(w, await frame(page)));
    }

    expect(found, 'the shell does not hold its regime at these widths').toEqual([]);
  });

  /**
   * 📁 **Design System v2 §17 `1.4.10`** — *"The shell reflows to 320px at 400%
   * zoom; only tables retain horizontal scroll."* ⚡ **400% of 1280 IS 320 CSS
   * pixels**, which is the equivalence a browser can be put into.
   */
  test('@a11y at 320 CSS pixels nothing overflows and nothing is clipped', async ({ page }) => {
    await page.setViewportSize({ width: 320, height: 512 });
    await page.goto('/accounts');
    await expect(page.getByRole('heading', { name: 'Companies', level: 1 })).toBeVisible({
      timeout: 30_000,
    });

    const f = await frame(page);
    expect(f.hScroll).toBe(false);
    expect(f.clipped).toEqual([]);
  });

  /**
   * 📁 *"Rail becomes a sheet from a top-bar button."* ⛔ **Every entry must be
   * reachable inside it** — 📁 [B-180](../../../docs/BUGS.md) is what a rail
   * that overflowed its own sheet cost.
   */
  test('@journey the sheet holds the whole rail, and the content keeps the viewport', async ({
    page,
  }) => {
    await page.setViewportSize({ width: 390, height: 844 });
    await page.goto('/accounts');
    await expect(page.getByRole('heading', { name: 'Companies', level: 1 })).toBeVisible({
      timeout: 30_000,
    });

    // ⛔ **No reservation underneath the content**, which is what a narrowed
    // rail would leave.
    expect((await frame(page)).contentStartsAt).toBe(0);

    // ⛔ **The exact control, not a pattern** — ⚠️ `/navigation/i` also matches
    // the sheet's own *"Close navigation"*, so `.first()` closed what it meant
    // to open and the entries stayed off-canvas.
    await page.getByRole('button', { name: 'Open navigation' }).click();
    await expect(page.locator('[data-sheet-open="true"]')).toBeVisible();
    // ⚡ **The sheet SLIDES** — 📁 `transition-transform duration-200`. ⛔ The
    // attribute flips on click; the geometry arrives a frame later, and
    // measuring in between reads the off-canvas position.
    await expect
      .poll(async () =>
        page.locator('#shell-navigation a').first().evaluate((el) => Math.round(el.getBoundingClientRect().x)),
      )
      .toBeGreaterThanOrEqual(0);

    const unreachable = await page.evaluate(() => {
      const de = document.documentElement;
      return Array.from(document.querySelectorAll('#shell-navigation a, #shell-navigation button'))
        .filter((el) => {
          const r = el.getBoundingClientRect();
          return r.right > de.clientWidth + 1 || r.left < -1 || r.bottom > de.clientHeight + 1;
        })
        .map((el) => (el.textContent ?? '').trim().slice(0, 20));
    });
    expect(unreachable, 'a rail entry the sheet cannot reach').toEqual([]);
  });

  /**
   * 📁 *"Collapsed items expose their label as an accessible name and a 300ms
   * tooltip."*
   */
  test('@a11y the collapsed rail keeps its tooltips', async ({ page }) => {
    await page.setViewportSize({ width: 1100, height: 900 });
    await page.goto('/accounts');
    await expect(page.getByRole('heading', { name: 'Companies', level: 1 })).toBeVisible({
      timeout: 30_000,
    });

    await page.locator('#shell-navigation a').first().hover();
    await expect(page.getByRole('tooltip')).toBeVisible();
  });

  /**
   * 📁 **1024–1279 — *"Filter strip stays; chips scroll horizontally."*** ⛔ **A
   * wrapping desktop row is not that**, and it is what produced four rows of
   * pills on a phone.
   */
  test('@journey the filter strip scrolls on a small laptop and collapses below it', async ({
    page,
  }) => {
    await page.setViewportSize({ width: 1100, height: 900 });
    await page.goto('/accounts');
    await expect(page.getByRole('heading', { name: 'Companies', level: 1 })).toBeVisible({
      timeout: 30_000,
    });

    const strip = page.locator('[role="group"][aria-label="Filters"]');
    await expect(strip).toBeVisible();
    expect(
      await strip.evaluate((el) => getComputedStyle(el).flexWrap),
      'the strip wraps where the design scrolls it',
    ).toBe('nowrap');

    await page.setViewportSize({ width: 390, height: 844 });
    await page.waitForTimeout(400);

    const scope = page.getByTestId('scope-control');
    await expect(scope).toBeVisible();
    // ♿ 📁 `2.5.8` — *"44px on touch."*
    // ⚡ **The direct child** — the surface it opens holds summaries of its own.
    const trigger = scope.locator('> summary');
    expect(Math.round((await trigger.boundingBox())!.height)).toBeGreaterThanOrEqual(44);
  });
});
