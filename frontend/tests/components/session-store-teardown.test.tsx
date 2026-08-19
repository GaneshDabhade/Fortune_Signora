/**
 * 🔴 **[B-1031](../../../docs/BUGS.md) — the leak this file measures, and the
 * only reason `tests/setup.ts` cleans a store nothing else touches.**
 *
 * **What certification reported, once, against a candidate that had nothing to
 * do with it:**
 *
 * ```
 * · gate 'frontend-suite' failed: did not report a total
 *
 * ReferenceError: window is not defined
 *  ❯ Object.cleanupBroadcastSetup  better-auth/…/broadcast-channel.mjs:35
 *  ❯ Object.cleanup                better-auth/…/session-refresh.mjs:109
 *  ❯ Timeout._onTimeout            nanostores/lifecycle/index.js:139
 * ```
 *
 * ⚡ **`nanostores` does not run a store's `onMount` destructors when its last
 * subscriber leaves — it SCHEDULES them**, `setTimeout(…, STORE_UNMOUNT_DELAY)`.
 * ⛔ **So every jsdom file that rendered a `useSession` consumer ends with that
 * timer armed**, and if the environment is torn down first, better-auth's
 * destructor reaches for a `window` that is no longer there.
 *
 * ## ⛔ Why this file asserts a dependency's internals, deliberately
 *
 * **`active` and `lc` are `nanostores`' own fields, and normally asserting
 * those would be reaching inside somebody else's implementation.** ⚡ **Here
 * they are the whole justification for a line in `tests/setup.ts`**, and the
 * two outcomes are both worth being told about:
 *
 * - **If unmount ever starts disarming by itself**, the first test fails and
 *   the setup line is dead code that should go.
 * - **If `cleanStores` ever stops disarming**, the second fails and the setup
 *   line has quietly become decorative.
 *
 * ⛔ **Neither is visible any other way.** 📁 The race itself is not
 * reproducible on demand — six attempts against the file vitest NAMED found
 * nothing, because it was attributed for running rather than for arming.
 */
import { render } from '@testing-library/react';
import { cleanStores, type Store } from 'nanostores';
import { expect, test } from 'vitest';

import { authClient, useSession } from '@/lib/auth/client';

function SessionConsumer(): null {
  useSession();
  return null;
}

/**
 * 📁 `nanostores`' own bookkeeping, and the two fields this file exists to read:
 * `lc` = live subscribers, `active` = destructors still owed.
 */
type SessionStore = Store & { active?: boolean; lc?: number };

/**
 * ⛔ **Reached by NAME, because `$store` cannot be enumerated.** 📁 It is a
 * `createDynamicPathProxy`: a path ending at an atom resolves to the atom, and
 * every other key returns a fresh proxy — **so `Object.values` yields `[]`**,
 * which is how the first version of this fix came to do nothing at all.
 */
function sessionAtom(): SessionStore {
  const atoms = (authClient.$store as unknown as { atoms: Record<string, SessionStore | undefined> })
    .atoms;
  const session = atoms.session;
  if (!session) {
    throw new Error(
      'better-auth no longer publishes $store.atoms.session — the cleanStores() call in ' +
        'tests/setup.ts is reaching for something that is not there.',
    );
  }
  return session;
}

test('🔴 unmounting the last session subscriber ARMS a destructor rather than running one', () => {
  const session = sessionAtom();

  const view = render(<SessionConsumer />);
  expect(session.lc, 'the session store was never subscribed, so nothing here is measured').toBe(1);
  expect(session.active).toBe(true);

  view.unmount();

  // ⚡ **This is the defect, stated as a measurement.** ⛔ **No subscribers and
  // still active** — the destructors are on a timer, and better-auth's touches
  // `window`.
  expect(session.lc).toBe(0);
  expect(
    session.active,
    'unmount now disarms by itself — the cleanStores() call in tests/setup.ts is dead code and should be removed',
  ).toBe(true);
});

test('✅ and cleanStores runs them synchronously, while there is still a window', () => {
  const session = sessionAtom();

  render(<SessionConsumer />).unmount();
  expect(session.active).toBe(true);

  cleanStores(session);

  // 📁 `lifecycle/index.js` guards the armed timer with `if ($store.active &&
  // !$store.lc)`. ✅ **With `active` false it fires into nothing**, which is
  // what stops it reaching a `window` that has gone.
  expect(
    session.active,
    'cleanStores no longer disarms the store — tests/setup.ts is not protecting anything',
  ).toBe(false);
});
