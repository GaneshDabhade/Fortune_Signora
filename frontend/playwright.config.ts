import { defineConfig } from '@playwright/test';

/**
 * E2E configuration.
 *
 * Tests requiring a real OAuth round trip are skipped unless provider
 * credentials are present: a suite that fails in every environment lacking
 * secrets trains people to ignore red, which is worse than a visible skip.
 * The tests that do not need OAuth run everywhere.
 */
export default defineConfig({
  testDir: './tests/e2e',
  timeout: 30_000,
  fullyParallel: false,
  reporter: process.env.CI ? 'github' : 'list',
  use: {
    baseURL: process.env.SIGNORA_APP_URL ?? 'http://localhost:3000',
    trace: 'retain-on-failure',
  },
});
