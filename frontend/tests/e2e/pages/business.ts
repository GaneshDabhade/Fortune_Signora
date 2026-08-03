/**
 * *Your business* — what the customer sells, who buys it, who decides, and
 * which companies they are chasing.
 *
 * **The head of the pipeline, as a screen.** Everything the intelligence
 * surface says about somebody else's company is relative to what is declared
 * here, which makes it the one place in the product where a customer's own
 * words are the input rather than the output.
 */

import { type Locator, type Page } from '@playwright/test';

export class BusinessPage {
  constructor(private readonly page: Page) {}

  async open(): Promise<void> {
    await this.page.goto('/settings/products');
  }

  get heading(): Locator {
    return this.page.getByRole('heading', { name: 'Your business', level: 1 });
  }

  section(name: string): Locator {
    return this.page.getByRole('heading', { name, level: 2 });
  }

  get addProduct(): Locator {
    return this.page.getByRole('button', { name: 'Add product' }).first();
  }

  get dialog(): Locator {
    return this.page.getByRole('dialog');
  }

  get productName(): Locator {
    return this.page.getByLabel('Name');
  }

  get save(): Locator {
    return this.page.getByRole('button', { name: 'Save' });
  }

  productRow(name: string): Locator {
    return this.page.getByRole('button', { name: `Edit ${name}` });
  }

  /** *Who you sell to* — the segment list. Empty for a new organization, and
   * designed as a statement rather than an apology. */
  get whoYouSellTo(): Locator {
    return this.section('Who you sell to');
  }

  get noSegmentsYet(): Locator {
    return this.page.getByText("You haven't described who buys from you yet");
  }
}
