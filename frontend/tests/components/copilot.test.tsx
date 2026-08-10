import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, expect, it } from 'vitest';

import { Copilot } from '@/components/shell/copilot';

/**
 * **Ask Signora** — [TASK-482](../../../docs/BACKLOG.md), 📁 App Shell §12.
 *
 * 🔴 **The row's Definition of Done is honesty, not capability**: *"it must
 * state honestly when it cannot answer — a panel that renders a hopeful empty
 * state instead of saying so is the false-affordance class this lane has
 * refused three times."*
 */

describe('📁 the entry is a control in the shell, never a floating bubble', () => {
  it('⛔ the design refuses a corner circle by name, and there is none', () => {
    // 📁 *"a persistent circle in the corner is a consumer pattern and it
    // covers data."*
    const { container } = render(<Copilot />);

    expect(screen.getByRole('button', { name: /Ask Signora/ })).toBeInTheDocument();
    expect(container.innerHTML).not.toMatch(/fixed|rounded-full/);
  });

  it('♿ the control says it opens a panel, and whether it is open', () => {
    render(<Copilot />);
    const entry = screen.getByRole('button', { name: /Ask Signora/ });

    expect(entry).toHaveAttribute('aria-haspopup', 'dialog');
    expect(entry).toHaveAttribute('aria-expanded', 'false');
  });

  it('⚡ opens on click', async () => {
    render(<Copilot />);
    // ⚠️ **Captured before opening.** Once the drawer is up its own close
    // control also carries the title, so a name query would match two.
    const entry = screen.getByRole('button', { name: /Ask Signora/ });

    await userEvent.click(entry);

    expect(entry).toHaveAttribute('aria-expanded', 'true');
  });

  it('📁 and on the design’s own shortcut, ⌘⇧A', async () => {
    // ⚡ Read from §15's shortcut table rather than chosen.
    render(<Copilot />);
    const entry = screen.getByRole('button', { name: /Ask Signora/ });

    await userEvent.keyboard('{Meta>}{Shift>}a{/Shift}{/Meta}');

    expect(entry).toHaveAttribute('aria-expanded', 'true');
  });
});

describe('🔴 it says it cannot answer, and does not pretend otherwise', () => {
  it('⛔ states the absence of the capability in plain words', async () => {
    render(<Copilot />);
    await userEvent.click(screen.getAllByRole('button', { name: /Ask Signora/ })[0] as HTMLElement);

    expect(screen.getByText(/cannot answer questions here yet/i)).toBeInTheDocument();
  });

  it('🔴 has NO input box, because a field that swallows a question is worse than none', async () => {
    /**
     * ⚡ **Somebody types their real question, loses it, and learns the product
     * is unreliable rather than unfinished.** ⛔ **That is the false
     * affordance the row names.**
     */
    render(<Copilot />);
    await userEvent.click(screen.getAllByRole('button', { name: /Ask Signora/ })[0] as HTMLElement);

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
    render(<Copilot />);
    await userEvent.click(screen.getAllByRole('button', { name: /Ask Signora/ })[0] as HTMLElement);

    expect(screen.queryByText(/try again/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/reload/i)).not.toBeInTheDocument();
  });

  it('✅ and it points at the reasoning that DOES exist, rather than only refusing', async () => {
    // ⚡ **A refusal that leaves somebody with nothing teaches them the product
    // is empty.** The narration, the evidence and the drawer are all shipped.
    render(<Copilot />);
    await userEvent.click(screen.getAllByRole('button', { name: /Ask Signora/ })[0] as HTMLElement);

    expect(screen.getByText(/In plain language/)).toBeInTheDocument();
  });
});

describe('📁 the scope is stated above the panel, when there is one', () => {
  it('⚡ a scope renders', async () => {
    render(<Copilot scope="EMEA · Enterprise · Q3" />);
    await userEvent.click(screen.getAllByRole('button', { name: /Ask Signora/ })[0] as HTMLElement);

    expect(screen.getByText('EMEA · Enterprise · Q3')).toBeInTheDocument();
  });

  it('⛔ and no scope renders nothing, rather than claiming "everything"', async () => {
    // ⚡ *"Everything"* would be a claim about what the assistant can see.
    render(<Copilot />);
    await userEvent.click(screen.getAllByRole('button', { name: /Ask Signora/ })[0] as HTMLElement);

    expect(screen.queryByText(/everything/i)).not.toBeInTheDocument();
  });
});
