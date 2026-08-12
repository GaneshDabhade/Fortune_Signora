import { PHASE_DEVELOPMENT_SERVER } from 'next/constants';
import type { NextConfig } from 'next';

const config: NextConfig = {
  reactStrictMode: true,
  // Emits a self-contained server bundle with only the node_modules it
  // actually imports, so the production image carries no dev toolchain and
  // no unused dependency tree.
  output: 'standalone',
  // Fail the build on type or lint errors rather than shipping them.
  // A build that succeeds despite errors trains everyone to ignore them.
  typescript: { ignoreBuildErrors: false },
  eslint: { ignoreDuringBuilds: false },
};

/**
 * **A build no longer destroys the running dev server** —
 * [B-219](../docs/BUGS.md), [TASK-1465](../docs/BACKLOG.md), on the product
 * owner's ruling at [C-282](../docs/LANE_COORDINATION.md): *"Approved: use a
 * separate Next.js build directory via `distDir`."*
 *
 * ## 🔴 The defect, and why it was read as an authentication failure
 *
 * ⛔ **`next dev` and `next build` shared one `.next/`.** ⚡ **Completion gate 4
 * runs `next build`; gate 5 runs the headed journeys against the server gate 4
 * has just overwritten** — **so every route returns `500` and Playwright fails
 * at *"sign in as the owner"*.** ⚠️ **The first thing that breaks names the
 * wrong subsystem**, which is why this sat open for three days.
 *
 * ✅ **Reproduced before it was fixed, in the order that causes it** — `dev`
 * running, `next build`, then `GET /`: **`500`.** ⛔ **Not on `next build`
 * succeeding, which it always did.**
 *
 * ## ⚡ Why the phase and not an environment variable
 *
 * ⛔ **`distDir` is one value, so setting it flat would move dev too and
 * separate nothing.** ⚠️ **An env var would work and would have to be
 * remembered** — by the Makefile, by CI, by every person running the gates by
 * hand — **and a separation that depends on somebody exporting a variable is a
 * separation that will be missing the day it matters.**
 *
 * ✅ **Next passes the phase to a function config**, so the rule holds
 * wherever it is invoked from and there is nothing to remember.
 *
 * ⛔ **`next start` must NOT be sent to `.next`** — it serves what `next build`
 * wrote, so it belongs on the same side of the split as the build. **Only the
 * dev server keeps `.next`.**
 *
 * ⚠️ **Nothing else in this file changes.** 📁 The ruling is explicit: *"Do not
 * introduce any additional architecture or configuration changes… Do not turn
 * it into a broader build-system redesign."*
 */
export const BUILD_DIST_DIR = '.next-build';
export const DEV_DIST_DIR = '.next';

export default function nextConfig(phase: string): NextConfig {
  return {
    ...config,
    distDir: phase === PHASE_DEVELOPMENT_SERVER ? DEV_DIST_DIR : BUILD_DIST_DIR,
  };
}
