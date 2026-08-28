/**
 * 📁 **The client half of the authenticated layout.**
 *
 * ⛔ **265 lines, no render witness** — ⚡ **and it carries two defects whose
 * fixes are invisible in the source unless you drive the states**: the latched
 * read failure ([B-237](../../../docs/BUGS.md)) and the threaded
 * `role`/`roleKnown` pair ([B-253](../../../docs/BUGS.md)).
 *
 * **`workspace-gate.ts` already has a unit test.** ⛔ **What it cannot see is
 * the shell's own composition** — which is where both bugs lived.
 */
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { beforeEach, describe, expect, it, vi } from 'vitest';

const useSession = vi.hoisted(() => vi.fn());
const useViewerRole = vi.hoisted(() => vi.fn());
const signOut = vi.hoisted(() => vi.fn());
const workspaceState = vi.hoisted(() => ({
  workspaces: [] as { id: string; name: string }[],
  activeWorkspace: null as { id: string; name: string } | null,
  isLoading: false,
  error: null as unknown,
}));

vi.mock('next/navigation', () => ({ usePathname: () => '/settings' }));
vi.mock('@/lib/auth/client', () => ({ useSession, signOut }));
vi.mock('@/lib/query/hooks/team', () => ({ useViewerRole }));
vi.mock('@/lib/state/workspace-provider', () => ({
  WorkspaceProvider: ({ children }: { children: React.ReactNode }) => <>{children}</>,
  useWorkspaceContext: () => workspaceState,
}));
vi.mock('@/components/workspace/resume-onboarding', () => ({
  ResumeOnboarding: () => null,
}));
vi.mock('@/components/auth/session-lock', () => ({
  SessionLock: ({ email }: { email: string }) => <div data-testid="lock">{email}</div>,
}));

/**
 * ⚡ **Probes rather than the real shell** — the assertions here are about what
 * this file THREADS, and a probe is the only way to see a prop that a child
 * consumes rather than renders.
 */
vi.mock('@/components/shell/app-shell', () => ({
  AppShell: ({
    role,
    roleKnown,
    name,
    children,
    signOut: signOutNode,
  }: {
    role: string | null;
    roleKnown: boolean;
    name: string | null;
    children: React.ReactNode;
    signOut: React.ReactNode;
  }) => (
    <div
      data-testid="shell"
      data-role={role === null ? 'null' : role}
      data-role-known={String(roleKnown)}
      data-name={name === null ? 'null' : name}
    >
      {signOutNode}
      {children}
    </div>
  ),
}));
vi.mock('@/components/shell/route-guard', () => ({
  RouteGuard: ({ children }: { children: React.ReactNode }) => (
    <div data-testid="guard">{children}</div>
  ),
}));

import { AuthenticatedShell } from '@/app/(app)/authenticated-shell';

const WORKSPACE = { id: 'w-1', name: 'Northwind' };

function shell(name: string | null = 'Marta Reinhardt') {
  return render(
    <AuthenticatedShell email="marta@northwind.com" name={name}>
      <p>page content</p>
    </AuthenticatedShell>,
  );
}

const gate = () => screen.getByTestId('shell');

beforeEach(() => {
  vi.clearAllMocks();
  Object.assign(workspaceState, {
    workspaces: [WORKSPACE],
    activeWorkspace: WORKSPACE,
    isLoading: false,
    error: null,
  });
  useSession.mockReturnValue({ data: { user: { id: 'u-1' } } });
  useViewerRole.mockReturnValue({ role: 'owner', resolved: true });
});

describe('🔴 B-237 — the failure is LATCHED, or the gate oscillates forever', () => {
  it('⛔ stays open when a refetch returns the query to pending and clears the error', () => {
    /**
     * 🔴 **Measured on the real loop: 121 fetches in 600ms.** ⚡ **When a query
     * holding NO data refetches, React Query returns it to `pending` and
     * CLEARS `error`** — so a gate reading `error` directly opens, mounts the
     * page, shuts, unmounts it, and repeats every ~3.1s.
     *
     * ⛔ **`refetchOnMount: false` does not help**: with no data at all a new
     * observer must fetch regardless. **The observer has to stop unmounting**,
     * which means the gate has to stop oscillating.
     *
     * ✅ ***"We have tried and we hold no organizations"* is a STABLE answer.**
     */
    Object.assign(workspaceState, {
      workspaces: [],
      activeWorkspace: null,
      isLoading: false,
      error: new Error('down'),
    });
    const { rerender } = shell();
    expect(screen.getByTestId('guard')).toBeInTheDocument();

    // ⚡ **The refetch**: pending again, error gone, still no data — the exact
    // frame that used to shut the gate.
    Object.assign(workspaceState, { isLoading: true, error: null });
    rerender(
      <AuthenticatedShell email="marta@northwind.com" name="Marta Reinhardt">
        <p>page content</p>
      </AuthenticatedShell>,
    );

    expect(screen.getByTestId('guard'), 'the gate shut on a refetch').toBeInTheDocument();
    expect(screen.getByText('page content')).toBeInTheDocument();
  });

  it('✅ and the latch releases when a read actually succeeds', () => {
    // ⚠️ **The vacuity half.** ⛔ A latch that never releases would pass the
    // assertion above and be a different defect.
    Object.assign(workspaceState, {
      workspaces: [],
      activeWorkspace: null,
      isLoading: false,
      error: new Error('down'),
    });
    const { rerender } = shell();

    Object.assign(workspaceState, {
      workspaces: [WORKSPACE],
      activeWorkspace: WORKSPACE,
      isLoading: false,
      error: null,
    });
    rerender(
      <AuthenticatedShell email="marta@northwind.com" name="Marta Reinhardt">
        <p>page content</p>
      </AuthenticatedShell>,
    );

    expect(screen.getByTestId('guard')).toBeInTheDocument();
  });
});

describe('🔴 B-253 — role and roleKnown are two answers, threaded rather than collapsed', () => {
  it('⛔ an unresolved role is not the same as no role', () => {
    /**
     * 🔴 **This passed `resolved ? role : null`**, ⛔ **and `null` meant both
     * *has no role* and *has not arrived*** — the rail could only read it as
     * the first, **so an OWNER was told *"Settings — restricted. Requires an
     * owner."* on every cold boot.**
     */
    useViewerRole.mockReturnValue({ role: null, resolved: false });
    shell();

    expect(gate()).toHaveAttribute('data-role-known', 'false');
    // ⛔ **The frame renders throughout; only its CONTENTS wait.**
    expect(screen.queryByTestId('guard')).toBeNull();
    expect(screen.queryByText('page content')).toBeNull();
  });

  it('✅ a settled non-member is roleKnown with a null role', () => {
    useViewerRole.mockReturnValue({ role: null, resolved: true });
    shell();

    expect(gate()).toHaveAttribute('data-role', 'null');
    expect(gate()).toHaveAttribute('data-role-known', 'true');
    expect(screen.getByTestId('guard')).toBeInTheDocument();
  });

  it('✅ and an owner is passed through as one', () => {
    shell();
    expect(gate()).toHaveAttribute('data-role', 'owner');
    expect(gate()).toHaveAttribute('data-role-known', 'true');
  });

  it('⛔ nothing is guarded while the WORKSPACE question is still open', () => {
    // ⚡ **Two questions, both must be answered**: *which organization is this*
    // and *what is this person in it*. ⛔ **`resolved` alone conflates a
    // workspace that is absent with one that has not arrived.**
    useViewerRole.mockReturnValue({ role: 'owner', resolved: true });
    Object.assign(workspaceState, { workspaces: [], activeWorkspace: null, isLoading: true });
    shell();

    expect(gate()).toHaveAttribute('data-role-known', 'false');
    expect(screen.queryByTestId('guard')).toBeNull();
  });
});

describe('🔴 B-429 — a name that is absent is stated by absence, never derived', () => {
  it('⛔ passes null through rather than deriving one from the address', () => {
    // ⚡ **Registration requires a full name**, so this is populated for every
    // account made through the product — ⛔ **but a session that genuinely
    // carries none must not be given `marta`.**
    shell(null);

    expect(gate()).toHaveAttribute('data-name', 'null');
    expect(gate().getAttribute('data-name')).not.toMatch(/marta/i);
  });

  it('✅ and passes a real name through unchanged', () => {
    shell('Marta Reinhardt');
    expect(gate()).toHaveAttribute('data-name', 'Marta Reinhardt');
  });
});

describe('🔴 signing out must actually sign you out', () => {
  it('⛔ calls the vendor client, and is not a form the vendor would refuse', async () => {
    /**
     * 🔴 **This was a native `<form method="post">`.** ⚡ **A browser submits
     * `application/x-www-form-urlencoded`; Better Auth accepts JSON only** — so
     * **every sign-out navigated the customer to a page of raw JSON and left
     * the session intact.**
     *
     * ⛔ **A security defect before it is a UX one**: on a shared machine, a
     * person who signed out was still signed in **and had been told otherwise.**
     */
    const user = userEvent.setup();
    shell();

    expect(document.querySelector('form')).toBeNull();
    await user.click(screen.getByRole('button', { name: 'Sign out' }));
    expect(signOut).toHaveBeenCalledTimes(1);
  });

  it('⚠️ and latches, because a second click during the round trip signs out twice', async () => {
    const user = userEvent.setup();
    shell();

    const button = screen.getByRole('button', { name: 'Sign out' });
    await user.click(button);
    await user.click(button);

    expect(signOut).toHaveBeenCalledTimes(1);
  });
});

describe('⚡ the shell is where two things must live exactly once', () => {
  it('📁 re-authentication happens OVER the view, so the lock is mounted at the shell', () => {
    // 📁 Design `18` requires re-authentication over the current view rather
    // than instead of it — ⛔ **a page-level lock would replace the screen.**
    shell();
    expect(screen.getByTestId('lock')).toHaveTextContent('marta@northwind.com');
  });

  it('📁 and the profile has an entrance, because a route with none is unreachable', () => {
    // ⛔ **The address was printed here and was not a link** — exactly the
    // "route with no entrance" `infra/reachability.py` refuses.
    shell();
    expect(screen.getByRole('link', { name: 'marta@northwind.com' })).toHaveAttribute(
      'href',
      '/profile',
    );
  });
});
