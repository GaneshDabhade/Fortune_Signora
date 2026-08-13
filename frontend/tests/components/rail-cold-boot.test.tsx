/**
 * **§16 tier one — the frame is the same on every route, including the first**
 * — [TASK-1471](../../../docs/BACKLOG.md).
 *
 * > 📁 ***"Cold boot paints the shell chrome immediately and skeletons only the
 * > content region — **the frame is never blank, because the frame is the same
 * > on every route**."***
 *
 * 🔴 **The property is that the rail's DESTINATION COUNT does not change while
 * the workspace read is in flight.** ⛔ **Measured before this row: 6 → 7 → 8
 * links across one cold boot**, because `Home` was dropped until the workspace
 * arrived — **and `Home` is the rail's first entry, so everything below it
 * moved.**
 */
import { render, screen } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

const workspace = vi.hoisted(() => vi.fn());
vi.mock('@/lib/state/workspace-provider', () => ({ useWorkspaceContext: workspace }));
vi.mock('@/components/shell/shortcuts-reference', () => ({
  useShortcutsReference: () => ({ open: vi.fn() }),
}));

import { Navigation, resolved } from '@/components/shell/navigation';

const ACTIVE = { id: 'w1', name: 'Northwind', created_at: '', updated_at: '' };

/** ⚡ **The three states a cold boot passes through**, named as the shell names them. */
function inFlight() {
  workspace.mockReturnValue({ activeWorkspace: null, workspaces: [], isLoading: true });
}
function settledWithWorkspace() {
  workspace.mockReturnValue({ activeWorkspace: ACTIVE, workspaces: [ACTIVE], isLoading: false });
}
function settledWithNone() {
  workspace.mockReturnValue({ activeWorkspace: null, workspaces: [], isLoading: false });
}

function rows() {
  const rail = screen.getByRole('navigation', { name: 'Primary' });
  // ⚡ **Every destination row, whatever it is rendered as** — a link, or a
  // place held open. ⛔ **Counting only links is what let the defect hide.**
  return rail.querySelectorAll('a[href^="/"], [data-pending="true"]');
}

beforeEach(() => workspace.mockReset());

describe('🔴 the frame does not change shape while the workspace resolves', () => {
  it('🔴 the same number of destinations before and after the read lands', () => {
    inFlight();
    const { unmount } = render(<Navigation role="owner" roleKnown />);
    const during = rows().length;
    unmount();

    settledWithWorkspace();
    render(<Navigation role="owner" roleKnown />);
    const after = rows().length;

    // ⛔ **This is the assertion the defect failed.** ⚠️ **It was 7 then 8.**
    expect(during).toBe(after);
  });

  it('✅ Home holds its place while the workspace is unknown', () => {
    inFlight();

    render(<Navigation role="owner" roleKnown />);

    const home = screen.getByLabelText('Home');
    expect(home).toHaveAttribute('data-pending', 'true');
    // ♿ **Resolving, never disabled** — nothing about this entry is refused,
    // and a reader told *disabled* would reasonably stop waiting for it.
    expect(home).toHaveAttribute('aria-busy', 'true');
    expect(home).not.toHaveAttribute('aria-disabled');
  });

  /**
   * ⛔ **A pending entry must not be reachable.** 📁
   * [B-233](../../../docs/BUGS.md): a `[workspace]` literal in a `<Link>`
   * **throws** in the App Router and took the whole navigation region down.
   * ⚡ **A link to `/` would be worse than none** — a different screen wearing
   * Home's label.
   */
  it('⛔ and it is not a link, because there is nowhere to go yet', () => {
    inFlight();

    render(<Navigation role="owner" roleKnown />);

    const home = screen.getByLabelText('Home');
    expect(home.tagName).not.toBe('A');
    expect(home.closest('a')).toBeNull();
  });

  it('✅ and becomes a real destination once the workspace is known', () => {
    settledWithWorkspace();

    render(<Navigation role="owner" roleKnown />);

    expect(screen.getByRole('link', { name: 'Home' })).toHaveAttribute(
      'href',
      '/w/w1/home',
    );
  });
});

describe('⛔ absent is still absent — the two are not collapsed back together', () => {
  /**
   * 🔴 **The distinction this row exists to draw**, and the half a careless fix
   * would lose. 📁 [B-306](../../../docs/BUGS.md): *"`resolved` alone conflates
   * a workspace that is absent with one that has not arrived."*
   *
   * ⛔ **A person who genuinely has no organization has no Home**, and holding
   * a place open for them forever would be a permanent loading state.
   */
  it('🔴 a reader with no organization gets no Home entry at all', () => {
    settledWithNone();

    render(<Navigation role="owner" roleKnown />);

    expect(screen.queryByLabelText('Home')).not.toBeInTheDocument();
    expect(screen.queryByRole('link', { name: 'Home' })).not.toBeInTheDocument();
  });

  it('⛔ and `resolved` says the same thing without a component around it', () => {
    const items = [{ id: 'home', label: 'Home', href: '/w/[workspace]/home', depth: 1 }];
    const asAny = items as never;

    // ⚡ **Known and none → dropped. Unknown → held.** Two inputs, two answers.
    expect(resolved(asAny, null, true)).toHaveLength(0);
    expect(resolved(asAny, null, false)).toHaveLength(1);
    expect(resolved(asAny, 'w1', true)).toHaveLength(1);
  });
});

describe('🔴 B-253 — an unresolved role renders an ordinary row, never a locked one', () => {
  /**
   * ⛔ **An OWNER was told *"Settings — restricted. Requires an owner."* on
   * every cold boot**, reproducibly, on the most-looked-at surface in the
   * product — 📁 [B-253](../../../docs/BUGS.md).
   *
   * ⚡ **The cause was one conflation**: `authenticated-shell` passed
   * `resolved ? role : null`, and **`null` meant both *has no role* and *has
   * not arrived***, which the rail could only read as the first.
   *
   * ✅ **The design decides the repair rather than this lane**: 📁 App Shell
   * §16 *Cold boot* — *"workspace name and rail appear before data
   * resolves"* — **so the rail is drawn before the role is known**, and 📁 Rail
   * States gives the lock to the RESOLVED-DENIED case only: *"restricted
   * destinations stay visible at 45% with a lock and explain on click."*
   */
  it('⛔ nothing is locked while the role is still arriving', () => {
    // ⚡ **The workspace has settled and the ROLE has not**, which is the exact
    // frame the defect lived in: `destinations=7 pending=0` then `8 pending=0`.
    settledWithWorkspace();
    render(<Navigation role={null} roleKnown={false} />);

    expect(screen.queryByText(/Requires an owner/i)).not.toBeInTheDocument();
    expect(screen.queryByRole('button', { name: /restricted/i })).not.toBeInTheDocument();
  });

  it('✅ and a resolved denial still locks, which is the half that must not regress', () => {
    settledWithWorkspace();
    // ⚡ **The fix must not become *never lock*.** 📁 A restricted destination
    // stays VISIBLE and explains on click — hiding it *"teaches a person the
    // feature does not exist, so they ask for the wrong thing or ask nobody."*
    render(<Navigation role="member" roleKnown />);

    expect(screen.getByRole('button', { name: /restricted/i })).toBeInTheDocument();
  });

  it('✅ an owner is never told they are not one, resolved or not', () => {
    settledWithWorkspace();
    for (const known of [false, true]) {
      const { unmount } = render(<Navigation role="owner" roleKnown={known} />);
      expect(screen.queryByText(/Requires an owner/i)).not.toBeInTheDocument();
      unmount();
    }
  });
});
