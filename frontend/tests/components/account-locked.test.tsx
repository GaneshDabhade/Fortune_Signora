/**
 * **The locked-account gate** — [TASK-1467](../../../docs/BACKLOG.md),
 * [B-242](../../../docs/BUGS.md).
 *
 * 🔴 **The entry engine has routed to `/auth/locked` since it shipped and the
 * route did not exist**, so a locked account met the 404 gate — *"that address
 * does not lead anywhere."* ⚠️ **It is the worst screen to lose to a 404**:
 * somebody who cannot sign in concludes the product is broken rather than that
 * their account needs unlocking, and there is no second place to find out.
 */
import { render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';

import AccountLockedPage from '@/app/(auth)/auth/locked/page';
import { RULES } from '@/lib/entry/rules';

describe('🔴 the route the entry engine already points at', () => {
  it('⛔ rule 05 routes to `/auth/locked`, and this file is what answers it', () => {
    // ⚡ **Read from the engine, never restated** — 📁 [§2](../../../CLAUDE.md),
    // *truth has exactly one authoritative representation*. **If somebody
    // re-points the rule, this test goes red rather than the screen going
    // quietly unreachable again.**
    const locked = RULES.find((rule) => rule.condition.startsWith('Account locked'));

    expect(locked).toBeDefined();
    expect(locked?.route(undefined as never, undefined as never)).toBe('/auth/locked');
  });
});

describe('✅ it states what happened and one route forward', () => {
  it('📁 the design’s heading, verbatim', () => {
    render(<AccountLockedPage />);

    expect(
      screen.getByRole('heading', { name: 'This account is locked' }),
    ).toBeInTheDocument();
  });

  it('✅ it says the lock is temporary, which decides whether somebody waits or acts', () => {
    render(<AccountLockedPage />);

    expect(screen.getByText(/unlocks on its own/i)).toBeInTheDocument();
  });

  it('✅ and it answers the fear a lock actually creates', () => {
    render(<AccountLockedPage />);

    // ⛔ **The fear is not the lock.** ⚡ **It is that the data is gone, or that
    // somebody else is inside the account.**
    expect(screen.getByText(/no one has been signed in/i)).toBeInTheDocument();
  });

  it('⛔ the way out is a password reset, never a "try again"', () => {
    render(<AccountLockedPage />);

    // ⚡ **The account is locked, so signing in is precisely what cannot
    // work** — a *try again* link would be the control-that-does-nothing
    // [§2](../../../CLAUDE.md) names.
    expect(screen.getByRole('link', { name: /reset your password/i })).toHaveAttribute(
      'href',
      '/forgot-password',
    );
    expect(screen.queryByRole('link', { name: /try again/i })).not.toBeInTheDocument();
  });
});

/**
 * 🔴 **The assertion that keeps a later change from inventing the design's
 * numbers.**
 *
 * 📁 The design draws *"Five failed sign-in attempts locked the account at
 * 09:02. It unlocks automatically at 09:17."* ⛔ **`AccountStanding` is
 * `'locked'` and nothing more** — no count, no lock time, no unlock time,
 * anywhere in `lib/auth` or `lib/entry`.
 *
 * ⚠️ **A wrong unlock time is worse than none**: somebody told *"09:17"* waits
 * until 09:17, and if the number was a guess they wait for nothing, twice.
 */
describe('⛔ it never prints a fact the platform does not publish', () => {
  it('🔴 no attempt count, no clock time', () => {
    render(<AccountLockedPage />);

    const text = document.body.textContent ?? '';
    // ⛔ **A time of day.** ⚡ **Asserted as a SHAPE rather than as the design's
    // literal `09:17`**, so inventing a different one fails too.
    expect(text).not.toMatch(/\b\d{1,2}:\d{2}\b/);
    // ⛔ **A specific number of attempts.**
    expect(text).not.toMatch(/\b(five|5|three|3)\s+failed/i);
  });
});
