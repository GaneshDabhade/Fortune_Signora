/**
 * Research, as a customer experiences it.
 *
 * **The only place in the product where a person asks Signora to spend
 * something**, so the tests that matter are about honesty rather than layout:
 * whether the wait is stated rather than hidden, whether a run that found
 * nothing is reported as a result rather than an error, and whether the
 * checkable half of the brief reaches the reader before the written half.
 */
import { render, screen, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, expect, it, vi } from 'vitest';

import { ResearchPanel } from '@/components/intelligence/research';
import type { AccountResearch, ResearchFinding } from '@/lib/api/types';

const CORROBORATION: ResearchFinding = {
  id: '11111111-1111-4111-8111-111111111111',
  ref: 'research_finding:11111111-1111-4111-8111-111111111111',
  derivation: 'corroboration',
  question:
    'Which conclusions rest on a single provider, and which are independently agreed?',
  attributes: { corroborated: '1', single_source: '3' },
  cites: ['business_event:aaaa', 'business_event:bbbb'],
};

const RECENCY: ResearchFinding = {
  id: '22222222-2222-4222-8222-222222222222',
  ref: 'research_finding:22222222-2222-4222-8222-222222222222',
  derivation: 'recency',
  question:
    'How old is the evidence beneath this conclusion, and how far apart does it fall?',
  attributes: { span_days: '41' },
  cites: ['business_event:aaaa'],
};

function research(overrides: Partial<AccountResearch> = {}): AccountResearch {
  return {
    request_id: '99999999-9999-4999-8999-999999999999',
    status: 'completed',
    requested_at: '2026-08-01T09:00:00Z',
    updated_at: '2026-08-01T09:01:00Z',
    detail: null,
    artifact: {
      task_id: '33333333-3333-4333-8333-333333333333',
      produced_at: '2026-08-01T09:01:00Z',
      statements: [
        {
          text: 'Three of this account’s four conclusions rest on one provider.',
          cites: [CORROBORATION.ref],
        },
        {
          text: 'The supporting evidence spans six weeks.',
          cites: [RECENCY.ref],
        },
      ],
      findings: [CORROBORATION, RECENCY],
      prompt_name: 'research_synthesis',
      prompt_version: 2,
      model: 'llama3.1:8b',
      evidence_digest: 'abc123',
    },
    ...overrides,
  };
}

function panel(value: AccountResearch | null, onRequest = vi.fn()) {
  render(<ResearchPanel research={value} onRequest={onRequest} isRequesting={false} />);
  return onRequest;
}

describe('before anybody has asked', () => {
  it('says what research would do rather than announcing a gap', () => {
    panel(null);

    // **Not "no research yet".** R8-02 retired three navigation entries for
    // advertising absence; an empty state that describes what is missing
    // teaches a reader the product is unfinished.
    expect(screen.getByText(/compare the evidence beneath this account/i)).toBeVisible();
    expect(screen.queryByText(/no research/i)).toBeNull();
  });

  it('states the wait in words before it is spent', () => {
    panel(null);

    // A spinner is a promise about duration. Ninety seconds behind one is a
    // promise the product cannot keep. The wording is measured — 62s, 87s and
    // 111s across three real runs — not estimated.
    expect(screen.getByText(/a minute or two/i)).toBeVisible();
  });

  it('offers the ask', async () => {
    const onRequest = panel(null);

    await userEvent.click(screen.getByRole('button', { name: /research this account/i }));

    expect(onRequest).toHaveBeenCalledOnce();
  });
});

describe('while it runs', () => {
  it('cannot be asked again', () => {
    panel(research({ status: 'running', artifact: null }));

    expect(screen.getByRole('button', { name: /researching/i })).toBeDisabled();
  });

  it('says what is happening rather than spinning', () => {
    panel(research({ status: 'running', artifact: null }));

    expect(screen.getByText(/comparing the evidence/i)).toBeVisible();
    expect(screen.getByText(/a minute or two/i)).toBeVisible();
  });

  it('tells a queued reader they may leave', () => {
    panel(research({ status: 'requested', artifact: null }));

    expect(screen.getByText(/leave this page and come back/i)).toBeVisible();
  });

  it('announces progress to a screen reader without stealing focus', () => {
    const { container } = render(
      <ResearchPanel
        research={research({ status: 'running', artifact: null })}
        onRequest={vi.fn()}
        isRequesting={false}
      />,
    );

    expect(container.querySelector('[aria-live="polite"]')).not.toBeNull();
  });
});

describe('finding nothing is an answer, not an error', () => {
  it('says there was nothing to compare and blames nobody', () => {
    panel(research({ status: 'nothing_to_research', artifact: null }));

    expect(screen.getByText(/nothing to compare here/i)).toBeVisible();
    expect(screen.queryByText(/fail/i)).toBeNull();
    expect(screen.queryByText(/error/i)).toBeNull();
  });

  it('lets the account be asked again', () => {
    panel(research({ status: 'nothing_to_research', artifact: null }));

    expect(screen.getByRole('button', { name: /research again/i })).toBeEnabled();
  });
});

describe('when it fails', () => {
  it('gives the reason verbatim', () => {
    panel(
      research({
        status: 'failed',
        artifact: null,
        detail: 'PromptNotReleasableError: research_synthesis@2 has no release for gpt-5',
      }),
    );

    // A customer who cannot see why cannot decide whether another minute is
    // worth spending.
    expect(screen.getByText(/research_synthesis@2 has no release/i)).toBeVisible();
  });

  it('does not claim anything was recorded', () => {
    panel(research({ status: 'failed', artifact: null, detail: 'boom' }));

    expect(screen.getByText(/nothing was recorded/i)).toBeVisible();
    expect(screen.queryByText(/what it means/i)).toBeNull();
  });
});

describe('the brief separates what was computed from what was written', () => {
  it('shows both halves, labelled', () => {
    panel(research());

    expect(screen.getByText('What was compared')).toBeVisible();
    expect(screen.getByText('What it means')).toBeVisible();
  });

  it('puts the computed half first', () => {
    const { container } = render(
      <ResearchPanel research={research()} onRequest={vi.fn()} isRequesting={false} />,
    );

    // **The order is the argument.** A reader who scrolls no further has still
    // seen the half nobody has to trust.
    const text = container.textContent ?? '';
    expect(text.indexOf('What was compared')).toBeLessThan(text.indexOf('What it means'));
  });

  it('says outright that the comparisons were not written', () => {
    panel(research());

    expect(screen.getByText(/computed, not written/i)).toBeVisible();
  });

  it('shows each finding under the catalog’s own question', () => {
    panel(research());

    expect(
      screen.getByText(/which conclusions rest on a single provider/i),
    ).toBeVisible();
    expect(screen.getByText(/how far apart does it fall/i)).toBeVisible();
  });

  it('never shows a derivation key', () => {
    const { container } = render(
      <ResearchPanel research={research()} onRequest={vi.fn()} isRequesting={false} />,
    );

    // The key is the platform's word. A screen showing `corroboration` would be
    // the data model reaching a salesperson (ADR-0034).
    expect(container.textContent).not.toContain('corroboration');
    expect(container.textContent).not.toContain('research_finding:');
  });
});

describe('every statement can be followed', () => {
  it('counts the comparisons a sentence rests on', () => {
    panel(research());

    expect(screen.getAllByRole('button', { name: /1 comparison/ })).toHaveLength(2);
  });

  it('opens the comparison, with the rows it compared', async () => {
    panel(research());

    await userEvent.click(screen.getAllByRole('button', { name: /1 comparison/ })[0]!);

    const dialog = screen.getByRole('dialog');
    expect(within(dialog).getByText(/2 records compared/i)).toBeVisible();
    expect(within(dialog).getByText('Corroborated')).toBeVisible();
  });

  it('says in the drawer that the arithmetic is the customer’s to repeat', async () => {
    panel(research());

    await userEvent.click(screen.getAllByRole('button', { name: /1 comparison/ })[0]!);

    expect(screen.getByText(/no model wrote any of it/i)).toBeVisible();
  });
});

describe('provenance is on the page', () => {
  it('names the model and the prompt version while they are being read', () => {
    panel(research());

    // Not behind a tooltip. A customer reading generated language is entitled
    // to know what generated it *while* they are reading it.
    expect(screen.getByText(/llama3\.1:8b/)).toBeVisible();
    expect(screen.getByText(/research_synthesis@2/)).toBeVisible();
  });
});

describe('a research read that failed is not an account nobody has researched', () => {
  /**
   * **Found by auditing wave 1 against 410's "each in six states", not by a
   * failure.** The panel took `research` and no error, so a failed fetch
   * arrived as `null` — indistinguishable from *"nobody has asked yet"* — and
   * rendered the invitation to start a run.
   *
   * Two things were wrong with that, and the second is the expensive one: the
   * sentence was false, and the button beside it was enabled. `inFlight` is
   * derived from a status the component could not load, so on an error it is
   * `false` and the control offers to spend a worker minute and a model call
   * on a run that may already be underway.
   */
  it('says the read failed rather than inviting a run', () => {
    render(
      <ResearchPanel research={null} onRequest={() => {}} isRequesting={false} isError />,
    );

    expect(screen.getByText(/could not load the research/i)).toBeInTheDocument();
    expect(screen.queryByText(/usually takes a minute or two/i)).not.toBeInTheDocument();
  });

  it('does not offer to start one it cannot see the state of', () => {
    render(
      <ResearchPanel research={null} onRequest={() => {}} isRequesting={false} isError />,
    );

    expect(screen.getByRole('button', { name: /research/i })).toBeDisabled();
  });

  it('still invites a run when nobody has genuinely asked', () => {
    /** The 404 case, which the caller separates. This must keep working. */
    render(<ResearchPanel research={null} onRequest={() => {}} isRequesting={false} />);

    expect(screen.getByText(/usually takes a minute or two/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /research/i })).toBeEnabled();
  });
});
