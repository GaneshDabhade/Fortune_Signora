/**
 * Real evidence about a company nobody can name.
 *
 * **A6, and it is C-321 wearing a slice's name.** The ruling answered six
 * questions and four of them are assertions here: an unnamed record appears,
 * it is off the working list, it keeps its score, and it is never workable.
 * The fifth and sixth belong to `opportunity_engine` and are not this
 * section's to encode.
 */
import { render, screen, within } from '@testing-library/react';
import { describe, expect, it } from 'vitest';

import { NeedsIdentity } from '@/components/intelligence/needs-identity';
import type { AccountAttention, AccountIdentity } from '@/lib/api/types';

const NAMELESS = '70b04700-1111-4111-8111-111111111111';

function account(overrides: Partial<AccountAttention> = {}): AccountAttention {
  return {
    id: 'aaaaaaaa-1111-4111-8111-111111111111',
    account_id: NAMELESS,
    score: 87,
    trend: 'rising',
    score_change: 4,
    signal_type: 'active_evaluation',
    contested: false,
    posture: 'expansionary',
    evidence: 'current',
    stage: 'tracking',
    owner_id: null,
    opened_at: '2026-07-01T00:00:00Z',
    since: '2026-07-01T00:00:00Z',
    ...overrides,
  };
}

function identity(overrides: Partial<AccountIdentity> = {}): AccountIdentity {
  return {
    account_id: NAMELESS,
    name: null,
    agreement: 'unknown',
    source_count: 4,
    source: null,
    observed_at: null,
    last_observed_at: '2026-07-28T00:00:00Z',
    ...overrides,
  };
}

const identities = (one: AccountIdentity = identity()) =>
  new Map([[one.account_id, one]]);

describe('an unnamed record appears rather than being discarded', () => {
  it('shows the account', () => {
    // "Hiding it discards real intelligence." 70b04700 has four weeks of
    // elevated research and peaked at 87.
    render(<NeedsIdentity accounts={[account()]} identities={identities()} />);

    expect(screen.getByRole('heading', { name: /needs identity/i })).toBeVisible();
    expect(screen.getByText('70b04700')).toBeInTheDocument();
  });

  it('keeps the score exactly as the pipeline computed it', () => {
    // The score measures evidence and the evidence is real. Discounting it
    // here would be a render overruling a reviewed scoring model.
    render(<NeedsIdentity accounts={[account({ score: 87 })]} identities={identities()} />);

    expect(screen.getByText('87')).toBeInTheDocument();
  });

  it('says why these are not on the working list', () => {
    // Without the sentence the section reads as a list of broken records
    // rather than as evidence Signora cannot attach to anybody callable.
    render(<NeedsIdentity accounts={[account()]} identities={identities()} />);

    expect(screen.getByText(/nobody to call/i)).toBeInTheDocument();
    expect(screen.getByText(/kept here rather than on your list/i)).toBeInTheDocument();
  });

  it('tells a screen reader why the row shows an identifier', () => {
    // The visible row is a truncated id. Without this, somebody who cannot see
    // the section heading meets eight hex characters and no explanation.
    render(<NeedsIdentity accounts={[account()]} identities={identities()} />);

    expect(screen.getByText(/— no source has named this account/i)).toBeInTheDocument();
  });

  it('says how much is known, because four sources is not one', () => {
    render(<NeedsIdentity accounts={[account()]} identities={identities()} />);

    expect(screen.getByText(/4 sources have reported/i)).toBeInTheDocument();
  });

  it('counts one source without saying "1 sources"', () => {
    render(
      <NeedsIdentity
        accounts={[account()]}
        identities={identities(identity({ source_count: 1 }))}
      />,
    );

    expect(screen.getByText(/1 source has reported/i)).toBeInTheDocument();
  });
});

describe('it is never workable, which is the half that was a live defect', () => {
  it('offers no way to take the account on', () => {
    /**
     * **PX-301.** The working list offered *"I'm working this"* on a record
     * nobody can name — a button that cannot work, pressed by somebody who
     * then has nothing to do. C-321 ruled workable **never**.
     */
    render(<NeedsIdentity accounts={[account()]} identities={identities()} />);

    expect(screen.queryByRole('button')).not.toBeInTheDocument();
  });

  it('does not say anybody holds it', () => {
    // An ownership badge here would imply somebody is working an account that
    // cannot be worked.
    const { container } = render(
      <NeedsIdentity accounts={[account({ owner_id: null })]} identities={identities()} />,
    );

    expect(container.textContent).not.toMatch(/yours|taken|being worked/i);
  });

  it('does not offer the account as a link', () => {
    // The working list deliberately keeps an unnamed account openable, because
    // it is the one a seller most wants to explain. Here the row is already
    // the statement, and dressing an id as a name puts the id where the name
    // would go.
    const { container } = render(
      <NeedsIdentity accounts={[account()]} identities={identities()} />,
    );

    expect(container.querySelector('a')).toBeNull();
  });
});

describe('a workspace whose sources name everything never learns this exists', () => {
  it('renders nothing when no account needs identifying', () => {
    const { container } = render(<NeedsIdentity accounts={[]} identities={identities()} />);

    expect(container).toBeEmptyDOMElement();
  });

  it('still lists the account when its identity row never arrived', () => {
    // The partition upstream is what decides an account belongs here. A
    // missing identity row must not make the row itself disappear — that
    // would drop evidence on the floor for the exact records this exists for.
    render(<NeedsIdentity accounts={[account()]} identities={undefined} />);

    expect(screen.getByText('70b04700')).toBeInTheDocument();
  });
});

describe('it speaks about one account differently from several', () => {
  it('uses the singular for a single record', () => {
    render(<NeedsIdentity accounts={[account()]} identities={identities()} />);

    const heading = screen.getByRole('heading', { name: /needs identity/i });
    const section = heading.closest('section');
    expect(section).not.toBeNull();
    expect(within(section as HTMLElement).getByText(/this company/i)).toBeInTheDocument();
  });

  it('uses the plural for more than one', () => {
    render(
      <NeedsIdentity
        accounts={[account(), account({ id: 'bbbb', account_id: 'ffffffff-2222-4222-8222-222222222222' })]}
        identities={identities()}
      />,
    );

    expect(screen.getByText(/these companies/i)).toBeInTheDocument();
  });
});
