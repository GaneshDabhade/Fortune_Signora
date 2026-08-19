import { afterAll, afterEach, vi } from 'vitest';

/**
 * Shared test setup.
 *
 * Runs for every file, including the node-environment unit tests, so
 * anything DOM-specific is guarded rather than assumed — importing
 * jest-dom unconditionally would fail the node tests at collection.
 */
if (typeof window !== 'undefined') {
  await import('@testing-library/jest-dom/vitest');
  const { cleanup } = await import('@testing-library/react');

  // Unmount between tests. Without it, queries match elements left behind
  // by a previous test and failures point at the wrong component.
  afterEach(cleanup);

  /**
   * 🔴 **[B-1031](../../docs/BUGS.md) — an exception thrown after the
   * environment was torn down, which killed the reporter and refused a
   * certification cycle the candidate had nothing to do with.**
   *
   * ```
   * ReferenceError: window is not defined
   *  ❯ Object.cleanupBroadcastSetup  better-auth/…/broadcast-channel.mjs:35
   *  ❯ Object.cleanup                better-auth/…/session-refresh.mjs:109
   *  ❯ Timeout._onTimeout            nanostores/lifecycle/index.js:139
   * ```
   *
   * ⚡ **The mechanism, and it is not the file vitest named.** 📁
   * `nanostores/lifecycle` does not run a store's `onMount` destructors when
   * the last subscriber leaves — **it schedules them, `setTimeout(…,
   * STORE_UNMOUNT_DELAY)`.** ⛔ **So `cleanup` above, which is what unmounts
   * the last `useSession` consumer, ARMS a timer rather than running one**,
   * and every jsdom file that ever rendered one ends with that timer pending.
   * **If the environment goes first, better-auth's destructor reaches for a
   * `window` that no longer exists.**
   *
   * ⚠️ **That is why it is intermittent, why six direct reproductions of the
   * named file found nothing, and why the row could not name a culprit test:
   * `companies-workspace.test.tsx` was attributed because it was RUNNING.**
   * 📁 vitest says so itself — *"it doesn't mean the error was thrown inside
   * the file itself."*
   *
   * ✅ **So the destructors are run here, synchronously, while there is still
   * a `window` for them to find.** ⚡ The armed timer then finds the store
   * already inactive and does nothing, 📁 which is exactly the guard
   * `lifecycle/index.js` already carries: `if ($store.active && !$store.lc)`.
   *
   * ⛔ **Not `dangerouslyIgnoreUnhandledErrors`**, which vitest offers and
   * which would have made the gate green by making it blind. **The gate's
   * verdict is the exit code, and it was right to be non-zero: an uncaught
   * exception means the run cannot be read.**
   *
   * ⚠️ **`afterAll`, not `afterEach`** — the timers only have to be gone
   * before the environment is, and a per-test store reset would change what
   * every auth test sees between its own cases.
   */
  const { cleanStores } = await import('nanostores');
  const { authClient } = await import('@/lib/auth/client');

  afterAll(() => {
    // ⛔ **Named, not enumerated, and the first attempt here got that wrong.**
    // 📁 `authClient.$store` is a `createDynamicPathProxy`, whose `get` returns
    // a fresh proxy for any key it cannot resolve to a function or an atom.
    // ⚠️ **`Object.values($store.atoms)` therefore yields `[]`** — the proxy
    // has no `ownKeys` trap over the real object — **so the call ran, matched
    // nothing, and would have shipped as a guard that cannot fail.**
    // ✅ **A path ending AT an atom does resolve**, which is why this names one.
    // 📁 `session` is the atom `tests/components/session-store-teardown.test.tsx`
    // measures arming a destructor; no other atom did.
    cleanStores(authClient.$store.atoms.session);
  });

  // jsdom implements neither of these, and shipped code uses both:
  // matchMedia by theme resolution, showModal by Dialog.
  Object.defineProperty(window, 'matchMedia', {
    writable: true,
    value: (query: string) => ({
      matches: false,
      media: query,
      onchange: null,
      addEventListener: vi.fn(),
      removeEventListener: vi.fn(),
      dispatchEvent: vi.fn(),
    }),
  });

  if (!HTMLDialogElement.prototype.showModal) {
    HTMLDialogElement.prototype.showModal = function showModal(this: HTMLDialogElement) {
      this.open = true;
    };
    HTMLDialogElement.prototype.close = function close(this: HTMLDialogElement) {
      this.open = false;
    };
  }
}
