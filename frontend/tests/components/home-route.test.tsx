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
const targets = vi.hoisted(() => vi.fn());
const viewerRole = vi.hoisted(() => vi.fn());
const cardsFor = vi.hoisted(() => vi.fn());

vi.mock('@/lib/state/workspace-provider', () => ({ useWorkspaceContext: workspace }));
vi.mock('@/lib/query/hooks/commercial', () => ({ useTargetAccounts: targets }));
vi.mock('@/lib/query/hooks/team', () => ({ useViewerRole: viewerRole }));
vi.mock('@/lib/home/cards', async () => {
  const actual = await vi.importActual<Record<string, unknown>>('@/lib/home/cards');
  return { ...actual, cardsFor };
});
vi.mock('@/lib/auth/client', () => ({ useSession: () => ({ data: { user: { id: 'u1' } } }) }));
// ⚡ **The first-run overlay reads a preference** — [TASK-1424]. ⛔ Mocked at the
// same boundary this file already mocks the other reads at, **and returning
// *dismissed* keeps these tests about the COMPOSITION**: an overlay in the
// output would make every assertion below answer a question it was not asking.
vi.mock('@/lib/query/hooks/preferences', () => ({
  usePreferences: () => ({ data: { first_run_dismissed: true } }),
  useDismissFirstRun: () => ({ mutate: () => {}, isPending: false }),
}));

import { Home } from '@/app/(app)/w/[workspace]/home/home';

function ready(version: number) {
  workspace.mockReturnValue({
    activeWorkspace: { id: 'w1', name: 'Northwind' },
    workspaces: [{ id: 'w1', name: 'Northwind' }],
    isLoading: false,
    error: null,
  });
  targets.mockReturnValue({
    data: { version, accounts: [], updated_at: null, updated_by: null },
    isPending: false,
    isError: false,
  });
}

beforeEach(() => {
  workspace.mockReset();
  targets.mockReset();
  viewerRole.mockReturnValue({ role: 'owner', resolved: true });
  // ⚡ **The real registry is empty**, which is what ships; individual tests
  // stub a contribution where the point is what Home does with one.
  cardsFor.mockReturnValue([]);
});

describe('🔴 Home always renders', () => {
  it('✅ a workspace that has declared nothing gets Activation', () => {
    ready(0);

    render(<Home />);

    // 📁 *"Any role, empty workspace"* — ⚡ **emptiness wins over role**, which
    // is the resolver's own ordering and not this screen's.
    expect(screen.getByTestId('home')).toHaveAttribute('data-composition', 'activation');
    expect(screen.getByText(/How do I begin\?/)).toBeInTheDocument();
  });

  /**
   * 🔴 **Every session resolves to Activation today, and that is honest rather
   * than a bug.**
   *
   * 📁 The design resolves a composition from *"the person's primary role"* and
   * ⛔ **`Membership.role` is `owner | member`** — the platform publishes no
   * primary role at all. ⚡ **So a workspace WITH data still resolves to
   * Activation**, because picking one of the other three would be inventing
   * what a person is.
   */
  it('🔴 and a workspace with data still does, because no role is published', () => {
    ready(3);

    render(<Home />);

    expect(screen.getByTestId('home')).toHaveAttribute('data-composition', 'activation');
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
    targets.mockReturnValue({ data: undefined, isPending: false, isError: true });

    render(<Home />);

    // ⚡ **`StatedAbsence` names the subject twice — once as the title and once
    // in the sentence** — so this asserts that it is stated, not how many times.
    expect(screen.getAllByText(/could not load your home/i).length).toBeGreaterThan(0);
    expect(screen.queryByTestId('home')).not.toBeInTheDocument();
  });

  it('⛔ and nothing is resolved while the read is still in flight', () => {
    workspace.mockReturnValue({
      activeWorkspace: { id: 'w1', name: 'Northwind' },
      workspaces: [],
      isLoading: false,
      error: null,
    });
    targets.mockReturnValue({ data: undefined, isPending: true, isError: false });

    render(<Home />);

    // ⚠️ **Guessing either way would flash the wrong Home at somebody.**
    expect(screen.queryByTestId('home')).not.toBeInTheDocument();
  });
});

describe('⛔ it renders no card the platform has not published', () => {
  /**
   * 🔴 **The registry is empty and Home says so in the customer's words.**
   *
   * 📁 [§20c](../../../CLAUDE.md): *"screens without a shipped module behind
   * them ship a designed empty state."* ⛔ **Never a placeholder card, never a
   * count of cards that do not exist, never *coming soon*.**
   */
  it('✅ a designed empty state, naming what would fill it', () => {
    ready(0);

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
     * ⚠️ **The example had to change and the RULE did not** —
     * [TASK-1424](../../../docs/BACKLOG.md). ⛔ This used `connect-a-crm`,
     * **which now has a renderer**, so the test was asserting that a card which
     * DOES draw does not draw. ⚡ **A stale example turns a live guard into a
     * false one**, and it fails loudly rather than quietly, which is why it was
     * caught.
     *
     * ✅ **`top-risks` is the honest stand-in**: it is a real `CardId`, it is
     * placed in the executive composition, and 📁 **nothing renders it** —
     * *"ranked risks with the population each was derived from"* has no read,
     * measured in [TASK-1425](../../../docs/BACKLOG.md).
     */
    ready(0);
    cardsFor.mockReturnValue([
      { id: 'top-risks', title: 'Top risks', module: 'signal_engine', requires: null },
    ]);

    render(<Home />);

    expect(document.querySelectorAll('[data-card]')).toHaveLength(0);
    // ⛔ **Its title must not appear either** — a heading with no card under it
    // is the placeholder TASK-1433 refused.
    expect(screen.queryByText('Top risks')).not.toBeInTheDocument();
    expect(screen.getByText(/nothing to put on your home yet/i)).toBeInTheDocument();
  });

  /**
   * 📁 *"not a separate screen with its own layout, navigation or breadcrumb."*
   * ⛔ **Home states which composition it is and stops** — a second navigation
   * here would make Home a destination rather than a slot.
   */
  it('⛔ it is a slot, not a screen — no navigation of its own', () => {
    ready(0);

    render(<Home />);

    expect(screen.queryByRole('navigation')).not.toBeInTheDocument();
  });
});
