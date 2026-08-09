/**
 * **The server-side half of step-up** — [TASK-1410](../../../docs/BACKLOG.md).
 *
 * 🔴 **This file exists because a fire-test found nothing protecting it.** I
 * removed `freshAge: 600` from `lib/auth/server.ts` and the whole suite passed
 * — 2158 green — **while the enforcement window silently reverted to Better
 * Auth's 24-hour default.** The dialog was tested; the thing the dialog is
 * about was not.
 *
 * ⛔ **That is the row's own warning arriving by the route it names**: *"a
 * step-up that only guards the dialog guards nothing."* ⚡ **A missing
 * `freshAge` is exactly that failure and it is invisible** — every screen
 * renders, every test passes, and an unlocked laptop carries a standing
 * authorisation for a day.
 *
 * ⚠️ **Third time this session that fire-testing found the load-bearing line
 * unprotected** — 📁 [B-224](../../../docs/BUGS.md)'s `recordConnection`,
 * [TASK-1436](../../../docs/BACKLOG.md)'s write, and now this. **The pattern is
 * consistent: the surface gets tested and the thing underneath it does not.**
 */
import { readFileSync } from 'node:fs';
import { join } from 'node:path';

import { describe, expect, it } from 'vitest';

/**
 * ⛔ **Read as source rather than imported.** `lib/auth/server.ts` builds a
 * live Better Auth instance at module load — a database URL, a signing secret,
 * an OTP transport — so importing it here would demand an environment this
 * suite deliberately does not have (📁 the same coupling
 * [B-104](../../../docs/BUGS.md) removed from the build). **The configured
 * value is what this asserts, and the value is in the file.**
 */
const source = readFileSync(join(process.cwd(), 'lib', 'auth', 'server.ts'), 'utf8');

/** ⛔ Comments stripped first — B-318's class: prose naming a value is not the value. */
const code = source.replace(/\/\*[\s\S]*?\*\//g, '').replace(/\/\/.*$/gm, '');

describe('🔴 the enforcement window is configured, not defaulted', () => {
  it('⛔ `freshAge` is set at all — removing it reverts to 24 hours in silence', () => {
    expect(code).toMatch(/freshAge\s*:/);
  });

  it("⚡ and it is the design's ten minutes", () => {
    // 📁 Security Center §02: "Step-up lasts 10 minutes, then expires — long
    // enough to finish a task, short enough that an unlocked laptop is not a
    // standing authorisation." 600 is read from the design, not chosen.
    const match = /freshAge\s*:\s*(\d+)/.exec(code);
    expect(match).not.toBeNull();
    expect(Number(match?.[1])).toBe(600);
  });

  it('🔴 ten minutes is not a day, stated as the property rather than the number', () => {
    // ⛔ The failure this catches is a well-meaning "make it less annoying"
    // change. Better Auth's default is 3600 * 24; anything approaching that is
    // the standing authorisation the design refuses.
    const seconds = Number(/freshAge\s*:\s*(\d+)/.exec(code)?.[1]);
    expect(seconds).toBeLessThan(3600);
  });
});

describe('⛔ the challenge is bought, not built', () => {
  it('🔴 no bespoke code generation or comparison lives in the auth tier', () => {
    /**
     * 📁 [§13](../../../CLAUDE.md) forbids a bespoke authentication mechanism
     * **by name**, and 📁 the row says *"if it writes its own OTP loop it has
     * re-implemented a bought capability"*. ⚡ **This is the row where somebody
     * would write one**, so the absence is asserted rather than assumed.
     */
    expect(code).not.toMatch(/Math\.random|randomInt|generateOtp|crypto\.randomBytes/i);
    // The OTP that exists is the plugin's, configured — not a loop of ours.
    expect(code).toMatch(/emailOTP\s*\(/);
  });

  it('⚡ and the guard can fire — it is not passing on an empty read', () => {
    // B-162's lesson: a scan proved only by passing is a scan nobody has seen
    // work. Both halves.
    expect(code.length).toBeGreaterThan(500);
    expect(/Math\.random/.test('const otp = Math.random();')).toBe(true);
  });
});
