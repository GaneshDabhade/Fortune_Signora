/**
 * Settings — the organization, and the way into the two pages beneath it.
 *
 * Owner-only, guarded client-side as a courtesy and server-side by Casbin as
 * the decision. The suite exercises both halves, because a route guard that
 * fails open and a policy that fails closed look identical to a customer
 * until the day they do not.
 */

import { type Locator, type Page } from '@playwright/test';

export class SettingsPage {
  constructor(private readonly page: Page) {}

  async open(): Promise<void> {
    await this.page.goto('/settings');
  }

  get heading(): Locator {
    return this.page.getByRole('heading', { name: 'Settings', level: 1 });
  }

  get newOrganization(): Locator {
    return this.page.getByRole('button', { name: 'New organization' }).first();
  }

  get organizationsTable(): Locator {
    return this.page.getByRole('table');
  }

  get toProducts(): Locator {
    return this.page.getByRole('link', { name: 'Products' });
  }

  get toConnections(): Locator {
    return this.page.getByRole('link', { name: 'Connections' });
  }

  get dialog(): Locator {
    return this.page.getByRole('dialog');
  }
}
