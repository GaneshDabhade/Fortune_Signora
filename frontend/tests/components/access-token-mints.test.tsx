import { afterEach, describe, expect, it, vi } from 'vitest';

import { apiRequest } from '@/lib/api/client';

/**
 * 🔴 **[B-1035](../../../docs/BUGS.md) — one RS256 signature per data read.**
 *
 * 📁 **Measured on `/accounts`: 15 mints for 16 reads, against a ceiling of 12
 * and a design target of 1.** ⚡ **A page opens by firing its queries together,
 * so the reads that were each minting a token are the same reads that can share
 * one.**
 *
 * ⛔ **This is deduplication of work in flight, NOT a cache** — nothing is
 * stored, and the entry is removed the moment the mint settles. **A cache wants
 * the token's own `exp`, and 📁 [§13](../../../CLAUDE.md) puts JWT parsing in
 * `signora_platform/auth/`.**
 *
 * ⚠️ **The browser guard is a SECURITY boundary, not an optimisation** — a
 * module-level map on the Next server would be shared by every request in the
 * process. It is asserted in `client.ts` by `typeof window`; jsdom is a browser
 * here, which is the environment this behaviour is for.
 */
function jsonResponse(body: unknown, status = 200): Response {
  return {
    ok: status >= 200 && status < 300,
    status,
    json: async () => body,
  } as Response;
}

afterEach(() => {
  vi.unstubAllGlobals();
  vi.restoreAllMocks();
});

describe('🔴 concurrent reads share one access token mint', () => {
  it('mints once for reads that start together', async () => {
    const calls: string[] = [];
    vi.stubGlobal(
      'fetch',
      vi.fn(async (input: RequestInfo | URL) => {
        const url = String(input);
        calls.push(url);
        if (url.includes('/api/token')) return jsonResponse({ access_token: 'a-token' });
        return jsonResponse({ ok: true });
      }),
    );

    // ⚡ **Five reads, started together, exactly as a page opens.**
    await Promise.all([
      apiRequest('/one', { workspaceId: 'w1' }),
      apiRequest('/two', { workspaceId: 'w1' }),
      apiRequest('/three', { workspaceId: 'w1' }),
      apiRequest('/four', { workspaceId: 'w1' }),
      apiRequest('/five', { workspaceId: 'w1' }),
    ]);

    const mints = calls.filter((url) => url.includes('/api/token'));
    expect(mints, 'five concurrent reads, one mint').toHaveLength(1);
    expect(calls.filter((url) => !url.includes('/api/token'))).toHaveLength(5);
  });

  it('⛔ a token minted for one organization is never handed to another', async () => {
    /**
     * ⚠️ **This was asserted by a SOURCE GREP** — `tests/unit` read
     * `client.ts` and checked it contained `const key = workspaceId ?? `.
     *
     * ⛔ **That passes on any refactor that keeps the string and breaks the
     * behaviour, and fails on any refactor that preserves the behaviour and
     * renames the variable.** ⚡ **It asserts the mechanism where the property
     * is what matters** — and the property is a tenancy one: 📁
     * [ADR-0034](../../../docs/architecture/adr/0034-ubiquitous-language.md)
     * aside, **a token is scoped to one organization** and sharing across keys
     * would hand a customer another customer's scope.
     *
     * ✅ **Asserted here as behaviour**, in the browser environment where the
     * sharing path is actually on.
     */
    const mints: string[] = [];
    vi.stubGlobal(
      'fetch',
      vi.fn(async (input: RequestInfo | URL) => {
        const url = String(input);
        if (url.includes('/api/token')) {
          mints.push(url);
          return jsonResponse({ access_token: `token-${mints.length}` });
        }
        return jsonResponse({ ok: true });
      }),
    );

    await Promise.all([
      apiRequest('/one', { workspaceId: 'w1' }),
      apiRequest('/two', { workspaceId: 'w2' }),
    ]);

    expect(mints, 'two organizations shared one token').toHaveLength(2);
    expect(mints[0]).toContain('workspace_id=w1');
    expect(mints[1]).toContain('workspace_id=w2');
  });

  it('🔴 B-1067 — a joiner inherits a SUCCESS, never a REJECTION', async () => {
    /**
     * ⛔ **Sharing a success is the point of the dedupe; sharing a rejection
     * removed retries it never meant to remove.**
     *
     * ⚡ **A mint's verdict is formed when its request ARRIVES at `/api/token`**,
     * and the server answers from the cookie it can see at that moment. ⚠️ **A
     * caller that joins later inherited a verdict formed before it existed** —
     * **including one firing after the cookie became readable, which would have
     * succeeded on its own.**
     *
     * 📁 **The row's measurement, identical timings, sharing the only
     * variable:**
     *
     * ```
     * shared    mints=1   0:rej 2:rej 4:rej 6:rej 40:rej       45:rej
     * control   mints=6   0:rej 2:rej 4:rej 6:rej 40:FULFILLED 45:FULFILLED
     * ```
     *
     * ⛔ **And nothing downstream recovers it**: `apiRequest` throws at
     * `await fetchAccessToken(...)` **before** its `fetch`, **so the 401 retry
     * never runs for a failed MINT** — it only ever covered a 401 *response*.
     * ⚠️ **Which is exactly what the test below this one asserts**, and why it
     * could not see this defect.
     */
    const calls: string[] = [];
    let mints = 0;
    vi.stubGlobal(
      'fetch',
      vi.fn(async (input: RequestInfo | URL) => {
        const url = String(input);
        calls.push(url);
        if (url.includes('/api/token')) {
          mints += 1;
          // ⚡ **The first mint fails; every later one succeeds** — the cookie
          // has become readable, which is the seconds-after-sign-in case.
          return mints === 1
            ? jsonResponse({ error: {} }, 401)
            : jsonResponse({ access_token: `token-${mints}` });
        }
        return jsonResponse({ ok: true });
      }),
    );

    // ⚡ **Started together**, so the second reaches `inFlightMints.get(key)`
    // while the first is still in flight — the only way to BE a joiner.
    const settled = await Promise.allSettled([
      apiRequest('/one', { workspaceId: 'w1' }),
      apiRequest('/two', { workspaceId: 'w1' }),
    ]);

    // ⛔ **The joiner minted its own rather than inheriting the rejection.**
    expect(mints, 'the joiner reused the failed mint').toBeGreaterThan(1);
    // ✅ **And therefore SUCCEEDED**, which is the customer-visible half: one
    // read failing where the other recovers, rather than both failing together.
    expect(settled.filter((r) => r.status === 'fulfilled')).toHaveLength(1);
    expect(settled.filter((r) => r.status === 'rejected')).toHaveLength(1);
  });

  it("🔴 a retry does NOT receive the mint that just 401'd", async () => {
    // ⛔ **Without this the second attempt awaits the same in-flight promise
    // and fails identically**, turning a recoverable 401 into a hard failure.
    const calls: string[] = [];
    let dataCalls = 0;
    vi.stubGlobal(
      'fetch',
      vi.fn(async (input: RequestInfo | URL) => {
        const url = String(input);
        calls.push(url);
        if (url.includes('/api/token')) return jsonResponse({ access_token: `token-${calls.length}` });
        dataCalls += 1;
        // ⚡ The first data read 401s; the retry succeeds.
        return dataCalls === 1 ? jsonResponse({ error: {} }, 401) : jsonResponse({ ok: true });
      }),
    );

    await apiRequest('/needs-a-retry', { workspaceId: 'w1' });

    const mints = calls.filter((url) => url.includes('/api/token'));
    expect(mints, 'the retry minted a fresh token rather than reusing one').toHaveLength(2);
  });
});
