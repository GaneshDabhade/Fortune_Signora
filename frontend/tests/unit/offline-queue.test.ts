/**
 * **Mutations queue offline and replay in order** —
 * [TASK-1435](../../../docs/BACKLOG.md).
 *
 * 🔴 **These drive the real `QueryClient` against a real `onlineManager`.** ⚡
 * **The row's Definition of Done is *"two edits made offline arrive in order"*,
 * and that is a claim about the LIBRARY's behaviour under this repository's
 * configuration** — ⛔ **so a test with a hand-rolled queue would prove
 * nothing, which is also why the row says *do not write a queue*.**
 */
import { MutationCache, QueryClient, onlineManager } from '@tanstack/react-query';
import { afterEach, beforeEach, describe, expect, it } from 'vitest';

import { queryClientConfig } from '@/lib/query/client';

let client: QueryClient;

beforeEach(() => {
  onlineManager.setOnline(true);
  client = new QueryClient({ ...queryClientConfig, mutationCache: new MutationCache() });
});

afterEach(() => {
  onlineManager.setOnline(true);
  client.clear();
});

/** Fires a mutation and records the order the server actually saw. */
function edit(sent: string[], label: string) {
  return client
    .getMutationCache()
    .build(client, {
      mutationFn: async () => {
        sent.push(label);
        return label;
      },
      meta: { queueTitle: label },
    })
    .execute(undefined);
}

describe('🔴 the configuration the promise rests on', () => {
  it('⛔ mutations are `networkMode: "online"`, declared rather than defaulted', () => {
    /**
     * ⚡ **This is the line that makes an offline mutation PAUSE instead of
     * fail.** ⛔ **It is the library's default today**, and it stopped being a
     * default the moment a customer-visible promise rested on it: **an upgrade
     * that changed it would turn *"your edits are queued"* into a lie and
     * nothing else here would fail.**
     */
    expect(queryClientConfig.defaultOptions?.mutations?.networkMode).toBe('online');
  });

  it('⛔ and mutations still do not retry — queuing is not retrying', () => {
    // A paused mutation is sent once when the connection returns. Retrying one
    // that may have succeeded is how duplicate workspaces get created, and
    // TASK-1435 must not quietly relax that.
    expect(queryClientConfig.defaultOptions?.mutations?.retry).toBe(false);
  });
});

describe('📁 "two edits are queued… sent in order when the connection returns"', () => {
  it('🔴 nothing is sent while offline', async () => {
    const sent: string[] = [];
    onlineManager.setOnline(false);

    void edit(sent, 'Rename Vantage Logistics');
    void edit(sent, 'Dismiss Northwind');
    await Promise.resolve();

    // ⛔ The whole premise: the edits are held, not failed and not sent.
    expect(sent).toEqual([]);
    expect(
      client.getMutationCache().findAll({ predicate: (m) => m.state.isPaused }),
    ).toHaveLength(2);
  });

  it('⚡ both arrive when the connection returns, IN ORDER', async () => {
    const sent: string[] = [];
    onlineManager.setOnline(false);

    void edit(sent, 'first');
    void edit(sent, 'second');
    await Promise.resolve();
    expect(sent).toEqual([]);

    onlineManager.setOnline(true);
    await client.resumePausedMutations();

    // 🔴 **Order is the acceptance criterion, not merely arrival.** Two edits
    // to one record applied backwards leave the wrong value, and the customer
    // was told they would be "sent in order".
    expect(sent).toEqual(['first', 'second']);
  });

  it('⛔ the queue empties once they are sent', async () => {
    const sent: string[] = [];
    onlineManager.setOnline(false);
    void edit(sent, 'only');
    await Promise.resolve();

    onlineManager.setOnline(true);
    await client.resumePausedMutations();

    expect(
      client.getMutationCache().findAll({ predicate: (m) => m.state.isPaused }),
    ).toHaveLength(0);
  });
});

describe('⚠️ in-session only, and that is the row’s line', () => {
  it('⛔ nothing is persisted — no persister exists to configure', async () => {
    /**
     * 📁 The row names the risk: *"persisting a mutation queue across sessions
     * without deciding what a stale queue means… a stale replay is a separate
     * decision and not this row's to take."* ⚡ **A queued edit replayed an
     * hour later against changed data is a decision somebody has to make, not
     * a default to inherit.**
     */
    // ⛔ **Asserted structurally rather than by poking storage.** These run in
    // the `node` environment, and *"no `window.localStorage` entries"* would
    // have been a check that passes because there is no `window` — a guard
    // that cannot fail (§2). **The durable property is that no persister
    // exists to be configured.**
    const pkg = JSON.parse(
      await (await import('node:fs/promises')).readFile('package.json', 'utf8'),
    ) as { dependencies?: Record<string, string>; devDependencies?: Record<string, string> };
    const installed = { ...pkg.dependencies, ...pkg.devDependencies };
    expect(installed['@tanstack/react-query-persist-client']).toBeUndefined();
    expect(installed['@tanstack/query-sync-storage-persister']).toBeUndefined();

    // And the client this repository builds declares no persister of its own.
    expect(JSON.stringify(queryClientConfig)).not.toMatch(/persist/i);
  });
});
