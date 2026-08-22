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
