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
    expect(SERVER).toMatch(/rateLimit:\s*\{[^}]*enabled:\s*true/);
  });

  it('🔴 keeps the counters OUT of process memory — C-287 ⓐ, ruled 2026-08-17', () => {
    /**
     * ⛔ **`enabled: true` alone was not protection.** Better Auth's `storage`
     * defaults to `"memory"` and falls back to it when neither
     * `rateLimit.storage` nor `secondaryStorage` is set — **and this file set
     * neither for nine days**, from the moment `enabled: true` landed.
     *
     * 📁 [ADR-0408](../../../docs/architecture/adr/0408-inbound-rate-limiting.md)
     * §9 states the consequence, and it is why this is 🔴 rather than a tidy-up:
     * ***"an in-process limiter in a horizontally scaled system does not
     * provide equivalent protection — it provides a number that is wrong by a
     * factor of n and looks right."*** ⚡ **A limiter that looks right is worse
     * than none, because nobody goes looking.**
     *
     * ✅ **The setting was verified BEHAVIOURALLY before this assertion was
     * written**, against a real database, by diffing the vendor's own migration
     * plan:
     *
     *     memory   : ["account","session","user","verification"]
     *     database : ["account","rateLimit","session","user","verification"]
     *
     * ⚡ **So `storage: 'database'` genuinely changes what Better Auth asks the
     * database for.** ⛔ **This test reads source only because the file's own
     * header already settled that trade** — *"the alternative is booting Better
     * Auth against a real database … a heavier test that would assert the same
     * fact less clearly."* **The heavier check was run once, by hand, and its
     * result is recorded above so the next reader need not repeat it.**
     *
     * ⚠️ **It requires `npm run auth:migrate`**, which creates the table. ⛔ **And
     * Alembic must never create it** — `0005_auth_schema.py` creates the schema
     * *"and nothing inside it"*, deliberately.
     */
    const rateLimit = /rateLimit:\s*\{[^}]*\}/.exec(SERVER)?.[0] ?? '';
    expect(rateLimit).toMatch(/storage:\s*'(database|secondary-storage)'/);
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
     * **The window, the maximum and the `/signin` special case are Better
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

});

describe('⑤ the reset token lives thirty minutes — C-243, ruled', () => {
  it('✅ sets the expiry the product owner chose, not the vendor default', () => {
    /**
     * **[D-185](../../../docs/DECISION_REGISTER.md) §1, 2026-08-08: thirty
     * minutes**, on a sentence that is standing guidance beyond this row —
     * ***"the framework should implement the product, not define it."***
     *
     * ⚠️ **This case previously asserted the exact opposite** — `expect(SERVER)
     * .not.toContain('resetPasswordTokenExpiresIn')` — **and it was right to.**
     * ⛔ **The row decided nothing while C-243 was open, and setting the value
     * would have decided it.** ✅ **The ruling landed, so the assertion
     * inverted rather than being deleted**: what it protects is unchanged —
     * *nobody changes a credential's lifetime quietly* — and it now guards a
     * decision that exists instead of the absence of one.
     */
    expect(SERVER).toMatch(/resetPasswordTokenExpiresIn:\s*1800\b/);
  });

  it('🔴 is the half of a pair, and the screen carries the other half', () => {
    /**
     * ⛔ **The config alone understates a credential's life to every customer
     * who reads screen `08`.** The pairing is asserted from the screen's side
     * in `tests/components/password-reset.test.tsx`, which *derives* its
     * expected sentence from this number — **so a change to one number alone
     * fails there.** ⚡ **Named here too**, because this is the file somebody
     * edits when they want to change the expiry, and the failure they will
     * get should not be a surprise.
     */
    expect(SERVER).toContain('resetPasswordTokenExpiresIn');
    expect(SERVER).not.toMatch(/resetPasswordTokenExpiresIn:\s*3600\b/);
  });
});
