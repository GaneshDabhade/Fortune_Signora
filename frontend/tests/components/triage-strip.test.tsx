/**
 * What the attention list is asking, above the list that answers it.
 *
 * **Not a card, not a chart, not a counter.** The homepage retired an Overview
 * page of three permanently-empty counters at M12.3 (**D38**), and a strip of
 * KPI tiles would be that page returning in a smaller font. These assertions
 * are what stop it becoming one: it disappears entirely when there is nothing
 * to say, and every line narrows the list rather than reporting on it.
 */
import { render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';

import { TriageStrip } from '@/components/intelligence/triage';
import type { AccountAttention } from '@/lib/api/types';
import { triage } from '@/lib/state/triage';

function account(overrides: Partial<AccountAttention> = {}): AccountAttention {
  return {
    id: 'opp-1',
    account_id: 'acc-1',
    score: 70,
    trend: 'steady',
    score_change: 0,
    signal_type: 'hiring_surge',
    posture: 'expansionary',
    contested: false,
    evidence: 'current',
    stage: 'tracking',
    owner_id: null,
    opened_at: '2026-07-01T00:00:00Z',
    since: '2026-07-01T00:00:00Z',
    ...overrides,
  };
}

describe('a list that raises nothing shows no strip at all', () => {
  it('renders nothing rather than an empty container', () => {
    // **Absent, never present at zero.** A control that always shows the same
    // thing teaches people to ignore controls (R1-06 · D6) — so a reader who
    // sees this strip knows, before reading it, that something needs a look.
    const { container } = render(
      <TriageStrip groups={triage([account(), account()])} active={null} scope="all" />,
    );

    expect(container).toBeEmptyDOMElement();
  });
});

describe('a list that raises something says what, and how many', () => {
  it('names the question in a seller"s words and counts it', () => {
    render(
      <TriageStrip
        groups={triage([account({ contested: true }), account({ contested: true })])}
        active={null}
        scope="all"
      />,
    );

    expect(screen.getByText('2')).toBeInTheDocument();
    expect(screen.getByText(/worth verifying/i)).toBeInTheDocument();
  });

  it('explains the question rather than leaving the label to be guessed at', () => {
    render(
      <TriageStrip groups={triage([account({ evidence: 'stale' })])} active={null} scope="all" />,
    );

    expect(screen.getByText(/evidence behind the score has aged/i)).toBeInTheDocument();
  });

  it('never puts a pipeline word in front of a seller', () => {
    // ADR-0034: the translation lives at the frontend edge and never travels
    // inward. `contested` and `evidence_state` are the pipeline's words.
    const { container } = render(
      <TriageStrip
        groups={triage([account({ contested: true, evidence: 'cooling' })])}
        active={null}
        scope="all"
      />,
    );

    expect(container.textContent?.toLowerCase()).not.toContain('contested');
    expect(container.textContent?.toLowerCase()).not.toContain('evidence_state');
  });
});

describe('every line narrows the list rather than reporting on it', () => {
  it('links to the filtered view', () => {
    render(
      <TriageStrip groups={triage([account({ contested: true })])} active={null} scope="all" />,
    );

    expect(screen.getByRole('link', { name: /worth verifying/i })).toHaveAttribute(
      'href',
      '/?raises=verify',
    );
  });

  it('keeps the seller"s scope when they filter', () => {
    // A seller looking at their own accounts who filters by question must not
    // silently be handed everybody else's.
    render(
      <TriageStrip groups={triage([account({ contested: true })])} active={null} scope="mine" />,
    );

    expect(screen.getByRole('link', { name: /worth verifying/i })).toHaveAttribute(
      'href',
      '/?owner=mine&raises=verify',
    );
  });

  it('clears the filter when the active question is clicked again', () => {
    // A filter a seller cannot switch off is a filter they navigate away from.
    render(
      <TriageStrip groups={triage([account({ contested: true })])} active="verify" scope="all" />,
    );

    expect(screen.getByRole('link', { name: /worth verifying/i })).toHaveAttribute('href', '/');
  });

  it('tells a screen reader which question is in force', () => {
    render(
      <TriageStrip groups={triage([account({ contested: true })])} active="verify" scope="all" />,
    );

    expect(screen.getByRole('link', { name: /worth verifying/i })).toHaveAttribute(
      'aria-current',
      'true',
    );
  });

  it('is a landmark a keyboard reader can reach', () => {
    render(
      <TriageStrip groups={triage([account({ contested: true })])} active={null} scope="all" />,
    );

    expect(screen.getByRole('navigation', { name: /raising/i })).toBeInTheDocument();
  });
});
