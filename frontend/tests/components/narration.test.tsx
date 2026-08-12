/**
 * Model-authored language, as a customer reads it.
 *
 * **The first generated content in the product**, and the tests that matter are
 * about trust rather than layout: whether a reader can tell what a machine
 * wrote, whether every sentence is visibly anchored, and whether the screen
 * ever presents prose as though it were a measurement.
 */
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, expect, it } from 'vitest';

import { NarrativeBlock } from '@/components/intelligence/narration';
import type { AccountNarration } from '@/lib/api/types';

function narration(overrides: Partial<AccountNarration> = {}): AccountNarration {
  return {
    account_id: '11111111-1111-4111-8111-111111111111',
    statements: [
      {
        text: 'Hiring and revenue both moved in the last month.',
        evidence: ['signal_contribution:aaaa', 'opportunity:bbbb'],
      },
      {
        text: 'Nothing in the evidence points the other way.',
        evidence: ['buying_score:cccc'],
      },
    ],
    facts: [
      {
        token: 'signal_contribution:aaaa',
        kind: 'signal_contribution',
        summary: 'Headcount in platform engineering grew over the quarter.',
        attributes: { contribution: '15', observed_on: '2026-07-04' },
      },
      {
        token: 'opportunity:bbbb',
        kind: 'opportunity',
        summary: 'An opportunity was opened for this account, qualified as automatic.',
        attributes: { score_at_creation: '48' },
      },
      {
        token: 'buying_score:cccc',
        kind: 'buying_score',
        summary:
          'The buying score that opened this opportunity was 48 out of 120, rising.',
        attributes: { value: '48', ceiling: '120' },
      },
    ],
    evidence_unchanged: true,
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

  it('makes a citation clickable only when it resolves', async () => {
    // **Replaces an assertion that was right until D42.** It read "does not
    // render a citation as something clickable", because evidence resolution
    // did not exist and a control going nowhere costs more trust than the
    // missing feature does. The invariant behind it survives unchanged: an
    // affordance appears exactly when there is something behind it.
    const user = userEvent.setup();
    render(<NarrativeBlock narration={narration()} />);

    await user.click(screen.getByRole('button', { name: '2 facts' }));

    expect(
      screen.getByText('Headcount in platform engineering grew over the quarter.'),
    ).toBeInTheDocument();
  });

  it('falls back to a plain count when nothing can be resolved', () => {
    // A closed opportunity keeps its narration (D27) and has no current
    // explanation to re-derive. The sentence is still anchored; the anchor is
    // out of reach, and a dead control would say otherwise.
    //
    // ⚠️ **Narrowed from `querySelector('button')`, and the property is
    // unchanged.** [B-312](../../../docs/BUGS.md) gave `Dialog` a Close control
    // in its header so that **every** dialog contains something a keyboard can
    // reach — and a `<dialog>` renders its children whether or not it is open,
    // so *any* button is no longer the same question as *a citation control*.
    // ⛔ **Asserting the absence of one element type was always a proxy**; this
    // asserts the thing the comment above actually describes.
    render(<NarrativeBlock narration={narration({ facts: [], evidence_unchanged: false })} />);

    expect(screen.queryByRole('button', { name: /evidence|citation|fact/i })).toBeNull();
    expect(screen.getByText('2 facts')).toBeInTheDocument();
  });

  it('never shows a raw citation token to a reader', () => {
    // `signal:aaaa` is an address, not information. Showing it would look like
    // a leaked identifier and tell a seller nothing.
    const { container } = render(<NarrativeBlock narration={narration()} />);

    expect(container.textContent).not.toContain('signal_contribution:aaaa');
    expect(container.textContent).not.toContain('opportunity:bbbb');
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

describe('a citation opens what the model was given', () => {
  it('shows the fact in the owning module’s own words, with its figures', async () => {
    // Not a record fetched afterwards — the summary and attributes here are
    // the ones assembled into the prompt, which is the strongest available
    // form of "here is what it was told".
    const user = userEvent.setup();
    render(<NarrativeBlock narration={narration()} />);

    await user.click(screen.getByRole('button', { name: '1 fact' }));

    expect(
      screen.getByText(
        'The buying score that opened this opportunity was 48 out of 120, rising.',
      ),
    ).toBeInTheDocument();
    expect(screen.getByText('120')).toBeInTheDocument();
  });

  it('opens only the facts the sentence cites', async () => {
    // The whole point of statement-level citation is that a sentence rests on
    // *these* facts. Showing the account's entire evidence set would discard
    // the mapping the grounding guarantee exists to preserve.
    const user = userEvent.setup();
    render(<NarrativeBlock narration={narration()} />);

    await user.click(screen.getByRole('button', { name: '1 fact' }));

    expect(
      screen.queryByText('Headcount in platform engineering grew over the quarter.'),
    ).not.toBeInTheDocument();
  });

  it('says the evidence moved, at the moment somebody is checking it', async () => {
    // A reader who has opened a citation is checking something, and that is
    // exactly when "what was true then" versus "what is true now" matters.
    const user = userEvent.setup();
    render(<NarrativeBlock narration={narration({ evidence_unchanged: false })} />);

    await user.click(screen.getByRole('button', { name: '1 fact' }));

    expect(
      screen.getByText(/evidence behind this account has changed/i),
    ).toBeInTheDocument();
  });

  it('says nothing about staleness when the evidence still matches', async () => {
    const user = userEvent.setup();
    render(<NarrativeBlock narration={narration()} />);

    await user.click(screen.getByRole('button', { name: '1 fact' }));

    expect(screen.queryByText(/has changed since/i)).not.toBeInTheDocument();
  });

  it('names an unrecognised kind rather than hiding it', async () => {
    // A new citation kind arriving is something a reader should see, not
    // something the browser should quietly swallow.
    const user = userEvent.setup();
    render(
      <NarrativeBlock
        narration={narration({
          statements: [{ text: 'Something new.', evidence: ['research_finding:z'] }],
          facts: [
            {
              token: 'research_finding:z',
              kind: 'research_finding',
              summary: 'A finding.',
              attributes: {},
            },
          ],
        })}
      />,
    );

    await user.click(screen.getByRole('button', { name: '1 fact' }));

    expect(screen.getByText('research_finding')).toBeInTheDocument();
  });
});

describe('three states that used to be one blank space — B-010', () => {
  // A reviewer opened twelve briefs, saw no explanation on any, and could not
  // tell whether the feature was broken. It was. Absence cannot distinguish
  // itself from failure, and neither could distinguish itself from *nothing
  // has been written yet*.

  it('says nothing has been written, where it used to say nothing', () => {
    render(<NarrativeBlock narration={undefined} notNarrated />);

    expect(screen.getByRole('heading', { name: 'In plain language' })).toBeVisible();
    expect(screen.getByText(/has not written one for this account yet/)).toBeVisible();
  });

  it('says the request failed, in different words', () => {
    render(<NarrativeBlock narration={undefined} isError />);

    expect(screen.getByText(/could not load the explanation/)).toBeVisible();
    expect(screen.queryByText(/has not written one/)).toBeNull();
  });

  it('says neither while the answer is still being fetched', () => {
    // Announcing "nothing has been written" during the first paint is a
    // confident wrong answer to an account that has an explanation.
    //
    // ⚠️ **This asserted `toBeEmptyDOMElement` until TASK-1476, and the
    // assertion encoded an IMPLEMENTATION rather than B-010's rule.** ⛔ The
    // rule is *says neither* — it never required blankness, and blankness had
    // its own cost: the whole section appeared when the read landed and
    // everything below it moved down the page. 📁 The design says *"header,
    // title and counts paint from cache; only the body skeletons."*
    //
    // ✅ **A skeleton says neither, and says so more honestly than nothing
    // does** — nothing is also what a section with no data looks like.
    const { container } = render(<NarrativeBlock narration={undefined} />);

    expect(screen.queryByText(/has not written one/)).toBeNull();
    expect(screen.queryByText(/could not load the explanation/)).toBeNull();
    // ⛔ **And no narration content is invented meanwhile.**
    expect(container.querySelectorAll('li')).toHaveLength(0);
  });

  it('reads as an answer rather than as a fault', () => {
    // Signora having nothing to add is not an error, and the sentence must not
    // borrow the vocabulary of one.
    render(<NarrativeBlock narration={undefined} notNarrated />);

    const said = screen.getByText(/has not written one for this account yet/).textContent;
    expect(said).not.toMatch(/error|failed|unavailable|problem/i);
  });
});

describe('a narration whose evidence has moved says so where it can be read', () => {
  it('explains on the panel when no citation can be opened', () => {
    // **The defect this found.** When nothing resolves, every citation renders
    // as a plain count rather than a button — so the dialog that explains why
    // has no way to be opened, and the explanation was only ever in the dialog.
    render(
      <NarrativeBlock narration={narration({ facts: [], evidence_unchanged: false })} />,
    );

    expect(screen.getByText(/can no longer be opened/)).toBeVisible();
    expect(screen.queryByRole('button', { name: /facts?$/ })).toBeNull();
  });

  it('leaves it to the dialog while the citations still open', async () => {
    // One explanation, placed wherever the reader can reach it — never both.
    // A reader who has opened a citation is checking something, and that is
    // the moment the difference between then and now matters.
    render(<NarrativeBlock narration={narration({ evidence_unchanged: false })} />);

    expect(screen.queryByText(/can no longer be opened/)).toBeNull();

    await userEvent.click(screen.getAllByRole('button', { name: /facts?$/ })[0]!);
    expect(screen.getByText(/has changed since/)).toBeVisible();
  });

  it('says nothing extra when the evidence is unchanged', () => {
    render(<NarrativeBlock narration={narration()} />);

    expect(screen.queryByText(/can no longer be opened/)).toBeNull();
    expect(screen.queryByText(/has changed since/)).toBeNull();
  });

  it('still shows the sentences, which are not wrong — only dated', () => {
    // A narration is never rewritten to catch up, and never withheld because
    // its evidence moved. It is a record of what was true when it was written.
    render(
      <NarrativeBlock narration={narration({ facts: [], evidence_unchanged: false })} />,
    );

    expect(
      screen.getByText('Hiring and revenue both moved in the last month.'),
    ).toBeVisible();
  });
});
