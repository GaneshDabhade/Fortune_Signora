/**
 * How Signora renders a company, and what it refuses to invent.
 *
 * The design rule these assert: **agreement is invisible, disagreement is
 * not.** A marker on every row saying "everything is fine" is noise that
 * trains people to stop reading markers; a disputed name is the one state
 * worth a second of a seller's attention.
 */
import { render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';

import { EntityName } from '@/components/intelligence/entity-name';
import type { AccountIdentity, NameAgreement } from '@/lib/api/types';

const ACCOUNT = '6b8efd21-1111-2222-3333-444455556666';

function identity(overrides: Partial<AccountIdentity> = {}): AccountIdentity {
  return {
    account_id: ACCOUNT,
    name: 'Northwind Traders',
    agreement: 'agreed',
    source_count: 2,
    source: 'apollo',
    observed_at: '2026-07-31T12:00:00Z',
    ...overrides,
  };
}

describe('a name is shown when one is known', () => {
  it('renders the company name', () => {
    render(<EntityName identity={identity()} fallbackId={ACCOUNT} />);

    expect(screen.getByText('Northwind Traders')).toBeInTheDocument();
  });

  it('does not show the raw identifier once a name exists', () => {
    render(<EntityName identity={identity()} fallbackId={ACCOUNT} />);

    expect(screen.queryByText(/6b8efd21/)).not.toBeInTheDocument();
  });
});

describe('absence is rendered as absence', () => {
  it('falls back to the real identifier, never a placeholder', () => {
    // A fabricated name would be indistinguishable from a real one. Being
    // told the truth badly beats being told a fiction well.
    render(<EntityName identity={undefined} fallbackId={ACCOUNT} />);

    expect(screen.getByText('6b8efd21')).toBeInTheDocument();
  });

  it('falls back when the identity exists but nobody named the account', () => {
    render(
      <EntityName
        identity={identity({ name: null, agreement: 'unknown', source_count: 0, source: null })}
        fallbackId={ACCOUNT}
      />,
    );

    expect(screen.getByText('6b8efd21')).toBeInTheDocument();
  });

  it('never renders any of the words a placeholder would use', () => {
    const { container } = render(<EntityName identity={undefined} fallbackId={ACCOUNT} />);
    const text = (container.textContent ?? '').toLowerCase();

    for (const invented of ['unknown company', 'untitled', 'acme', 'n/a', 'unnamed']) {
      expect(text).not.toContain(invented);
    }
  });
});

describe('only disagreement is marked', () => {
  it.each(['agreed', 'single_source'] as NameAgreement[])(
    'shows no marker when agreement is %s',
    (agreement) => {
      render(<EntityName identity={identity({ agreement })} fallbackId={ACCOUNT} />);

      expect(screen.queryByLabelText(/disagree/i)).not.toBeInTheDocument();
    },
  );

  it('marks a disputed name', () => {
    render(<EntityName identity={identity({ agreement: 'disputed' })} fallbackId={ACCOUNT} />);

    expect(screen.getByLabelText('Sources disagree on this name')).toBeInTheDocument();
  });

  it('says who reported the shown name and how many sources exist', () => {
    // Progressive disclosure: the row carries the fact, the detail explains
    // it on demand rather than by default.
    render(
      <EntityName
        identity={identity({ agreement: 'disputed', source: 'builtwith', source_count: 3 })}
        fallbackId={ACCOUNT}
      />,
    );

    expect(screen.getByLabelText('Sources disagree on this name')).toHaveAttribute(
      'title',
      expect.stringContaining('builtwith'),
    );
  });

  it('still shows the chosen name while marking the dispute', () => {
    // Disagreement is surfaced, never resolved away — and never hidden by
    // refusing to show a name at all.
    render(<EntityName identity={identity({ agreement: 'disputed' })} fallbackId={ACCOUNT} />);

    expect(screen.getByText('Northwind Traders')).toBeInTheDocument();
  });
});
