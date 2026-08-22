/**
 * 🔴 **[B-1067](../../docs/BUGS.md) — the token mint shared its FAILURES, and a
 * failure is not a thing to share.**
 *
 * ## ⛔ What 📁 [B-1035](../../docs/BUGS.md) meant, and what it did
 *
 * ✅ **Deduplicating mints already in flight is right**: a page opens by firing
 * its queries together, and fifteen simultaneous `POST /api/token` for one
 * customer are fourteen too many. **That part stays.**
 *
 * ⛔ **But a mint's verdict is formed when its request ARRIVES**, from the
 * session cookie the server can see at that moment — **so a caller that joined
 * later inherited an answer formed before it existed.** ⚠️ **Including a caller
 * that fired AFTER the cookie became readable and would have succeeded alone.**
 *
 * ⚡ **And nothing downstream recovered it.** 📁 `apiRequest` throws at
 * `await fetchAccessToken(...)` **before** its `fetch`, so its single 401 retry
 * never ran for a failed *mint* — it only ever covered a 401 *response*.
 *
 * ## ⚠️ Why this file holds a CONTROL and not just a reproduction
 *
 * 🔴 **The reproduction alone passes on any build where mints never fail** —
 * which would make it the kind of instrument that cannot fail in the case it
 * exists for, and this repository collected six of those in one day. **The
 * control fires the identical timings with the SHARING removed**, by giving
 * each caller a distinct key so `inFlightMints` cannot match them.
 *
 * ⛔ **The control does not fork the logic.** It runs the same
 * `apiRequest` → `fetchAccessToken` → `mintAccessToken` path, so it proves
 * something about the product rather than about a copy of it.
 */
import { beforeEach, describe, expect, it, vi } from 'vitest';

import { apiRequest } from '@/lib/api/client';

/** When the session cookie becomes readable and `/api/token` starts answering. */
const COOKIE_READABLE_AT = 30;
/** How long a mint takes. ⚡ **The window is this**: callers that fire inside it
 *  are the ones that can join somebody else's verdict. */
const MINT_LATENCY = 60;
/** A page's queries, then two reads that land after the cookie is readable. */
const OFFSETS = [0, 2, 4, 6, 40, 45];

let start = 0;
let mints = 0;

const sleep = (ms: number) => new Promise((resolve) => setTimeout(resolve, ms));

beforeEach(() => {
  mints = 0;
  start = Date.now();
  vi.stubGlobal(
    'fetch',
    vi.fn(async (url: string) => {
      if (!String(url).includes('/api/token')) {
        return new Response(JSON.stringify({ ok: true }), { status: 200 });
      }
      mints += 1;
      // ⛔ **Decided on ARRIVAL, not on resolution** — that is what the server
      // does, and it is the whole reason a late joiner can inherit a stale no.
      const arrived = Date.now() - start;
      await sleep(MINT_LATENCY);
      return arrived < COOKIE_READABLE_AT
        ? new Response('{}', { status: 401 })
        : new Response(JSON.stringify({ access_token: 'tok' }), { status: 200 });
    }),
  );
});

/** Fires one read per offset. `distinctKeys` removes the sharing and nothing else. */
async function fire(distinctKeys = false): Promise<PromiseSettledResult<unknown>[]> {
  return Promise.allSettled(
    OFFSETS.map(
      (delay, i) =>
        new Promise((resolve, reject) => {
          setTimeout(() => {
            apiRequest('/anything', distinctKeys ? { workspaceId: `w${i}` } : {}).then(
              resolve,
              reject,
            );
          }, delay);
        }),
    ),
  );
}

const settled = (results: PromiseSettledResult<unknown>[]) =>
  results.map((result, i) => `${OFFSETS[i]}:${result.status === 'fulfilled' ? 'ok' : 'rej'}`);

describe('🔴 B-1067 — a mint shares its success, never its failure', () => {
  it('a caller that fires after the cookie is readable succeeds, even when it joined', async () => {
    const results = await fire();

    // ⚡ **These two are the defect.** They fire at 40ms and 45ms — ten and
    // fifteen milliseconds AFTER the cookie is readable — so alone they
    // succeed. 🔴 **Before the fix they inherited a rejection formed at 0ms**,
    // and the run read `mints=1` with all six rejected.
    expect(settled(results).slice(4)).toEqual(['40:ok', '45:ok']);

    /**
     * ⛔ **The caller at 0ms still fails, and that is the assertion that stops
     * this being a test which simply made everything pass.**
     *
     * ⚠️ **It is the ORIGINATOR.** It inherited nothing: it issued its own
     * request at 0ms and was legitimately refused, because at 0ms there was no
     * readable cookie. **A fix that rescued it too would be inventing a retry
     * that never existed** — before 📁 [B-1035](../../docs/BUGS.md) it failed
     * here as well, so this is not a regression and not something to paper
     * over.
     *
     * ⚡ **The joiners at 2, 4 and 6ms DO succeed, and this surprised me.**
     * They fired inside the pre-cookie window too — but their own mint is
     * issued when the shared one settles, at ~60ms, **by which time the cookie
     * is readable.** ✅ **So the retry does not merely restore what sharing
     * took away; it lands later and therefore lands better.**
     *
     * 🔴 **The asymmetry is real and is recorded rather than smoothed**: one
     * caller gets one chance and the rest effectively get two. **Giving the
     * originator a retry as well is a behaviour change, not a defect fix**, and
     * it belongs to whoever rules on 📁
     * [C-1549](../../../docs/LANE_COORDINATION.md).
     */
    expect(settled(results).slice(0, 4)).toEqual(['0:rej', '2:ok', '4:ok', '6:ok']);
  });

  /**
   * ⚠️ **THE CONTROL.** Identical timings, sharing removed. ⛔ **If this does
   * not show the same two successes, the timings above are not what makes them
   * succeed** and the assertion above is measuring something else.
   */
  it('CONTROL — the same six with the sharing removed behave identically', async () => {
    const results = await fire(true);

    expect(mints, 'distinct keys must not share, or this is not a control').toBe(OFFSETS.length);
    expect(settled(results)).toEqual(['0:rej', '2:rej', '4:rej', '6:rej', '40:ok', '45:ok']);
  });

  /**
   * 🔴 **📁 [B-1035](../../docs/BUGS.md) must survive its own fix.** ⛔ **The
   * cheapest way to make the assertions above pass is to delete the
   * deduplication**, which would put fifteen mints back on every page open.
   * ✅ **Success is still shared, and this is what says so.**
   */
  it('concurrent callers still share ONE mint when it succeeds', async () => {
    // ⚡ Fired after the cookie is readable, so the mint they share succeeds.
    await sleep(COOKIE_READABLE_AT + 5);
    const results = await Promise.allSettled([
      apiRequest('/anything'),
      apiRequest('/anything'),
      apiRequest('/anything'),
      apiRequest('/anything'),
      apiRequest('/anything'),
    ]);

    expect(results.every((r) => r.status === 'fulfilled')).toBe(true);
    expect(mints, 'five concurrent reads must cost one mint').toBe(1);
  });
});
