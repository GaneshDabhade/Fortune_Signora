/**
 * Signed in, and belonging to nowhere.
 *
 * **The state every brand-new account is in**, and the one that rendered a
 * heading and blank space until M12.3 (D36). A page that renders nothing is
 * indistinguishable from a broken one, and this is the first thing somebody
 * sees before they have done anything wrong.
 */
import { render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';

import { NoWorkspace } from '@/components/workspace/no-workspace';

describe('a signed-in reader with no workspace is told so', () => {
  it('says what is missing rather than showing nothing', () => {
    render(<NoWorkspace />);

    expect(screen.getByText(/not in a workspace yet/i)).toBeInTheDocument();
  });

  it('explains what a workspace is before asking for one', () => {
    // Somebody meeting this word for the first time is being asked to name
    // something they have not had explained. The description is the
    // explanation, which is why `EmptyState` requires one.
    render(<NoWorkspace />);

    expect(
      screen.getByText(/where your accounts, evidence and decisions live/i),
    ).toBeInTheDocument();
  });

  it('offers both ways out of the state', () => {
    // Creating one is not the only answer: most sellers are added to a
    // colleague's workspace and never create anything.
    render(<NoWorkspace />);

    expect(screen.getByRole('link', { name: /create a workspace/i })).toHaveAttribute(
      'href',
      '/settings',
    );
    expect(screen.getByText(/ask a colleague to add you/i)).toBeInTheDocument();
  });

  it('does not describe it as an empty workspace', () => {
    // **The distinction is the whole point.** "No accounts need your
    // attention" and "you are not in a workspace" have different next
    // actions, and reusing the first would be a confident wrong answer.
    const { container } = render(<NoWorkspace />);
    const text = (container.textContent ?? '').toLowerCase();

    for (const wrong of ['no accounts', 'nothing needs', 'all quiet']) {
      expect(text).not.toContain(wrong);
    }
  });
});
