/**
 * **A build cannot overwrite the dev server's output** —
 * [B-219](../../../docs/BUGS.md), [TASK-1465](../../../docs/BACKLOG.md),
 * verification ⑤: *"a regression test or executable check if appropriate."*
 *
 * ## 🔴 Why this check exists rather than a note in a runbook
 *
 * ⚠️ **The defect took three days to name because the first thing it broke was
 * the wrong subsystem**: 📁 every route returned `500` and Playwright failed at
 * *"sign in as the owner"*, **which reads as an authentication defect.**
 *
 * ⛔ **A person who re-flattens `distDir` to a constant** — a reasonable thing
 * to do while tidying a config — **would not see the consequence until a gate
 * ran in a particular order, on somebody else's machine.** ✅ **This turns that
 * into a failing unit test.**
 */
import { PHASE_DEVELOPMENT_SERVER, PHASE_PRODUCTION_BUILD, PHASE_PRODUCTION_SERVER } from 'next/constants';
import { describe, expect, it } from 'vitest';

import nextConfig, { BUILD_DIST_DIR, DEV_DIST_DIR } from '../../next.config';

describe('🔴 the dev server and a production build write to different places', () => {
  /**
   * ⛔ **The assertion the original configuration failed.** ⚡ **One `.next/`
   * for both is the whole of [B-219](../../../docs/BUGS.md)**, and it is one
   * comparison.
   */
  it('🔴 `next dev` and `next build` do not share a directory', () => {
    const dev = nextConfig(PHASE_DEVELOPMENT_SERVER).distDir;
    const build = nextConfig(PHASE_PRODUCTION_BUILD).distDir;

    expect(dev).toBe(DEV_DIST_DIR);
    expect(build).toBe(BUILD_DIST_DIR);
    expect(dev).not.toBe(build);
  });

  /**
   * 🔴 **`next start` serves what `next build` wrote**, so it belongs on the
   * build's side of the split. ⛔ **Sending it to `.next` would produce a
   * production server that boots against whatever the dev server last
   * compiled** — ⚡ **a subtler version of the same defect, and one that would
   * only appear in a deployed environment.**
   */
  it('⛔ `next start` reads the build’s directory, never the dev server’s', () => {
    expect(nextConfig(PHASE_PRODUCTION_SERVER).distDir).toBe(BUILD_DIST_DIR);
  });

  /**
   * ⚠️ **The ruling was narrow and this asserts the narrowness.** 📁
   * [C-282](../../../docs/LANE_COORDINATION.md): *"Do not introduce any
   * additional architecture or configuration changes… Do not turn it into a
   * broader build-system redesign."* ⛔ **`next.config.ts` is 🔴 frontend
   * foundation, unlocked for `distDir` and for nothing else.**
   */
  it('✅ nothing else about the configuration changed with the phase', () => {
    const dev = nextConfig(PHASE_DEVELOPMENT_SERVER);
    const build = nextConfig(PHASE_PRODUCTION_BUILD);

    for (const config of [dev, build]) {
      expect(config.output).toBe('standalone');
      expect(config.reactStrictMode).toBe(true);
      expect(config.typescript?.ignoreBuildErrors).toBe(false);
      expect(config.eslint?.ignoreDuringBuilds).toBe(false);
    }
  });
});
