/**
 * **Screen `07 · Verify email`** — Workflow 3, [TASK-486](../../../docs/BACKLOG.md).
 *
 * ⚡ **The tests are about the resend, because that is what this screen can
 * honestly do.** The design draws six digit boxes; `lib/auth/server.ts` sends
 * a link and no endpoint would accept a typed code — [C-241](../../../docs/LANE_COORDINATION.md).
 * **So the boxes are not drawn, and one test asserts their absence** for the
 * same reason `join.test.tsx` asserts *Request access* is never offered.
 */
import { act, render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

const resendVerification = vi.hoisted(() => vi.fn());
vi.mock('@/lib/auth/client', () => ({
  resendVerification: (...args: unknown[]) => resendVerification(...args),
}));

import { ResendVerification } from '@/app/(auth)/verify/resend';

const ADDRESS = 'm.reinhardt@northwind.com';

/**
 * 🔴 **Every test in this file drives the clock, and none of them lets it
 * run** — [B-273](../../../docs/BUGS.md), found by QE when it cost a
 * 16-minute certification run.
 *
 * ⛔ **The countdown is a pure tick counter** — 📁 `resend-timer.tsx`:
 * `setInterval(() => setRemaining((left) => left - 1), 1000)`. ⚡ **So one real
 * second elapsing between a click and an assertion turns `0:45` into `0:44`**,
 * and on an unloaded machine that never happens.
 *
 * ⚠️ **`shouldAdvanceTime: true` was the cause and it looked like the fix.**
 * **It makes the FAKE clock advance by REAL elapsed time**, which reintroduces
 * exactly the dependency fake timers exist to remove. ✅ **It was there so
 * `userEvent`'s own internal waits could resolve — and
 * `userEvent.setup({ advanceTimers })` already does that**, which is what that
 * option is for. **Two mechanisms for one need, and the redundant one was the
 * non-deterministic one.**
 *
 * 🔴 **The rule: a test that asserts an exact time must own every millisecond
 * that passes. If real elapsed time can reach the assertion, the machine is an
 * input.**
 */
beforeEach(() => {
  vi.clearAllMocks();
  resendVerification.mockResolvedValue({ ok: true });
  /**
   * 🔴 **`toFake` is the whole repair, and a bare `vi.useFakeTimers()` does
   * NOT work here.**
   *
   * ⛔ **Faking everything stalls React**: its scheduler and `userEvent`'s
   * internal waits run on `setTimeout`/`setImmediate`/`MessageChannel`, and a
   * fake clock nobody advances leaves every one of them pending — **nine tests
   * time out rather than fail, which is a worse signal than the flake.**
   *
   * ✅ **The countdown uses `setInterval` and nothing else** — 📁
   * `resend-timer.tsx`. **So that is all that is frozen**, and everything React
   * and `userEvent` need keeps its real clock. ⚡ **The countdown can now move
   * only where `advanceTimersByTime` says**, which is the property the file
   * was missing.
   */
  vi.useFakeTimers({ toFake: ['setInterval', 'clearInterval'] });
});

afterEach(() => vi.useRealTimers());

/**
 * ⚡ **Let the mocked send resolve, WITHOUT letting the clock move.**
 *
 * ⛔ **`findByRole` cannot be used here.** 📁 **`waitFor` polls on the real
 * clock, so under `useFakeTimers` it never re-checks and the test times out**
 * — which is precisely why `shouldAdvanceTime: true` was in this file: it was
 * holding `findBy*` up, and it was doing that by making the countdown tick in
 * real time. ⚡ **One option was serving two purposes and only one of them was
 * wanted.**
 *
 * ✅ **The wait here is for a PROMISE, not for a timer** — `resendVerification`
 * is mocked and already resolved — **so flushing microtasks is the honest wait
 * and it moves no clock at all.**
 */
async function sendResolves() {
  await act(async () => {});
}

/** ⚡ **The only way this file builds a user**, so no test can forget the clock. */
function person() {
  // ⛔ **`delay: null` matters.** ⚡ **`userEvent` inserts its own waits between
  // key and pointer events, and under fake timers nothing advances them** —
  // which is the second thing `shouldAdvanceTime: true` was quietly doing.
  // ✅ **Skipping those waits is honest here: this file tests a countdown, not
  // typing cadence.**
  // ⛔ **No `advanceTimers` hook.** ⚡ **`userEvent` would call it during its
  // own waits and tick the countdown mid-click** — the same defect one layer
  // down. ✅ **Its waits run on the real `setTimeout`, which is not faked.**
  return userEvent.setup();
}

/** Send once and let the countdown start. */
async function resendOnce(user: ReturnType<typeof userEvent.setup>) {
  await user.click(screen.getByRole('button', { name: 'Resend' }));
  await sendResolves();
  expect(screen.getByRole('button', { name: /Resend in/ })).toBeInTheDocument();
}

describe('the timer the design specifies', () => {
  it('starts at 45 seconds and prints the time remaining', async () => {
    // *"The resend timer starts at 45s and doubles."* And the design's own
    // accessibility note asks for the remaining time to be shown rather than
    // the control merely being disabled.
    const user = person();
    render(<ResendVerification email={ADDRESS} />);

    await resendOnce(user);

    expect(screen.getByRole('button', { name: 'Resend in 0:45' })).toBeDisabled();
  });

  it('counts down in real seconds', async () => {
    const user = person();
    render(<ResendVerification email={ADDRESS} />);

    await resendOnce(user);
    await act(async () => {
      await vi.advanceTimersByTimeAsync(3000);
    });

    expect(screen.getByRole('button', { name: 'Resend in 0:42' })).toBeInTheDocument();
  });

  it('doubles on the second send', async () => {
    const user = person();
    render(<ResendVerification email={ADDRESS} />);

    await resendOnce(user);
    await act(async () => {
      await vi.advanceTimersByTimeAsync(45_000);
    });
    await resendOnce(user);

    // 45 → 90. `1:30`, printed as the design prints it.
    expect(screen.getByRole('button', { name: 'Resend in 1:30' })).toBeInTheDocument();
  });

  it('⛔ does not start the wait when the send failed', async () => {
    /**
     * **A failure that began a 45-second countdown would punish somebody for
     * the product's own error**, and leave them no way to retry.
     */
    resendVerification.mockResolvedValue({ ok: false, error: 'Could not be reached.' });
    const user = person();
    render(<ResendVerification email={ADDRESS} />);

    await user.click(screen.getByRole('button', { name: 'Resend' }));

    await sendResolves();
    expect(screen.getByRole('button', { name: 'Resend' })).toBeEnabled();
    expect(screen.getByText('Could not be reached.')).toBeVisible();
  });

  it('suggests spam and the corporate filter on the third send', async () => {
    // The design's own escalation: by the third attempt the likely cause is
    // not a slow queue, and saying so is more use than sending again.
    const user = person();
    render(<ResendVerification email={ADDRESS} />);

    for (const wait of [45_000, 90_000]) {
      await resendOnce(user);
      await act(async () => {
        await vi.advanceTimersByTimeAsync(wait);
      });
    }
    await resendOnce(user);

    expect(screen.getByText(/spam folder and ask whether your corporate filter/i)).toBeVisible();
  });

  it('says nothing about filters before then', async () => {
    const user = person();
    render(<ResendVerification email={ADDRESS} />);

    await resendOnce(user);

    expect(screen.queryByText(/corporate filter/i)).not.toBeInTheDocument();
    expect(screen.getByText(/check the address above/i)).toBeVisible();
  });
});

describe('what the screen does not claim', () => {
  it('⛔ never draws six code boxes, because nothing would verify them', () => {
    /**
     * **C-241.** `better-auth/plugins/email-otp` is installed and
     * unregistered; the server sends `{ user, url }`. **A control whose
     * outcome cannot depend on its input is a false affordance** — the rule
     * this lane already applied to `/join`'s *Request access* and `/sso`'s
     * domain field. **Six digits typed into a screen that cannot check them
     * is the strongest version of it: it looks like it worked until it does
     * not.**
     */
    render(<ResendVerification email={ADDRESS} />);

    expect(screen.queryByLabelText(/digit|code/i)).not.toBeInTheDocument();
    expect(screen.queryAllByRole('textbox')).toHaveLength(1);
  });

  it('keeps the address prefilled and editable', () => {
    // The most likely reader is somebody who mistyped it one screen ago.
    render(<ResendVerification email={ADDRESS} />);

    expect(screen.getByLabelText('Work email')).toHaveValue(ADDRESS);
  });

  it('announces the wait politely, never as an alert', async () => {
    // It changes every second; an interruption per second is not feedback.
    const user = person();
    render(<ResendVerification email={ADDRESS} />);

    await resendOnce(user);

    expect(screen.queryByRole('alert')).not.toBeInTheDocument();
    expect(document.querySelector('[aria-live="polite"]')).toHaveTextContent(/send again in/i);
  });
});
