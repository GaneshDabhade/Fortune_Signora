/**
 * Model-authored language, as a customer reads it.
 *
 * **The first generated content in the product**, and the tests that matter are
 * about trust rather than layout: whether a reader can tell what a machine
 * wrote, whether every sentence is visibly anchored, and whether the screen
 * ever presents prose as though it were a measurement.
 */
import { render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';

import { NarrativeBlock } from '@/components/intelligence/narration';
import type { AccountNarration } from '@/lib/api/types';

function narration(overrides: Partial<AccountNarration> = {}): AccountNarration {
  return {
    account_id: '11111111-1111-4111-8111-111111111111',
    statements: [
      {
        text: 'Hiring and revenue both moved in the last month.',
        evidence: ['signal:aaaa', 'business_event:bbbb'],
      },
      {
        text: 'Nothing in the evidence points the other way.',
        evidence: ['buying_score:cccc'],
      },
    ],
    prompt: 'explanation_narration@1',
    model: 'llama3.1:8b',
    vendor: 'ollama',
    generated_at: '2026-08-01T09:00:00Z',
    ...overrides,
  };
}

describe('every sentence arrives with the evidence it rests on', () => {
  it('renders each statement the model wrote, in order', () => {
    render(<NarrativeBlock narration={narration()} />);
    const items = screen.getAllByRole('listitem');

    expect(items).toHaveLength(2);
    expect(items[0]!.textContent).toContain('Hiring and revenue both moved');
    expect(items[1]!.textContent).toContain('Nothing in the evidence points');
  });

  it('shows how many facts each sentence rests on', () => {
    render(<NarrativeBlock narration={narration()} />);

    expect(screen.getByText('2 facts')).toBeInTheDocument();
    expect(screen.getByText('1 fact')).toBeInTheDocument();
  });

  it('does not render a citation as something clickable', () => {
    // Evidence resolution is M12.3's. A citation drawn as a link and going
    // nowhere costs more trust than the missing feature does.
    const { container } = render(<NarrativeBlock narration={narration()} />);

    expect(container.querySelector('a')).toBeNull();
    expect(container.querySelector('button')).toBeNull();
  });

  it('never shows a raw citation token to a reader', () => {
    // `signal:aaaa` is an address, not information. Showing it would look like
    // a leaked identifier and tell a seller nothing.
    const { container } = render(<NarrativeBlock narration={narration()} />);

    expect(container.textContent).not.toContain('signal:aaaa');
    expect(container.textContent).not.toContain('business_event:bbbb');
  });

  it('joins nothing into a paragraph', () => {
    // Joining the statements would discard the mapping from claim to evidence,
    // which is the only reason to trust any of them.
    render(<NarrativeBlock narration={narration()} />);

    expect(
      screen.queryByText(
        'Hiring and revenue both moved in the last month. Nothing in the evidence points the other way.',
      ),
    ).not.toBeInTheDocument();
  });
});

describe('the reader is told what wrote this', () => {
  it('names the model and the prompt version on the page', () => {
    // Provenance on the page, not behind a tooltip: a customer reading
    // generated language is entitled to know what generated it while they are
    // reading it.
    render(<NarrativeBlock narration={narration()} />);

    expect(screen.getByText('llama3.1:8b')).toBeInTheDocument();
    expect(screen.getByText('explanation_narration@1')).toBeInTheDocument();
  });

  it('states what the model did and did not choose', () => {
    // Signora's entire AI claim in seven words. Without it a reader has no way
    // to tell this from any other tool's summary.
    render(<NarrativeBlock narration={narration()} />);

    expect(screen.getByText(/chose the words, not the facts/)).toBeInTheDocument();
  });

  it('never presents the prose as a measurement', () => {
    const { container } = render(<NarrativeBlock narration={narration()} />);
    const text = (container.textContent ?? '').toLowerCase();

    for (const overclaim of ['predicts', 'guarantees', 'certain', 'confidence score']) {
      expect(text).not.toContain(overclaim);
    }
  });
});

describe('a single-statement narration is still a narration', () => {
  it('renders without a summary line above it', () => {
    // There is deliberately no headline anywhere: the sentence a reader looks
    // at first must not be the one exempt from grounding.
    render(
      <NarrativeBlock
        narration={narration({
          statements: [{ text: 'One thing happened.', evidence: ['signal:x'] }],
        })}
      />,
    );

    expect(screen.getAllByRole('listitem')).toHaveLength(1);
    expect(screen.getByText('One thing happened.')).toBeInTheDocument();
  });
});
