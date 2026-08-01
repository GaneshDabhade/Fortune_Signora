/**
 * Signed in, and belonging to nowhere.
 *
 * **The copy said "workspace" until ADR-0034**, which explained Signora's
 * tenancy model to a salesperson at the first moment they ever saw the
 * product. Every assertion below survived the rewording unchanged in intent:
 * what is missing, what it is, and both ways out.
 *
 * **The state every brand-new account is in**, and the one that rendered a
 * heading and blank space until M12.3 (D36). A page that renders nothing is
 * indistinguishable from a broken one, and this is the first thing somebody
 * sees before they have done anything wrong.
 */
import { render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';

import { NoWorkspace } from '@/components/workspace/no-workspace';

describe('a signed-in reader who belongs to no organization is told so', () => {
  it('says what is missing rather than showing nothing', () => {
    render(<NoWorkspace />);

    expect(screen.getByText(/not part of an organization yet/i)).toBeInTheDocument();
  });

  it('explains what an organization is before asking for one', () => {
    // Somebody meeting this word for the first time is being asked to name
    // something they have not had explained. The description is the
    // explanation, which is why `EmptyState` requires one.
    render(<NoWorkspace />);

    expect(
      screen.getByText(/your company on Signora — where its accounts, evidence/i),
    ).toBeInTheDocument();
  });

  it('offers both ways out of the state', () => {
    // Creating one is not the only answer: most sellers are added to a
    // colleague's organization and never create anything.
    render(<NoWorkspace />);

    expect(screen.getByRole('link', { name: /create an organization/i })).toHaveAttribute(
      'href',
      '/settings',
    );
    expect(screen.getByText(/ask a colleague to add you/i)).toBeInTheDocument();
  });

  it('does not describe it as an empty account list', () => {
    // **The distinction is the whole point.** "No accounts need your
    // attention" and "you belong to no organization" have different next
    // actions, and reusing the first would be a confident wrong answer.
    const { container } = render(<NoWorkspace />);
    const text = (container.textContent ?? '').toLowerCase();

    for (const wrong of ['no accounts', 'nothing needs', 'all quiet']) {
      expect(text).not.toContain(wrong);
    }
  });
});
