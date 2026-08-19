/**
 * **Home resolves a composition and renders it** —
 * [TASK-1405](../../../docs/BACKLOG.md), the route half.
 *
 * 🔴 **The property worth protecting is that Home ALWAYS renders.** 📁 The
 * design: *"a composition always resolves, so Home always renders"* — ⛔ **and
 * the second property is that it renders no card the platform has not
 * published.**
 */
import { render, screen } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { beforeEach, describe, expect, it, vi } from 'vitest';

const workspace = vi.hoisted(() => vi.fn());
/**
 * ⚠️ **`targets` is gone and that is the point of this rewrite.** 🔴 Home used to
 * decide rule 1 from the target-account version; 📁 the Home document's rule 1 is
 * *"no integration has ever completed a sync"*, **which is a different question**
 * — a workspace can declare no target accounts and be fully connected.
 */
const viewerRole = vi.hoisted(() => vi.fn());
const cardsFor = vi.hoisted(() => vi.fn());
const integrations = vi.hoisted(() => vi.fn());
/**
 * ⚠️ **`accounts` is gone and that is deliberate.** 🔴 Home's scope line used to
 * count `AccountAttention` rows; the product owner ruled that read out of Home
 * on 2026-08-17, and 📁 the registry's dependency for `card.attention` is
 * *"signals + deals"*. **The open signal queue is the signals half, and the
 * scope line and the card now read the same list.**
 */
const triage = vi.hoisted(() => vi.fn());
const statedRole = vi.hoisted(() => vi.fn());
/**
 * ⚡ **Home's activation state** — 📁 states 01, 03, 04 and 14 all read it.
 * ⚠️ **Fourth time this file has needed a new mock as Home grew a read**, which
 * is the test doing its job: it renders the REAL Home against mocked
 * boundaries, so a new dependency cannot arrive silently.
 */
const activationState = vi.hoisted(() => vi.fn());
/** ⚡ **State 05's second half** — 📁 *"record count is zero"*. */
const accountsCount = vi.hoisted(() => vi.fn());
/** ⚡ **State 08's page half** — what the cards reported. */
const outcomes = vi.hoisted(() => vi.fn());
/** ⚡ **Hierarchy 2** — what `POST /workspaces/{id}/entry` answered. */
const recordEntry = vi.hoisted(() => vi.fn());
/** ⚡ **§10** — what the Customise drawer saved. */
const chooseLayout = vi.hoisted(() => vi.fn());

vi.mock('@/lib/state/workspace-provider', () => ({ useWorkspaceContext: workspace }));
vi.mock('@/lib/query/hooks/team', () => ({
  useViewerRole: viewerRole,
  // ⚡ **State 09's panel names the approvers** — the workspace's owners.
  useWorkspaceMembers: () => ({ data: { items: [] } }),
}));
vi.mock('@/lib/home/cards', async () => {
  const actual = await vi.importActual<Record<string, unknown>>('@/lib/home/cards');
  return { ...actual, cardsFor };
});
vi.mock('@/lib/auth/client', () => ({
  useSession: () => ({ data: { user: { id: 'u1', name: 'Aurélie Fontaine' } } }),
}));
// ⚡ **The first-run overlay reads a preference** — [TASK-1424]. ⛔ Mocked at the
// same boundary this file already mocks the other reads at, **and returning
// *dismissed* keeps these tests about the COMPOSITION**: an overlay in the
// output would make every assertion below answer a question it was not asking.
// ⚡ **The activation progress line reads the connection set** — [TASK-1424].
// ⚠️ **Third time this file has needed a new mock as Home grew a read**, and
// that is the test doing its job: it renders the REAL Home against mocked
// boundaries, **so a new dependency cannot arrive silently.**
vi.mock('@/lib/query/hooks/integrations', () => ({ useIntegrations: integrations }));
vi.mock('@/lib/query/hooks/triage', () => ({ useWorkspaceTriage: triage }));
vi.mock('@/lib/query/hooks/home', () => ({
  useStatedRole: statedRole,
  useActivationState: activationState,
}));
vi.mock('@/lib/query/hooks/accounts-count', () => ({ useAccountsCount: accountsCount }));
vi.mock('@/components/home/card-outcomes', async () => {
  const actual = await vi.importActual<Record<string, unknown>>('@/components/home/card-outcomes');
  return { ...actual, useCardOutcomes: outcomes };
});
vi.mock('@/lib/query/hooks/preferences', () => ({
  // ⚡ **`setup_complete_seen: false` is *told nobody yet*** — 📁 state 04's strip
  // is silent until the preference is READ, so omitting the field here would
  // hide it for a reason that has nothing to do with the state under test.
  usePreferences: () => ({
    data: {
      first_run_dismissed: true,
      invite_hidden: false,
      setup_complete_seen: false,
      // ⚡ **Never customised by default** — 📁 an absent key renders the
      // registry's own order, which is what every other test here assumes.
      home_layout: {},
    },
  }),
  useDismissFirstRun: () => ({ mutate: () => {}, isPending: false }),
  useSkipInvite: () => ({ mutate: () => {}, isPending: false }),
  // ⚡ **State 04's strip records that it was shown** — 📁 *"exactly once"*.
  useAcknowledgeSetupComplete: () => ({ mutate: () => {}, isPending: false }),
  /**
   * ⚡ **Hierarchy 2's strip records the entry and reads the answer back** — 📁
   * Entry rule 12. ⛔ **`first_entry_today: false` by default**, so the strip is
   * absent unless a test is about it: an unrelated assertion must not have to
   * account for a four-second courtesy appearing above the greeting.
   */
  useRecordEntry: () => ({ mutateAsync: recordEntry, isPending: false }),
  /** ⚡ **§10's *Customise* drawer writes one composition's arrangement.** */
  useChooseHomeLayout: () => ({ mutate: chooseLayout, isPending: false }),
  // ⚡ **The switcher writes this** — 📁 rule 2's input, and [C-1530](../../../docs/LANE_COORDINATION.md).
  useChangePreferences: () => ({ mutate: () => {}, isPending: false }),
}));

import { Home } from '@/app/(app)/w/[workspace]/home/home';

/**
 * ⚡ **`connected` is rule 1's input** — 📁 *"no integration has ever completed a
 * sync."* **`false` resolves activation; `true` falls through to rules 2–5.**
 */
function ready(connected: boolean) {
  workspace.mockReturnValue({
    activeWorkspace: { id: 'w1', name: 'Northwind' },
    workspaces: [{ id: 'w1', name: 'Northwind' }],
    isLoading: false,
    error: null,
  });
  integrations.mockReturnValue({
    data: connected
      ? [{ integration: 'salesforce', capabilities: [], connectable: true, working: true, needs_attention: false, connections: [{ id: 'c1', connected_at: null }] }]
      : [],
    isPending: false,
    isError: false,
    refetch: () => {},
  });
}

/**
 * 📁 **What activation reports**, for the states that read it.
 *
 * ⚡ **`done`/`total` count BLOCKING cards only**, which is the design's own
 * rule — so `2 of 2` is state 04 and `0 of 2` is state 01.
 */
function activation({ done, total = 2 }: { done: number; total?: number }) {
  activationState.mockReturnValue({
    resolved: true,
    complete: {
      'connect-a-crm': done >= 1,
      'connect-calls': done >= 2,
      'invite-the-team': false,
    },
    progress: { done, total, optional: 1 },
    inviteHidden: false,
  });
}

beforeEach(() => {
  workspace.mockReset();
  integrations.mockReset();
  viewerRole.mockReturnValue({ role: 'owner', resolved: true });
  triage.mockReturnValue({ data: { items: [] }, isPending: false, isError: false, refetch: () => {} });
  // 📁 **Rule 5's case by default** — *"anything else… the default and the most
  // common outcome"*. Individual tests state a role where that is the subject.
  statedRole.mockReturnValue({ data: null });
  // ⚡ **The real registry is empty**, which is what ships; individual tests
  // stub a contribution where the point is what Home does with one.
  cardsFor.mockReturnValue([]);
  // ⚡ **Nothing connected by default**, matching `ready(false)` — individual
  // tests state a completion where that is the subject.
  activation({ done: 0 });
  // ⚡ **A book with records by default**, so state 05's strip is absent unless a
  // test asks for it. ⛔ `0` is a real answer and is the subject of its own test.
  accountsCount.mockReturnValue({ data: { total: 41 } });
  // ⛔ **Nothing failed by default**, so the page-level line is absent unless a
  // test is about it.
  outcomes.mockReturnValue({ failed: 0, retryAll: () => {}, report: () => {}, forget: () => {} });
  recordEntry.mockReset();
  recordEntry.mockResolvedValue({ first_entry_today: false, role_change: null });
  chooseLayout.mockReset();
});

describe('🔴 Home always renders', () => {
  it('✅ a workspace that has declared nothing gets Activation', () => {
    ready(false);

    render(<Home />);

    // 📁 *"Any role, empty workspace"* — ⚡ **emptiness wins over role**, which
    // is the resolver's own ordering and not this screen's.
    expect(screen.getByTestId('home')).toHaveAttribute('data-composition', 'activation');
    // ⚠️ **The question moved.** 📁 Home's greeting is *"name, date, and a count"*
    // — the composition is NAMED on the scope line, and *"How do I begin?"* is the
    // question the design asks in its own prose rather than on the screen.
    expect(screen.getByText(/Activation/)).toBeInTheDocument();
  });

  /**
   * 🔴 **This asserted `activation` and the Home document reversed it.**
   *
   * ⚠️ **The old reasoning was sound when written**: no primary role existed, so
   * picking one of the other three would have been inventing what a person is.
   * ⛔ **But 📁 rule 5 makes SELLER the default** — *"anything else… the default
   * and the most common outcome"* — **and state 04 forbids a fully activated
   * workspace rendering a setup sequence.**
   *
   * ✅ **And the role now exists**: onboarding screen `05` collects it.
   */
  it('🔴 a connected workspace with no stated role gets SELLER, not activation', () => {
    ready(true);

    render(<Home />);

    expect(screen.getByTestId('home')).toHaveAttribute('data-composition', 'seller');
  });

  it('📁 rule 3 · a revenue leader gets the executive composition', () => {
    ready(true);
    statedRole.mockReturnValue({ data: 'revenue_leader' });

    render(<Home />);

    expect(screen.getByTestId('home')).toHaveAttribute('data-composition', 'executive');
  });

  it('🔴 rule 1 outranks rule 3 — P-01, and an executive still gets activation', () => {
    // 📁 *"Rendering an empty executive dashboard to an executive is the worst
    // first impression available."*
    ready(false);
    statedRole.mockReturnValue({ data: 'revenue_leader' });

    render(<Home />);

    expect(screen.getByTestId('home')).toHaveAttribute('data-composition', 'activation');
  });

  /**
   * 📁 **State 07 — *"the greeting and scope line render immediately from session
   * data… Never skeletonised."***
   *
   * ⛔ **Home used to return a page-level *"Resolving your home…"***, which is the
   * full-page placeholder the design refuses.
   */
  it('✅ the greeting is real while the reads are still in flight', () => {
    workspace.mockReturnValue({
      activeWorkspace: { id: 'w1', name: 'Northwind' },
      workspaces: [],
      isLoading: false,
      error: null,
    });
    integrations.mockReturnValue({ data: undefined, isPending: true, isError: false, refetch: () => {} });

    render(<Home />);

    // ⚡ **The name is there before any card can be.**
    expect(screen.getByRole('heading', { level: 1 })).toHaveTextContent(/Aurélie/);
    // ⛔ **And the count is absent rather than zero** — 📁 *"never shown as 0
    // while loading."*
    expect(screen.queryByText(/0 things need you/)).not.toBeInTheDocument();
  });

  /**
   * 🔴 **[P-A](../../../docs/DOMAIN_DISCOVERY_REGISTER.md) decides which HOME a
   * customer sees, not merely how much of it.**
   *
   * ⛔ **A failed read looks exactly like an empty workspace**, and an empty
   * workspace resolves Activation — **so an established customer would be shown
   * *"How do I begin?"* because a request failed.**
   */
  it('⛔ a failed read says so rather than resolving the wrong composition', () => {
    workspace.mockReturnValue({
      activeWorkspace: { id: 'w1', name: 'Northwind' },
      workspaces: [],
      isLoading: false,
      error: null,
    });
    integrations.mockReturnValue({ data: undefined, isPending: false, isError: true, refetch: () => {} });

    render(<Home />);

    // ⚡ **`StatedAbsence` names the subject twice — once as the title and once
    // in the sentence** — so this asserts that it is stated, not how many times.
    expect(screen.getAllByText(/could not load your home/i).length).toBeGreaterThan(0);
    expect(screen.queryByTestId('home')).not.toBeInTheDocument();
  });

  /**
   * 📁 **State 12 — *"the activation registry returned zero cards."***
   *
   * ⛔ **The design says what must NOT happen**: *"Never a progress bar at 0 of 0,
   * and never an empty activation composition."*
   */
  it('📁 an activation composition with no cards renders HM-COPY-11 and no progress bar', () => {
    ready(false);
    cardsFor.mockReturnValue([]);

    render(<Home />);

    expect(screen.getByText('Setup steps could not be loaded.')).toBeInTheDocument();
    // ⛔ **No progress bar**, which is the half a reader would misread as *nothing
    // to do* rather than *we could not ask*.
    expect(screen.queryByRole('progressbar')).not.toBeInTheDocument();
    expect(screen.queryByText(/0 of 0/)).not.toBeInTheDocument();
  });
});

describe('📁 Entry rule 21 — the role-change notice', () => {
  /**
   * 📁 *"Role changed since last session — Home, with a notice naming **what
   * changed and by whom**. The composition may differ from yesterday and **that
   * must not be silent**."*
   */
  it('🔴 says what changed and who changed it', async () => {
    ready(true);
    recordEntry.mockResolvedValue({
      first_entry_today: false,
      role_change: {
        previous_role: 'member',
        new_role: 'owner',
        changed_by: 'u2',
        changed_by_email: 'dana.reyes@northwind.example',
        at: '2026-08-19T08:00:00Z',
      },
    });

    render(<Home />);

    expect(await screen.findByTestId('role-change')).toBeVisible();
    expect(
      screen.getByText(/dana\.reyes@northwind\.example made you able to administer Signora\./),
    ).toBeVisible();
  });

  /**
   * ⚡ **The repository's own wording for the other direction** —
   * `components/team/history.tsx` publishes both sentences, and 📁 ADR-0034 is
   * why Home does not invent a second phrasing for one event.
   */
  it('uses the ratified sentence when somebody is moved to working accounts', async () => {
    ready(true);
    recordEntry.mockResolvedValue({
      first_entry_today: false,
      role_change: {
        previous_role: 'owner',
        new_role: 'member',
        changed_by: 'u2',
        changed_by_email: null,
        at: '2026-08-19T08:00:00Z',
      },
    });

    render(<Home />);

    // 📁 **D23's fallback** for an actor with no known address.
    expect(await screen.findByText(/Somebody moved you to working accounts\./)).toBeVisible();
  });

  /**
   * ⛔ **Silent on every ordinary arrival**, which is the overwhelming majority
   * of them.
   */
  it('⛔ and says nothing when nothing changed', async () => {
    ready(true);
    recordEntry.mockResolvedValue({ first_entry_today: false, role_change: null });

    render(<Home />);
    await screen.findByTestId('home');

    expect(screen.queryByTestId('role-change')).not.toBeInTheDocument();
  });

  /**
   * 🔴 **Independent of rule 12's strip.** ⚡ Rule 12 needs several memberships
   * and a first visit; ⛔ **rule 21 needs neither** — somebody whose role changed
   * must be told on a second visit, and in their only workspace.
   */
  it('🔴 shows on a return visit in a single-workspace account', async () => {
    workspace.mockReturnValue({
      activeWorkspace: { id: 'w1', name: 'Northwind' },
      workspaces: [{ id: 'w1', name: 'Northwind' }],
      isLoading: false,
      error: null,
    });
    integrations.mockReturnValue({ data: [], isPending: false, isError: false, refetch: () => {} });
    recordEntry.mockResolvedValue({
      first_entry_today: false,
      role_change: {
        previous_role: 'member',
        new_role: 'owner',
        changed_by: 'u2',
        changed_by_email: 'k.bruun@northwind.example',
        at: '2026-08-19T08:00:00Z',
      },
    });

    render(<Home />);

    expect(await screen.findByTestId('role-change')).toBeVisible();
    // ⛔ **And rule 11 still draws no confirmation strip.**
    expect(screen.queryByTestId('workspace-confirmation')).not.toBeInTheDocument();
  });
});

describe('📁 state 09 — the forbidden card', () => {
  /**
   * 📁 *"The card is **replaced in place** by a same-footprint panel naming the
   * missing permission and the approvers. **Never hidden** — hiding it makes
   * people think the capability is absent."*
   *
   * ⚡ **The design's example is `card.requests` and an analyst**, which has no
   * producer. 📁 **`policy.csv` grants `member:add` to `owner` alone**, so a
   * member who meets the activation composition is the same rule reaching the
   * card that does exist.
   */
  it('🔴 a member sees the panel where the card would be, not a gap', () => {
    ready(false);
    viewerRole.mockReturnValue({ role: 'member', resolved: true });
    cardsFor.mockReturnValue([
      { id: 'invite-the-team', title: 'Invite the team', module: 'x', requires: 'member:add' },
    ]);

    render(<Home />);

    // ⛔ **The card's own slot is still there** — `AC-H11`'s *"the same footprint
    // as the card it replaces"*.
    expect(screen.getByTestId('home').querySelector('[data-card="invite-the-team"]')).not.toBeNull();
    expect(screen.getByTestId('invite-the-team-forbidden')).toBeVisible();
  });

  /**
   * ⛔ **It names the permission and never the withheld data** — 📁 the design's
   * own rule for this panel, and `HM-COPY-08`'s shape.
   */
  it('🔴 names the permission in the customer\'s words, not a slug', () => {
    ready(false);
    viewerRole.mockReturnValue({ role: 'member', resolved: true });
    cardsFor.mockReturnValue([
      { id: 'invite-the-team', title: 'Invite the team', module: 'x', requires: 'member:add' },
    ]);

    render(<Home />);

    // ⚡ **Twice by design** — the panel's title names the permission and
    // `HM-COPY-08` repeats it in the sentence that also names the approvers.
    expect(screen.getAllByText(/Invite members permission/).length).toBeGreaterThan(0);
    expect(screen.getByText(/Approvers:/)).toBeVisible();
    // ⛔ **`member:add` is engineering's word** — ADR-0034 puts the translation
    // at the frontend edge.
    expect(screen.queryByText(/member:add/)).not.toBeInTheDocument();
  });

  it('⛔ and an owner sees the card itself', () => {
    ready(false);
    viewerRole.mockReturnValue({ role: 'owner', resolved: true });
    cardsFor.mockReturnValue([
      { id: 'invite-the-team', title: 'Invite the team', module: 'x', requires: 'member:add' },
    ]);

    render(<Home />);

    expect(screen.queryByTestId('invite-the-team-forbidden')).not.toBeInTheDocument();
  });
});

describe('📁 hierarchy 2 — the workspace confirmation strip, and state 13', () => {
  /**
   * 📁 **Entry rule 12**: *"Several memberships, last-used recorded and healthy.
   * Enter the last used. **The workspace strip confirms which for four
   * seconds.**"*
   */
  /**
   * ⚡ **Two memberships**, because rule 12 is *"several memberships"* and
   * `ready()`'s default is one — which is rule 11's case and draws no strip.
   */
  function severalWorkspaces() {
    workspace.mockReturnValue({
      activeWorkspace: { id: 'w1', name: 'Northwind' },
      workspaces: [
        { id: 'w1', name: 'Northwind' },
        { id: 'w2', name: 'Ashgrove' },
      ],
      isLoading: false,
      error: null,
    });
  }

  it('✅ confirms which organization on a first entry today', async () => {
    ready(true);
    severalWorkspaces();
    recordEntry.mockResolvedValue({ first_entry_today: true, role_change: null });

    render(<Home />);

    expect(await screen.findByTestId('workspace-confirmation')).toBeVisible();
    expect(screen.getByText('Northwind')).toBeVisible();
  });

  /**
   * 🔴 **State 13 · `state.returning`** — *"second or later entry on the same
   * calendar day in this workspace"* renders *"identical to state 06 with the
   * workspace confirmation strip suppressed. **Home does not congratulate people
   * for returning.**"*
   *
   * ⛔ **Suppressed, not replaced.** ⚡ There is no *"welcome back"* — the design
   * bans that phrase by name — so state 13 is the absence of a strip and nothing
   * else.
   */
  it('🔴 state 13 · says nothing at all on the second entry of the day', async () => {
    ready(true);
    severalWorkspaces();
    recordEntry.mockResolvedValue({ first_entry_today: false, role_change: null });

    render(<Home />);
    await screen.findByTestId('home');

    expect(screen.queryByTestId('workspace-confirmation')).not.toBeInTheDocument();
    // ⛔ **And nothing congratulates them either.**
    expect(screen.queryByText(/Welcome back/i)).not.toBeInTheDocument();
  });

  /**
   * 📁 **Entry rule 11**: *"Exactly one membership. Enter it. **No confirmation,
   * no picker, no interstitial.**"* ⚡ There is nothing to confirm when there was
   * never a choice.
   */
  it('⛔ and confirms nothing to somebody with one organization', async () => {
    workspace.mockReturnValue({
      activeWorkspace: { id: 'w1', name: 'Northwind' },
      workspaces: [{ id: 'w1', name: 'Northwind' }],
      isLoading: false,
      error: null,
    });
    integrations.mockReturnValue({
      data: [],
      isPending: false,
      isError: false,
      refetch: () => {},
    });
    recordEntry.mockResolvedValue({ first_entry_today: true, role_change: null });

    render(<Home />);
    await screen.findByTestId('home');

    expect(screen.queryByTestId('workspace-confirmation')).not.toBeInTheDocument();
  });

  /**
   * ⛔ **A failed entry record shows no strip.** ⚡ It is a courtesy, and guessing
   * *"probably your first visit"* is the one thing it must not do.
   */
  it('⛔ and stays silent when the entry could not be recorded', async () => {
    ready(true);
    severalWorkspaces();
    recordEntry.mockRejectedValue(new Error('down'));

    render(<Home />);
    await screen.findByTestId('home');

    expect(screen.queryByTestId('workspace-confirmation')).not.toBeInTheDocument();
  });
});

describe('📁 state 08, the page half — AC-H07', () => {
  /**
   * ⚡ **A real query client, because these tests need cards that RENDER.**
   *
   * ⛔ Every id with a renderer reads something of its own, and `rendered.length`
   * is half of Home's rule — so a card list with nothing in it cannot exercise
   * it. ✅ **The reads sit pending and the cards draw their skeletons**, which is
   * all this rule needs from them.
   */
  function renderHome() {
    const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
    return render(
      <QueryClientProvider client={client}>
        <Home />
      </QueryClientProvider>,
    );
  }

  /**
   * 📁 *"The composition never collapses. **If every card fails, the page states
   * that and offers one retry for all.**"*
   *
   * ⚡ **Home's RULE is what is asserted here** — the count itself is the
   * registry's, and `card-outcomes.test.tsx` asserts that. ⛔ Rendering real
   * cards to make them fail would test four other modules' reads on the way
   * past.
   */
  it('🔴 states it when every rendered card has failed', () => {
    ready(true);
    cardsFor.mockReturnValue([{ id: 'recents', title: 'Pick up where you left off' }]);
    outcomes.mockReturnValue({ failed: 1, retryAll: () => {}, report: () => {}, forget: () => {} });

    renderHome();

    expect(screen.getByTestId('home-all-failed')).toBeVisible();
    expect(screen.getByRole('button', { name: 'Retry all' })).toBeVisible();
  });

  /**
   * ⛔ **The composition never collapses.** ⚡ The page-level statement is
   * *added*, not substituted — which is what stops a total failure becoming a
   * blank page.
   */
  it('⛔ and the cards keep their own footprints underneath it', () => {
    ready(true);
    cardsFor.mockReturnValue([{ id: 'recents', title: 'Pick up where you left off' }]);
    outcomes.mockReturnValue({ failed: 1, retryAll: () => {}, report: () => {}, forget: () => {} });

    renderHome();

    expect(screen.getByTestId('home').querySelector('[data-card]')).not.toBeNull();
  });

  /**
   * 🔴 **`0 === 0` would have claimed total failure on a page that made no
   * request at all.** ⚡ A composition with nothing rendered is state 12 or the
   * designed empty state, and neither is a failure.
   */
  it('⛔ and never claims failure on a composition with no cards', () => {
    ready(true);
    cardsFor.mockReturnValue([]);
    outcomes.mockReturnValue({ failed: 0, retryAll: () => {}, report: () => {}, forget: () => {} });

    renderHome();

    expect(screen.queryByTestId('home-all-failed')).not.toBeInTheDocument();
  });

  /**
   * ⛔ **One working card is not total failure.** 📁 *"No sibling is affected"* —
   * the line must not appear while anything on the page still works.
   */
  it('⛔ and stays silent while one card still works', () => {
    ready(true);
    cardsFor.mockReturnValue([
      { id: 'recents', title: 'Pick up where you left off' },
      { id: 'integration-health', title: 'Integration health' },
    ]);
    outcomes.mockReturnValue({ failed: 1, retryAll: () => {}, report: () => {}, forget: () => {} });

    renderHome();

    expect(screen.queryByTestId('home-all-failed')).not.toBeInTheDocument();
  });
});

describe('⛔ no composition is drawn before it is resolved', () => {
  /**
   * 🔴 **Found in a browser, on a workspace created through the product.**
   *
   * 📁 Rule 1's input is a READ — *"has any integration ever completed a sync"* —
   * so until it lands the resolver falls through to rule 5. ⛔ **A brand-new
   * workspace's first paint was therefore the SELLER composition's cards,
   * replaced a moment later by the three activation steps.**
   *
   * 📁 **Two rules forbid it**: the prohibition table's *"no composition
   * substitution"*, and §09's *"each skeleton uses the card's declared height, so
   * **nothing reflows when data lands**"*.
   */
  it('🔴 draws no card while the activation read is in flight', () => {
    ready(false);
    integrations.mockReturnValue({
      data: undefined,
      isPending: true,
      isError: false,
      refetch: () => {},
    });
    cardsFor.mockReturnValue([{ id: 'recents', title: 'Pick up where you left off' }]);

    render(<Home />);

    expect(screen.getByTestId('home-resolving')).toBeInTheDocument();
    expect(screen.queryByTestId('home')?.querySelector('[data-card]')).toBeNull();
  });

  /**
   * ⛔ **And the scope line does not name a composition it does not know.** ⚡ Same
   * class of claim as rendering `0` for a count that has not arrived — 📁 *"never
   * shown as 0 while loading"*.
   */
  it('⛔ and names no composition until one is resolved', () => {
    ready(false);
    integrations.mockReturnValue({
      data: undefined,
      isPending: true,
      isError: false,
      refetch: () => {},
    });

    render(<Home />);

    expect(screen.getByText(/Northwind/)).toBeVisible();
    expect(screen.queryByText(/Seller|Activation|Executive|Operations/)).not.toBeInTheDocument();
  });
});

describe('📁 the activation greeting — states 01 and 03', () => {
  /**
   * 🔴 **The design ties the sentence to what is COMPLETE, not to the clock.**
   *
   * 📁 State 01 renders: *"Three activation cards, none complete, progress at 0
   * of 2. **Greeting reads 'Let us get Northwind Global connected'**."*
   *
   * ⛔ **A brand-new workspace was getting *"Good afternoon, Aurélie"***, which
   * is the data compositions' greeting and says nothing about what to do.
   */
  it('🔴 state 01 · nothing complete opens with the connection sentence, not the clock', () => {
    ready(false);
    activation({ done: 0 });

    render(<Home />);

    expect(
      screen.getByRole('heading', { level: 1, name: /Let us get Northwind connected/i }),
    ).toBeVisible();
    // ⛔ **The greeting is REPLACED, never appended to** — two openings in one
    // sentence is what the design's single line rules out.
    expect(screen.queryByText(/Good morning|Good afternoon|Good evening/)).not.toBeInTheDocument();
  });

  /**
   * 📁 **The estimate is omitted rather than invented.** ⛔ The activation rules
   * say it *"comes from measured p50 completion time, **not a guess**"*, and
   * nothing measures one — so a constant would be the guess the design forbids,
   * carrying the copy table's authority.
   */
  it('⛔ and states no time estimate, because nothing measures one', () => {
    ready(false);
    activation({ done: 0 });

    render(<Home />);

    expect(screen.queryByText(/about \d+ minutes/i)).not.toBeInTheDocument();
  });

  /**
   * 📁 State 03 — *"at least one blocking card complete, at least one
   * incomplete"* → `HM-COPY-03`, *"is nearly ready. Step 2 of 2"*.
   */
  it('📁 state 03 · one blocking step done reads "nearly ready"', () => {
    ready(false);
    activation({ done: 1 });

    render(<Home />);

    expect(
      screen.getByRole('heading', { level: 1, name: /Northwind is nearly ready\. Step 2 of 2/i }),
    ).toBeVisible();
  });

  /**
   * ⛔ **Every data composition greets by the clock.** ⚡ The activation sentence
   * belongs to the activation composition and nowhere else — a seller who
   * finished setup last March must not be told *"let us get you connected"*.
   */
  it('⛔ and a data composition is never given the activation sentence', () => {
    ready(true);
    activation({ done: 2 });

    render(<Home />);

    expect(screen.queryByText(/Let us get|nearly ready/i)).not.toBeInTheDocument();
    expect(screen.getByText(/Good morning|Good afternoon|Good evening/)).toBeVisible();
  });
});

describe('📁 state 04 — the setup-complete strip', () => {
  /**
   * 📁 *"A one-time strip states that setup is finished and what changed."*
   * **`AC-H03`** — *"the next render is the role composition, with the strip
   * shown exactly once."*
   */
  it('✅ appears on the role composition once every blocking step is done', () => {
    ready(true);
    activation({ done: 2 });

    render(<Home />);

    expect(screen.getByTestId('setup-complete')).toBeVisible();
    expect(
      screen.getByText(/Setup is complete\. Home now shows your accounts, deals and signals\./),
    ).toBeVisible();
  });

  /**
   * ⛔ **Never on the activation composition.** 📁 State 04's own render is
   * *"composition switches to SELLER, OPERATIONS or EXECUTIVE"* — a strip drawn
   * beside the steps would announce completion next to the work it completed.
   */
  it('⛔ and never beside the steps it completed', () => {
    ready(false);
    activation({ done: 2 });

    render(<Home />);

    expect(screen.queryByTestId('setup-complete')).not.toBeInTheDocument();
  });

  it('⛔ and not while blocking work remains', () => {
    ready(true);
    activation({ done: 1 });

    render(<Home />);

    expect(screen.queryByTestId('setup-complete')).not.toBeInTheDocument();
  });
});

describe('📁 state 05 — no meaningful business data', () => {
  /**
   * 📁 *"Sync succeeded AND record count is zero. **Distinct from state 06b.**"*
   *
   * ⛔ **Contract item 4 makes sharing one component a violation**, and **P-02**
   * gives the reason: conflating them *"sends someone to review a pipeline that
   * does not exist"*.
   */
  it('🔴 names the source that returned nothing', () => {
    ready(true);
    activation({ done: 2 });
    accountsCount.mockReturnValue({ data: { total: 0 } });

    render(<Home />);

    expect(screen.getByText(/Salesforce is connected/i)).toBeVisible();
    expect(screen.getByText(/Signora needs records to work from/i)).toBeVisible();
    // ⛔ **`AC-H04`** — *"HM-COPY-06 does not appear anywhere in the DOM."*
    expect(screen.queryByText(/Nothing needs you this morning/i)).not.toBeInTheDocument();
  });

  /**
   * ⛔ **A workspace with records is state 06**, however thin it looks. ⚡ The
   * design's test is *zero exactly*.
   */
  it('⛔ and says nothing once the workspace holds a single record', () => {
    ready(true);
    activation({ done: 2 });
    accountsCount.mockReturnValue({ data: { total: 1 } });

    render(<Home />);

    expect(screen.queryByText(/Signora needs records to work from/i)).not.toBeInTheDocument();
  });

  /**
   * ⛔ **Silent while the count is unknown.** ⚡ Accusing a working integration of
   * emptiness on a slow connection is the one thing this strip must not do — it
   * is the strip a person acts on by opening their CRM.
   */
  it('⛔ and stays silent while the count is unread', () => {
    ready(true);
    activation({ done: 2 });
    accountsCount.mockReturnValue({ data: undefined });

    render(<Home />);

    expect(screen.queryByText(/Signora needs records to work from/i)).not.toBeInTheDocument();
  });

  /**
   * ⛔ **Not on activation**, which the design excludes by name — *"setup is
   * complete"*. ⚡ A workspace that has connected nothing has no source to name.
   */
  it('⛔ and never on the activation composition', () => {
    ready(false);
    activation({ done: 0 });
    accountsCount.mockReturnValue({ data: { total: 0 } });

    render(<Home />);

    expect(screen.queryByText(/Signora needs records to work from/i)).not.toBeInTheDocument();
  });
});

describe('⛔ it renders no card the platform has not published', () => {
  // ⚡ **A connected workspace**, so the composition is a data one and the
  // *nothing composed* branch is the one under test rather than state 12.
  beforeEach(() => ready(true));
  /**
   * 🔴 **The registry is empty and Home says so in the customer's words.**
   *
   * 📁 [§20c](../../../CLAUDE.md): *"screens without a shipped module behind
   * them ship a designed empty state."* ⛔ **Never a placeholder card, never a
   * count of cards that do not exist, never *coming soon*.**
   */
  it('✅ a designed empty state, naming what would fill it', () => {
    ready(true);

    render(<Home />);

    expect(screen.getByText(/nothing to put on your home yet/i)).toBeInTheDocument();
    expect(screen.queryByText(/coming soon/i)).not.toBeInTheDocument();
  });

  /**
   * 🔴 **A card the platform HAS published, and Home still cannot draw.**
   *
   * ⚠️ **The first version of this test could not fail.** ⛔ **`cardsFor`
   * already returns nothing from an empty registry, so asserting *no cards
   * render* asserted somebody else's guarantee** — and the renderer filter this
   * file adds was [§2](../../../CLAUDE.md)'s Decorative Logic: **removing it
   * changed nothing.** ✅ **Found by fire-testing, and fixed by testing the
   * seam rather than the outcome.**
   *
   * ⚡ **So the registry is stubbed with a real contract.** 📁 `CardContract`
   * carries `id`, `title`, `module` and `requires` — **and no component** —
   * so **a registered card with nothing to render it must be SKIPPED**, never
   * drawn as a title with a blank body.
   */
  it('🔴 a registered card with no renderer is skipped, not drawn empty', () => {
    /**
     * ⚠️ **The example has now gone stale TWICE, and the RULE has not moved.**
     * ⛔ It was `connect-a-crm` until that gained a renderer
     * ([TASK-1424](../../../docs/BACKLOG.md)); it was then `top-risks`, **which
     * gained one the moment the risk/opportunity posture was found to be
     * published already** — `scoring_model@1.json`, one module over from where
     * the earlier audit looked.
     *
     * 🔴 **Twice is a pattern, so the third example is chosen so it cannot
     * recur**: 📁 **`forecast-vs-plan` can NEVER acquire a renderer.**
     * `buying_score_engine` states in two files that *it does not forecast a
     * purchase*, so `forecast.committed` is refused by domain law rather than
     * merely unbuilt — [C-1528](../../../docs/LANE_COORDINATION.md).
     *
     * ⚡ **An example that is absent by decision outlives every example that is
     * absent by schedule.**
     */
    cardsFor.mockReturnValue([
      { id: 'forecast-vs-plan', title: 'Forecast vs plan', module: 'opportunity_engine', requires: null },
    ]);

    render(<Home />);

    expect(document.querySelectorAll('[data-card]')).toHaveLength(0);
    // ⛔ **Its title must not appear either** — a heading with no card under it
    // is the placeholder TASK-1433 refused.
    expect(screen.queryByText('Forecast vs plan')).not.toBeInTheDocument();
    expect(screen.getByText(/nothing to put on your home yet/i)).toBeInTheDocument();
  });

  /**
   * 📁 *"not a separate screen with its own layout, navigation or breadcrumb."*
   * ⛔ **Home states which composition it is and stops** — a second navigation
   * here would make Home a destination rather than a slot.
   */
  it('⛔ it is a slot, not a screen — no navigation of its own', () => {
    ready(false);

    render(<Home />);

    expect(screen.queryByRole('navigation')).not.toBeInTheDocument();
  });
});
