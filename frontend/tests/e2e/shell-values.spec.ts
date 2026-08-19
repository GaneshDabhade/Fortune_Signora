/**
 * **§03 · §09 · §14 — the App Shell values the design states exactly** —
 * [TASK-1414 → TASK-1462](../../../docs/BACKLOG.md).
 *
 * 🔴 **Every assertion here is GEOMETRY, never a class name.**
 *
 * ⚠️ **The row is explicit about why**: *"every value in §03, §09 and §14 is
 * asserted from geometry rather than from a class name."* ⛔ **A test that
 * asserts `max-w-xl` passes while the palette is 576px and the design says
 * 640** — **which is exactly the defect this row exists to close**, and
 * exactly what a class-name assertion cannot see.
 */
import { expect, test } from './fixtures/signora';

test.describe('§09 · the command palette', () => {
  test('@journey it is anchored at 14% of the viewport height and is 640px wide', async ({
    page,
  }) => {
    await page.setViewportSize({ width: 1280, height: 900 });
    await page.goto('/');

    await page.keyboard.press('Meta+k');
    const palette = page.getByRole('dialog');
    await expect(palette).toBeVisible();

    const box = await palette.boundingBox();
    expect(box, 'the palette has no geometry').toBeTruthy();

    // 📁 *"640px, anchored at 14vh, modal elevation."*
    expect(Math.round(box!.width)).toBe(640);
    expect(Math.round((box!.y / 900) * 100)).toBe(14);
  });

  /**
   * 🔴 **[TASK-1484](../../../docs/BACKLOG.md) ⓐ — *"group order is fixed"*,
   * measured in the browser rather than in a unit test's mock.**
   *
   * ⚠️ **The unit test asserts the order against the sentence in the design
   * document.** ⛔ **This asserts that a customer pressing ⌘K on the real
   * product SEES it** — which is a different claim, and the one the row's
   * Definition of Done is written in: *"a user presses ⌘K and sees the
   * design's seven groups in the design's order."*
   *
   * ⚡ **Not every group appears**, and that is the design read correctly:
   * `Reports` and `Actions` have no source in this product today, and an empty
   * heading is a promise about something that does not exist.
   */
  test('@journey ⌘K shows the design\'s groups, in the design\'s order', async ({ page }) => {
    await page.setViewportSize({ width: 1440, height: 900 });
    await page.goto('/');
    await expect(page.getByRole('button', { name: 'Ask Signora' })).toBeVisible({
      timeout: 30_000,
    });
    /**
     * ⚠️ **The reads settle first, and this is a finding rather than a
     * precaution.** ⛔ Pressing ⌘K immediately renders a palette with **no
     * `Settings` group and one fewer `Navigate` row**: `guardFor`/`can` are
     * given `role = null` until the viewer-role read returns, and a guarded
     * destination is withheld from somebody who simply has not been checked
     * yet. 🔴 **The same class as [B-290](../../../docs/BUGS.md)** — a pending
     * read rendered as a settled answer — 📁 filed as
     * [B-291](../../../docs/BUGS.md) and NOT fixed here: it is the rail's guard
     * and the shell's, not this row's.
     */
    await page.keyboard.press('Meta+k');
    await expect(page.getByRole('dialog')).toBeVisible();

    /**
     * ✅ **`Settings` is on the page from the first frame** — 🔴
     * [B-291](../../../docs/BUGS.md), fixed.
     *
     * ⚠️ **This wait was a FINDING for an hour and is now an ordinary
     * assertion.** ⛔ The rail offered `Settings` immediately and the palette
     * withheld it for ~3 seconds, because `guardFor`/`can` were handed
     * `role = null` until the viewer-role read returned — **the palette being a
     * second answer to *what can this person reach*.** ✅ The palette takes
     * `roleKnown` now, as the rail has since
     * [B-253](../../../docs/BUGS.md), and 📁 the design's own rule applies to
     * both: *an unresolved role renders an ordinary row, never a locked one.*
     */
    await expect(
      page.locator('[role="listbox"] > div > p').filter({ hasText: /^Settings$/i }),
      'the palette offered no guarded group, so the order below measured a partial list',
    ).toBeVisible({ timeout: 30_000 });

    /**
     * ⚠️ **`textContent`, not `innerText`.** ⛔ The heading is uppercased in
     * CSS, so `allInnerTexts()` returns *"ASK SIGNORA"* — **a test comparing
     * that to the design's words fails on a rule about letterforms.**
     */
    const headings = await page
      .locator('[role="listbox"] > div > p')
      .evaluateAll((els) => els.map((el) => el.textContent!.trim()));
    expect(headings.length, 'the palette rendered no groups at all').toBeGreaterThan(0);

    // 📁 The design's seven, in the design's order, with the absent ones closed
    // up — ⛔ never re-sorted by how many results each happened to return.
    const DESIGN = ['Ask Signora', 'Recents', 'Records', 'Reports', 'Actions', 'Navigate', 'Settings'];
    expect(headings).toEqual(DESIGN.filter((group) => headings.includes(group)));
    // ⚡ **The two this row added are on the page**, so the assertion above is
    // a measurement rather than a statement about an empty list.
    expect(headings).toContain('Ask Signora');
    expect(headings).toContain('Settings');
  });
});

test.describe('§07 · the system status pill', () => {
  /**
   * 🔴 **[TASK-1484](../../../docs/BACKLOG.md) ⓑ.** 📁 *"System status is a
   * persistent pill in the top bar rather than a banner… and it expands into
   * detail on click."*
   *
   * ⚠️ **The slot held `OfflineStatus`, which answers *is this browser
   * online*** — a narrower question than §07's, and one that renders nothing at
   * all on a healthy connection. ⛔ **So the slot was empty on every screen a
   * customer has ever seen.**
   */
  test('@journey a healthy product says so, and expands into its services', async ({ page }) => {
    await page.setViewportSize({ width: 1440, height: 900 });
    await page.goto('/');

    const pill = page.getByTestId('system-status');
    await expect(pill).toBeVisible({ timeout: 30_000 });
    // ⚡ **The real `/ready`, through the real hop** — nothing is stubbed here.
    await expect(pill).toHaveAttribute('data-status', 'healthy');

    await pill.click();
    const detail = page.getByTestId('system-status-detail');
    await expect(detail).toBeVisible();
    // 📁 *"render what `/ready` returns and nothing else"* — two services, and
    // ⛔ none of the three the design draws that nothing publishes.
    await expect(detail.getByRole('listitem')).toHaveCount(2);
    await expect(detail).toContainText('Database');
    await expect(detail).toContainText('Authentication');
  });

  /**
   * 📁 *"Green shows a dot only below 1280px; amber and red always keep their
   * label."* ⚡ **The label goes; the accessible name never does.**
   */
  test('@a11y the healthy label drops below 1280 and the name does not', async ({ page }) => {
    await page.setViewportSize({ width: 1279, height: 900 });
    await page.goto('/');

    const pill = page.getByTestId('system-status');
    await expect(pill).toBeVisible({ timeout: 30_000 });
    await expect(pill).toHaveAccessibleName('All systems normal');
    await expect(pill).not.toContainText('All systems normal');
  });
});

test.describe('§12 · the assistant drawer', () => {
  /**
   * 🔴 **The number the row listed as *verified* and which was never set.**
   *
   * ⚡ **`copilot.tsx` quoted §12's *"non-modal 420px drawer"* in its own
   * header and passed no width**, so the panel opened at whatever the shell
   * gave it. ⛔ **A test reading the doc comment would have agreed with the
   * row; a test reading the geometry does not.**
   */
  test('@journey it opens at the 420px the design states', async ({ page }) => {
    await page.setViewportSize({ width: 1280, height: 900 });
    await page.goto('/');

    await page.getByRole('button', { name: 'Ask Signora' }).click();
    const panel = page.getByRole('complementary', { name: 'Ask Signora' });
    await expect(panel).toBeVisible();

    const box = await panel.boundingBox();
    expect(Math.round(box!.width)).toBe(420);
  });
});
