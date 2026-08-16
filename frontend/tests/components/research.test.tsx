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

    // 📁 **The finalized design has ONE label** — *"Refresh research"* — so the
    // control no longer renames itself while a run is in flight. ⚡ **What it is
    // doing is said by the body**, which is where a reader is already looking.
    // ⛔ **Disabled is unchanged, and that was never a design question**: a
    // minute of a worker and two model calls is not spent on a guess.
    expect(screen.getByRole('button', { name: /refresh research/i })).toBeDisabled();
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

    expect(screen.getByRole('button', { name: /refresh research/i })).toBeEnabled();
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

describe('the brief keeps the deterministic half legible inside the design’s grid', () => {
  /**
   * 🔴 **The property these protect is unchanged; the structure that carried it
   * is not.**
   *
   * ⚠️ **The previous generation split this into two labelled lists** —
   * *What was compared* above *What it means* — **and the finalized design has
   * ONE grid** (`grid-template-columns:repeat(2,1fr)`), each cell a key, a
   * paragraph and a citation.
   *
   * ⛔ **Collapsing them naively would have presented a computed comparison as
   * model prose.** ✅ **So the distinction moved INTO the cell**: the key is the
   * domain expert's question, the paragraph is the model's sentence, and the
   * whole card carries the intelligence hue — **which is what these now
   * assert.**
   */
  it('titles itself as the design does, not as the previous generation did', () => {
    panel(research());

    expect(screen.getByRole('heading', { name: 'Research summary' })).toBeVisible();
    // ⛔ **The superseded wording is gone rather than aliased.**
    expect(screen.queryByText('Deeper research')).toBeNull();
    expect(screen.queryByText('What was compared')).toBeNull();
    expect(screen.queryByText('What it means')).toBeNull();
  });

  it('marks the whole card as machine-authored, so no cell reads as unattributed', () => {
    const { container } = render(
      <ResearchPanel research={research()} onRequest={vi.fn()} isRequesting={false} />,
    );

    // ⚡ **The intelligence hue is the attribution now that the headings are
    // gone** — 📁 the design's `--ai` border and `--ai-tint` band. ⛔ **A token,
    // never a literal colour** (§20c).
    expect(container.querySelector('section')?.className).toContain('border-ai');
    expect(container.querySelector('.bg-ai-subtle')).not.toBeNull();
  });

  it('still names the model and the prompt that wrote the sentences', () => {
    panel(research());

    // ⚡ **Provenance survived the restructure.** ⛔ It moved into the design's
    // footer rather than being dropped with the heading that used to carry it.
    expect(screen.getByText(/llama3\.1/i)).toBeVisible();
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

    expect(screen.getByRole('button', { name: /^(refresh research|research this account)$/i })).toBeDisabled();
  });

  it('still invites a run when nobody has genuinely asked', () => {
    /** The 404 case, which the caller separates. This must keep working. */
    render(<ResearchPanel research={null} onRequest={() => {}} isRequesting={false} />);

    expect(screen.getByText(/usually takes a minute or two/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /^(refresh research|research this account)$/i })).toBeEnabled();
  });
});

describe('the design’s six states — Collapsed and Expanded', () => {
  /**
   * 📁 ***"Each of the 27 sections above ships in all six states"*** — Normal,
   * Loading, Error, Empty, **Collapsed** and **Expanded**. ⚠️ **The last two
   * were absent from this section entirely**, which made it the only
   * intelligence section on the page that could not be folded away.
   */
  it('folds to a summary that still states the count', async () => {
    render(
      <ResearchPanel
        id="research"
        research={research()}
        onRequest={vi.fn()}
        isRequesting={false}
        viewerId="user-1"
        kind="account"
      />,
    );

    await userEvent.click(screen.getByRole('button', { name: /research summary/i }));

    // 🔴 📁 ***"A collapsed section still states its count and its worst
    // status, so collapsing never hides a risk."***
    expect(screen.getByText(/2 comparisons/i)).toBeVisible();
    // ⛔ **The body is gone, not merely hidden behind opacity.**
    expect(screen.queryByText(/rest on one provider/i)).not.toBeVisible();
  });

  it('remembers the fold per viewer and per account kind, never per record', async () => {
    window.localStorage.clear();
    render(
      <ResearchPanel
        id="research"
        research={research()}
        onRequest={vi.fn()}
        isRequesting={false}
        viewerId="user-1"
        kind="account"
      />,
    );

    await userEvent.click(screen.getByRole('button', { name: /research summary/i }));

    const key = Object.keys(window.localStorage).find((k) => k.includes('collapse'));
    expect(key).toBeDefined();
    // ⛔ **The account id must not appear in the key** — 📁 the collapse law's
    // own rule, and the reason `collapseKey` is shared rather than rebuilt.
    expect(key).not.toContain('22222222');
    expect(window.localStorage.getItem(key!)).toBe('collapsed');
  });

  it('offers focus mode only when the page can carry the URL', () => {
    panel(research());

    // ⛔ **Absent rather than inert.** 📁 The design's expansion *"keeps the URL
    // so the expanded view is shareable"* — a control that could not do that
    // would be advertising a capability the page does not have.
    expect(screen.queryByRole('button', { name: /focus mode/i })).toBeNull();
  });

  it('asks the page to expand, rather than expanding itself', async () => {
    const onToggleExpanded = vi.fn();
    render(
      <ResearchPanel
        id="research"
        research={research()}
        onRequest={vi.fn()}
        isRequesting={false}
        onToggleExpanded={onToggleExpanded}
      />,
    );

    await userEvent.click(screen.getByRole('button', { name: /open research in focus mode/i }));

    // ⚡ **The URL is the page's to write**, so the section reports intent and
    // the page owns `withExpanded`. ⛔ A component writing the query string
    // would be a second definition of the shareable-view rule.
    expect(onToggleExpanded).toHaveBeenCalledWith(true);
  });

  it('leaves focus mode on Escape', async () => {
    const onToggleExpanded = vi.fn();
    render(
      <ResearchPanel
        id="research"
        research={research()}
        onRequest={vi.fn()}
        isRequesting={false}
        isExpanded
        onToggleExpanded={onToggleExpanded}
      />,
    );

    await userEvent.keyboard('{Escape}');

    // 📁 ***"Esc returns to the record at the same scroll position."***
    expect(onToggleExpanded).toHaveBeenCalledWith(false);
  });

  it('widens the grid in focus mode rather than only renaming a state', async () => {
    const { container, rerender } = render(
      <ResearchPanel research={research()} onRequest={vi.fn()} isRequesting={false} />,
    );
    const narrow = container.querySelector('[class*="grid-cols"]')?.className ?? '';

    rerender(
      <ResearchPanel
        research={research()}
        onRequest={vi.fn()}
        isRequesting={false}
        isExpanded
        onToggleExpanded={vi.fn()}
      />,
    );
    const wide = container.querySelector('[class*="grid-cols"]')?.className ?? '';

    // 📁 ***"Expansion widens to the full content region."*** ⛔ **A guard that
    // cannot fail is documentation pretending to be code** (§2) — so the
    // widening is asserted as a real difference, not as a prop being set.
    expect(wide).not.toEqual(narrow);
    expect(wide).toContain('laptop:grid-cols-3');
  });
});
