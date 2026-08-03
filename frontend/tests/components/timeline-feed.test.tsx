import { render, screen, within } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';

import {
  AccountHistory,
  HEADLINE,
  PROMINENCE,
  detailLine,
  headlineOf,
} from '@/components/timeline/feed';
import type { TimelineEntry, TimelineEntryKind } from '@/lib/api/types';

const KINDS: TimelineEntryKind[] = [
  'observation_recorded',
  'observation_superseded',
  'business_event_detected',
  'business_event_superseded',
  'signal_generated',
  'signal_superseded',
  'buying_score_updated',
  'opportunity_created',
  'opportunity_stage_changed',
];

function entry(overrides: Partial<TimelineEntry> = {}): TimelineEntry {
  return {
    id: crypto.randomUUID(),
    kind: 'signal_generated',
    occurred_at: '2026-05-01T09:30:00+00:00',
    source_module: 'signal_engine',
    source_ref: crypto.randomUUID(),
    detail: {},
    ...overrides,
  };
}

function renderFeed(entries: TimelineEntry[], overrides: Record<string, unknown> = {}) {
  return render(
    <AccountHistory
      entries={entries}
      hasMore={false}
      isLoading={false}
      isLoadingMore={false}
      isError={false}
      onLoadMore={vi.fn()}
      {...overrides}
    />,
  );
}

describe('every kind is renderable', () => {
  it.each(KINDS)('%s has a headline and a prominence', (kind) => {
    // A kind the API can send and this component cannot render would reach a
    // customer as a blank row. The maps are exhaustive by type; this asserts
    // the values are real rather than merely present.
    expect(HEADLINE[kind]).toBeTruthy();
    expect(PROMINENCE[kind]).toBeTruthy();
  });

  it('says nothing in engineering vocabulary', () => {
    const forbidden = /observation|business event|buying score|entity|projection|signal type/i;
    for (const kind of KINDS) expect(HEADLINE[kind]).not.toMatch(forbidden);
  });
});

describe('emphasis is presentation, never ranking', () => {
  it('shows quiet entries as well as loud ones', () => {
    // **The invariant this component could most easily break.** Timeline ranks
    // nothing; if de-emphasis became filtering, the feed would start deciding
    // what a seller is allowed to see.
    renderFeed([
      entry({ kind: 'opportunity_created' }),
      entry({ kind: 'observation_recorded' }),
    ]);
    expect(screen.getByText(HEADLINE.opportunity_created)).toBeInTheDocument();
    expect(screen.getByText(HEADLINE.observation_recorded)).toBeInTheDocument();
  });

  it('keeps the order it was given', () => {
    renderFeed([
      entry({ kind: 'observation_recorded', occurred_at: '2026-05-01T11:00:00+00:00' }),
      entry({ kind: 'opportunity_created', occurred_at: '2026-05-01T09:00:00+00:00' }),
    ]);
    // A guard that narrows, rather than `!` or a cast. `getAllByRole` returns
    // `HTMLElement[]`, and under `noUncheckedIndexedAccess` an index yields
    // `HTMLElement | undefined`. Throwing states what the test already depends
    // on — two rows rendered — and fails here with a readable message instead
    // of somewhere less obvious if the feed ever renders none.
    const [first, second] = screen.getAllByRole('listitem');
    if (!first || !second) throw new Error('expected two entries to render');
    expect(within(first).getByText(HEADLINE.observation_recorded)).toBeInTheDocument();
    expect(within(second).getByText(HEADLINE.opportunity_created)).toBeInTheDocument();
  });
});

describe('grouping', () => {
  it('groups entries under the day they happened', () => {
    renderFeed([
      entry({ occurred_at: '2026-05-02T09:00:00+00:00' }),
      entry({ occurred_at: '2026-05-01T09:00:00+00:00' }),
      entry({ occurred_at: '2026-05-01T18:00:00+00:00' }),
    ]);
    expect(screen.getAllByRole('list')).toHaveLength(2);
  });
});

describe('detail lines', () => {
  it('reads a stage change as a movement', () => {
    expect(
      detailLine(
        entry({
          kind: 'opportunity_stage_changed',
          detail: { previous_stage: 'open', new_stage: 'in_progress' },
        }),
      ),
    ).toBe('Open to In progress');
  });

  it('does not say a stage moved when it did not — LO-04', () => {
    // **A hand-over is a workflow state whose stage did not move**, so it
    // arrives here as `opportunity.stage_changed` with both stages equal and
    // would have read *"Opportunity moved — Working it to Working it"*: a
    // sentence that says nothing twice, on the feed a seller uses to
    // understand an account. Found by asking what the new capability would
    // project, rather than after somebody saw it.
    const handover = entry({
      kind: 'opportunity_stage_changed',
      detail: {
        previous_stage: 'engaged',
        new_stage: 'engaged',
        reason: 'On leave until March.',
      },
    });

    expect(headlineOf(handover)).toBe('Account handed over');
    // The reason is the entire content of the entry — what a colleague opening
    // this account next week actually needs.
    expect(detailLine(handover)).toBe('On leave until March.');
  });

  it('still reads a real stage change as a movement', () => {
    const moved = entry({
      kind: 'opportunity_stage_changed',
      detail: { previous_stage: 'tracking', new_stage: 'engaged' },
    });

    expect(headlineOf(moved)).toBe(HEADLINE.opportunity_stage_changed);
    expect(detailLine(moved)).toBe('Tracking to Engaged');
  });

  it('says a score out of one hundred rather than a bare number', () => {
    expect(detailLine(entry({ kind: 'buying_score_updated', detail: { score: 62 } }))).toBe(
      'Now 62 out of 100',
    );
  });

  it('omits the line rather than inventing one when detail is absent', () => {
    // The API sends a bounded allow-list and an optional field may simply not
    // be there. A component that filled the gap would be inventing content.
    expect(detailLine(entry({ kind: 'signal_generated', detail: {} }))).toBeNull();
  });
});

describe('states a customer can reach', () => {
  it('says so when nothing has been recorded', () => {
    renderFeed([]);
    expect(screen.getByText(/nothing has been recorded/i)).toBeInTheDocument();
  });

  it('renders an error rather than vanishing', () => {
    // The defect B-006 was: a section that disappears on failure reads as a
    // feature the customer does not have.
    renderFeed([], { isError: true });
    expect(screen.getByText(/could not be loaded/i)).toBeInTheDocument();
  });

  it('says the history is complete when there is no more', () => {
    renderFeed([entry()]);
    expect(screen.getByText(/whole history/i)).toBeInTheDocument();
  });

  it('offers earlier activity when there is more', () => {
    renderFeed([entry()], { hasMore: true });
    expect(screen.getByRole('button', { name: /earlier activity/i })).toBeInTheDocument();
  });
});
