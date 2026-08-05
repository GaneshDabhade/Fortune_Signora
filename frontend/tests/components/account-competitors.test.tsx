/**
 * A workspace declaration, read on one account's page.
 *
 * **The risk this section carries is not layout, it is misreading.** The same
 * three names appear on every account, and a heading that implied otherwise
 * would have Signora asserting a competitor is present at a company it knows
 * nothing of the sort about. Every test here is about that sentence.
 */
import { render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';

import { CompetitorContext } from '@/components/intelligence/competitors';
import type { DeclaredCompetitors } from '@/lib/api/types';

function declared(overrides: Partial<DeclaredCompetitors> = {}): DeclaredCompetitors {
  return {
    version: 3,
    competitors: [
      { id: '11111111-1111-4111-8111-111111111111', name: 'Cadenza' },
      { id: '22222222-2222-4222-8222-222222222222', name: 'Orbital' },
    ],
    updated_at: new Date().toISOString(),
    updated_by: '33333333-3333-4333-8333-333333333333',
    ...overrides,
  };
}

describe('the declared list is shown as a declaration', () => {
  it('names what the customer declared', () => {
    render(<CompetitorContext competitors={declared()} />);

    expect(screen.getByText('Cadenza')).toBeInTheDocument();
    expect(screen.getByText('Orbital')).toBeInTheDocument();
  });

  it('says it is the same on every account', () => {
    /**
     * **The load-bearing sentence.** Without it a reader takes a workspace
     * declaration for an account finding, and the product has asserted
     * something it never concluded.
     */
    render(<CompetitorContext competitors={declared()} />);

    expect(screen.getByText(/same on every account/i)).toBeInTheDocument();
  });

  it('points at the signal for the account-specific claim', () => {
    /**
     * `competitor_entry` is where Signora says a competitor is *at* an
     * account, with evidence. This section must send a reader there rather
     * than answer it badly.
     */
    render(<CompetitorContext competitors={declared()} />);

    expect(screen.getByText(/raising a signal, with its evidence/i)).toBeInTheDocument();
  });

  it('grades nothing', () => {
    /**
     * No threat level, no rank, no ordering by importance. How much a rival
     * moves an account is a reviewed scoring model's decision, not a list a
     * customer typed.
     */
    const { container } = render(<CompetitorContext competitors={declared()} />);

    expect(container.textContent).not.toMatch(/threat|risk level|high|medium|low/i);
  });
});

describe('a workspace that has declared nothing', () => {
  it('renders no section at all when the list is empty', () => {
    /**
     * A section explaining its own absence, on every account, of a workspace
     * that has not filled this in, is noise on the screen a seller lives on.
     * The declaration page is where that prompt belongs.
     */
    const { container } = render(
      <CompetitorContext competitors={declared({ version: 0, competitors: [] })} />,
    );

    expect(container).toBeEmptyDOMElement();
  });

  it('renders nothing while the answer has not arrived', () => {
    const { container } = render(<CompetitorContext competitors={undefined} />);

    expect(container).toBeEmptyDOMElement();
  });
});
