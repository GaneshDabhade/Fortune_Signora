/**
 * **The three controls that were ruled and could not be executed** —
 * [TASK-498](../../../docs/BACKLOG.md).
 *
 * ⚡ **Why a test at all, when each is one line of vendor configuration.**
 * **These three took three workflows and four coordination items to land**:
 * [C-434](../../../docs/LANE_COORDINATION.md) was Workflow 1's,
 * [C-240](../../../docs/LANE_COORDINATION.md) Workflow 2's,
 * [C-241](../../../docs/LANE_COORDINATION.md) Workflow 3's. **Every screen
 * shipped without its control and said so.** ⛔ **A line that expensive to
 * arrive at should not be able to leave silently** — deleting it would break
 * no screen and no other test, which is exactly the class of regression
 * nothing catches.
 *
 * ⛔ **This asserts registration, not vendor behaviour.** Better Auth's
 * hashing, its `429` window and its OTP storage are the vendor's and are
 * tested by the vendor; **restating them here would be the second copy this
 * codebase keeps refusing** (`lib/auth/email.ts`, on why a port existed
 * before a vendor did).
 */
import { describe, expect, it } from 'vitest';

import { readFileSync } from 'node:fs';
import { join } from 'node:path';

/** Read as source, because the alternative is booting Better Auth against a
 * real database to inspect an options object — a heavier test that would
 * assert the same fact less clearly. */
const SERVER = readFileSync(join(process.cwd(), 'lib/auth/server.ts'), 'utf8');

describe('the controls are registered', () => {
  it('⚡ checks passwords against the breach corpus — C-240 ①, ruled', () => {
    // Restores the design's fourth rule on screen 06. The password never
    // leaves the process: five hex characters of a SHA-1 go to the range API.
    expect(SERVER).toContain('haveIBeenPwned()');
  });

  it('🔴 accepts a six-digit code — C-241, and the design chose the length', () => {
    /**
     * **`otpLength: 6` is a read, not a choice.** Screen `07` says *"Enter the
     * 6-digit code"* and [D-138](../../../docs/DECISION_REGISTER.md) makes the
     * snapshot the implementation authority. **The number is asserted so that
     * changing it becomes a deliberate act against the design rather than a
     * quiet edit.**
     */
    expect(SERVER).toContain('emailOTP(');
    expect(SERVER).toMatch(/otpLength:\s*6/);
  });

  it('⚡ rate-limits outside production — C-240 ②, and D-170 §3 before it', () => {
    /**
     * ⛔ **Better Auth defaults this to production only.** Without it the
     * throttled screen Workflow 1 built against the real `429` and the real
     * `X-Retry-After` cannot be reached at any review — **a state that is
     * built, tested and unreachable is the defect `reachability.py` exists to
     * catch, one layer down.**
     */
    expect(SERVER).toMatch(/rateLimit:\s*\{\s*enabled:\s*true\s*\}/);
  });
});

describe('what this row was forbidden to do, asserted rather than promised', () => {
  it('⛔ adds no private signing key or password storage to this tier', () => {
    // §13 and ADR-0026: Better Auth is the sole Authentication Authority and
    // the Python tier only verifies RS256. The row names these by name.
    expect(SERVER).not.toMatch(/BEGIN (RSA )?PRIVATE KEY/);
    expect(SERVER).not.toMatch(/skipAuth|disableAuth|bypassAuth/i);
  });

  it('⛔ does not restate the vendor’s own limits', () => {
    /**
     * **The window, the maximum and the `/sign-in` special case are Better
     * Auth's.** Copying them here would create two sources for one fact —
     * the defect this codebase has refused since `lib/auth/email.ts` was a
     * port with one implementation.
     */
    // ⚠️ **Scoped to the `rateLimit` block, and the first draft was not.**
    // A bare `/max:\s*\d+/` matched `max: 10` — **the Postgres pool size** —
    // so the assertion would have failed for a reason it was never about.
    // **A guard that fires on the wrong fact teaches people to widen it**,
    // which is how a guard stops guarding.
    const rateLimit = /rateLimit:\s*\{[^}]*\}/.exec(SERVER)?.[0] ?? '';
    expect(rateLimit).toBeTruthy();
    expect(rateLimit).not.toMatch(/window:\s*\d+/);
    expect(rateLimit).not.toMatch(/max:\s*\d+/);
  });

  it('⛔ leaves the reset-token expiry alone, because C-243 is undecided', () => {
    /**
     * **The design says thirty minutes; `resetPasswordTokenExpiresIn` defaults
     * to an hour; screen `08` prints the true number.** ⛔ **This row decides
     * nothing** — and setting the value here would decide it. **The screen
     * stays truthful until the product owner picks.**
     */
    expect(SERVER).not.toContain('resetPasswordTokenExpiresIn');
  });
});
