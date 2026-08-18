/**
 * The attention list — a seller's morning.
 *
 * **Locators are roles and text, never CSS.** Not a style preference: the
 * product ships no `data-testid` anywhere, and a suite keyed on Tailwind
 * classes would break on a spacing change while missing a broken workflow.
 * What a customer perceives — a heading, a link, a named button — is the most
 * stable thing on the page and the only thing worth asserting.
 */

import { expect, type Locator, type Page } from '@playwright/test';

export class AttentionPage {
  constructor(private readonly page: Page) {}

  /**
   * ⚠️ **`/attention`, not `/`.** 📁 The Authenticated Entry document gives `/`
   * to the shell's resolver — *"entry resolution belongs to the shell,
   * exclusively"* — and this screen took its own address when that was wired.
   */
  async open(): Promise<void> {
    await this.page.goto('/attention');
  }

  get heading(): Locator {
    return this.page.getByRole('heading', { name: 'Attention', level: 1 });
  }

  /** Every account row, in the order the pipeline ranked them. */
  get rows(): Locator {
    return this.page.locator('main ol > li');
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

  /** The empty state a workspace sees when it has declared no accounts. */
  get neverAsked(): Locator {
    return this.page.getByText('Signora does not know which companies to watch yet');
  }

  get noOrganization(): Locator {
    return this.page.getByText('You are not part of an organization yet');
  }
}
