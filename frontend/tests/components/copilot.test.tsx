import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, expect, it, vi } from 'vitest';

/**
 * ⚡ **§19 made the assistant read the workspace context** —
 * [TASK-1463](../../../docs/BACKLOG.md), *"the assistant carries the workspace
 * name in its header"*. ⛔ **Stubbed to ONE workspace here**, which is §19's own
 * *do not label* case — **so every assertion below still describes the panel
 * this suite was written about.** ⚡ **The labelling itself is
 * `workspace-label.test.tsx`'s**, where both sides of the condition are
 * exercised.
 */
vi.mock('@/lib/state/workspace-provider', () => ({
  useWorkspaceContext: () => ({
    workspaces: [{ id: 'w1', name: 'Northwind', role: 'owner' }],
    activeWorkspace: { id: 'w1', name: 'Northwind', role: 'owner' },
  }),
}));

import { Copilot, useCopilot } from '@/components/shell/copilot';

/**
 * 🔴 **The ENTRY moved to the rail** — [TASK-1470](../../../docs/BACKLOG.md).
 *
 * 📁 The design puts `Ask Signora` first in the rail's pinned bottom group, and
 * ⛔ **it sat below the utilities, mounted outside the rail entirely.** ⚡ **So
 * `Copilot` now publishes the ROOM and the rail publishes one of its doors** —
 * 📁 §12, *"four doors, one room"*.
 *
 * ✅ **These assertions are about the ROOM and are unchanged in substance.**
 * ⛔ **The button they used to click is asserted where it now lives**, in
 * [`rail-assistant.test.tsx`](rail-assistant.test.tsx) — **by POSITION, because
 * this row is ordering rather than absence.**
 */
function OpenIt() {
  const copilot = useCopilot();
  return (
    <button type="button" onClick={() => copilot?.open()}>
      open the assistant
    </button>
  );
}

function room() {
  return render(
    <Copilot>
      <OpenIt />
    </Copilot>,
  );
}

async function openRoom() {
  await userEvent.click(screen.getByRole('button', { name: 'open the assistant' }));
}

/**
 * **Ask Signora** — [TASK-482](../../../docs/BACKLOG.md), 📁 App Shell §12.
 *
 * 🔴 **The row's Definition of Done is honesty, not capability**: *"it must
 * state honestly when it cannot answer — a panel that renders a hopeful empty
 * state instead of saying so is the false-affordance class this lane has
 * refused three times."*
 */

describe('📁 the room, and the doors that reach it', () => {
  it('⛔ the design refuses a corner circle by name, and there is none', async () => {
    // 📁 *"a persistent circle in the corner is a consumer pattern and it
    // covers data."* ⚡ **Nothing is fixed and nothing is a circle.**
    const { container } = room();

    await openRoom();

    expect(container.innerHTML).not.toMatch(/fixed|rounded-full/);
  });

  it('⚡ a door opens it', async () => {
    room();

    await openRoom();

    expect(screen.getByRole('complementary', { name: /Ask Signora/ })).toBeInTheDocument();
  });

  it('📁 and so does the design’s own shortcut, ⌘⇧A', async () => {
    room();

    await userEvent.keyboard('{Meta>}{Shift>}a{/Shift}{/Meta}');

    expect(screen.getByRole('complementary', { name: /Ask Signora/ })).toBeInTheDocument();
  });

  /**
   * ⛔ **No provider means no door, never a control that does nothing.**
   *
   * ⚡ **`useCopilot` returns `null` outside the provider** — 📁 the same rule
   * `ShortcutsReference` keeps, and the reason the rail renders no assistant
   * entry in a tree that has no room to open.
   */
  it('🔴 a door outside the room is not a door', () => {
    render(<OpenIt />);

    // ⛔ **It renders, and pressing it opens nothing** — which is why the RAIL
    // returns `null` rather than drawing a control that cannot work.
    expect(screen.getByRole('button', { name: 'open the assistant' })).toBeInTheDocument();
    expect(screen.queryByRole('complementary')).not.toBeInTheDocument();
  });
});

describe('🔴 it says it cannot answer, and does not pretend otherwise', () => {
  it('⛔ states the absence of the capability in plain words', async () => {
    room();
    await openRoom();

    expect(screen.getByText(/cannot answer questions here yet/i)).toBeInTheDocument();
  });

  it('🔴 has NO input box, because a field that swallows a question is worse than none', async () => {
    /**
     * ⚡ **Somebody types their real question, loses it, and learns the product
     * is unreliable rather than unfinished.** ⛔ **That is the false
     * affordance the row names.**
     */
    room();
    await openRoom();

    expect(screen.queryByRole('textbox')).not.toBeInTheDocument();
    expect(screen.queryByPlaceholderText(/ask/i)).not.toBeInTheDocument();
  });

  it('⛔ does NOT say "try again", because nothing failed', async () => {
    /**
     * ⚠️ **The refusal is not an error state.** ⚡ **The capability is not
     * built** — borrowing `StatedAbsence`'s *"reload to try again"* would be a
     * false instruction, exactly as it would be for
     * [TASK-1411](../../../docs/BACKLOG.md)'s absent confidence.
     */
    room();
    await openRoom();

    expect(screen.queryByText(/try again/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/reload/i)).not.toBeInTheDocument();
  });

  it('✅ and it points at the reasoning that DOES exist, rather than only refusing', async () => {
    // ⚡ **A refusal that leaves somebody with nothing teaches them the product
    // is empty.** The narration, the evidence and the drawer are all shipped.
    room();
    await openRoom();

    expect(screen.getByText(/In plain language/)).toBeInTheDocument();
  });
});

describe('📁 the scope is stated above the panel, when there is one', () => {
  it('⚡ a scope renders', async () => {
    render(
      <Copilot scope="EMEA · Enterprise · Q3">
        <OpenIt />
      </Copilot>,
    );
    await openRoom();

    expect(screen.getByText('EMEA · Enterprise · Q3')).toBeInTheDocument();
  });

  it('⛔ and no scope renders nothing, rather than claiming "everything"', async () => {
    // ⚡ *"Everything"* would be a claim about what the assistant can see.
    room();
    await openRoom();

    expect(screen.queryByText(/everything/i)).not.toBeInTheDocument();
  });
});
