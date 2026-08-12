/**
 * **§19 · a workspace-scoped surface says which workspace** —
 * [TASK-1463](../../../docs/BACKLOG.md).
 *
 * 🔴 **The condition is the whole test.** 📁 *"whenever more than one is
 * available to the user"* — ⛔ **and a rule with a condition is a rule that can
 * be implemented as *always*, which passes every test that only checks the
 * label appears.** ⚡ **So both sides are asserted, on both surfaces.**
 */
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { beforeEach, describe, expect, it, vi } from 'vitest';

const context = vi.hoisted(() => vi.fn());

vi.mock('next/navigation', () => ({ useRouter: () => ({ push: vi.fn() }) }));
vi.mock('@/lib/state/workspace-provider', () => ({ useWorkspaceContext: context }));
vi.mock('@/lib/query/hooks/search', () => ({
  useAccountSearch: () => ({ data: undefined, isFetching: false, isError: false }),
}));

import { Copilot, useCopilot } from '@/components/shell/copilot';
import { ShellPalette } from '@/components/shell/shell-palette';

/**
 * ⚡ **The assistant's entry moved to the rail** —
 * [TASK-1470](../../../docs/BACKLOG.md), §12 door `01`. ⛔ **`Copilot` now
 * publishes the room**, so a test that needs the panel opens it through the
 * provider rather than through a button this component no longer renders.
 */
function OpenIt() {
  const copilot = useCopilot();
  return (
    <button type="button" onClick={() => copilot?.open()}>
      open the assistant
    </button>
  );
}

async function openAssistant(scope?: string) {
  render(
    <Copilot {...(scope === undefined ? {} : { scope })}>
      <OpenIt />
    </Copilot>,
  );
  await userEvent.click(screen.getByRole('button', { name: 'open the assistant' }));
}

function workspaces(n: number) {
  const all = Array.from({ length: n }, (_, i) => ({
    id: `w${i + 1}`,
    name: i === 0 ? 'Northwind Global' : `Workspace ${i + 1}`,
    role: 'owner' as const,
  }));
  context.mockReturnValue({ workspaces: all, activeWorkspace: all[0] ?? null });
}

beforeEach(() => context.mockReset());

describe('🔴 the assistant', () => {
  it('✅ carries the workspace name when the reader has more than one', async () => {
    workspaces(2);
    await openAssistant();

    expect(screen.getByText('Northwind Global')).toBeInTheDocument();
  });

  /**
   * 🔴 **The assertion the *always* implementation fails.**
   *
   * ⚡ **Somebody with one workspace has no ambiguity to resolve**, and a chip
   * naming their only organization is noise on every panel it appears on —
   * 📁 which is why §19 wrote a condition rather than a rule.
   */
  it('⛔ and says nothing about it when they have only one', async () => {
    workspaces(1);
    await openAssistant();

    expect(screen.queryByText('Northwind Global')).not.toBeInTheDocument();
  });

  /**
   * ⛔ **A caller's own scope is NARROWER than the workspace and must win.**
   *
   * 📁 §12 gives the assistant *"Scoped to EMEA enterprise · Q3 · 2 filters"*.
   * ⚠️ **Overwriting it with the workspace name would WIDEN what the panel
   * claims to be answering within** — the direction
   * [`scope.ts`](../../lib/shell/scope.ts) refuses by name.
   */
  it('🔴 never widens a scope the caller already narrowed', async () => {
    workspaces(3);
    await openAssistant('Scoped to EMEA enterprise');

    expect(screen.getByText('Scoped to EMEA enterprise')).toBeInTheDocument();
    expect(screen.queryByText('Northwind Global')).not.toBeInTheDocument();
  });
});

describe('🔴 the search palette', () => {
  async function openPalette() {
    await userEvent.keyboard('{Meta>}k{/Meta}');
  }

  it('✅ names the workspace it is searching, above the input', async () => {
    workspaces(2);
    render(<ShellPalette role="owner" />);

    await openPalette();

    // ⚡ **Above the input, because the reader must know whose data they are
    // about to search BEFORE they type it.**
    expect(screen.getByTestId('palette-scope')).toHaveTextContent('Northwind Global');
  });

  it('⛔ and stays silent for a single-workspace reader', async () => {
    workspaces(1);
    render(<ShellPalette role="owner" />);

    await openPalette();

    expect(screen.queryByTestId('palette-scope')).not.toBeInTheDocument();
  });
});
