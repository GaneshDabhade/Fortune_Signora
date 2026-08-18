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

vi.mock('@/lib/state/workspace-provider', () => ({ useWorkspaceContext: workspace }));
vi.mock('@/lib/query/hooks/team', () => ({ useViewerRole: viewerRole }));
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
vi.mock('@/lib/query/hooks/preferences', () => ({
  // ⚡ **`setup_complete_seen: false` is *told nobody yet*** — 📁 state 04's strip
  // is silent until the preference is READ, so omitting the field here would
  // hide it for a reason that has nothing to do with the state under test.
  usePreferences: () => ({
    data: { first_run_dismissed: true, invite_hidden: false, setup_complete_seen: false },
  }),
  useDismissFirstRun: () => ({ mutate: () => {}, isPending: false }),
  useSkipInvite: () => ({ mutate: () => {}, isPending: false }),
  // ⚡ **State 04's strip records that it was shown** — 📁 *"exactly once"*.
  useAcknowledgeSetupComplete: () => ({ mutate: () => {}, isPending: false }),
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
