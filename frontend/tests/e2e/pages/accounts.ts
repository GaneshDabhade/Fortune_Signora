/**
 * The Companies list — the book of accounts.
 *
 * 🔴 **This was `AttentionPage`, at `/attention`, and that screen is retired.**
 * 📁 The App Shell's nine destinations are **Home · Forecast · Pipeline ·
 * Accounts · Deals · Conversations · Signals · Reports** — ⛔ **Attention is
 * not among them and no design document defines it.** ✅ **The journeys that
 * used it were never ABOUT it**: they entered the product through a list and
 * opened a brief, and Companies is the approved list to enter through.
 *
 * **Locators are roles and text, never CSS.** Not a style preference: the
 * product ships no `data-testid` anywhere, and a suite keyed on Tailwind
 * classes would break on a spacing change while missing a broken workflow.
 * What a customer perceives — a heading, a link, a named button — is the most
 * stable thing on the page and the only thing worth asserting.
 */

import { expect, type Locator, type Page } from '@playwright/test';

export class AccountsPage {
  constructor(private readonly page: Page) {}

  /**
   * ⛔ **`/accounts`, and never `/`** — 📁 the Authenticated Entry document
   * gives `/` to the shell's resolver: *"entry resolution belongs to the
   * shell, exclusively."* Going there would resolve a workspace and land on
   * Home rather than on a list.
   */
  async open(): Promise<void> {
    await this.page.goto('/accounts');
  }

  get heading(): Locator {
    return this.page.getByRole('heading', { name: 'Companies', level: 1 });
  }

  /** Every account row. ⚡ **The row element, not a list item** — Companies
   * draws a table where the retired screen drew an ordered list. */
  get rows(): Locator {
    return this.page.locator('main a[href^="/accounts/"]');
  }

  /** The link that opens a brief. One per row, and the only clickable part of
   * it — the product deliberately refuses a row-wide hover target. */
  get accountLinks(): Locator {
    return this.page.locator('main a[href^="/accounts/"]');
  }

  row(name: string): Locator {
    return this.rows.filter({ hasText: name });
  }

  /** Waits until the list has actually loaded rather than for a duration.
   * Returns the account names in ranked order. */
  async names(): Promise<string[]> {
    await expect(this.accountLinks.first()).toBeVisible({ timeout: 20_000 });
    return this.accountLinks.allInnerTexts();
  }

  async openFirstAccount(): Promise<string> {
    await expect(this.accountLinks.first()).toBeVisible({ timeout: 20_000 });
    const name = (await this.accountLinks.first().innerText()).trim();
    await this.accountLinks.first().click();
    await this.page.waitForURL(/\/accounts\/[0-9a-f-]{36}/);
    return name;
  }

  get noOrganization(): Locator {
    return this.page.getByText('You are not part of an organization yet');
  }
}
