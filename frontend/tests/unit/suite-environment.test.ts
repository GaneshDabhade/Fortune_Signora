/**
 * **The suite's environment is its own, not the operator's** — 📁
 * [B-1088](../../../docs/BUGS.md).
 *
 * ⛔ **Cycle 277's certification reported `frontend-suite 9 failed` against a
 * candidate that touched no authentication file.** The cause was
 * `env SIGNORA_ENVIRONMENT=lane-qe make certify`, which exports the variable
 * into vitest, where `isDeployed()` treats anything outside `['local','test']`
 * as deployed — so a real safety check on the console email transport fired.
 *
 * 🔴 **The trap is that naming the environment is the DOCUMENTED remedy.**
 * `require-e2e-url` instructs `SIGNORA_ENVIRONMENT=lane-a make …`, written for
 * [B-1014](../../../docs/BUGS.md), and neither message mentions the other.
 *
 * ⚠️ **This file is the witness, and it must be able to fail.** A test that
 * asserted the pin from inside the pin's own scope would be the pin restating
 * itself. **Fire-tested both ways before it was committed:**
 *
 *     SIGNORA_ENVIRONMENT=lane-qe npx vitest run tests/unit/suite-environment.test.ts
 *         → passes, because the config's `env` wins over the shell
 *     …with `env: { SIGNORA_ENVIRONMENT: 'test' }` removed from vitest.config.ts
 *         → fails, which is the condition that produced the nine
 */

import { describe, expect, it } from 'vitest';

describe('📁 B-1088 — the suite’s environment is pinned, whatever the shell exported', () => {
  it('⚡ is `test`, and not whatever the operator happened to export', () => {
    expect(
      process.env.SIGNORA_ENVIRONMENT,
      'vitest.config.ts must pin SIGNORA_ENVIRONMENT — without it the suite ' +
        'inherits the operator’s shell, and a lane naming its own environment ' +
        'makes nine tests believe they are running in production (B-1088)',
    ).toBe('test');
  });

  it('⛔ and the pinned value is one the deployment guard treats as NOT deployed', async () => {
    const { authMode } = await import('@/lib/auth/config');
    expect(
      authMode(),
      'the pinned value must sit inside isDeployed()’s allow-list, or the pin ' +
        'trades one wrong environment for another',
    ).toBe('development');
  });
});
