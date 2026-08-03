/**
 * The account brief — *"why this account?"*
 *
 * The page exists to be argued with, so the page object exposes the argument:
 * the score, what contributed, what has happened, and the evidence behind any
 * one line of it.
 */

import { expect, type Locator, type Page } from '@playwright/test';

export class BriefPage {
  constructor(private readonly page: Page) {}

  async open(accountId: string): Promise<void> {
    await this.page.goto(`/accounts/${accountId}`);
  }

  /** The account id currently in the address bar. */
  accountId(): string {
    const match = /\/accounts\/([0-9a-f-]{36})/.exec(this.page.url());
    if (!match) throw new Error(`Not on a brief: ${this.page.url()}`);
    return match[1];
  }

  get backToList(): Locator {
    return this.page.getByRole('link', { name: 'All accounts' });
  }

  section(name: string): Locator {
    return this.page.getByRole('heading', { name, level: 2 });
  }

  get whatContributed(): Locator {
    return this.section('What contributed');
  }

  get whatHasHappened(): Locator {
    return this.section('What has happened');
  }

  /** Every citation on the page — the underlined reasons that open the
   * evidence drawer. Named by their screen-reader suffix, which is the one
   * part of them that is identical on every line. */
  get citations(): Locator {
    return this.page.getByRole('button', {
      name: /show the provider readings behind this/,
    });
  }

  get evidenceDialog(): Locator {
    return this.page.getByRole('dialog');
  }

  async openFirstCitation(): Promise<void> {
    await expect(this.citations.first()).toBeVisible({ timeout: 20_000 });
    await this.citations.first().click();
    await expect(this.evidenceDialog).toBeVisible();
  }

  /** The three workflow moves, offered on every open account. */
  get workingThis(): Locator {
    return this.page.getByRole('button', { name: "I'm working this" });
  }

  get notARealOpportunity(): Locator {
    return this.page.getByRole('button', { name: 'Not a real opportunity' });
  }

  get lostWithoutPursuing(): Locator {
    return this.page.getByRole('button', { name: 'Lost without pursuing' });
  }

  get neverScored(): Locator {
    return this.page.getByText('Nothing has scored this account yet');
  }

  async waitForScore(): Promise<void> {
    await expect(this.page.getByText(/Attention score \d+ out of 100/)).toBeVisible({
      timeout: 20_000,
    });
  }
}
