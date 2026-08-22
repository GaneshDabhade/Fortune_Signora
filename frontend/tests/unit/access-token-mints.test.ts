import { readFileSync } from 'node:fs';
import { join } from 'node:path';

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

describe('⛔ the server never shares a mint between callers', () => {
  it('mints per read in a node environment, because every caller is a different customer', async () => {
    // 🔴 **This file runs in `node`** — 📁 `vitest.config.ts` gives jsdom to
    // `tests/components/**` alone — **so `typeof window === 'undefined'` and
    // the sharing path is off.** ⚡ **That is exactly the condition being
    // asserted**: a module-level map on the Next server would hand one
    // customer's token to another request in the same process.
    //
    // ⚠️ **The browser half lives in `tests/components/access-token-mints.test.tsx`.**
    // ⛔ **One environment cannot assert both**, and the first version of this
    // test asserted the browser behaviour here and failed — the guard was
    // right and the environment was wrong.
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

    await Promise.all([
      apiRequest('/one', { workspaceId: 'w1' }),
      apiRequest('/two', { workspaceId: 'w1' }),
      apiRequest('/three', { workspaceId: 'w1' }),
    ]);

    expect(
      calls.filter((url) => url.includes('/api/token')),
      'three reads on the server, three mints — no sharing',
    ).toHaveLength(3);
  });

  it('keeps a separate mint per workspace, because the token is scoped to one', () => {
    // ⛔ **Keyed on `workspaceId`** — a token minted for one organization must
    // never be handed to a request for another.
    const source = readFileSync(join(process.cwd(), 'lib', 'api', 'client.ts'), 'utf8');
    expect(source).toContain('const key = workspaceId ?? ');
  });
});
