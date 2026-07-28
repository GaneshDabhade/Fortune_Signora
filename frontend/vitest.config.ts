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
