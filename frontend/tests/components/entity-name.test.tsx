/**
 * How Signora renders a company, and what it refuses to invent.
 *
 * The design rule these assert: **agreement is invisible, disagreement is
 * not.** A marker on every row saying "everything is fine" is noise that
 * trains people to stop reading markers; a disputed name is the one state
 * worth a second of a seller's attention.
 */
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
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

describe('the row does not rewrite itself under the reader', () => {
  it('reserves the space a name will occupy while it loads', () => {
    // A list that shifts as names arrive costs more confidence than the
    // moment it saved.
    const { container } = render(
      <EntityName identity={undefined} fallbackId={ACCOUNT} isLoading />,
    );

    expect(container.querySelector('.animate-pulse')).toBeInTheDocument();
    expect(screen.queryByText('6b8efd21')).not.toBeInTheDocument();
  });

  it('shows the identifier once loading finishes with no name', () => {
    render(<EntityName identity={undefined} fallbackId={ACCOUNT} isLoading={false} />);

    expect(screen.getByText('6b8efd21')).toBeInTheDocument();
  });
});

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

  it('marks a disputed name with a real control, not a hover', () => {
    // **An unreachable control is a defect, not an enhancement** (§20c). A
    // `title` tooltip is invisible on touch and unreachable by keyboard.
    render(<EntityName identity={identity({ agreement: 'disputed' })} fallbackId={ACCOUNT} />);

    const disclosure = screen.getByRole('button', { name: /sources disagree/i });
    expect(disclosure).toBeInTheDocument();
    expect(disclosure).toHaveAttribute('aria-expanded', 'false');
  });

  it('nothing depends on a title attribute', () => {
    const { container } = render(
      <EntityName identity={identity({ agreement: 'disputed' })} fallbackId={ACCOUNT} />,
    );

    expect(container.querySelector('[title]')).toBeNull();
  });

  it('explains itself to a screen reader before it is opened', () => {
    // The explanation is in the accessibility tree whether or not the
    // disclosure is expanded — `hidden` would remove it from both the tree
    // and browser search, which is exactly what the tooltip did.
    render(
      <EntityName
        identity={identity({ agreement: 'disputed', source: 'builtwith', source_count: 3 })}
        fallbackId={ACCOUNT}
      />,
    );

    expect(screen.getByText(/builtwith/)).toBeInTheDocument();
    expect(screen.getByText(/3 sources/)).toBeInTheDocument();
  });

  it('opens and closes from the keyboard', async () => {
    const user = userEvent.setup();
    render(<EntityName identity={identity({ agreement: 'disputed' })} fallbackId={ACCOUNT} />);
    const disclosure = screen.getByRole('button', { name: /sources disagree/i });

    await user.tab();
    expect(disclosure).toHaveFocus();

    await user.keyboard('{Enter}');
    expect(disclosure).toHaveAttribute('aria-expanded', 'true');

    await user.keyboard('{Enter}');
    expect(disclosure).toHaveAttribute('aria-expanded', 'false');
  });

  it('points at the region it controls', () => {
    render(<EntityName identity={identity({ agreement: 'disputed' })} fallbackId={ACCOUNT} />);
    const disclosure = screen.getByRole('button', { name: /sources disagree/i });

    const controlled = disclosure.getAttribute('aria-controls');
    expect(controlled).toBeTruthy();
    expect(document.getElementById(controlled as string)).toBeInTheDocument();
  });

  it('still shows the chosen name while marking the dispute', () => {
    // Disagreement is surfaced, never resolved away — and never hidden by
    // refusing to show a name at all.
    render(<EntityName identity={identity({ agreement: 'disputed' })} fallbackId={ACCOUNT} />);

    expect(screen.getByText('Northwind Traders')).toBeInTheDocument();
  });
});

describe('the name opens the account brief', () => {
  it('links the name when there is somewhere to go', () => {
    render(<EntityName identity={identity()} fallbackId={ACCOUNT} href="/opportunities/x" />);

    expect(screen.getByRole('link', { name: 'Northwind Traders' })).toHaveAttribute(
      'href',
      '/opportunities/x',
    );
  });

  it('renders no link at all without an href', () => {
    // On the brief itself there is nowhere to go. A link back to the page you
    // are already on is a control that does nothing, and a disabled-looking
    // one is worse than none.
    render(<EntityName identity={identity()} fallbackId={ACCOUNT} />);

    expect(screen.queryByRole('link')).not.toBeInTheDocument();
  });

  it('links an account nobody has named yet', () => {
    // The account with the worst label is the one a seller most wants to open.
    // Withholding the link because the name is poor hides the page that
    // explains why it is poor.
    render(<EntityName identity={undefined} fallbackId={ACCOUNT} href="/opportunities/x" />);

    expect(screen.getByRole('link')).toBeInTheDocument();
  });

  it('keeps the disclosure outside the link', () => {
    // A control inside a link is invalid, activates the wrong thing on touch,
    // and lands in the wrong place in the keyboard order. The two stay
    // siblings.
    render(
      <EntityName
        identity={identity({ agreement: 'disputed' })}
        fallbackId={ACCOUNT}
        href="/opportunities/x"
      />,
    );
    const link = screen.getByRole('link');
    const disclosure = screen.getByRole('button', { name: /sources disagree/i });

    expect(link.contains(disclosure)).toBe(false);
  });
});
