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

test.describe('§04 · §05 — the breadcrumb is in the top bar', () => {
  /**
   * 🔴 **The slot existed, the trail existed, and nothing joined them.**
   *
   * ⚠️ **Measured on `/accounts` at 1440 × 900 before the fix:** the top bar's
   * `[data-slot="breadcrumb"]` was **`617 × 0` with zero children**, while
   * `nav[aria-label="Breadcrumb"]` sat at **`@281,107`** — inside the page's own
   * content. ⛔ **So the design's one breadcrumb was drawn in the one place the
   * design does not put it.**
   *
   * 📁 **§04 — *"Left: breadcrumb only."*** 📁 **§05 — *"Mandatory below the
   * first level, because most sessions start from a deep link."***
   */
  test('@journey a second-level screen states its trail in the top bar, once', async ({ page }) => {
    await page.setViewportSize({ width: 1440, height: 900 });
    await page.goto('/accounts');
    await expect(page.getByRole('heading', { name: 'Companies', level: 1 })).toBeVisible({
      timeout: 30_000,
    });

    const slot = page.locator('[data-slot="breadcrumb"]');
    await expect(slot).toContainText('Accounts');
    await expect(slot).toContainText('Companies');
    // ⛔ **Height, not merely presence** — the defect was a slot with content
    // measuring zero, which every text assertion would have passed.
    expect(Math.round((await slot.boundingBox())?.height ?? 0)).toBeGreaterThan(12);

    // ⛔ **Exactly one trail on the page.** ⚡ Moving it must not leave a copy
    // behind, which is the failure mode of every *"add it to the shell too"*.
    await expect(page.locator('main nav[aria-label="Breadcrumb"]')).toHaveCount(0);
  });

  /**
   * 🔴 **A route change is where this broke, and only in the browser.**
   *
   * ⚠️ **Clicking a row left the slot EMPTY while loading the same URL directly
   * filled it.** **React mounts the incoming tree before unmounting the
   * outgoing one**, so the outgoing screen's cleanup cleared a trail its
   * successor had already published.
   */
  test('@journey the trail follows a click into an account, and is the account\'s name', async ({
    page,
  }) => {
    await page.setViewportSize({ width: 1440, height: 900 });
    await page.goto('/accounts');
    const first = page.locator('main a[href^="/accounts/"]').first();
    const name = (await first.textContent())?.trim() ?? '';
    await first.click();
    await page.waitForURL(/\/accounts\/[0-9a-f-]{36}/, { timeout: 30_000 });

    const slot = page.locator('[data-slot="breadcrumb"]');
    await expect(slot).toContainText('Accounts');
    await expect(slot).toContainText(name);
  });
});

test.describe('§13 · the collapsed utility panel', () => {
  /**
   * 📁 ***"Collapsing leaves a 28px rail with the tab icons."***
   *
   * 🔴 **It left a rail of LETTERS at 19 × 26** — `I`, `A`, `N` — measured on
   * `/accounts` at 1440 × 900. ⛔ **`2.5.8` asks for 24 × 24 with 8px
   * separation**, and a bare initial is not the icon the design names.
   */
  test('@a11y the tab rail is 24px targets with 8px separation', async ({ page }) => {
    await page.setViewportSize({ width: 1440, height: 900 });
    await page.goto('/accounts');
    await expect(page.getByRole('heading', { name: 'Companies', level: 1 })).toBeVisible({
      timeout: 30_000,
    });

    // 🔴 **`[role="tab"]` until [B-1055](../../../docs/BUGS.md), and the change
    // is the point rather than an inconvenience.**
    //
    // ⛔ **Collapsed, this rail published three `role="tab"` for a panel it was
    // not rendering** — a screen-reader user was told *"tab, selected"* and
    // given nothing to reach. ✅ **Collapsed they are DISCLOSURES**:
    // `aria-expanded="false"`, and clicking one now opens the panel, which it
    // previously did not do at all.
    //
    // ⚡ **Everything this test asserts is unchanged** — 📁 §17 `2.5.8`, 24×24
    // targets with 8px separation, and the word as the accessible name.
    // ⛔ **Only the role the controls carry has changed**, so this re-aims the
    // selector rather than relaxing the assertion.
    const tabs = page.locator('#shell-utility-panel button[aria-expanded]');
    await expect(tabs).toHaveCount(3);

    // ⛔ **And no tab role at all while collapsed**, which is the half the old
    // selector could not have caught: it counted three and was satisfied.
    await expect(page.locator('#shell-utility-panel [role="tab"]')).toHaveCount(0);

    const boxes = [];
    for (let i = 0; i < 3; i += 1) boxes.push((await tabs.nth(i).boundingBox())!);

    for (const box of boxes) {
      expect(Math.round(box.width), 'a target narrower than 24px').toBeGreaterThanOrEqual(24);
      expect(Math.round(box.height), 'a target shorter than 24px').toBeGreaterThanOrEqual(24);
    }
    // ⛔ **The separation, which the letters did not have** — 4px between 26px
    // rows. 📁 `2.5.8` counts the gap, not only the box.
    for (let i = 1; i < boxes.length; i += 1) {
      const gap = boxes[i]!.y - (boxes[i - 1]!.y + boxes[i - 1]!.height);
      expect(Math.round(gap), 'less than 8px between two targets').toBeGreaterThanOrEqual(8);
    }

    // ♿ **The word is still the accessible name**, so nothing was lost with
    // the letters.
    await expect(tabs.nth(0)).toHaveAccessibleName('Insights');
  });
});
