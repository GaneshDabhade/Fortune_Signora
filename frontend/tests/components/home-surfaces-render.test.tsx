/**
 * **Every Home surface that had no witness** — [TASK-1441](../../../docs/BACKLOG.md).
 *
 * 🔴 **Seven components under `components/home/` were rendered by nothing in
 * this repository**, and one of them was printing an engineering docstring
 * above the fold — 📁 [B-1085](../../../docs/BUGS.md).
 *
 * ⛔ **A component with no test is not a coverage gap. It is a surface with no
 * witness**, and the defect it shipped was visible to anybody who looked at
 * Home and invisible to every gate.
 *
 * ## ⚡ What this file asserts, and why it is a sweep rather than a suite
 *
 * **It renders each surface and reads the text a customer would see**, looking
 * for the four ways an absent value reaches a screen: `undefined` · `null` ·
 * `NaN` · `[object Object]`, and the comment markers B-1085 was made of.
 *
 * ⚠️ **This is deliberately shallow.** ⛔ It is not a substitute for each
 * component's own assertions — 📁 `home-forbidden-card.test.tsx` and
 * `workspace-strip.test.tsx` are those. ✅ **It is the witness**: the thing
 * that would have failed on the day the docstring appeared.
 *
 * 📁 **The absent-value half is this lane's own recurring finding** — three
 * instances in two days of a missing case silently joining a real one.
 */
import { render } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

const useWorkspaceMembers = vi.hoisted(() => vi.fn());

vi.mock('@/lib/query/hooks/team', () => ({ useWorkspaceMembers }));

import { NoDataStrip } from '@/components/home/no-data-strip';
import { SourceStrip } from '@/components/home/source-strip';
import { RoleChangeNotice } from '@/components/home/role-change-notice';
import { ForbiddenCard } from '@/components/home/forbidden-card';
import { NoRegistry } from '@/components/home/no-registry';

/** ⚡ **The four ways an absence reaches a screen**, plus B-1085's markers. */
const NEVER = ['undefined', 'null', 'NaN', '[object Object]', '/**', '*/'];

function system(overrides: Record<string, unknown> = {}) {
  return {
    integration: 'salesforce',
    working: true,
    needs_attention: false,
    connections: [
      {
        id: 'c1',
        state: 'connected',
        health: 'healthy',
        connected_at: '2026-03-18T09:00:00Z',
      },
    ],
    ...overrides,
  };
}

beforeEach(() => {
  vi.clearAllMocks();
  useWorkspaceMembers.mockReturnValue({
    data: { items: [{ role: 'owner', member_email: 'a.duval@northwind.com' }] },
  });
});

const SURFACES: readonly (readonly [string, () => React.ReactElement])[] = [
  [
    'no-data strip',
    () => (
      <NoDataStrip
        systems={[system() as never]}
        accounts={0}
        activation={false}
        loading={false}
      />
    ),
  ],
  [
    'source strip — a connection that stopped',
    () => (
      <SourceStrip
        systems={[system({ needs_attention: true }) as never]}
        loading={false}
      />
    ),
  ],
  [
    // ⚡ **The nullable branch too** — 📁 a connection with no `connected_at`
    // takes the *"an earlier date"* path, and that path had never been rendered.
    'source strip — with no connection date',
    () => (
      <SourceStrip
        systems={[
          system({
            needs_attention: true,
            connections: [{ id: 'c1', state: 'revoked', health: 'failing', connected_at: null }],
          }) as never,
        ]}
        loading={false}
      />
    ),
  ],
  [
    'role change notice',
    () => (
      <RoleChangeNotice
        change={{ new_role: 'owner', previous_role: 'member', changed_by_email: null } as never}
      />
    ),
  ],
  [
    'forbidden card',
    () => (
      <ForbiddenCard
        card="Pending requests"
        permission="Approve access"
        workspaceId="w1"
      />
    ),
  ],
  ['no registry', () => <NoRegistry onRetry={() => {}} />],
];

describe('⛔ no Home surface prints an absence, a comment, or an object', () => {
  for (const [name, element] of SURFACES) {
    it(`✅ ${name}`, () => {
      const { container } = render(element());
      const text = container.textContent ?? '';

      // ⚡ **The vacuity half, and it matters more here than usual**: every
      // assertion below passes against an empty container, and four of these
      // six components return `null` under the wrong props. ⛔ **A sweep that
      // rendered nothing would report six clean surfaces.**
      expect(text.trim().length).toBeGreaterThan(0);

      for (const forbidden of NEVER) {
        expect(text).not.toContain(forbidden);
      }
    });
  }

  it('🔴 and the sweep can fail — proved on the string B-1085 actually shipped', () => {
    /**
     * ⚠️ **A guard that cannot fail is documentation pretending to be code**,
     * and a text sweep is exactly the shape that quietly stops matching.
     * ✅ **So the oracle is checked against the real defect** rather than
     * trusted.
     */
    const shipped =
      '/** * role="status" — 4.1.3, "entry announces once", and the greeting */';
    expect(NEVER.some((forbidden) => shipped.includes(forbidden))).toBe(true);
    // ⛔ And it must NOT fire on ordinary Home copy.
    expect(
      NEVER.some((forbidden) =>
        'Salesforce is connected, but it returned no open opportunities.'.includes(
          forbidden,
        ),
      ),
    ).toBe(false);
  });
});
