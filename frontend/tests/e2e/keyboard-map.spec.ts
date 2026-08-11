/**
 * **The keyboard map, pressed rather than read** — [TASK-1445](../../../docs/BACKLOG.md).
 *
 * ## 🔴 Why this journey exists and the component test does not replace it
 *
 * ⛔ **jsdom has no `<dialog>`**, so the component test stubs `showModal()`.
 * ⚡ **Everything about a modal that matters to a customer is the part that was
 * stubbed** — the top layer, the backdrop, Escape, and the focus that lands
 * inside it.
 *
 * 🔴 **And the journey asserts the thing the whole row is about: pressing a
 * shortcut the map calls LIVE does something, and the map is what says which.**
 * ⚠️ **A reference is the one screen where reading it is free and disproving it
 * costs a keypress** — so the disproving is done here, in a browser, on every
 * run.
 */

import { expect, test } from './fixtures/signora';

test.describe('finding out what the keyboard does', () => {
  test('? opens the reference from wherever you are', async ({ page }) => {
    await page.goto('/');
    await expect(page.getByRole('heading', { name: 'Attention', level: 1 })).toBeVisible();

    await page.keyboard.press('?');

    const reference = page.getByRole('dialog');
    await expect(reference).toBeVisible();
    await expect(reference.getByText('Keyboard shortcuts')).toBeVisible();
  });

  test('it says how many of its shortcuts actually work', async ({ page }) => {
    await page.goto('/');
    await page.keyboard.press('?');

    // ⛔ **The sentence is derived from the registry**, so this asserts the
    // shape rather than a number that a new binding would make stale.
    await expect(page.getByText(/\d+ of these \d+ shortcuts work today/)).toBeVisible();
    await expect(page.getByText('Not bound', { exact: true }).first()).toBeVisible();
  });

  test("it groups them the way the design's three groups do", async ({ page }) => {
    await page.goto('/');
    await page.keyboard.press('?');

    const reference = page.getByRole('dialog');
    for (const group of ['Surfaces', 'Navigate', 'Work']) {
      await expect(reference.getByText(group, { exact: true })).toBeVisible();
    }
  });

  test('escape closes it, and the page is where it was', async ({ page }) => {
    await page.goto('/');
    await page.keyboard.press('?');
    await expect(page.getByRole('dialog')).toBeVisible();

    await page.keyboard.press('Escape');
    await expect(page.getByRole('dialog')).toBeHidden();
    await expect(page.getByRole('heading', { name: 'Attention', level: 1 })).toBeVisible();
  });

  /**
   * ⛔ **The guard every modifier-free shortcut needs.** ⚠️ **A reference that
   * opens while somebody is typing a question mark into a search box is a
   * reference they turn into a complaint.**
   */
  test('typing a question mark into a field does not open it', async ({ page }) => {
    await page.goto('/');

    // ⚡ **The palette's own input, rather than a search box on the page.**
    // ⚠️ The attention screen has no inline field, and 📁 the palette is where
    // somebody would actually type a question — *"Search or ask…"* — **so it is
    // the realistic place for this shortcut to fire when it must not.**
    await page.keyboard.press('ControlOrMeta+k');
    const field = page.getByRole('dialog').getByRole('textbox').first();
    await expect(field).toBeVisible();

    await field.fill('why?');

    await expect(field).toHaveValue('why?');
    // ⛔ **The palette is a dialog too**, so the assertion names the reference's
    // own heading rather than *a dialog is open*.
    await expect(page.getByRole('heading', { name: 'Keyboard shortcuts' })).toBeHidden();
  });
});

test.describe("the map's claims survive being pressed", () => {
  /**
   * 🔴 **The row's central assertion.** 📁 The map lists `⌘K` under `Surfaces`
   * as live — ⛔ **so pressing it must open the palette.** ⚡ **If the registry
   * and the binding ever disagree, this is where a customer would find out and
   * this is where it is found instead.**
   */
  test('a shortcut the map calls live does what the map says', async ({ page }) => {
    await page.goto('/');

    await page.keyboard.press('?');
    const reference = page.getByRole('dialog');
    // ⚠️ **`exact`, because *"Works in the command palette"* is the limit
    // sentence on two other rows** — a loose match resolves to three elements
    // and the assertion stops naming one thing.
    await expect(reference.getByText('Command palette', { exact: true })).toBeVisible();
    await page.keyboard.press('Escape');
    await expect(page.getByRole('dialog')).toBeHidden();

    await page.keyboard.press('ControlOrMeta+k');
    await expect(page.getByRole('dialog')).toBeVisible();
  });

  test('the rail collapses on [, which the map lists under Navigate', async ({ page }) => {
    await page.goto('/');
    const rail = page.getByRole('navigation', { name: 'Primary' });
    const before = await rail.boundingBox();

    await page.keyboard.press('[');

    await expect(async () => {
      const after = await rail.boundingBox();
      expect(after?.width).not.toBe(before?.width);
    }).toPass();
  });
});
