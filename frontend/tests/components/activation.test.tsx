/**
 * **§18 · the activation checklist a brand-new workspace works through** —
 * [TASK-1463](../../../docs/BACKLOG.md).
 *
 * > 📁 ***"The content region holds a three-step activation checklist with live
 * > counts."***
 *
 * 🔴 **The two properties worth protecting are *live* and *honest*.** ⚡ **Live**
 * means every tick is read from the workspace, so it is right for somebody who
 * connected their CRM on another machine. ⛔ **Honest** means the screen a
 * customer reads first prints no figure the platform does not publish.
 */
import { render, screen, within } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import type { IntegrationSystem, Membership } from '@/lib/api/types';

const integrations = vi.hoisted(() => vi.fn());
const members = vi.hoisted(() => vi.fn());

vi.mock('@/lib/query/hooks/integrations', () => ({ useIntegrations: integrations }));
vi.mock('@/lib/query/hooks/team', () => ({ useWorkspaceMembers: members }));
vi.mock('@/lib/state/workspace-provider', () => ({
  useWorkspaceContext: () => ({
    activeWorkspace: { id: 'w1', name: 'Northwind Global', role: 'owner' },
    workspaces: [{ id: 'w1', name: 'Northwind Global', role: 'owner' }],
  }),
}));

import { ActivationChecklist } from '@/components/shell/activation';

function system(
  integration: string,
  capabilities: IntegrationSystem['capabilities'],
  working: boolean,
): IntegrationSystem {
  return {
    integration,
    capabilities,
    connectable: true,
    working,
    needs_attention: false,
    connections: [],
  };
}

function member(id: string): Membership {
  return {
    id,
    workspace_id: 'w1',
    user_id: id,
    role: 'member',
    created_at: '2026-08-01T00:00:00Z',
  } as Membership;
}

function ready(systems: IntegrationSystem[], people: Membership[], hasMore = false) {
  integrations.mockReturnValue({ data: systems, isPending: false, isError: false });
  members.mockReturnValue({
    data: { items: people, next_cursor: null, has_more: hasMore },
    isPending: false,
    isError: false,
  });
}

function step(id: string) {
  const node = document.querySelector(`[data-step="${id}"]`);
  if (node === null) throw new Error(`no step ${id}`);
  return node as HTMLElement;
}

beforeEach(() => {
  integrations.mockReset();
  members.mockReset();
});

describe('🔴 a failed read is never rendered as an empty setup', () => {
  /**
   * 🔴 **[P-A](../../../docs/DOMAIN_DISCOVERY_REGISTER.md) at its most
   * expensive.**
   *
   * ⛔ **The empty result on this screen is *"you have connected nothing"*** —
   * so a customer who connected Salesforce yesterday would be told they had
   * not, **on the screen whose whole job is to say what is left to do.**
   */
  it('⛔ says the read failed rather than showing three undone steps', () => {
    integrations.mockReturnValue({ data: undefined, isPending: false, isError: true });
    members.mockReturnValue({ data: undefined, isPending: false, isError: false });

    render(<ActivationChecklist />);

    expect(screen.getByText(/could not load/i)).toBeInTheDocument();
    expect(screen.queryByTestId('activation-checklist')).not.toBeInTheDocument();
  });

  it('⛔ and the same when the roster is the read that failed', () => {
    integrations.mockReturnValue({ data: [], isPending: false, isError: false });
    members.mockReturnValue({ data: undefined, isPending: false, isError: true });

    render(<ActivationChecklist />);

    expect(screen.getByText(/could not load/i)).toBeInTheDocument();
  });
});

describe('✅ every tick is read from the workspace', () => {
  it('⛔ nothing connected means nothing ticked', () => {
    ready([], [member('u1')]);

    render(<ActivationChecklist />);

    expect(screen.getByTestId('activation-progress')).toHaveTextContent('0 of 3');
    expect(step('crm')).toHaveAttribute('data-done', 'false');
  });

  it('✅ a working CRM ticks the first step', () => {
    ready([system('salesforce', ['crm_activity'], true)], [member('u1')]);

    render(<ActivationChecklist />);

    expect(step('crm')).toHaveAttribute('data-done', 'true');
    expect(screen.getByTestId('activation-progress')).toHaveTextContent('1 of 3');
  });

  /**
   * 🔴 **A connection that exists is not a connection that works.**
   *
   * 📁 `IntegrationSystem.working` says so in its own words — *"at least one
   * connection Signora can currently use — **not merely present**"*. ⛔ **A step
   * ticked by a broken connection tells somebody they have finished setting up
   * a product that cannot see their data.**
   */
  it('🔴 a present but broken connection does NOT tick it', () => {
    ready([system('salesforce', ['crm_activity'], false)], [member('u1')]);

    render(<ActivationChecklist />);

    expect(step('crm')).toHaveAttribute('data-done', 'false');
  });

  it('✅ either conversation source satisfies the second step', () => {
    ready([system('google_calendar', ['meetings'], true)], [member('u1')]);

    render(<ActivationChecklist />);

    // 📁 *"Calendar, email and call recording. Signora cannot score engagement
    // without at least one."*
    expect(step('conversations')).toHaveAttribute('data-done', 'true');
  });

  it('✅ a second person ticks the third', () => {
    ready([], [member('u1'), member('u2')]);

    render(<ActivationChecklist />);

    expect(step('team')).toHaveAttribute('data-done', 'true');
  });
});

describe('⛔ it prints no figure the platform does not publish', () => {
  it('🔴 no imported-account count, which no read returns', () => {
    ready([system('salesforce', ['crm_activity'], true)], [member('u1')]);

    render(<ActivationChecklist />);

    // 📁 The design prints *"8,412 accounts imported · field mapping
    // confirmed"* — ⛔ **[C-289](../../../docs/LANE_COORDINATION.md): the
    // browse read publishes no total**, and no mapping exists to confirm.
    expect(screen.queryByText(/8,412|imported|field mapping/i)).not.toBeInTheDocument();
  });

  it('⛔ no territories and no quota, because neither is built', () => {
    ready([], [member('u1')]);

    render(<ActivationChecklist />);

    expect(within(step('team')).queryByText(/territor|quota|region/i)).not.toBeInTheDocument();
  });

  /**
   * 🔴 **A page is not a total, and `CursorPage` publishes no total.**
   *
   * ⚠️ **Saying *"2 people"* while `has_more` is true is the same invention as
   * printing an imported-account count** — it just looks like arithmetic.
   */
  it('🔴 counts people exactly only when the page is the whole set', () => {
    ready([], [member('u1'), member('u2')], true);

    render(<ActivationChecklist />);

    expect(within(step('team')).getByText(/More than 2 people/)).toBeInTheDocument();
  });

  it('✅ and states it plainly when it is', () => {
    ready([], [member('u1')]);

    render(<ActivationChecklist />);

    expect(within(step('team')).getByText(/One person is in this organization/)).toBeInTheDocument();
  });

  /**
   * ⛔ **No *"about twelve minutes"***. 📁 The design prints a duration and
   * **nothing measures it** — a promise about how long somebody's setup takes
   * is a claim the product cannot keep.
   */
  it('⛔ promises no duration', () => {
    ready([], [member('u1')]);

    render(<ActivationChecklist />);

    expect(screen.queryByText(/minutes/i)).not.toBeInTheDocument();
  });
});

describe('♿ the state is readable without seeing the mark', () => {
  it('✅ each step says whether it is done, in words', () => {
    ready([system('salesforce', ['crm_activity'], true)], [member('u1')]);

    render(<ActivationChecklist />);

    // 🔴 **Never colour alone** — the rule `StepRail` already establishes.
    expect(within(step('crm')).getByText(/— done/)).toBeInTheDocument();
    expect(within(step('team')).getByText(/— not done yet/)).toBeInTheDocument();
  });

  it('✅ every step leads somewhere that ships', () => {
    ready([], [member('u1')]);

    render(<ActivationChecklist />);

    // ⛔ **Nothing here declares a target account**, which is the one control
    // [C-007](../../../docs/LANE_COORDINATION.md) reserves.
    const hrefs = Array.from(document.querySelectorAll('a')).map((a) => a.getAttribute('href'));
    expect(hrefs).toEqual([
      '/settings/connections',
      '/settings/connections',
      '/settings/team',
    ]);
  });
});
