/**
 * Home — where a seller's morning starts.
 *
 * 🔴 **The morning used to start on `/attention` and that screen is retired.**
 * 📁 The App Shell's nine destinations do not include it. ⚡ **Home is what
 * replaced it** — 📁 *"Home tells a person what to do next, using the
 * workspace's own data, with a reason attached to every item."*
 *
 * ⚠️ **Companies is not the same list and cannot stand in for it.** 📁
 * Companies is the whole book, in the book's own order; 📁 `card.attention` is
 * *"up to five ordered items"* **ranked by what it costs to ignore them**. ⛔
 * A journey that opens *the account a seller would work next* and then argues
 * with its score must enter through the ranked list — the book's first row is
 * whichever account sorts first, and the Playground's is one no provider has
 * scored. Pointing those journeys at Companies silently dropped a guarantee
 * they had always been given, which is [B-1022](../../../docs/BUGS.md)'s
 * second half.
 *
 * **`data-card` rather than a role**, and only here: Home's cards are a
 * registry, the registry's ids are the design's own vocabulary, and a locator
 * keyed on a card's heading would break every time copy is revised while
 * missing a card that stopped rendering entirely.
 */

import { expect, type Locator, type Page } from '@playwright/test';

export class HomePage {
  constructor(private readonly page: Page) {}

  /**
   * ⛔ **`/` rather than a workspace address** — 📁 the Authenticated Entry
   * document gives `/` to the shell's resolver: *"entry resolution belongs to
   * the shell, exclusively."* A test that composed the URL itself would be
   * asserting a resolution it had performed on the shell's behalf.
   */
  async open(): Promise<void> {
    await this.page.goto('/');
    await this.page.waitForURL(/\/w\/[0-9a-f-]{36}\/home$/, { timeout: 30_000 });
  }

  card(id: string): Locator {
    return this.page.locator(`[data-card="${id}"]`);
  }

  /** 📁 `card.attention` — *"what needs you today"*, ranked. */
  get needsYouToday(): Locator {
    return this.card('needs-you-today');
  }

  /** The way into each ranked item. One per row. */
  get rankedAccounts(): Locator {
    return this.needsYouToday.locator('a[href^="/accounts/"]');
  }

  /**
   * Opens the account Home ranks first, and returns its id.
   *
   * **The id rather than the name**, deliberately: 📁 a name is a resolved
   * claim and *"no source has named this account yet"* is a real answer the
   * identity surface may give, so a caller checking it arrived at the account
   * it clicked would be checking a value the product is allowed to withhold.
   * The id is what the click promised and what the address bar reports back.
   */
  async openFirstRankedAccount(): Promise<string> {
    const link = this.rankedAccounts.first();
    await expect(link).toBeVisible({ timeout: 20_000 });
    const href = await link.getAttribute('href');
    const id = /\/accounts\/([0-9a-f-]{36})/.exec(href ?? '')?.[1];
    if (id === undefined) {
      throw new Error(`Home's first ranked item is not an account link: ${href}`);
    }
    await link.click();
    await this.page.waitForURL(new RegExp(`/accounts/${id}`));
    return id;
  }
}
