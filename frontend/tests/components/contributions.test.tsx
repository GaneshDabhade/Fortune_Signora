/**
 * The arithmetic, as a customer reads it.
 *
 * These are not rendering tests. Each asserts a **product rule** that would be
 * invisible if it broke: a figure quietly recomputed in the browser, a line
 * silently dropped, a reason paraphrased into something friendlier and
 * uncheckable. The ledger is the one artifact in Signora whose whole job is to
 * be argued with, and a screen that softens it destroys the only thing no
 * competitor's summary survives.
 */
import { render, screen, within } from '@testing-library/react';
import { describe, expect, it } from 'vitest';

import {
  ContributionList,
  PostureSplit,
  ReadingValidity,
  ScoreArithmetic,
  WhatMovedIt,
} from '@/components/intelligence/contributions';
import type { AccountScore, ScoreContribution } from '@/lib/api/types';

function line(overrides: Partial<ScoreContribution> = {}): ScoreContribution {
  return {
    business_event_id: '11111111-1111-4111-8111-111111111111',
    signal_id: '22222222-2222-4222-8222-222222222222',
    posture: 'expansionary',
    relevance: 'primary',
    evidence_age: 'fresh',
    points: 24,
    counted: true,
    dissenting: false,
    reason:
      'Displacement opportunity · primary relevance · fresh evidence (100%) — 24 points',
    ...overrides,
  };
}

function reading(overrides: Partial<AccountScore> = {}): AccountScore {
  return {
    account_id: '33333333-3333-4333-8333-333333333333',
    score: 40,
    trend: 'rising',
    score_change: 8,
    trigger: 'signal_generated',
    contested: false,
    computed_at: '2026-07-01T00:00:00Z',
    valid_until: '2026-08-12T00:00:00Z',
    is_current: true,
    points: 48,
    ceiling: 120,
    attention_by_posture: { expansionary: 48 },
    contributions: [line()],
    ...overrides,
  };
}

describe('the score is shown as a division, not a gauge', () => {
  it("shows the number beside the design's denominator", () => {
    // 📁 **The design's figure row is `38` then `/ 100`** — `Design Documents/
    // Fortune Signora Account 360.html`, the `#score` card. ⛔ **This asserted
    // `48 of 120 points`**, which is the RAW arithmetic the design puts one
    // level down, in the contribution rows.
    render(<ScoreArithmetic score={reading()} />);

    expect(screen.getByText('40')).toBeInTheDocument();
    expect(screen.getByText('/ 100')).toBeInTheDocument();
  });

  it('never lets a screen reader announce a figure the screen does not show', () => {
    // As two adjacent fragments these read out concatenated: a score of 1
    // beside 2 points announced as "attention score 12 of 120 points" — a
    // different number, stated confidently. One sentence replaces both.
    const { container } = render(
      <ScoreArithmetic score={reading({ score: 1, points: 2, ceiling: 120 })} />,
    );

    const announced = Array.from(container.querySelectorAll(':not([aria-hidden])'))
      .map((node) => node.textContent ?? '')
      .join(' ');

    expect(announced).toContain('Account score 1 out of 100');
    expect(announced).not.toMatch(/score 12\b/);
  });

  it('draws no progress element and states no percentage', () => {
    // A filled ring implies a maximum that means something. This is an
    // ordering of attention; 40 is not "40% likely to buy".
    const { container } = render(<ScoreArithmetic score={reading()} />);

    expect(container.querySelector('progress, meter, svg')).toBeNull();
    expect(container.textContent).not.toContain('%');
  });

  it('displays the point total the server sent rather than re-adding the lines', () => {
    // **The ledger has exactly one implementation.** If the screen summed the
    // contributions itself it would silently disagree the first time an
    // uncounted line was included — which is every contested account.
    const server = reading({
      points: 48,
      contributions: [
        line({ points: 24 }),
        line({
          signal_id: '44444444-4444-4444-8444-444444444444',
          points: 24,
          counted: false,
        }),
      ],
    });

    const { container } = render(<ScoreArithmetic score={server} />);

    // ⚡ **Asserted in the ACCESSIBLE SENTENCE, which already carried it** —
    // ⛔ **not weakened**: the property is *the server's total is displayed
    // rather than re-added*, and the sentence states exactly that figure. 📁
    // The visible denominator moved to the design's `/ 100`; the arithmetic did
    // not move, it was always in both places.
    const announced = Array.from(container.querySelectorAll(':not([aria-hidden])'))
      .map((node) => node.textContent ?? '')
      .join(' ');
    expect(announced).toContain('from 48 of 120');
  });
});

describe('a reading states how long it is correct for', () => {
  it('says until when, rather than how recent it is', () => {
    render(<ReadingValidity score={reading()} />);

    expect(screen.getByText(/Exactly correct until/)).toBeInTheDocument();
  });

  it('says an expired reading expired, and does not hide it', () => {
    render(<ReadingValidity score={reading({ is_current: false })} />);

    expect(screen.getByText(/expired/)).toBeInTheDocument();
  });

  it('trusts the server about currency rather than the browser clock', () => {
    // `valid_until` is in the past and `is_current` is true. A screen
    // comparing timestamps itself would call this expired — and would give two
    // readers in two time zones two different answers about one stored fact.
    render(
      <ReadingValidity
        score={reading({ valid_until: '2000-01-01T00:00:00Z', is_current: true })}
      />,
    );

    expect(screen.queryByText(/expired/)).not.toBeInTheDocument();
  });

  it('explains a null validity instead of leaving the sentence unfinished', () => {
    render(<ReadingValidity score={reading({ valid_until: null })} />);

    expect(screen.getByText(/new evidence arrives/)).toBeInTheDocument();
  });
});

describe('posture is shown, never summed', () => {
  it('lists each posture that carries attention', () => {
    render(
      <PostureSplit
        score={reading({
          attention_by_posture: { expansionary: 30, contractionary: 18 },
        })}
      />,
    );

    expect(screen.getByText('30')).toBeInTheDocument();
    expect(screen.getByText('18')).toBeInTheDocument();
  });

  it('does not net opposing readings into one figure', () => {
    // 30 expansion and 18 risk is not "12". Netting them would score a
    // fought-over account like an inert one, and those are the two most
    // different accounts in the book.
    const { container } = render(
      <PostureSplit
        score={reading({
          attention_by_posture: { expansionary: 30, contractionary: 18 },
        })}
      />,
    );

    expect(container.textContent).not.toContain('12');
  });

  it('renders nothing when no posture carries attention', () => {
    const { container } = render(
      <PostureSplit score={reading({ attention_by_posture: {} })} />,
    );

    expect(container).toBeEmptyDOMElement();
  });
});

describe('every line stays on the page', () => {
  it('keeps a line that counted nothing, with its reason', () => {
    // A zero you can read is information; a row that vanished is a mystery —
    // and the question it produces goes to support instead.
    // A different signal reading the same business event — which is exactly
    // the shape an uncounted line has, and why the row is keyed on the pair.
    const uncounted = line({
      signal_id: '44444444-4444-4444-8444-444444444444',
      points: 0,
      counted: false,
      reason: 'Already counted through a higher-weighted hypothesis.',
    });

    render(<ContributionList score={reading({ contributions: [line(), uncounted] })} />);

    expect(
      screen.getByText('Already counted through a higher-weighted hypothesis.'),
    ).toBeInTheDocument();
  });

  it('renders the reason the pipeline wrote, word for word', () => {
    // **A placement, never a paraphrase.** The sentence is rendered from the
    // same fields an auditor checks; rewording it here would make the number
    // uncheckable against the record.
    const reason =
      'Budget unlocked · supporting relevance · ageing evidence (30%) — 6 points';

    render(<ContributionList score={reading({ contributions: [line({ reason })] })} />);

    expect(screen.getByText(reason)).toBeInTheDocument();
  });

  it('marks the lines that disagree with the majority reading', () => {
    render(
      <ContributionList
        score={reading({ contributions: [line({ dissenting: true })] })}
      />,
    );

    expect(screen.getByText('Disagrees with the majority reading')).toBeInTheDocument();
  });

  it('says nothing about dissent when nothing dissents', () => {
    render(<ContributionList score={reading()} />);

    expect(screen.queryByText(/Disagrees/)).not.toBeInTheDocument();
  });

  it('preserves the order the pipeline recorded', () => {
    // Storage order *is* the explanation's order — largest contribution first,
    // so the first line read is the one that most explains the number.
    // Re-sorting here would answer a different question from the ledger's.
    const score = reading({
      contributions: [
        line({ reason: 'first', points: 24 }),
        line({
          reason: 'second',
          points: 18,
          signal_id: '44444444-4444-4444-8444-444444444444',
        }),
      ],
    });

    render(<ContributionList score={score} />);
    const [first, second] = screen.getAllByRole('listitem');

    expect(within(first!).getByText('first')).toBeInTheDocument();
    expect(within(second!).getByText('second')).toBeInTheDocument();
  });
});


/**
 * 🔴 **📁 *"What moved it"* — the Opportunity Intelligence design's waterfall.**
 *
 * ⚡ **The properties worth protecting are about DERIVATION**: the design gives
 * each factor a `left` and a `width`, and both must come from the running total
 * rather than from the document's own worked example.
 */
describe('what moved it — the design\'s waterfall', () => {
  it('📁 renders the design\'s heading and one row per counted move', () => {
    render(
      <WhatMovedIt
        score={reading({
          contributions: [
            line({ signal_id: '22222221-2222-4222-8222-222222222221', points: -9, reason: 'Two close-date slips' }),
            line({ signal_id: '22222222-2222-4222-8222-222222222222', points: -5, reason: '19 days without contact' }),
            line({ signal_id: '22222223-2222-4222-8222-222222222223', points: 2, reason: 'Usage 91%, support clean' }),
          ],
        })}
      />,
    );

    expect(screen.getByRole('heading', { name: 'What moved it' })).toBeInTheDocument();
    expect(screen.getAllByRole('listitem')).toHaveLength(3);
    // ⚡ **Signed, and the positive one carries its `+`** — 📁 the design writes
    // `−9` and `+2`, and an unsigned `2` reads as a magnitude.
    expect(screen.getByText('-9')).toBeInTheDocument();
    expect(screen.getByText('+2')).toBeInTheDocument();
  });

  /**
   * 🔴 **The waterfall property.** ⛔ **A bar chart starts every bar at the same
   * edge**; 📁 the design offsets each by where it acted on the running total,
   * **so the reader sees a descent rather than five magnitudes.**
   */
  it('🔴 offsets each segment by the running total, and the widths sum to the whole', () => {
    const { container } = render(
      <WhatMovedIt
        score={reading({
          contributions: [
            line({ signal_id: '22222224-2222-4222-8222-222222222224', points: -6, reason: 'first' }),
            line({ signal_id: '22222225-2222-4222-8222-222222222225', points: -2, reason: 'second' }),
            line({ signal_id: '22222226-2222-4222-8222-222222222226', points: 2, reason: 'third' }),
          ],
        })}
      />,
    );

    const bars = [...container.querySelectorAll('[style*="width"]')] as HTMLElement[];
    const widths = bars.map((b) => Number.parseFloat(b.style.width));
    const lefts = bars.map((b) => Number.parseFloat(b.style.left));

    // 10 points of movement: 60% · 20% · 20%.
    expect(widths).toEqual([60, 20, 20]);
    // ⚡ **Each starts where the previous ended** — that is the waterfall.
    expect(lefts).toEqual([0, 60, 80]);
  });

  /**
   * ⛔ **`counted: false` means the evidence did not move the number.** ⚡ **A
   * segment for it would draw a descent that never happened** — and the line is
   * still visible in `ContributionList`, where the question is different.
   */
  it('⛔ draws nothing for a line that did not move the score', () => {
    render(
      <WhatMovedIt
        score={reading({
          contributions: [
            line({ signal_id: '22222227-2222-4222-8222-222222222227', points: -6, reason: 'counted' }),
            line({ signal_id: '22222228-2222-4222-8222-222222222228', points: -9, reason: 'ignored', counted: false }),
            line({ signal_id: '22222229-2222-4222-8222-222222222229', points: 0, reason: 'zero', counted: true }),
          ],
        })}
      />,
    );

    expect(screen.getAllByRole('listitem')).toHaveLength(1);
    expect(screen.queryByText('ignored')).not.toBeInTheDocument();
  });

  /**
   * 🔴 **📁 The design's label is the FACTOR'S NAME, not the whole sentence** —
   * *"Two close-date slips"*, not *"Two close-date slips · primary relevance ·
   * fresh evidence (100%) — 9 points"*.
   *
   * ⚠️ **This shipped wrong and a screenshot caught it**: the full `reason`
   * truncated to *"Active evaluation · primary ..."* at the design's 180px, and
   * duplicated the row directly above it.
   */
  it("🔴 shows the factor's name, not the composed sentence", () => {
    render(
      <WhatMovedIt
        score={reading({
          contributions: [
            line({
              signal_id: '29292929-2929-4929-8929-292929292929',
              points: -9,
              reason:
                'Two close-date slips \u00b7 primary relevance \u00b7 fresh evidence (100%) — 9 points',
            }),
          ],
        })}
      />,
    );

    expect(screen.getByText('Two close-date slips')).toBeInTheDocument();
    expect(screen.queryByText(/primary relevance/)).not.toBeInTheDocument();
    // ⚡ **The whole sentence stays reachable rather than discarded.**
    expect(screen.getByTitle(/primary relevance/)).toBeInTheDocument();
  });

  /** ⛔ **A coupling stated rather than hidden** — if the server ever stops
   *  separating the title, the whole sentence is used and nothing breaks. */
  it('falls back to the whole sentence when there is no separator', () => {
    render(
      <WhatMovedIt
        score={reading({
          contributions: [
            line({
              signal_id: '30303030-3030-4030-8030-303030303030',
              points: -4,
              reason: 'A sentence with no separator at all',
            }),
          ],
        })}
      />,
    );
    expect(screen.getByText('A sentence with no separator at all')).toBeInTheDocument();
  });

  /** ⚡ **Absent, never an empty frame** — a heading over nothing states that a
   *  section exists and has failed, which is not what an unmoved score means. */
  it('renders nothing at all when no line moved the score', () => {
    const { container } = render(<WhatMovedIt score={reading({ contributions: [] })} />);
    expect(container).toBeEmptyDOMElement();
  });

  it('survives a score that has not loaded', () => {
    const { container } = render(<WhatMovedIt score={undefined} />);
    expect(container).toBeEmptyDOMElement();
  });
});
