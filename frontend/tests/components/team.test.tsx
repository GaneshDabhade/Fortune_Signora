/**
 * The screen that lets an organization grow.
 *
 * **Until this shipped, a workspace was permanently whoever created it** —
 * `POST /members` takes a `user_id`, and nothing resolved an address to one.
 *
 * These assert the product rules rather than the rendering: that a forgotten
 * invitation is raised rather than waited for, that settled invitations stay
 * visible because an expired one is the signal to act on, and that the words a
 * customer reads are theirs rather than the enum's.
 */
import { fireEvent, render, screen, within } from '@testing-library/react';
import type { ReactElement } from 'react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import type { Invitation, Membership } from '@/lib/api/types';

const workspaceContext = vi.hoisted(() => vi.fn());
const invitations = vi.hoisted(() => vi.fn());
const invite = vi.hoisted(() => vi.fn());
const revoke = vi.hoisted(() => vi.fn());
const resend = vi.hoisted(() => vi.fn());
const removeMember = vi.hoisted(() => vi.fn());
const changeRole = vi.hoisted(() => vi.fn());
const transfer = vi.hoisted(() => vi.fn());
const orgHistory = vi.hoisted(() => vi.fn());
const members = vi.hoisted(() => vi.fn());
const viewerRole = vi.hoisted(() => vi.fn());
const session = vi.hoisted(() => vi.fn());

vi.mock('@/lib/state/workspace-provider', () => ({
  useWorkspaceContext: workspaceContext,
}));

vi.mock('@/lib/query/hooks/team', () => ({
  useInvitations: invitations,
  useInviteMember: () => ({ mutate: invite, isPending: false }),
  useRevokeInvitation: () => ({ mutate: revoke, isPending: false }),
  useResendInvitation: () => ({ mutate: resend, isPending: false }),
  useRemoveMember: () => ({ mutate: removeMember, isPending: false }),
  useChangeRole: () => ({ mutate: changeRole, isPending: false }),
  useTransferOwnership: () => ({ mutate: transfer, isPending: false }),
  useOrganizationHistory: orgHistory,
  useWorkspaceMembers: members,
  useViewerRole: viewerRole,
}));

vi.mock('@/lib/auth/client', () => ({ useSession: session }));

vi.mock('@/components/ui/toast', () => ({ useToast: () => ({ toast: vi.fn() }) }));

import TeamPage from '@/app/(app)/settings/team/page';

const WORKSPACE = { id: 'aaaaaaaa-1111-4111-8111-111111111111', name: 'Acme Revenue' };
const IDLE = { data: undefined, isLoading: false, isError: false };

function invitation(overrides: Partial<Invitation> = {}): Invitation {
  return {
    id: 'i1',
    workspace_id: WORKSPACE.id,
    invited_email: 'sam@acme.com',
    role: 'member',
    state: 'pending',
    expires_at: new Date(Date.now() + 6 * 864e5).toISOString(),
    created_at: new Date().toISOString(),
    invited_by: 'u1',
    ...overrides,
  };
}

const ME = 'user-me';

function person(overrides: Partial<Membership> = {}): Membership {
  return {
    id: 'm1',
    workspace_id: WORKSPACE.id,
    user_id: ME,
    role: 'owner',
    created_at: '2026-08-01T09:00:00Z',
    member_email: 'ana@acme.com',
    ...overrides,
  };
}

function draw(): ReactElement {
  return <TeamPage />;
}

beforeEach(() => {
  vi.clearAllMocks();
  workspaceContext.mockReturnValue({ activeWorkspace: WORKSPACE, isLoading: false });
  invitations.mockReturnValue({ ...IDLE, data: [] });
  session.mockReturnValue({ data: { user: { id: ME } } });
  viewerRole.mockReturnValue({ role: 'owner', resolved: true });
  members.mockReturnValue({ ...IDLE, data: { items: [person()] } });
  orgHistory.mockReturnValue({ ...IDLE, data: [] });
});

describe('an organization with nobody in it says what to do about it', () => {
  it('offers the invitation rather than showing an empty table', () => {
    // A table of one row with column headings is the product showing its
    // schema. The one moment an administrator is guaranteed to be looking is
    // the moment to ask for a colleague.
    //
    // **Scoped to the Invited card**, because the roster above it legitimately
    // renders a table — the founder is always in it.
    render(draw());
    const invited = screen.getByRole('heading', { name: 'Invited' }).closest('div')!
      .parentElement!;

    expect(screen.getByText('Nobody has been invited yet')).toBeVisible();
    expect(within(invited).queryByRole('table')).toBeNull();
  });
});

describe('the list answers *did anybody not come?*', () => {
  it('keeps settled invitations, because an expired one is the signal', () => {
    invitations.mockReturnValue({
      ...IDLE,
      data: [invitation({ id: 'i2', invited_email: 'kit@acme.com', state: 'expired' })],
    });

    render(draw());

    expect(screen.getByText('kit@acme.com')).toBeVisible();
    expect(screen.getByText('Expired')).toBeVisible();
  });

  it('puts everyone still waiting above everyone settled', () => {
    invitations.mockReturnValue({
      ...IDLE,
      data: [
        invitation({ id: 'a', invited_email: 'settled@acme.com', state: 'revoked' }),
        invitation({ id: 'b', invited_email: 'waiting@acme.com', state: 'pending' }),
      ],
    });

    const { container } = render(draw());
    const text = container.textContent ?? '';

    expect(text.indexOf('waiting@acme.com')).toBeLessThan(text.indexOf('settled@acme.com'));
  });

  it('offers to withdraw only what can still be withdrawn', () => {
    // Withdrawing an accepted invitation would claim an act that changes
    // nothing — the colleague is already in the organization, and removing
    // them is a different operation with a different blast radius.
    invitations.mockReturnValue({
      ...IDLE,
      data: [invitation({ state: 'accepted', invited_email: 'joined@acme.com' })],
    });

    render(draw());

    expect(screen.queryByRole('button', { name: 'Withdraw' })).toBeNull();
  });

  it('withdraws the invitation the button belongs to', () => {
    invitations.mockReturnValue({ ...IDLE, data: [invitation({ id: 'i9' })] });

    render(draw());
    fireEvent.click(screen.getByRole('button', { name: 'Withdraw' }));

    expect(revoke).toHaveBeenCalledWith('i9');
  });
});

describe('a forgotten invitation is raised, not waited for', () => {
  it('says so when one has been unanswered for over a week', () => {
    // Nobody goes looking for a forgotten invitation — that is what forgotten
    // means — so the page has to raise it.
    invitations.mockReturnValue({
      ...IDLE,
      data: [invitation({ created_at: new Date(Date.now() - 9 * 864e5).toISOString() })],
    });

    render(draw());

    expect(screen.getByText(/sent over a week ago/)).toBeVisible();
  });

  it('stays quiet about a recent one', () => {
    invitations.mockReturnValue({ ...IDLE, data: [invitation()] });

    render(draw());

    expect(screen.queryByText(/sent over a week ago/)).toBeNull();
  });

  it('never counts a settled invitation as forgotten', () => {
    // An invitation withdrawn a month ago is not waiting for anybody.
    invitations.mockReturnValue({
      ...IDLE,
      data: [
        invitation({
          state: 'revoked',
          created_at: new Date(Date.now() - 30 * 864e5).toISOString(),
        }),
      ],
    });

    render(draw());

    expect(screen.queryByText(/sent over a week ago/)).toBeNull();
  });
});

describe('the words are the customer’s', () => {
  it('describes a role by what it lets somebody do', () => {
    // **The same words wherever a role appears**, whether it is held, offered,
    // or being chosen — a role means one thing, and the roster's control and
    // the invited list must not describe it differently.
    invitations.mockReturnValue({ ...IDLE, data: [invitation({ role: 'owner' })] });

    render(draw());

    // On an invitation, as text — and the same words appear in the roster's
    // control and in the role explanation, which is the catalog working
    // rather than a duplicate.
    expect(screen.getAllByText('Can administer Signora').length).toBeGreaterThan(1);
    // On a member, as the chosen option of the control that changes it.
    expect(screen.getByLabelText('What ana@acme.com can do')).toHaveValue('owner');
    expect(
      screen.getAllByRole('option', { name: 'Can administer Signora' }).length,
    ).toBeGreaterThan(0);
  });

  it('says *Withdrawn* rather than *Revoked*', () => {
    // A salesperson withdraws an offer; a system revokes a credential.
    invitations.mockReturnValue({ ...IDLE, data: [invitation({ state: 'revoked' })] });

    render(draw());

    expect(screen.getByText('Withdrawn')).toBeVisible();
    expect(screen.queryByText('Revoked')).toBeNull();
  });

  it('tells the administrator what sending one does, and that it is reversible', () => {
    render(draw());
    fireEvent.click(screen.getAllByRole('button', { name: 'Invite a colleague' })[0]!);

    expect(screen.getByText(/You can withdraw it any time before they accept/)).toBeVisible();
  });
});

describe('sending an invitation', () => {
  function openDialog() {
    render(draw());
    fireEvent.click(screen.getAllByRole('button', { name: 'Invite a colleague' })[0]!);
    return screen.getByRole('dialog');
  }

  it('cannot be sent without an address', () => {
    const dialog = openDialog();

    expect(within(dialog).getByRole('button', { name: 'Send invitation' })).toBeDisabled();
  });

  it('sends the address and the role together', () => {
    const dialog = openDialog();

    fireEvent.change(within(dialog).getByLabelText('Their email addresses'), {
      target: { value: ' Sam@Acme.com ' },
    });
    fireEvent.click(within(dialog).getByRole('button', { name: 'Send invitation' }));

    expect(invite).toHaveBeenCalledWith(
      { email: 'Sam@Acme.com', role: 'member' },
      expect.anything(),
    );
  });

  it('defaults to the role that cannot administer anything', () => {
    // The safe default. Making somebody an administrator is a deliberate act.
    const dialog = openDialog();

    expect(within(dialog).getByLabelText('What they can do')).toHaveValue('member');
  });
});

describe('it says when it could not load, rather than disappearing', () => {
  it('reports the failure and reassures about the data', () => {
    invitations.mockReturnValue({ ...IDLE, isError: true });

    render(draw());

    expect(screen.getByText(/could not be loaded/)).toBeVisible();
    expect(screen.getByRole('heading', { name: 'Invited' })).toBeVisible();
  });
});

describe('the banner promised “send it again”, and now there is a control', () => {
  // **A defect in TM-03a, found by reading its own copy.** The forgotten-
  // invitation banner offered two actions and the table had one. A control
  // that goes nowhere costs more trust than an absent one — and here the
  // product was describing an action it could not perform.

  it('offers Send again on anything still waiting', () => {
    invitations.mockReturnValue({ ...IDLE, data: [invitation()] });

    render(draw());

    expect(screen.getByRole('button', { name: 'Send again' })).toBeVisible();
  });

  it('resends the invitation the button belongs to', () => {
    invitations.mockReturnValue({ ...IDLE, data: [invitation({ id: 'i7' })] });

    render(draw());
    fireEvent.click(screen.getByRole('button', { name: 'Send again' }));

    expect(resend).toHaveBeenCalledWith('i7', expect.anything());
  });

  it('does not offer it on a settled invitation', () => {
    // Re-sending a withdrawn invitation delivers a link that cannot be used,
    // which is worse than not sending one.
    invitations.mockReturnValue({ ...IDLE, data: [invitation({ state: 'expired' })] });

    render(draw());

    expect(screen.queryByRole('button', { name: 'Send again' })).toBeNull();
  });

  it('offers the recoverable action before the deliberate one', () => {
    invitations.mockReturnValue({ ...IDLE, data: [invitation()] });

    const { container } = render(draw());
    const text = container.textContent ?? '';

    expect(text.indexOf('Send again')).toBeLessThan(text.indexOf('Withdraw'));
  });
});

describe('the roster answers *who is in my organization?*', () => {
  it('names people by the address their membership was created with', () => {
    render(draw());

    expect(screen.getByText('ana@acme.com')).toBeVisible();
  });

  it('says *Somebody here* rather than an identifier when no address is known', () => {
    // **D23.** A membership added by identifier before invitations existed has
    // no address, and a UUID would be the same absence dressed as information.
    members.mockReturnValue({
      ...IDLE,
      data: { items: [person(), person({ id: 'm2', user_id: 'other', member_email: null })] },
    });

    const { container } = render(draw());

    expect(screen.getByText('Somebody here')).toBeVisible();
    expect(container.textContent).not.toContain('other');
  });

  it('marks which row is you', () => {
    render(draw());

    expect(screen.getByText('You')).toBeVisible();
  });

  it('says how many people, and how many can administer Signora', () => {
    // The second is what makes the last-owner refusal comprehensible before
    // anybody meets it.
    members.mockReturnValue({
      ...IDLE,
      data: {
        items: [person(), person({ id: 'm2', user_id: 'b', role: 'member', member_email: 'jo@acme.com' })],
      },
    });

    render(draw());

    expect(screen.getByText(/2 people · 1 can administer Signora/)).toBeVisible();
  });
});

describe('removing somebody is offered only where it is real', () => {
  it('is not offered to a member', () => {
    // Presentation, never enforcement — the server refuses it regardless, and
    // a control that goes nowhere costs more trust than an absent one.
    viewerRole.mockReturnValue({ role: 'member', resolved: true });
    members.mockReturnValue({
      ...IDLE,
      data: { items: [person(), person({ id: 'm2', user_id: 'b', member_email: 'jo@acme.com' })] },
    });

    render(draw());

    expect(screen.queryByRole('button', { name: 'Remove' })).toBeNull();
  });

  it('is never offered on your own row', () => {
    // Leaving is a different operation with a different invariant, and it is
    // blocked on C-207.
    render(draw());

    expect(screen.queryByRole('button', { name: 'Remove' })).toBeNull();
  });

  it('names the person and the consequence rather than asking *are you sure*', () => {
    members.mockReturnValue({
      ...IDLE,
      data: { items: [person(), person({ id: 'm2', user_id: 'b', member_email: 'jo@acme.com' })] },
    });

    render(draw());
    fireEvent.click(screen.getByRole('button', { name: 'Remove' }));

    expect(screen.getByText(/jo@acme.com will lose access/)).toBeVisible();
  });

  it('promises that what they decided stays on the record', () => {
    // D3: the membership is ended, never deleted, so decision history and the
    // timeline still say who acted.
    members.mockReturnValue({
      ...IDLE,
      data: { items: [person(), person({ id: 'm2', user_id: 'b', member_email: 'jo@acme.com' })] },
    });

    render(draw());
    fireEvent.click(screen.getByRole('button', { name: 'Remove' }));

    expect(screen.getByText(/already decided stays on the record/)).toBeVisible();
  });
});

describe('changing what somebody can do', () => {
  function twoPeople() {
    members.mockReturnValue({
      ...IDLE,
      data: {
        items: [
          person(),
          person({ id: 'm2', user_id: 'b', role: 'member', member_email: 'jo@acme.com' }),
        ],
      },
    });
  }

  it('puts the control on the role itself rather than behind a menu', () => {
    // An owner deciding whether somebody should administer Signora is already
    // looking at this column.
    twoPeople();

    render(draw());

    expect(screen.getByLabelText('What jo@acme.com can do')).toBeVisible();
  });

  it('a member reads roles and cannot change them', () => {
    viewerRole.mockReturnValue({ role: 'member', resolved: true });
    twoPeople();

    render(draw());

    expect(screen.queryByLabelText('What jo@acme.com can do')).toBeNull();
    expect(screen.getAllByText('Works accounts').length).toBeGreaterThan(0);
  });

  it('explains the gain when promoting', () => {
    twoPeople();

    render(draw());
    fireEvent.change(screen.getByLabelText('What jo@acme.com can do'), {
      target: { value: 'owner' },
    });

    expect(screen.getByText(/will be able to invite people, remove them/)).toBeVisible();
  });

  it('explains what stays as well as what goes when demoting', () => {
    // Not "are you sure". What changes, and what does not.
    members.mockReturnValue({
      ...IDLE,
      data: {
        items: [person(), person({ id: 'm2', user_id: 'b', member_email: 'jo@acme.com' })],
      },
    });

    render(draw());
    fireEvent.change(screen.getByLabelText('What jo@acme.com can do'), {
      target: { value: 'member' },
    });

    expect(screen.getByText(/will keep working accounts, and will no longer be able to/)).toBeVisible();
  });

  it('warns you specifically when you are demoting yourself', () => {
    // **The one irreversible-by-you case.** An owner may step back, and must
    // be told they cannot step forward again alone.
    render(draw());
    fireEvent.change(screen.getByLabelText('What ana@acme.com can do'), {
      target: { value: 'member' },
    });

    expect(screen.getByText(/That includes you — you will not be able to undo this yourself/)).toBeVisible();
  });

  it('sends the membership and the new role together', () => {
    twoPeople();

    render(draw());
    fireEvent.change(screen.getByLabelText('What jo@acme.com can do'), {
      target: { value: 'owner' },
    });
    fireEvent.click(screen.getByRole('button', { name: 'Let them administer' }));

    expect(changeRole).toHaveBeenCalledWith(
      { membershipId: 'm2', role: 'owner' },
      expect.anything(),
    );
  });
});

describe('roles are explained as capabilities, never as permissions', () => {
  // **One reviewed catalog.** Before it, the same distinction was written in
  // the selector, the roster and the invitation dialog — three copies of one
  // fact, which eventually disagree.

  /** jsdom hides the contents of a closed `<details>`, correctly — so opening
   * it is part of the test rather than a workaround. */
  function openExplanation(): HTMLElement {
    const summary = screen.getByText('What each role can do');
    const details = summary.closest('details')!;
    details.setAttribute('open', '');
    return details;
  }

  it('explains what each role can do, where an owner is choosing', () => {
    render(draw());
    const explanation = openExplanation();

    expect(
      within(explanation).getByText('Invite colleagues, and withdraw an invitation'),
    ).toBeVisible();
    expect(
      within(explanation).getByText(
        'See every account Signora is watching, and why it matters',
      ),
    ).toBeVisible();
  });

  it('says what a member cannot do, so the difference is a real one', () => {
    render(draw());
    const explanation = openExplanation();

    expect(
      within(explanation).getByText(/Cannot invite or remove colleagues/),
    ).toBeVisible();
  });

  it('explains the role being offered, inside the invitation dialog', () => {
    // An administrator inviting somebody as an owner should not have to open a
    // disclosure elsewhere to learn what that grants.
    render(draw());
    fireEvent.click(screen.getAllByRole('button', { name: 'Invite a colleague' })[0]!);
    const dialog = screen.getByRole('dialog');

    expect(
      within(dialog).getByText('Decide on an account — take it on, close it, or disagree'),
    ).toBeVisible();
  });

  it('tells a member who can do what they cannot', () => {
    // A screen that simply omits the control leaves somebody wondering whether
    // the feature exists. Naming who *can* is a fact they can act on; 403 is
    // a fact about a request.
    viewerRole.mockReturnValue({ role: 'member', resolved: true });

    render(draw());

    expect(screen.getByText(/Only owners can invite colleagues/)).toBeVisible();
    expect(screen.getByText(/Ask somebody who administers this organization/)).toBeVisible();
  });

  it('never uses the platform’s vocabulary for any of it', () => {
    // **The property that makes the catalog worth having.** Adding
    // `timeline:read` to `member` must change nothing here, because "see
    // everything Signora finds" was already true and already said.
    render(draw());
    const text = (document.body.textContent ?? '').toLowerCase();

    for (const forbidden of [
      'casbin',
      'policy',
      'permission',
      'workspace:',
      'member:',
      'resource',
      'tuple',
      'forbidden',
      '403',
    ]) {
      expect(text).not.toContain(forbidden);
    }
  });
});

describe('handing the organization over is one operation', () => {
  function withColleague() {
    members.mockReturnValue({
      ...IDLE,
      data: {
        items: [
          person(),
          person({ id: 'm2', user_id: 'b', role: 'member', member_email: 'jo@acme.com' }),
        ],
      },
    });
  }

  it('is offered at the foot, away from the roster', () => {
    // Danger separated by scope: an administrator scanning names should not be
    // one mis-click from handing over the organization.
    withColleague();

    render(draw());

    expect(screen.getByRole('button', { name: 'Hand over to jo@acme.com' })).toBeVisible();
  });

  it('promises that there is never a moment with two owners', () => {
    // The reason this exists rather than promote-then-demote.
    withColleague();

    render(draw());

    expect(screen.getByText(/never a moment when both of you are owners/)).toBeVisible();
  });

  it('is not offered when there is nobody to hand over to', () => {
    // A one-person organization has nobody to give it to. Asserted on the
    // affordance rather than on the heading, because the dialog carries the
    // same words and is mounted closed.
    render(draw());

    expect(screen.queryByRole('button', { name: /Hand over to/ })).toBeNull();
  });

  it('is not offered to a member', () => {
    viewerRole.mockReturnValue({ role: 'member', resolved: true });
    withColleague();

    render(draw());

    expect(screen.queryByRole('button', { name: /Hand over to/ })).toBeNull();
  });

  it('explains the gain, the loss, and what only they can undo', () => {
    withColleague();

    render(draw());
    fireEvent.click(screen.getByRole('button', { name: 'Hand over to jo@acme.com' }));

    expect(screen.getByText(/will be able to invite people/)).toBeVisible();
    expect(screen.getByText(/You will keep working accounts/)).toBeVisible();
    expect(screen.getByText(/Only they can hand it back/)).toBeVisible();
  });

  it('sends both memberships in one request', () => {
    withColleague();

    render(draw());
    fireEvent.click(screen.getByRole('button', { name: 'Hand over to jo@acme.com' }));
    fireEvent.click(screen.getByRole('button', { name: 'Hand over' }));

    expect(transfer).toHaveBeenCalledWith(
      { fromMembershipId: 'm1', toMembershipId: 'm2' },
      expect.anything(),
    );
  });
});
