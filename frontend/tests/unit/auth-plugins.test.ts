/**
 * **The plugins that are registered, and the two that cannot be** —
 * [TASK-493](../../../docs/BACKLOG.md).
 *
 * 📁 **The row's Definition of Done**: *"Four capabilities registered and
 * reachable, zero journeys changed · ⛔ the RS256 pin asserted unchanged."*
 *
 * ⚠️ **Two of the four are not registered, and this file is where that is
 * checkable rather than merely reported**: 🔴 **`passkey` and `sso` do not
 * ship in `better-auth` 1.6.25**, so adopting them is a new dependency and
 * needs an ADR ([§6](../../../CLAUDE.md), [§21](../../../CLAUDE.md)).
 */
import { readFileSync } from 'node:fs';
import { join } from 'node:path';

import { describe, expect, it } from 'vitest';

const SERVER = readFileSync(join(process.cwd(), 'lib', 'auth', 'server.ts'), 'utf8');

describe('✅ the capability that ships AND works is registered', () => {
  it('⚡ multiSession is registered', () => {
    expect(SERVER).toContain('multiSession()');
    expect(SERVER).toMatch(/import \{[^}]*multiSession[^}]*\} from 'better-auth\/plugins'/);
  });

  it('🔴 twoFactor is NOT registered, because registering it broke registration', () => {
    /**
     * 📁 **[B-231](../../../docs/BUGS.md).** ⛔ **Every `POST /api/auth/sign-up`
     * failed with `column "twoFactorEnabled" of relation "user" does not
     * exist`** — the plugin needs schema and this repository has no route to
     * create it.
     *
     * 🔴 **This test previously asserted the OPPOSITE and was green while
     * registration was dead.** ⚡ **It asserted the plugin was imported and
     * never touched Better Auth's database** — **a test of the configuration,
     * not of the capability.** ⛔ **That is why the assertion is inverted here
     * rather than deleted: the next reader needs to know it is absent on
     * purpose.**
     *
     * ✅ **It returns when the schema mechanism does**, which is
     * [C-280](../../../docs/LANE_COORDINATION.md)'s ADR.
     */
    // ⚠️ **Asserted against the IMPORT, not against the file's prose.** The
    // comment recording why it is absent necessarily names it, and a
    // `toContain` would match that — **a guard that fails on its own
    // explanation is a guard nobody keeps.**
    expect(SERVER).not.toMatch(/import \{[^}]*twoFactor[^}]*\} from 'better-auth\/plugins'/);
    // ⛔ And no bare call survives in the plugins array.
    expect(SERVER).not.toMatch(/^\s*twoFactor\(\),\s*$/m);
  });

  it('⛔ and they are imported from the vendor, never re-implemented', () => {
    /**
     * 📁 **[§13](../../../CLAUDE.md) forbids a bespoke authentication
     * mechanism by name.** ⚡ **A hand-rolled TOTP loop is exactly the thing it
     * names**, and the assertion that it is absent is worth more than the
     * assertion that the plugin is present.
     */
    expect(SERVER).not.toMatch(/function\s+(generate|verify)(Totp|TwoFactor|Otp)/i);
    expect(SERVER).not.toMatch(/speakeasy|otplib|node-2fa/);
  });
});

describe('🔴 the two that do not ship are absent, and stay absent until an ADR says otherwise', () => {
  it.each(['passkey', 'sso'])('⛔ %s is not registered', (plugin) => {
    /**
     * ⚠️ **Measured, not assumed**: `require.resolve('better-auth/plugins/passkey')`
     * fails against 1.6.25 and neither name appears in the package's plugin
     * directory. 🔴 **So each is a NEW DEPENDENCY** — 📁 [§6](../../../CLAUDE.md):
     * *"never introduce a new framework, library, or major dependency without
     * explicit approval."*
     *
     * ⛔ **This test is the thing that stops a later session quietly adding
     * one** to satisfy a row that says all four ship.
     */
    expect(SERVER).not.toContain(`${plugin}(`);
  });

  it('⚡ and the package genuinely does not carry them, so the row is what is stale', () => {
    // ⛔ **Asserted against `node_modules` rather than against a memory of it.**
    // If a future upgrade ships them, this test fails and the row becomes
    // buildable — which is the correct direction for a guard to fail in.
    for (const plugin of ['passkey', 'sso']) {
      expect(() => require.resolve(`better-auth/plugins/${plugin}`)).toThrow();
    }
    // ✅ And the two that do ship resolve, so the check discriminates.
    for (const plugin of ['two-factor', 'multi-session']) {
      expect(() => require.resolve(`better-auth/plugins/${plugin}`)).not.toThrow();
    }
  });
});

describe('⛔ the boundary the row says to assert unchanged', () => {
  it('🔴 RS256 stays pinned, and nothing widened it', () => {
    // 📁 [ADR-0026](../../../docs/architecture/adr/0026-jwt-boundary-architecture.md)
    // and [§13](../../../CLAUDE.md): *"never widen this, and never accept an
    // unpinned algorithms argument — it reopens alg: none."*
    const jwt = readFileSync(join(process.cwd(), 'lib', 'auth', 'jwt.ts'), 'utf8');
    expect(jwt).toContain('RS256');
    expect(jwt).not.toMatch(/HS256|none/);
  });

  it('⛔ no plugin brought an authorization model with it', () => {
    /**
     * 🔴 **[D-175](../../../docs/DECISION_REGISTER.md) refuses Better Auth's
     * organization roles permanently**, and the row's budget marks it 🔴.
     * ⚡ **Casbin decides authorization; a plugin that started deciding it
     * would be a second answer to one question.**
     */
    expect(SERVER).not.toContain('organization(');
    expect(SERVER).not.toContain('admin(');
  });
});
