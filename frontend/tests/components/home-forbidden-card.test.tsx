/**
 * **Home's state 09 — the forbidden card** — [TASK-1441](../../../docs/BACKLOG.md),
 * against 📁 `Authenticated Entry`'s P-11 and `System States` §05.
 *
 * 🔴 **This component had no test either.** ⛔ **Nothing in the repository
 * rendered it**, so nothing could see what colour it came out.
 */
import { render, screen } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

const useWorkspaceMembers = vi.hoisted(() => vi.fn());

vi.mock('@/lib/query/hooks/team', () => ({ useWorkspaceMembers }));

import { ForbiddenCard } from '@/components/home/forbidden-card';

beforeEach(() => {
  vi.clearAllMocks();
  useWorkspaceMembers.mockReturnValue({
    data: {
      items: [
        { role: 'owner', member_email: 'a.duval@northwind.com' },
        { role: 'member', member_email: 'j.okafor@northwind.com' },
      ],
    },
  });
});

function card() {
  return render(
    <ForbiddenCard
      card="Pending requests"
      permission="Approve access"
      workspaceId="w1"
      testId="forbidden"
    />,
  );
}

describe('🔴 what this panel says, and the one thing it says wrongly', () => {
  it('⚠️ it is risk-toned, which is WRONG, and pinned here so the day it changes this fires', () => {
    /**
     * 🔴 **This asserts a DEFECT, deliberately, and that needs justifying.**
     * 📁 [C-1576](../../../docs/LANE_COORDINATION.md).
     *
     * ⛔ **The grammar's rule is unambiguous** — *"warn for permission and
     * interruption, risk for genuine failure. **The colour is never
     * decorative.**"* — **and this panel renders `risk`**, so a person who
     * simply lacks a permission meets a danger-tinted panel on Home.
     *
     * ⛔ **It cannot be fixed without a ruling.** The design's scope table
     * gives region exactly four states and assigns `permission required` to
     * Page; §05 names *"Permission required — in place"* as distinct. ⚠️
     * **Adding the state was tried and `scope-ladder.test.ts` refused it,
     * correctly** — that guard reads the design at test time.
     *
     * ✅ **Pinned rather than left silent**: the day the ruling lands and the
     * state changes, **this test fails and names the row**, which is the
     * opposite of a defect that quietly becomes correct with nobody noticing.
     */
    card();
    const panel = screen.getByTestId('forbidden').firstElementChild;
    expect(panel).toHaveAttribute('data-severity', 'risk');
    expect(panel).toHaveAttribute('data-scope', 'region');
  });

  it('📁 it names the permission and the approvers, and never the withheld data', () => {
    // 📁 P-11 — *"named permission, named approvers, same footprint."*
    card();
    // ⚡ **Twice on purpose** — the title names the permission and the
    // description repeats it inside `HM-COPY-08`'s verbatim sentence.
    expect(screen.getAllByText(/Approve access/).length).toBeGreaterThan(0);
    expect(screen.getByText(/a.duval@northwind.com/)).toBeInTheDocument();
    // ⛔ **A member is not an approver** — `policy.csv` grants every `member:*`
    // action to `owner` alone.
    expect(screen.queryByText(/j.okafor@northwind.com/)).toBeNull();
  });

  it('⛔ and with no owner on the page it says "an owner", never an empty list', () => {
    /**
     * ⚠️ **The members read is one page**, so naming none is possible.
     * 📁 [B-284](../../../docs/BUGS.md) is the defect that taught this:
     * **naming three owners is useful; naming none is not**, and an empty
     * *"Approvers: "* is worse than a general sentence.
     */
    useWorkspaceMembers.mockReturnValue({ data: { items: [] } });
    card();

    expect(screen.getByText(/an owner of this organization/)).toBeInTheDocument();
  });
});
