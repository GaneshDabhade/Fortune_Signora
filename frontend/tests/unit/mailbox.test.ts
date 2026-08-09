/**
 * **The development mailbox** — [TASK-474](../../../docs/BACKLOG.md) milestone 1.
 *
 * ⚡ **The tests are mostly about what it refuses.** A mailbox that keeps
 * every verification and reset link this process has sent **is a record of
 * credentials being issued** — the row says so — so the interesting
 * properties are the bounds, not the storage.
 */
import { readFileSync } from 'node:fs';
import { join } from 'node:path';

import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

import { MAILBOX_CAPACITY, delivery, forget, remember } from '@/lib/auth/mailbox';

const LINK = {
  to: 'm.reinhardt@northwind.com',
  purpose: 'verify-email',
  url: 'http://localhost:3000/verify?token=a-real-token',
} as const;

beforeEach(() => forget());
afterEach(() => vi.unstubAllEnvs());

describe('it keeps what was actually sent', () => {
  it('remembers a delivery, newest first', () => {
    remember(LINK);
    remember({ ...LINK, purpose: 'reset-password' });

    expect(delivery().map((e) => e.purpose)).toEqual(['reset-password', 'verify-email']);
  });

  it('keeps the URL Better Auth built, untouched', () => {
    // The port's oldest rule: a transport that rewrote a link could
    // invalidate it, and the failure would look like an expired token.
    remember(LINK);

    expect(delivery()[0]?.url).toBe(LINK.url);
  });

  it('⛔ hands out a copy, so nothing can post mail that was never sent', () => {
    /**
     * **A delivery record that a caller can append to is not a record.** The
     * one thing this must never show is an email the product did not send.
     */
    remember(LINK);
    const seen = delivery() as unknown as typeof LINK[];
    (seen as unknown as unknown[]).push({ ...LINK, to: 'attacker@example.com' });

    expect(delivery()).toHaveLength(1);
  });
});

describe('the bounds, which are the point', () => {
  it(`holds at most ${MAILBOX_CAPACITY}, discarding the oldest`, () => {
    // Unbounded is a slow leak in a long development session, and the oldest
    // entries are the least useful.
    for (let i = 0; i < MAILBOX_CAPACITY + 10; i += 1) {
      remember({ ...LINK, to: `person-${i}@northwind.example` });
    }

    expect(delivery()).toHaveLength(MAILBOX_CAPACITY);
    expect(delivery()[0]?.to).toBe(`person-${MAILBOX_CAPACITY + 9}@northwind.example`);
  });

  it('⛔ nothing reaches a disk — a restart is the retention policy', () => {
    /**
     * **In memory makes the bound structural rather than remembered**: there
     * is no file to forget to delete and no row to forget to purge. This
     * asserts the module writes nothing, because a future convenience — "let
     * us persist it across restarts" — is exactly how a credential log is
     * born.
     */
    const source = readFileSync(
      join(process.cwd(), 'lib/auth/mailbox.ts'),
      'utf8',
    );

    expect(source).not.toMatch(/writeFile|appendFile|createWriteStream|fs\./);
    expect(source).not.toMatch(/localStorage|sessionStorage|indexedDB/);
  });
});


describe('🔴 it cannot exist in a deployed environment', () => {
  it('refuses at startup, not at a request', async () => {
    /**
     * ⛔ **The console transport already carries this refusal and the mailbox
     * carries it for a stronger reason**: the console writes one credential to
     * stdout; the mailbox *keeps a history* of them and offers a surface to
     * read it. **A startup failure stops a misconfigured deployment; a request
     * check serves it until somebody notices.**
     */
    vi.stubEnv('SIGNORA_AUTH_EMAIL_TRANSPORT', 'mailbox');
    vi.stubEnv('SIGNORA_ENVIRONMENT', 'production');
    vi.resetModules();

    const { loadAuthConfig } = await import('@/lib/auth/config');

    expect(() => loadAuthConfig()).toThrow(/record of credentials/i);
  });

  it('is selectable locally, which is the whole point', async () => {
    vi.stubEnv('SIGNORA_AUTH_EMAIL_TRANSPORT', 'mailbox');
    vi.stubEnv('SIGNORA_ENVIRONMENT', 'local');
    vi.stubEnv('SIGNORA_AUTH_DATABASE_URL', 'postgresql://x@localhost:5432/signora');
    vi.stubEnv('BETTER_AUTH_SECRET', 'a-secret-this-suite-sets');
    vi.resetModules();

    const { loadAuthConfig } = await import('@/lib/auth/config');

    expect(loadAuthConfig().emailTransport).toBe('mailbox');
  });

  it('⛔ still refuses a transport this build does not have', async () => {
    vi.stubEnv('SIGNORA_AUTH_EMAIL_TRANSPORT', 'smtp');
    vi.resetModules();

    const { loadAuthConfig } = await import('@/lib/auth/config');

    expect(() => loadAuthConfig()).toThrow(/not a transport this build has/i);
  });
});

describe('the surface exists only where the store can', () => {
  it('🔴 404s unless the mailbox is the transport', async () => {
    /**
     * ⛔ **One guard, and it is the transport itself.** `loadAuthConfig`
     * already refuses to start with `mailbox` in a deployed environment, so
     * tying the page to the transport means **the surface cannot exist where
     * the store cannot exist** — there is no second condition to keep in step
     * with the first.
     *
     * ⚠️ **A 404 rather than an empty page**: with `console` selected there is
     * nothing to show, and *"no emails yet"* would be indistinguishable from a
     * mailbox that had lost them.
     */
    vi.stubEnv('SIGNORA_AUTH_EMAIL_TRANSPORT', 'console');
    vi.stubEnv('SIGNORA_ENVIRONMENT', 'local');
    vi.stubEnv('SIGNORA_AUTH_DATABASE_URL', 'postgresql://x@localhost:5432/signora');
    vi.stubEnv('BETTER_AUTH_SECRET', 'a-secret-this-suite-sets');
    vi.resetModules();

    const notFound = vi.fn(() => {
      throw new Error('NEXT_NOT_FOUND');
    });
    vi.doMock('next/navigation', () => ({ notFound }));

    const { default: MailboxPage } = await import('@/app/dev/mailbox/page');

    expect(() => MailboxPage()).toThrow('NEXT_NOT_FOUND');
    expect(notFound).toHaveBeenCalled();
    vi.doUnmock('next/navigation');
  });
});
