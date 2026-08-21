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
    const id = /\/accounts\/([0-9a-f-]{36})/.exec(this.page.url())?.[1];
    if (!id) throw new Error(`Not on a brief: ${this.page.url()}`);
    return id;
  }

  /**
   * ⚡ **The record header's title — §08's `Title` role, and the page's ONE
   * level-1 heading.**
   *
   * 🔴 **This replaced `backToList`**, a *"← All accounts"* link the approved
   * design does not draw: 📁 §04 puts *"breadcrumb only"* on the left, and the
   * trail *Accounts / <this company>* is published by the screen itself. ⛔ **A
   * back link beside a breadcrumb is two wayfinding controls for one journey**,
   * and the tests were using the one the design removed as their proof that the
   * page had arrived.
   *
   * ⚠️ **It is a stronger proof than the link was.** 📁 [B-313](../../../docs/BUGS.md)
   * — a record page carries exactly one `<h1>`, so this asserts the outline as
   * well as the paint.
   */
  get title(): Locator {
    return this.page.getByRole('heading', { level: 1 });
  }

  section(name: string): Locator {
    return this.page.getByRole('heading', { name, level: 2 });
  }

  get whatContributed(): Locator {
    return this.section('Account score');
  }

  get whatHasHappened(): Locator {
    return this.section('Recent activity');
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
    await expect(this.page.getByText(/Account score \d+ out of 100/)).toBeVisible({
      timeout: 20_000,
    });
  }
}
