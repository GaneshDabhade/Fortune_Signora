/**
 * **WS-B — the standalone chooser** — [TASK-1421](../../../docs/BACKLOG.md),
 * against 📁 `Fortune Signora Workspace Chooser.dc.html`.
 *
 * 🔴 **The route was a 404 and four entry rules already sent people to it**,
 * so the first assertion is that it renders at all. ⛔ **The rest are the
 * states the design specifies and the ones P-A says get skipped.**
 */
import { fireEvent, render, screen, within } from '@testing-library/react';
import { readFileSync } from 'node:fs';
import { join } from 'node:path';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import type { Workspace } from '@/lib/api/types';

const workspaceContext = vi.hoisted(() => vi.fn());
const push = vi.hoisted(() => vi.fn());
const setActive = vi.hoisted(() => vi.fn());

vi.mock('@/lib/state/workspace-provider', () => ({
  useWorkspaceContext: workspaceContext,
}));
vi.mock('next/navigation', () => ({ useRouter: () => ({ push }) }));
vi.mock('@/lib/auth/client', () => ({
  useSession: () => ({ data: { user: { id: 'u1', email: 'a.duval@northwind.com' } } }),
}));

import ChooserPage from '@/app/workspaces/page';

function workspace(name: string, id = name): Workspace {
  return {
    id,
    name,
    created_at: '2026-08-01T09:00:00Z',
    updated_at: '2026-08-01T09:00:00Z',
  };
}

const IDLE = { isLoading: false, error: null, activeWorkspace: null, setActiveWorkspace: setActive };

beforeEach(() => {
  vi.clearAllMocks();
  workspaceContext.mockReturnValue({
    ...IDLE,
    workspaces: [workspace('Northwind Global'), workspace('Ashgrove Retail')],
  });
});

describe('the chooser exists, which is the whole defect it closes', () => {
  it('renders the decision rather than a 404', () => {
    // 📁 The design's own §01: "Four Entry rules dead-ended here… nothing drew
    // it." ⛔ `app/workspaces/` held only `none/page.tsx`.
    render(<ChooserPage />);

    expect(
      screen.getByRole('heading', { name: 'Choose an organization' }),
    ).toBeVisible();
  });

  it('says how many there are and that the choice is remembered', () => {
    // 📁 "You are a member of four. Signora will remember this choice on this
    // device, so you will not be asked again." ⚡ The count is a WORD in a
    // sentence — a digit mid-sentence reads as a metric.
    render(<ChooserPage />);

    expect(screen.getByText(/You are a member of two organizations/)).toBeVisible();
    expect(screen.getByText(/remember this choice on this device/)).toBeVisible();
  });

  it('enters the organization the customer picked', () => {
    render(<ChooserPage />);
    fireEvent.click(screen.getByRole('button', { name: /Northwind Global/ }));

    expect(setActive).toHaveBeenCalledWith('Northwind Global');
    expect(push).toHaveBeenCalledWith('/');
  });
});

describe('the states the design specifies', () => {
  it('never renders a failed read as an empty list', () => {
    // 🔴 **P-A.** ⛔ An empty list here says "you belong to nothing", which is
    // a sentence about somebody's access rather than about a request.
    workspaceContext.mockReturnValue({ ...IDLE, workspaces: [], error: new Error('nope') });

    render(<ChooserPage />);

    expect(screen.getByText(/could not be loaded/)).toBeVisible();
    expect(screen.queryByText(/not in an organization yet/)).toBeNull();
  });

  it('never claims a count while the answer is still unknown', () => {
    // ⛔ "You are a member of no organizations" during a load is a false
    // statement about somebody's access, and it is the loading cousin of P-A.
    workspaceContext.mockReturnValue({ ...IDLE, workspaces: [], isLoading: true });

    render(<ChooserPage />);

    expect(screen.queryByText(/You are a member of/)).toBeNull();
    expect(screen.getByText(/remember this choice on this device/)).toBeVisible();
  });

  it('answers an empty list rather than showing a blank column', () => {
    // ⚠️ The entry engine does not route here in this state — rule 10 sends a
    // person with no membership to /workspaces/none. ⛔ It is rendered anyway:
    // somebody who bookmarks this route and later leaves their last
    // organization arrives exactly here.
    workspaceContext.mockReturnValue({ ...IDLE, workspaces: [] });

    render(<ChooserPage />);

    expect(screen.getByText('You are not in an organization yet')).toBeVisible();
  });
});

describe('search appears above six, and names the query when nothing matches', () => {
  const many = Array.from({ length: 7 }, (_, i) => workspace(`Org ${i}`, `w${i}`));

  it('is absent for a list somebody can still scan', () => {
    // 📁 "Search appears above six workspaces." ⛔ Six, not five — the same
    // threshold the shell switcher uses, because it is the same judgement.
    render(<ChooserPage />);

    expect(screen.queryByRole('searchbox')).toBeNull();
  });

  it('appears once there are more than six', () => {
    workspaceContext.mockReturnValue({ ...IDLE, workspaces: many });

    render(<ChooserPage />);

    expect(screen.getByRole('searchbox')).toBeVisible();
  });

  it('names the query rather than saying no results', () => {
    // ⛔ The design bans "No workspaces found" outright.
    workspaceContext.mockReturnValue({ ...IDLE, workspaces: many });

    render(<ChooserPage />);
    fireEvent.change(screen.getByRole('searchbox'), { target: { value: 'zzz' } });

    expect(screen.getByText(/No organization matches “zzz”/)).toBeVisible();
  });

  it('clears the filter on Escape', () => {
    // 📁 "Esc clears the filter." ⚡ Behaviour, and it needs no field the
    // platform lacks.
    workspaceContext.mockReturnValue({ ...IDLE, workspaces: many });

    render(<ChooserPage />);
    const search = screen.getByRole('searchbox');
    fireEvent.change(search, { target: { value: 'zzz' } });
    fireEvent.keyDown(search, { key: 'Escape' });

    expect(screen.getByRole('list', { name: 'Your organizations' })).toBeVisible();
    expect(screen.queryByText(/No organization matches/)).toBeNull();
  });
});

describe('what it deliberately does not say', () => {
  it('never names an organization the person cannot see', () => {
    // 📁 The design's banned list: "any message that names a workspace the
    // person cannot see." ⛔ So the footer asks them to ask somebody, and
    // names nothing.
    render(<ChooserPage />);

    expect(
      screen.getByText(/Expecting an organization that is not here\? Ask an administrator/),
    ).toBeVisible();
  });

  it('uses the customer’s word rather than the platform’s', () => {
    // 🔴 [C-1517](../../../docs/LANE_COORDINATION.md) — the design's verbatim
    // copy says *workspace*, ADR-0034 assigns that to the platform, and the
    // shipped switcher already says *organization*. ⛔ Two surfaces disagreeing
    // about what the thing is called is the defect this asserts against.
    const { container } = render(<ChooserPage />);
    const text = (container.textContent ?? '').toLowerCase();

    expect(text).not.toContain('workspace');
    expect(text).toContain('organization');
  });

  it('says who is signed in, because this screen is reached on shared machines', () => {
    // 🔴 **Found by looking at it rendered, not by an assertion.** 📁 The
    // design's WS-B header carries the product mark and the person's address.
    // ⛔ Somebody arriving here after an SSO redirect, or on a shared laptop,
    // cannot otherwise tell whose organizations these are.
    render(<ChooserPage />);

    expect(screen.getByText('a.duval@northwind.com')).toBeVisible();
  });

  it('abbreviates a name the same way the rail does', () => {
    // ⚡ One implementation, shared — two would eventually render `NG` in the
    // rail and `NO` here for one organization.
    render(<ChooserPage />);
    const row = screen.getByRole('button', { name: /Northwind Global/ });

    expect(within(row).getByText('NG')).toBeInTheDocument();
  });

  it('🔴 focus lands on the heading, never on the search field', () => {
    /**
     * 📁 **`2.4.3`**: *"WS-B places focus on the h1 on load, **not the search
     * field**, so the list is announced before the control."*
     *
     * ⛔ **The search field carried `autoFocus`**, so a screen-reader user
     * arrived inside a filter for a list they had not been told existed —
     * ⚡ **and the sentence under the heading, *"you are a member of four"*,
     * is the fact that makes a filter make sense.**
     */
    workspaceContext.mockReturnValue({
      ...IDLE,
      workspaces: Array.from({ length: 9 }, (_, i) => workspace(`Org ${i + 1}`)),
    });
    render(<ChooserPage />);

    const heading = screen.getByRole('heading', { name: 'Choose an organization' });
    expect(heading).toHaveFocus();
    // ⚡ **The vacuity half**: the search field must EXIST at this count, or
    // the assertion above passes for the wrong reason.
    expect(screen.getByRole('searchbox')).toBeInTheDocument();
    expect(screen.getByRole('searchbox')).not.toHaveFocus();
  });

  it('⛔ and `autoFocus` is not on the field, which the render above CANNOT prove', () => {
    /**
     * 🔴 **Fire-tested, and the first version of the guard above did not
     * fail.** ⚡ **Restoring `autoFocus` left the suite green**, because jsdom
     * does not honour it on a React-rendered input and the effect that focuses
     * the heading runs afterwards either way.
     *
     * ⛔ **So the render proves the heading half and nothing about the other
     * half** — 📁 the repository's own rule, one register over: *a guard that
     * cannot fail is documentation pretending to be code.*
     *
     * ✅ **A source read CAN fail**, which is why the second half is asserted
     * here instead of pretended above. ⚠️ **Narrow on purpose**: it bans the
     * attribute in this one file, not everywhere — `autoFocus` is correct on a
     * dialog's first field and this is not a rule about dialogs.
     */
    const source = readFileSync(
      join(process.cwd(), 'app/workspaces/page.tsx'),
      'utf8',
    );
    expect(source).not.toContain('autoFocus');
    // ⚡ **The vacuity half**: the file must still be the one that renders the
    // search field, or an empty read would satisfy the assertion above.
    expect(source).toContain('type="search"');
  });

  it('⛔ the filter appears ABOVE six organizations, not at six', () => {
    /**
     * 📁 *"Search appears **above 6 memberships**"* — ⚡ which is seven.
     * ⚠️ **The switcher already used `>` and this used `>=`**, so the two
     * surfaces disagreed about one word.
     */
    workspaceContext.mockReturnValue({
      ...IDLE,
      workspaces: Array.from({ length: 6 }, (_, i) => workspace(`Org ${i + 1}`)),
    });
    const six = render(<ChooserPage />);
    expect(screen.queryByRole('searchbox')).toBeNull();
    six.unmount();

    workspaceContext.mockReturnValue({
      ...IDLE,
      workspaces: Array.from({ length: 7 }, (_, i) => workspace(`Org ${i + 1}`)),
    });
    render(<ChooserPage />);
    expect(screen.getByRole('searchbox')).toBeInTheDocument();
  });
});
