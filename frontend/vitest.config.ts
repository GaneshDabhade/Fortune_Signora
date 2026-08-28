import react from '@vitejs/plugin-react';
import { defineConfig } from 'vitest/config';

/**
 * `@vitejs/plugin-react` is pinned to **v4, not v5**.
 *
 * v5 requires Vite 6+, while Vitest 2 pins Vite 5 — installing it produces
 * an unsatisfiable peer graph. v4 supports Vite 5, which is why this
 * dependency could be reinstated without `--legacy-peer-deps`; that flag
 * would have hidden the conflict rather than resolved it. Repays the debt
 * recorded against M1.2 in PROJECT_STATUS.
 */
export default defineConfig({
  plugins: [react()],
  test: {
    // `node` by default: the JWT and key-management tests use WebCrypto
    // through jose and are testing server-side code paths. jsdom is
    // applied only where a DOM is genuinely needed, so the existing suite
    // keeps running in the environment it was written for.
    /**
     * ⛔ **The suite's declared input is the tree. Its ACTUAL input was the
     * tree AND the operator's shell** — 📁 [B-1088](../docs/BUGS.md).
     *
     * `environmentName()` returns `process.env.SIGNORA_ENVIRONMENT ?? 'local'`
     * and `isDeployed()` treats anything outside `['local','test']` as
     * deployed. ⚡ **So `env SIGNORA_ENVIRONMENT=lane-qe make certify` — which
     * is the remedy [`require-e2e-url`](../Makefile) DOCUMENTS for
     * [B-1014](../docs/BUGS.md) — made nine tests believe they were running in
     * production**, and a real [ADR-0033](../docs/architecture/adr/) safety
     * check on the console email transport fired. **The gate reported nine
     * failures against a candidate that touched no auth file.**
     *
     * ✅ **Pinned here rather than in `make certify`**, because fixing the
     * caller leaves `npx vitest run`, an IDE and every lane's own loop carrying
     * the same dependency. **The environment becomes part of the suite's
     * contract instead of the shell's.**
     *
     * ⚡ **`test` and `local` are behaviourally identical, measured rather than
     * assumed**: the only comparisons in `lib/auth/config.ts` are `?? 'local'`,
     * the `['local','test']` allow-list, and `=== 'demo'`. **So this changes
     * nothing a clean shell already did**, and every test that cares sets the
     * value explicitly and restores it.
     */
    env: { SIGNORA_ENVIRONMENT: 'test' },
    environment: 'node',
    environmentMatchGlobs: [['tests/components/**', 'jsdom']],
    setupFiles: ['./tests/setup.ts'],
    include: ['tests/unit/**/*.test.ts', 'tests/components/**/*.test.tsx'],
    coverage: {
      provider: 'v8',
      reporter: ['text'],
      include: ['components/**', 'lib/**'],
      // Exercised by Playwright and by `make smoke` against the real
      // stack, where their behaviour is meaningful. A jsdom test of a
      // server component asserts only that it renders.
      exclude: ['lib/auth/server.ts', 'lib/auth/config.ts', '**/*.d.ts'],
    },
  },
  resolve: { alias: { '@': new URL('./', import.meta.url).pathname } },
});
