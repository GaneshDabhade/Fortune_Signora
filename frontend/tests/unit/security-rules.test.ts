/**
 * **The Security Center's rules** — [TASK-1414](../../../docs/BACKLOG.md).
 *
 * 🔴 **Every assertion here is about a sentence a customer reads on the one
 * screen where a wrong sentence is dangerous.** 📁 The design: *"no screen
 * claims an outcome the system cannot guarantee."*
 */
import { describe, expect, it } from 'vitest';

import {
  BACKUP_CODE_FLOOR,
  NEVER_DOES,
  RECOVERY_ROUTES,
  RESISTANCE,
  backupCodesAreLow,
  byResistance,
  posture,
  removalConsequence,
  type SecondFactor,
} from '@/app/(app)/profile/security/rules';

const totp: SecondFactor = {
  id: 'totp',
  name: 'Authenticator app',
  state: 'Active',
  resistance: 'codes',
  explanation: 'Six-digit TOTP.',
};
const backup: SecondFactor = {
  id: 'backup',
  name: 'Backup codes',
  state: 'Shown once',
  resistance: 'last-resort',
  explanation: 'Single-use codes.',
};

describe('⚡ the order is stated rather than implied', () => {
  it('✅ sorts by resistance class and not by the order it was given', () => {
    expect(byResistance([backup, totp]).map((factor) => factor.id)).toEqual(['totp', 'backup']);
  });

  /**
   * ⛔ **The fire test for the sort.** ⚡ **A list that happens to arrive in the
   * right order passes any assertion that only checks the output** — so the
   * input here is deliberately the reverse of the answer, and returning the
   * input unchanged turns this red.
   */
  it('🔴 the vocabulary is closed and phishing-resistance leads it', () => {
    expect(RESISTANCE[0]).toBe('phishing-resistant');
    expect(RESISTANCE).toHaveLength(4);
  });
});

describe('🔴 removal states its blast radius and never refuses', () => {
  it('⛔ says the account is left with a password alone when nothing survives', () => {
    const sentence = removalConsequence([totp], 'totp');

    expect(sentence).toContain('password and nothing else');
    // ⚡ **The half a customer does not expect** — backup codes are codes for a
    // factor they would no longer have, and nothing else on the page says so.
    expect(sentence).toContain('backup codes stop working');
  });

  it('✅ names what survives when something does', () => {
    expect(removalConsequence([totp, backup], 'totp')).toContain('Backup codes');
  });

  /**
   * 🔴 **The assertion that would catch a refusal creeping back in.**
   *
   * 📁 The design refuses removing the last phishing-resistant factor. ⛔ **This
   * product has none**, so a refusal would be a policy invented from a mockup
   * and enforced on somebody's own account — **and a branch that cannot be
   * reached besides** ([§2](../../../CLAUDE.md)).
   */
  it('⛔ never returns a refusal, in either shape', () => {
    for (const sentence of [
      removalConsequence([totp], 'totp'),
      removalConsequence([totp, backup], 'totp'),
    ]) {
      expect(sentence).not.toMatch(/cannot|refused|not allowed|must add/i);
    }
  });
});

describe('📁 below three remaining', () => {
  it('✅ three is not below three', () => {
    expect(BACKUP_CODE_FLOOR).toBe(3);
    expect(backupCodesAreLow(3)).toBe(false);
  });

  // ⚡ **The off-by-one is the whole rule.** A `<=` here would prompt a
  // regeneration one code early and teach a customer the number is a guess.
  it('🔴 two is', () => {
    expect(backupCodesAreLow(2)).toBe(true);
  });
});

describe('🔴 a posture cell either knows something or says it does not', () => {
  /**
   * ⛔ **The most dangerous sentence this product could print.**
   *
   * 📁 [P-A](../../../docs/DOMAIN_DISCOVERY_REGISTER.md) — *a failed read must
   * never render as an empty result* — **and the empty result here reads
   * `Open alerts: none`.** ⚡ **A person who has been compromised would read it
   * and stop looking.**
   */
  it('⛔ open alerts is NEVER known, because nothing reads the event stream', () => {
    const cell = posture({ factors: 2, sessions: 3 }).find(
      (candidate) => candidate.label === 'Open alerts',
    );

    expect(cell?.reading.known).toBe(false);
    expect(cell?.reading.known === false ? cell.reading.because : '').toContain(
      'will not say “none”',
    );
  });

  it('✅ all five cells are rendered, including the three that cannot answer', () => {
    const cells = posture({ factors: 2, sessions: 3 });

    expect(cells.map((cell) => cell.label)).toEqual([
      'Open alerts',
      'Second factors',
      'Active sessions',
      'Backup codes',
      'Recovery',
    ]);
    expect(cells.filter((cell) => cell.reading.known)).toHaveLength(2);
  });

  it('🔴 a failed read is not a zero', () => {
    const cells = posture({ factors: null, sessions: null });

    for (const label of ['Second factors', 'Active sessions']) {
      const cell = cells.find((candidate) => candidate.label === label);
      expect(cell?.reading.known).toBe(false);
    }
  });

  it('⛔ an account with no second factor reads as a risk, not as a neutral fact', () => {
    const cell = posture({ factors: 0, sessions: 1 }).find(
      (candidate) => candidate.label === 'Second factors',
    );

    expect(cell?.reading.known === true ? cell.reading.tone : null).toBe('risk');
    expect(cell?.reading.known === true ? cell.reading.meta : '').toContain('only factor');
  });

  it('✅ one session is singular, because a count that reads “1 sessions” is a count nobody wrote', () => {
    const cell = posture({ factors: 2, sessions: 1 }).find(
      (candidate) => candidate.label === 'Active sessions',
    );

    expect(cell?.reading.known === true ? cell.reading.value : '').toBe('1 session');
  });
});

describe('🔴 a recovery route that does not exist says so', () => {
  /**
   * ⛔ **The invariant that stops a fake route shipping quietly.** ⚡ **The
   * design draws four as though all four work**, and a row added later with
   * `built: false` and no sentence would look identical to a working one.
   */
  it('⛔ every unbuilt route carries the sentence that says it is unbuilt', () => {
    for (const route of RECOVERY_ROUTES.filter((candidate) => !candidate.built)) {
      expect(route.absent, `${route.title} is unbuilt and says nothing about it`).toBeTruthy();
    }
  });

  it('✅ admin-assisted recovery is the one that is not built', () => {
    const admin = RECOVERY_ROUTES.find((route) => route.title === 'Admin-assisted recovery');

    expect(admin?.built).toBe(false);
    expect(admin?.absent).toContain('does not exist yet');
  });

  it('✅ a backup code is the first route, because it needs no third party', () => {
    expect(RECOVERY_ROUTES[0]?.title).toBe('A backup code');
  });
});

describe('📁 what Signora never does', () => {
  /**
   * ⚠️ **The row calls this *"the sentence the row is really about"*** — a
   * commitment a support agent can be held to. ⛔ **Four, and each one is a
   * behaviour, never a reassurance.**
   */
  it('✅ four commitments, each one a thing that will not happen', () => {
    expect(NEVER_DOES).toHaveLength(4);
    for (const commitment of NEVER_DOES) {
      expect(commitment).not.toMatch(/we take .* seriously|committed to/i);
    }
  });

  it('⛔ includes the one an attacker relies on — support cannot read your codes', () => {
    expect(NEVER_DOES.join(' ')).toContain('backup codes');
  });
});
