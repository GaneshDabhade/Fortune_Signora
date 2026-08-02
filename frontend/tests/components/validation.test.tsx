/**
 * The first thing Signora says about what to *do*.
 *
 * These assert the rules that keep it from becoming something it is not: a
 * recommendation, a hedge, or a checklist that forgets. The content is
 * domain-authored catalog prose — the screen's whole job is to place it without
 * changing what it claims.
 */
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, expect, it, vi } from 'vitest';

import { ValidationBlock } from '@/components/intelligence/validation';
import type { AccountValidation, HypothesisValidation } from '@/lib/api/types';

function hypothesis(overrides: Partial<HypothesisValidation> = {}): HypothesisValidation {
  return {
    signal_id: '11111111-1111-4111-8111-111111111111',
    title: 'Expansion opportunity',
    hypothesis:
      'Sustained investment across several fronts suggests the company is adding capacity.',
    relevance: 'primary',
    limitations: [
      'Investment ahead of growth says nothing about budget for your category.',
      'It does not indicate that a purchase decision is underway.',
      'Growth in one division does not imply growth in the one you sell to.',
    ],
    suggested_validation: [
      'Check which functions the recent hiring is in.',
      'Ask on a first call which division the investment sits in.',
    ],
    observed: [
      {
        business_event_id: 'eeee1111-1111-4111-8111-111111111111',
        summary: 'Headcount in platform engineering grew 29,000 to 34,000.',
        occurred_at: '2026-07-04T00:00:00Z',
      },
    ],
    ...overrides,
  };
}

function validation(overrides: Partial<AccountValidation> = {}): AccountValidation {
  return {
    account_id: '22222222-2222-4222-8222-222222222222',
    hypotheses: [hypothesis()],
    ...overrides,
  };
}

describe('the checks are what a seller acts on', () => {
  it('shows every step the catalog suggests', () => {
    render(<ValidationBlock validation={validation()} />);

    expect(
      screen.getByText('Check which functions the recent hiring is in.'),
    ).toBeInTheDocument();
    expect(
      screen.getByText('Ask on a first call which division the investment sits in.'),
    ).toBeInTheDocument();
  });

  it('renders no checkbox, because there is nowhere to store a tick', () => {
    // It looks exactly like a checklist and nothing owns per-user state. A
    // control that forgets is worse than no control.
    const { container } = render(<ValidationBlock validation={validation()} />);

    expect(container.querySelector('input[type="checkbox"]')).toBeNull();
  });

  it('leaves the hypothesis phrased as a possibility', () => {
    // A signal suggests and never asserts. Firming this into a statement would
    // move the claim past what the evidence supports.
    render(<ValidationBlock validation={validation()} />);

    expect(
      screen.getByText(/suggests the company is adding capacity/),
    ).toBeInTheDocument();
  });

  it('renders nothing at all when no hypothesis is live', () => {
    // Not an empty state: the brief explains itself without this, and a panel
    // announcing a gap is worse than the gap.
    const { container } = render(
      <ValidationBlock validation={validation({ hypotheses: [] })} />,
    );

    expect(container).toBeEmptyDOMElement();
  });
});

describe('the limitations are present, and subordinate', () => {
  it('is collapsed on arrival', async () => {
    render(<ValidationBlock validation={validation()} />);

    expect(screen.getByRole('button', { name: /cannot tell you/ })).toHaveAttribute(
      'aria-expanded',
      'false',
    );
  });

  it('puts the first limitation on the page, unopened', () => {
    // **R2-02.** "This is the bit I'd want my reps to read, and it's the bit
    // they'll never open." No competitor tells a seller what their signal
    // cannot prove; it was the most differentiating sentence on the screen and
    // the smallest text on it.
    render(<ValidationBlock validation={validation()} />);

    expect(
      screen.getByText(/Investment ahead of growth says nothing about budget/),
    ).toBeVisible();
  });

  it("promotes the catalog's first limitation, not an arbitrary one", () => {
    // The catalog orders them and the first is the strongest. Showing one is
    // only defensible because showing *the first* is not showing any old one.
    //
    // Asserted by structure rather than by visibility: the others are
    // `sr-only`, deliberately, so a screen reader can still reach them — and
    // `toBeVisible` cannot tell `sr-only` from on-screen.
    render(<ValidationBlock validation={validation()} />);

    // `.closest('p')` because the label is its own span — the sentence lives
    // in the paragraph around it.
    const promoted =
      screen.getByText(/What this cannot tell you/).closest('p')?.textContent ?? '';

    expect(promoted).toContain('Investment ahead of growth says nothing about budget');
    expect(promoted).not.toContain('Growth in one division');
  });

  it('reads as calibration rather than as a warning', () => {
    // A limitation drawn as an alert would make Signora look unsure of a
    // conclusion it is in fact sure of. What it is unsure of is precisely and
    // only what the sentence says.
    const { container } = render(<ValidationBlock validation={validation()} />);

    const inline = screen.getByText(/Investment ahead of growth/);
    expect(inline.className).not.toMatch(/danger|warning/);
    expect(container.querySelector('[class*="warning"]')).toBeNull();
  });

  it('offers no disclosure when there is nothing more to disclose', () => {
    render(
      <ValidationBlock
        validation={validation({
          hypotheses: [
            {
              ...validation().hypotheses[0]!,
              limitations: ['The only thing it cannot tell you.'],
            },
          ],
        })}
      />,
    );

    expect(screen.getByText('The only thing it cannot tell you.')).toBeVisible();
    expect(screen.queryByRole('button', { name: /more things/ })).toBeNull();
  });

  it('counts what is still hidden, not what is on the screen', () => {
    // "2 more things this cannot tell you" is itself information — it sets the
    // expectation rather than making the reader discover the volume. Since
    // R2-02 the first is inline, so a trigger still saying *three* would be
    // counting a sentence the reader can already see.
    render(<ValidationBlock validation={validation()} />);

    expect(screen.getByRole('button', { name: /^2 more things/ })).toBeInTheDocument();
  });

  it('keeps every caveat in the accessibility tree while closed', async () => {
    // `sr-only` rather than `hidden`: a caveat a screen reader cannot reach is
    // a caveat that was not given, and browser search must find it too.
    render(<ValidationBlock validation={validation()} />);

    expect(
      screen.getByText('It does not indicate that a purchase decision is underway.'),
    ).toBeInTheDocument();
  });

  it('opens and closes from the keyboard', async () => {
    const user = userEvent.setup();
    render(<ValidationBlock validation={validation()} />);
    const disclosure = screen.getByRole('button', { name: /cannot tell you/ });

    await user.tab();
    expect(disclosure).toHaveFocus();

    await user.keyboard('{Enter}');
    expect(disclosure).toHaveAttribute('aria-expanded', 'true');

    await user.keyboard('{Enter}');
    expect(disclosure).toHaveAttribute('aria-expanded', 'false');
  });

  it('names which hypothesis it is qualifying', () => {
    // A limitation detached from what it qualifies is meaningless — "this
    // cannot tell you about budget" is unreadable without knowing which
    // "this". The grouping is a correctness property, not a layout choice.
    render(<ValidationBlock validation={validation()} />);

    expect(
      screen.getByRole('button', { name: /Expansion opportunity cannot tell you/ }),
    ).toBeInTheDocument();
  });
});

describe('relevance is shown only when it explains something', () => {
  it('says nothing on a primary hypothesis', () => {
    render(<ValidationBlock validation={validation()} />);

    expect(screen.queryByText('primary')).not.toBeInTheDocument();
  });

  it('labels one that is lower than the reader would expect', () => {
    // The entries are already ordered by relevance, so the label earns its
    // place exactly when it explains why something sits further down.
    render(
      <ValidationBlock
        validation={validation({ hypotheses: [hypothesis({ relevance: 'contextual' })] })}
      />,
    );

    expect(screen.getByText('contextual')).toBeInTheDocument();
  });
});

describe('nothing here is a recommendation', () => {
  it('never states what to do about this specific company', () => {
    // The guidance is a property of the hypothesis type — identical for every
    // account and every workspace. Prose naming the account would be an
    // inference wearing the catalog's clothes.
    const { container } = render(<ValidationBlock validation={validation()} />);
    const text = container.textContent ?? '';

    expect(text).not.toContain('22222222-2222-4222-8222-222222222222');
  });

  it('offers no confidence figure', () => {
    // A number here would be a judgement about this account that nothing
    // computed. The catalog knows what a hypothesis cannot prove; it does not
    // know how likely this one is.
    const { container } = render(<ValidationBlock validation={validation()} />);

    expect(container.textContent).not.toMatch(/\d+%/);
  });
});

describe('the generic guidance is anchored to this account — R2-01', () => {
  it('names what this account actually did', () => {
    // "It gave me the same advice for two different companies, so I assumed it
    // wasn't really looking at either." The advice is generic by design; what
    // it points at is not.
    render(<ValidationBlock validation={validation()} />);

    expect(
      screen.getByText('Headcount in platform engineering grew 29,000 to 34,000.'),
    ).toBeVisible();
  });

  it('keeps the checks generic — they are a property of the type', () => {
    // Making the checks per-account would make them a recommendation, which is
    // a different product with a different burden of proof.
    render(<ValidationBlock validation={validation()} />);

    expect(
      screen.getByText('Check which functions the recent hiring is in.'),
    ).toBeVisible();
  });

  it('opens the recorded event in the drawer the ledger already uses', async () => {
    const open = vi.fn();
    render(<ValidationBlock validation={validation()} onOpenEvidence={open} />);

    await userEvent.click(screen.getByRole('button', { name: /Headcount in platform/ }));

    // One citation, one drawer, one wording. A second concept for the same
    // fact is how a customer catches a product contradicting itself.
    expect(open).toHaveBeenCalledWith('eeee1111-1111-4111-8111-111111111111');
  });

  it('draws no affordance when there is nowhere to send the reader', () => {
    // The rule the ledger already follows: a control that looks clickable and
    // goes nowhere costs more trust than the missing feature does.
    render(<ValidationBlock validation={validation()} />);

    expect(screen.queryByRole('button', { name: /Headcount in platform/ })).toBeNull();
  });

  it('says nothing at all when the cited events no longer resolve', () => {
    // A signal cannot exist citing nothing, so an empty list means the
    // evidence was removed underneath it — rendered as absence, never a guess.
    render(
      <ValidationBlock
        validation={validation({ hypotheses: [hypothesis({ observed: [] })] })}
      />,
    );

    expect(screen.queryByText('What we saw here')).toBeNull();
  });
});
