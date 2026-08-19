/**
 * 🔴 **The product refuses a fourth sign-in in ten seconds, and it is RIGHT to**
 * — [C-109](../../../../docs/LANE_COORDINATION.md), [B-1030](../../../../docs/BUGS.md).
 *
 * 📁 Better Auth's defaults, `getDefaultSpecialRules()`:
 *
 * | Paths | Limit |
 * |---|---|
 * | `/sign-in` · `/sign-up` · `/change-password` · `/change-email` | **3 per 10s** |
 * | `/forget-password` · `/request-password-reset` · `/send-verification-email` | **3 per 60s** |
 *
 * ⚡ **`auth.setup.ts` signs in three times back to back** — the limit exactly,
 * before one journey has run — **so the suite trips a real security control
 * simply by being a suite.** 📁 That produced four failures whose symptoms
 * varied between runs, and a row that spent a day unable to name a cause.
 *
 * ## ⛔ What this is NOT
 *
 * **The control is not weakened, not raised, and not turned off.** ⛔ **A
 * control that is off wherever it is tested is a control nobody tests.**
 * ⚡ **The suite waits, because the product tells it how long to** — the
 * refusal carries `x-retry-after`, in seconds — **and then makes the request
 * it was always going to make.**
 *
 * ⚠️ **This ends in a sleep, which [B-1032](../../../../docs/BUGS.md) refused
 * an hour earlier, and the distinction is the whole point.** ⛔ There, the
 * duration was a GUESS about an animation nobody had asked. ✅ **Here the
 * server states the number.**
 *
 * ## Why at the transport rather than in each flow
 *
 * ⛔ **Four flows across three limited paths hand-write their own submits** —
 * `/register`, `/forgot-password`, `/signin` in `auth-credential-journeys`,
 * and a second sign-in in `security-center`. ⚡ **Repairing the page object
 * alone recovered exactly one of five failures, measured** — 📁 the other four
 * never go through it. **One interceptor covers every auth path there is,
 * including the ones nobody has written yet.**
 */
import type { Page } from '@playwright/test';

/** 📁 Better Auth's own header on a refusal, in seconds. */
const WINDOW_HEADER = 'x-retry-after';

/**
 * ⛔ **Better Auth's window for the paths that carry the tightest rule.**
 * ⚠️ Used only if a refusal arrives without the header — **a refusal without
 * it is still a refusal**, and a wait slightly too long costs seconds where
 * one too short costs the failure this exists to remove.
 */
const ASSUMED_WINDOW_SECONDS = 10;

/** ⛔ **Three refusals in a row is not the suite outrunning its own budget.** */
const REFUSALS_BEFORE_GIVING_UP = 3;

/**
 * Retry any authentication request the product refuses, after the window it
 * names.
 *
 * ⚠️ **Install it on any bare `Page`** — the suite's own `test` does it for
 * every journey, and `auth.setup.ts` and the endurance recorder do it for
 * themselves, because neither uses that fixture.
 */
export async function honourTheRateLimiter(page: Page): Promise<void> {
  await page.route('**/api/auth/**', async (route) => {
    for (let refusals = 0; ; refusals += 1) {
      const response = await route.fetch();
      if (response.status() !== 429 || refusals + 1 >= REFUSALS_BEFORE_GIVING_UP) {
        // ⚡ **The last refusal is DELIVERED, not swallowed.** ⛔ A limiter that
        // never reaches a test is one no test could ever assert.
        await route.fulfill({ response });
        return;
      }
      const named = Number(response.headers()[WINDOW_HEADER]);
      const seconds = Number.isFinite(named) && named > 0 ? named : ASSUMED_WINDOW_SECONDS;
      // `+1` because the window is inclusive of the second it names, and a
      // boundary miss costs another whole one.
      await new Promise((resume) => setTimeout(resume, (seconds + 1) * 1_000));
    }
  });
}
