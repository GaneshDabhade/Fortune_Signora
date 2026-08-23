/**
 * 🔴 **Leaving an organization** — 📁 User Profile → Activity → *"Your data"*.
 *
 * ## ⛔ The gap was not a missing capability. It was a stale blocker
 *
 * ⚡ **`POST /workspaces/{id}/membership/leave` has been shipping**, and its own
 * docstring calls it *"the half of team management the product never had"*.
 * 📁 [C-207](../../docs/LANE_COORDINATION.md) closed **2026-08-05** and its
 * *unblocks* column names this exact capability. ⛔ **`settings/team/page.tsx`
 * carried a comment saying leaving was *"blocked on C-207"* for eighteen days
 * afterwards** — and a stale blocker in a comment is indistinguishable from a
 * live one, which is why nobody looked at the endpoint again.
 *
 * ## ⚠️ What this guard pins that a render test would not
 *
 * ⛔ **The endpoint takes NO target**, and that is a security property rather
 * than a convenience: 📁 *"there is no `membership_id` to substitute, so there
 * is no check that the caller owns the one they named."* ✅ **So the mutation
 * must send no body and no id** — and this asserts that, because a future
 * refactor "tidying" it to look like {@link useRemoveMember} would reintroduce
 * exactly the substitution the endpoint was shaped to prevent.
 */
import { readFileSync } from 'node:fs';
import { join } from 'node:path';

import { describe, expect, it } from 'vitest';

const ROOT = join(__dirname, '..', '..');
const PANEL = join(ROOT, 'app', '(app)', 'profile', 'data-rights-panel.tsx');
const HOOKS = join(ROOT, 'lib', 'query', 'hooks', 'team.ts');

function source(path: string): string {
  const body = readFileSync(path, 'utf8');
  // ⛔ **Comments stripped.** 🔴 Three guards in this repository have matched
  // the contract quoted in their own docblock rather than the code.
  return body.replace(/\/\*[\s\S]*?\*\//g, '').replace(/\/\/.*$/gm, '');
}

describe('🔴 leaving an organization is built, and calls the endpoint that exists', () => {
  it('the mutation posts to /membership/leave and sends no target', () => {
    const hooks = source(HOOKS);

    expect(hooks, 'the leave endpoint is not called at all').toContain('/membership/leave');

    const fn = /export function useLeaveOrganization[\s\S]*?\n\}/.exec(hooks)?.[0] ?? '';
    expect(fn, 'useLeaveOrganization is not exported').not.toBe('');
    // ⚡ The endpoint derives the membership from the verified token.
    expect(fn, 'the mutation names a membership id the server ignores').not.toMatch(
      /membershipId|membership_id/,
    );
    expect(fn, 'the mutation sends a body the endpoint does not read').not.toMatch(/body:/);
  });

  /**
   * 🔴 **The design's sentence is NOT rendered, and that is deliberate.**
   * 📁 It promises *"Work you own must be reassigned first, and your
   * administrator is notified."* ⛔ **`leave_workspace.py` does neither** — it
   * counts live owners and refuses an ownerless workspace, and nothing else.
   * ⚠️ **This asserts the promise stays out of the product** until
   * 📁 [C-1552](../../docs/LANE_COORDINATION.md) is ruled, because copy that
   * tells somebody their work was reassigned is worse than no copy.
   */
  it('does not promise reassignment or an administrator notification', () => {
    const panel = source(PANEL);

    expect(panel.toLowerCase()).not.toContain('reassign');
    expect(panel.toLowerCase()).not.toContain('administrator is notified');
  });

  /**
   * ⛔ **No pre-check on the last owner.** 📁 ADR-0404 put that invariant in the
   * application layer because *"a check in an interface can be raced by a
   * second tab"*. ⚡ **A client-side guard would be a second answer** to a
   * question the server already owns — and the wrong one, whenever another tab
   * has just promoted somebody.
   */
  it('leaves the ownerless-workspace refusal to the server', () => {
    const panel = source(PANEL);

    expect(panel).not.toMatch(/live_owners|countOwners|isLastOwner|ownerCount/);
    // ✅ …and renders what the server said instead.
    expect(panel, 'the server refusal is never shown to the customer').toMatch(
      /leave\.error/,
    );
  });
});
