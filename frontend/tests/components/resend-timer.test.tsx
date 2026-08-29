/**
 * **The resend cooldown on the verification screen** — 📁
 * `Fortune Signora Authentication.dc.html`, verbatim:
 *
 * > 📁 ***"The resend timer starts at 45s and doubles; the third resend
 * > suggests checking spam and the corporate filter."***
 *
 * ## ⛔ It was built, exported, rendered — and witnessed by nothing
 *
 * ⚠️ **Found by asking which components nothing names**: 2 of 131, and this is
 * the one carrying logic. ⚡ **`app/(auth)/verify/resend.tsx` renders it**, so
 * this is not an unreachable primitive — **it is a reachable one whose
 * arithmetic no assertion had ever read.**
 *
 * ⛔ **And the arithmetic IS the design statement.** *45 and doubles* is the
 * whole of what this component promises; **a version that reset to 45 every
 * time would look correct on any single screenshot** and would quietly offer
 * the control four times faster than the design says by the third attempt.
 *
 * ## ⚡ Fake timers, so the intervals are ORDERING rather than duration
 *
 * ⛔ **A real-clock test of a 45-second timer either sleeps for 45 seconds or
 * asserts nothing about it.** 📁 [B-1092](../../docs/BUGS.md) is what a
 * wall-clock dependency costs when the machine is busy — **so the clock moves
 * only when this file moves it.**
 */
import { act, renderHook } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

import {
  ATTEMPTS_BEFORE_FILTER_HINT,
  FIRST_RESEND_DELAY_SECONDS,
  formatRemaining,
  useResendTimer,
} from '@/components/ui/resend-timer';

beforeEach(() => vi.useFakeTimers());
afterEach(() => vi.useRealTimers());

const tick = (seconds: number) => act(() => void vi.advanceTimersByTime(seconds * 1000));

describe('📁 the design prints the remaining time, never a bare disabled button', () => {
  it('pads the seconds, because `0:5` is not a time', () => {
    /**
     * 📁 The design's own example is `0:42`. ⛔ **`0:5` reads as five minutes
     * to somebody scanning**, which is the one way a countdown can mislead.
     */
    expect(formatRemaining(42)).toBe('0:42');
    expect(formatRemaining(5)).toBe('0:05');
    expect(formatRemaining(0)).toBe('0:00');
  });

  it('⚡ crosses the minute boundary, which the second interval reaches', () => {
    // ⛔ **90 is not a hypothetical**: it is the second delay, so a formatter
    // that printed `0:90` would ship on the second resend of every session.
    expect(formatRemaining(90)).toBe('1:30');
    expect(formatRemaining(60)).toBe('1:00');
    expect(formatRemaining(180)).toBe('3:00');
  });
});

describe('🔴 45 and DOUBLING — the design statement, and the part nothing read', () => {
  it('⛔ offers the control immediately, before anything has been sent', () => {
    /**
     * ⚠️ **`0`, not 45.** ⛔ **A cooldown that begins on arrival would make
     * somebody wait 45 seconds for a mail the product had not yet failed to
     * deliver** — and the screen reaches this state by *arriving*, not by
     * asking.
     */
    const { result } = renderHook(() => useResendTimer());

    expect(result.current.remaining).toBe(0);
    expect(result.current.attempts).toBe(0);
  });

  it('starts the first interval at the design’s 45 seconds', () => {
    const { result } = renderHook(() => useResendTimer());

    act(() => result.current.sent());

    expect(result.current.remaining).toBe(FIRST_RESEND_DELAY_SECONDS);
    expect(result.current.attempts).toBe(1);
  });

  it('counts down a second at a time and stops at zero', () => {
    const { result } = renderHook(() => useResendTimer());
    act(() => result.current.sent());

    tick(10);
    expect(result.current.remaining).toBe(35);

    // ⛔ **Past the end, deliberately.** ⚡ `Math.max(0, …)` is the guard, and a
    // countdown that went negative would print `-1:59` rather than offering
    // the control.
    tick(60);
    expect(result.current.remaining).toBe(0);
  });

  it('🔴 doubles: 45, then 90, then 180', () => {
    /**
     * ⚡ **This is the assertion the component existed without.** ⛔ **A
     * version that reset to 45 each time passes every other test in this
     * file** — the first interval is right, the format is right, the count is
     * right — **and offers the control four times sooner than the design says
     * by the third attempt.**
     *
     * ⚠️ **Each send is made from a settled timer**, so what is measured is
     * the NEXT interval rather than whatever remained of the last one.
     */
    const { result } = renderHook(() => useResendTimer());

    act(() => result.current.sent());
    expect(result.current.remaining).toBe(45);

    tick(45);
    act(() => result.current.sent());
    expect(result.current.remaining).toBe(90);

    tick(90);
    act(() => result.current.sent());
    expect(result.current.remaining).toBe(180);
  });

  it('⚡ and the doubling does not depend on waiting the interval out', () => {
    /**
     * ⛔ **A person can resend the moment the control returns, or minutes
     * later, and the sequence is the same.** ⚠️ **The delay is held in a ref
     * precisely so the countdown effect does not restart it** — and a version
     * that derived the next delay from `remaining` would produce 45, 45, 45
     * here while passing the test above.
     */
    const { result } = renderHook(() => useResendTimer());

    act(() => result.current.sent());
    tick(45);
    tick(600); // idle, long past the interval
    act(() => result.current.sent());

    expect(result.current.remaining).toBe(90);
  });
});

describe('📁 the third resend is where the screen starts explaining', () => {
  it('reaches the filter-hint threshold on the third send and not before', () => {
    /**
     * 📁 *"The third resend suggests checking spam and the corporate filter."*
     * ⛔ **`attempts` is what the screen reads**, and
     * `verify/resend.tsx:81` compares it against
     * `ATTEMPTS_BEFORE_FILTER_HINT` — **so an off-by-one here is a hint that
     * arrives on the second attempt or never.**
     */
    const { result } = renderHook(() => useResendTimer());

    for (const expected of [1, 2, 3]) {
      act(() => result.current.sent());
      expect(result.current.attempts).toBe(expected);
      tick(600);
    }

    expect(result.current.attempts).toBeGreaterThanOrEqual(ATTEMPTS_BEFORE_FILTER_HINT);
  });

  it('⛔ and the threshold is 3, which is the number the design names', () => {
    // ⚠️ **The constant is asserted against the DESIGN's number, not against
    // itself.** A test reading `ATTEMPTS_BEFORE_FILTER_HINT` twice would agree
    // with whatever it had been changed to.
    expect(ATTEMPTS_BEFORE_FILTER_HINT).toBe(3);
    expect(FIRST_RESEND_DELAY_SECONDS).toBe(45);
  });
});
