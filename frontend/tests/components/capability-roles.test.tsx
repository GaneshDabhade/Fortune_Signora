/**
 * Roles a customer defines, and what changing somebody's would trade.
 *
 * 📁 **[TASK-1479](../../../docs/BACKLOG.md) ⓸**, releasing
 * [ADR-0410](../../../docs/architecture/adr/0410-authorization-capability-layer.md)
 * §6.
 *
 * 🔴 **The subject is what the screen SAYS, because that is the only thing
 * about this layer a customer can act on.** ⛔ Two sentences are load-bearing
 * and both would be easy to lose: **a new role grants nothing**, and **a role
 * change is a trade rather than a promotion.**
 */
import { fireEvent, render, screen, within } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

const capabilityRoles = vi.hoisted(() => vi.fn());
const createRole = vi.hoisted(() => vi.fn());
const assignRole = vi.hoisted(() => vi.fn());
const effectivePermissions = vi.hoisted(() => vi.fn());
const preview = vi.hoisted(() => vi.fn());

vi.mock('@/lib/query/hooks/capability-roles', async () => {
  // ⚡ **`trade` is imported, not stubbed.** 📁 It is the derivation the whole
  // dialog rests on — **a fake one would let a component that showed the wrong
  // direction pass**, which is precisely the assertion these tests exist for.
  const actual = await vi.importActual<
    typeof import('@/lib/query/hooks/capability-roles')
  >('@/lib/query/hooks/capability-roles');
  return {
    trade: actual.trade,
    useCapabilityRoles: capabilityRoles,
    useCreateCapabilityRole: () => ({ mutate: createRole, isPending: false }),
    useAssignCapabilityRole: () => ({ mutate: assignRole, isPending: false }),
    useEffectivePermissions: effectivePermissions,
    useRoleChangePreview: preview,
  };
});

vi.mock('@/components/ui/toast', () => ({ useToast: () => ({ toast: vi.fn() }) }));

import {
  EffectivePermissionsPanel,
  RoleChangeDialog,
  RolesAndPermissions,
} from '@/components/team/capability-roles';

const WORKSPACE = 'aaaaaaaa-1111-4111-8111-111111111111';
const IDLE = { data: undefined, isLoading: false, isError: false };

function permissions(...pairs: [string, string][]) {
  return pairs.map(([resource, action]) => ({ resource, action }));
}

beforeEach(() => {
  vi.clearAllMocks();
  capabilityRoles.mockReturnValue({ ...IDLE, data: { roles: [] } });
  effectivePermissions.mockReturnValue({ ...IDLE, data: undefined });
  preview.mockReturnValue({ ...IDLE, data: undefined });
});

describe('a new role is deliberately useless, and the dialog says so', () => {
  it('warns that creating one takes access away rather than granting any', () => {
    // 🔴 **The one lie this screen is placed to prevent.** 📁 ADR-0410 §5 — a
    // capability that is not yet granted denies. ⛔ Somebody who believed *New
    // role* produced a working role would define `Analyst`, assign it, and cut
    // their colleague off believing they had narrowed them.
    render(<RolesAndPermissions workspaceId={WORKSPACE} canAdminister />);
    fireEvent.click(screen.getByRole('button', { name: 'New role' }));

    expect(screen.getByText(/starts able to do nothing at all/)).toBeVisible();
    expect(screen.getByText(/takes their access away/)).toBeVisible();
  });

  it('does not offer to create one until it has been named', () => {
    render(<RolesAndPermissions workspaceId={WORKSPACE} canAdminister />);
    fireEvent.click(screen.getByRole('button', { name: 'New role' }));

    expect(screen.getByRole('button', { name: 'Create role' })).toBeDisabled();
  });

  it('creates the role the customer named', () => {
    render(<RolesAndPermissions workspaceId={WORKSPACE} canAdminister />);
    fireEvent.click(screen.getByRole('button', { name: 'New role' }));
    fireEvent.change(screen.getByLabelText('What to call it'), {
      target: { value: 'Analyst' },
    });
    fireEvent.click(screen.getByRole('button', { name: 'Create role' }));

    expect(createRole).toHaveBeenCalledWith({ name: 'Analyst' }, expect.anything());
  });
});

describe('the roles list', () => {
  it('says nobody holds a role rather than showing a bare zero', () => {
    // ⚡ **`holders` is the honest fact a new role has**, and it is what a
    // *remove* control would have to ask first.
    capabilityRoles.mockReturnValue({
      ...IDLE,
      data: { roles: [{ role_id: 'r1', name: 'Analyst', holders: 0 }] },
    });

    render(<RolesAndPermissions workspaceId={WORKSPACE} canAdminister />);

    expect(screen.getByText('Nobody holds this')).toBeVisible();
  });

  it('says why an organization might want a role, rather than saying it has none', () => {
    // ⚡ **The empty state is the ORDINARY one** — nobody has defined a role,
    // and that is a complete organization rather than a broken screen. ⛔ *"No
    // roles"* would leave an administrator with nothing to decide from, so it
    // says what a role is FOR and, critically, that a role can only narrow.
    //
    // ⚠️ **Asserted here rather than in the journey.** It was in the journey
    // and failed on the second run, because the creation test leaves a role
    // behind — **a state a component test can simply supply.**
    render(<RolesAndPermissions workspaceId={WORKSPACE} canAdminister />);

    expect(screen.getByText('Every colleague is an owner or a member')).toBeVisible();
    expect(
      screen.getByText(/narrow what a colleague may do, never widen it/),
    ).toBeVisible();
  });

  it('renders the failure rather than vanishing', () => {
    // 📁 **P-A** — a failed read must never render as an empty result. ⛔ A
    // section that disappears reads as a feature the customer does not have.
    capabilityRoles.mockReturnValue({ ...IDLE, isError: true });

    render(<RolesAndPermissions workspaceId={WORKSPACE} canAdminister />);

    expect(screen.getByText(/could not be loaded/)).toBeVisible();
    expect(screen.queryByText(/Every colleague is an owner or a member/)).toBeNull();
  });

  it('offers no way to define one to somebody who may not', () => {
    // **Presentational only** — Casbin on the server is the decision (§20c).
    render(<RolesAndPermissions workspaceId={WORKSPACE} canAdminister={false} />);

    expect(screen.queryByRole('button', { name: 'New role' })).toBeNull();
  });
});

describe('changing a role is a trade, and both directions are shown', () => {
  const analyst = {
    user_id: 'u1',
    current: {
      user_id: 'u1',
      role_name: null,
      permissions: permissions(
        ['account', 'read'],
        ['member', 'add'],
        ['signal', 'resolve'],
      ),
    },
    proposed: {
      user_id: 'u1',
      role_name: 'Analyst',
      permissions: permissions(['account', 'read']),
    },
  };

  function open() {
    return render(
      <RoleChangeDialog
        workspaceId={WORKSPACE}
        open
        onClose={vi.fn()}
        person="ana@acme.com"
        userId="u1"
        roleId="r1"
        roleName="Analyst"
      />,
    );
  }

  it('names what is lost, not only what is gained', () => {
    // 📁 **The design's own words**: *"Both directions are shown, because a
    // role change is a trade rather than a promotion."* ⛔ A dialog listing
    // only gains would describe a promotion, and this layer exists precisely
    // so a role can narrow.
    preview.mockReturnValue({ ...IDLE, data: analyst });

    open();
    const loses = screen.getByRole('heading', { name: 'Loses' }).parentElement!;

    expect(within(loses).getByText('Your colleagues, and what they can do')).toBeVisible();
    expect(within(loses).getByText('What Signora finds, and why it matters')).toBeVisible();
  });

  it('does not list what they keep as either gained or lost', () => {
    // ⛔ **`account, read` is on both sides** — a trade that reported it as
    // both would say the customer gains and loses the same thing.
    preview.mockReturnValue({ ...IDLE, data: analyst });

    open();
    const gains = screen.getByRole('heading', { name: 'Gains' }).parentElement!;

    expect(within(gains).queryByText('The companies you watch')).toBeNull();
    expect(
      within(screen.getByRole('heading', { name: 'Loses' }).parentElement!).queryByText(
        'The companies you watch',
      ),
    ).toBeNull();
  });

  it('says plainly that a role granting nothing gains them nothing', () => {
    // ⚠️ **Today's honest answer**, and it stops being it on its own the day
    // somebody adds a `cap:` row — computed, never held.
    preview.mockReturnValue({
      ...IDLE,
      data: {
        ...analyst,
        proposed: { user_id: 'u1', role_name: 'Analyst', permissions: [] },
      },
    });

    open();
    const gains = screen.getByRole('heading', { name: 'Gains' }).parentElement!;

    expect(
      within(gains).getByText('Nothing. Analyst has not been granted anything yet.'),
    ).toBeVisible();
  });

  it('will not let somebody confirm a trade it could not describe', () => {
    // 🔴 **P-A's loading cousin.** ⛔ Two empty lists would read as *"nothing
    // changes"* — the most dangerous sentence this dialog could produce.
    preview.mockReturnValue({ ...IDLE, isError: true });

    open();

    expect(screen.getByRole('button', { name: 'Change to Analyst' })).toBeDisabled();
    expect(screen.getByText(/could not be worked out/)).toBeVisible();
  });

  it('changes them to the role when confirmed', () => {
    preview.mockReturnValue({ ...IDLE, data: analyst });

    open();
    fireEvent.click(screen.getByRole('button', { name: 'Change to Analyst' }));

    expect(assignRole).toHaveBeenCalledWith(
      { userId: 'u1', roleId: 'r1' },
      expect.anything(),
    );
  });

  it('says ownership is unaffected, because the design separates the two', () => {
    preview.mockReturnValue({ ...IDLE, data: analyst });

    open();

    expect(screen.getByText(/Ownership is not affected/)).toBeVisible();
  });
});

describe('effective permissions name where they come from', () => {
  it('names the membership role when nothing has been narrowed', () => {
    effectivePermissions.mockReturnValue({
      ...IDLE,
      data: {
        user_id: 'u1',
        role_name: null,
        permissions: permissions(['account', 'read']),
      },
    });

    render(
      <EffectivePermissionsPanel
        workspaceId={WORKSPACE}
        userId="u1"
        membershipRole="a member"
      />,
    );

    expect(screen.getByText('Comes from being a member.')).toBeVisible();
    expect(screen.getByText('Can see')).toBeVisible();
  });

  it('names the capability role when one is held', () => {
    effectivePermissions.mockReturnValue({
      ...IDLE,
      data: {
        user_id: 'u1',
        role_name: 'Analyst',
        permissions: permissions(['account', 'read'], ['account', 'update']),
      },
    });

    render(
      <EffectivePermissionsPanel
        workspaceId={WORKSPACE}
        userId="u1"
        membershipRole="a member"
      />,
    );

    expect(screen.getByText('Comes from the Analyst role.')).toBeVisible();
    expect(screen.getByText('Can see and change')).toBeVisible();
  });

  it('never renders a failure as an empty permission list', () => {
    // 🔴 **P-A, and this is the instance that would hurt most.** ⛔ An empty
    // list here reads as *"this person may do nothing"* — a sentence about
    // somebody with no access at all.
    effectivePermissions.mockReturnValue({ ...IDLE, isError: true });

    render(
      <EffectivePermissionsPanel
        workspaceId={WORKSPACE}
        userId="u1"
        membershipRole="a member"
      />,
    );

    expect(screen.getByText(/could not be loaded/)).toBeVisible();
  });

  it('counts what it cannot describe rather than dropping it', () => {
    // ⛔ **Under-reporting what somebody may do is the worst failure this
    // panel has**, because a reader acts on the absence — and naming the
    // resource would put the platform's vocabulary on the screen.
    effectivePermissions.mockReturnValue({
      ...IDLE,
      data: {
        user_id: 'u1',
        role_name: null,
        permissions: permissions(['something_nobody_catalogued', 'read']),
      },
    });

    render(
      <EffectivePermissionsPanel
        workspaceId={WORKSPACE}
        userId="u1"
        membershipRole="a member"
      />,
    );

    expect(screen.getByText(/And one more that this screen cannot describe yet/)).toBeVisible();
    expect(screen.queryByText(/something_nobody_catalogued/)).toBeNull();
  });
});
