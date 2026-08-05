/**
 * The commercial vocabulary, as a customer reads it.
 *
 * These are not rendering tests. Each one asserts a **product rule** that
 * would be invisible if it broke: a trigger silently reworded, a badge that
 * starts appearing on every row, a score drawn as a percentage it never was.
 * The pipeline computes these meanings carefully; the screen must not blur
 * them on the way out.
 */
import { render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';

import {
  AttentionScore,
  ContestedMark,
  EvidenceHealth,
  Hypothesis,
  HeldSince,
  Ownership,
  PostureMark,
  ScoreMovement,
  WhyNow,
} from '@/components/intelligence/attention';
import type { ScoreTrigger } from '@/lib/api/types';

describe('the score is an ordering, not a probability', () => {
  it('renders the number the pipeline computed', () => {
    render(<AttentionScore score={73} />);

    expect(screen.getByText('73')).toBeInTheDocument();
  });

  it('renders no score at all when the evidence has expired', () => {
    // Not a zero. Zero is a reading; absence is the lack of one, and showing
    // 0 would rank a stale account as actively uninteresting.
    render(<AttentionScore score={null} />);

    expect(screen.queryByText('0')).not.toBeInTheDocument();
    expect(screen.getByLabelText('No current score')).toBeInTheDocument();
  });

  it('draws no percentage, gauge or progress element', () => {
    // A filled ring implies a maximum that means something. This number is
    // an ordering of attention; a 90 is not "90% likely to buy".
    const { container } = render(<AttentionScore score={90} />);

    expect(container.querySelector('progress, meter, svg')).toBeNull();
    expect(container.textContent).not.toContain('%');
  });
});

describe('every trigger has its own wording', () => {
  const triggers: ScoreTrigger[] = [
    'signal_generated',
    'signal_superseded',
    'model_changed',
    'profile_changed',
    'evidence_aged',
  ];

  it.each(triggers)('%s reads as something a seller can check', (trigger) => {
    render(<WhyNow trigger={trigger} />);

    expect(screen.getByText(/\w/)).toBeInTheDocument();
  });

  it('gives five triggers five distinct sentences', () => {
    // **A translation, never a paraphrase.** Blurring two triggers into one
    // friendly phrase makes the reason uncheckable against the record, which
    // is the one thing this product cannot afford.
    const wordings = triggers.map((trigger) => {
      const { container, unmount } = render(<WhyNow trigger={trigger} />);
      const text = container.textContent ?? '';
      unmount();
      return text;
    });

    expect(new Set(wordings).size).toBe(triggers.length);
  });

  it('says there is no reading rather than inventing a reason', () => {
    render(<WhyNow trigger={null} />);

    expect(screen.getByText('No current reading')).toBeInTheDocument();
  });
});

describe('movement answers what changed overnight', () => {
  it('shows a rise with its sign', () => {
    render(<ScoreMovement trend="rising" change={8} />);

    expect(screen.getByText('+8')).toBeInTheDocument();
  });

  it('shows a fall', () => {
    render(<ScoreMovement trend="falling" change={-5} />);

    expect(screen.getByText('-5')).toBeInTheDocument();
  });

  it('says so plainly when nothing moved', () => {
    render(<ScoreMovement trend="steady" change={0} />);

    expect(screen.getByText('No change')).toBeInTheDocument();
  });
});

describe('badges appear only when they carry information', () => {
  it('says nothing when the evidence is current', () => {
    // A badge on every row saying "everything is fine" is noise, and noise
    // trains people to stop reading badges — including the one that matters.
    const { container } = render(<EvidenceHealth evidence="current" />);

    expect(container).toBeEmptyDOMElement();
  });

  it.each(['cooling', 'stale'] as const)('warns when the evidence is %s', (evidence) => {
    const { container } = render(<EvidenceHealth evidence={evidence} />);

    expect(container).not.toBeEmptyDOMElement();
  });

  it('marks a contested account and stays silent on a quiet one', () => {
    const { container: quiet } = render(<ContestedMark contested={false} />);
    expect(quiet).toBeEmptyDOMElement();

    render(<ContestedMark contested />);
    expect(screen.getByText('Contested')).toBeInTheDocument();
  });

  it('does not describe a contested account as uncertain', () => {
    // The Buying Score Engine refuses to average opposing readings away
    // because a fought-over account warrants *more* attention. Wording that
    // implied doubt would invert the meaning the pipeline computed.
    const { container } = render(<ContestedMark contested />);
    const text = (container.textContent ?? '').toLowerCase();

    for (const wrong of ['uncertain', 'unclear', 'conflict', 'warning', 'unreliable']) {
      expect(text).not.toContain(wrong);
    }
  });
});

describe('the row says what is happening, not that something happened', () => {
  it('names the hypothesis in the words the catalog owns', () => {
    render(<Hypothesis signalType="active_evaluation" title="Active evaluation" />);

    expect(screen.getByText('Active evaluation')).toBeInTheDocument();
  });

  it('never renders the raw key', () => {
    // `expansion_opportunity` is not a sentence. A reader who saw one would
    // learn that this line is machine output — and this is the line the whole
    // row is read for.
    const { container } = render(
      <Hypothesis signalType="expansion_opportunity" title={undefined} />,
    );

    expect(container.textContent).not.toContain('expansion_opportunity');
  });

  it('shows nothing at all while the vocabulary is in flight', () => {
    // The name arrives in a separate request from the row. Blocking the list
    // on it would trade the decision for the label; showing a placeholder
    // would put a shape on screen that then moves.
    const { container } = render(
      <Hypothesis signalType="active_evaluation" title={undefined} />,
    );

    expect(container).toBeEmptyDOMElement();
  });

  it('says there is no reading when no score is live', () => {
    // The opportunity is still open and its justification has expired. That is
    // a real answer, and it is not the same as "we do not know".
    render(<Hypothesis signalType={null} title={undefined} />);

    expect(screen.getByText('No current reading')).toBeInTheDocument();
  });

  it('holds no translation table of its own', async () => {
    // **A second vocabulary is wrong the moment the catalog changes, and
    // invisible when it does.** The proof is that a title the catalog has
    // never contained still renders verbatim.
    render(
      <Hypothesis signalType="active_evaluation" title="Something Else Entirely" />,
    );

    expect(screen.getByText('Something Else Entirely')).toBeInTheDocument();
  });
});

describe('a contraction risk does not read as a weak opportunity', () => {
  it('marks a contraction risk so it survives scanning', () => {
    // **R9-03, and the ruling behind TASK-905.** *Datadog · Contraction risk ·
    // 5* rendered identically to *Salesforce · New decision maker · 10*. The
    // word was already there; a manager scanning twelve rows had to read
    // twelve titles.
    render(<PostureMark posture="contractionary" />);

    expect(screen.getByText(/at risk/i)).toBeInTheDocument();
  });

  it('marks the row without waiting for the catalog', () => {
    // **The hole this slice closes.** The mark used to hang off the catalog's
    // title, so a row whose title had not arrived rendered unmarked — on every
    // first paint, and *permanently* for a score formed under a catalog
    // version that no longer declares its key. Posture is on the wire so a
    // client never needs the catalog to know which way a row cuts.
    render(
      <>
        <Hypothesis signalType="contraction_risk" title={undefined} />
        <PostureMark posture="contractionary" />
      </>,
    );

    expect(screen.getByText(/at risk/i)).toBeInTheDocument();
  });

  it('says what it means to somebody who cannot see the badge', () => {
    // Two words fit the lane a phone reflows; the sentence they abbreviate is
    // what a screen reader hears.
    render(<PostureMark posture="contractionary" />);

    expect(screen.getByText(/at risk/i)).toHaveTextContent(
      /at risk to existing revenue/i,
    );
  });

  it('leaves an expansion row exactly as it was', () => {
    // Marking every posture would mark almost every row, and a badge on every
    // row saying "everything is fine" trains people to stop reading badges.
    const { container } = render(<PostureMark posture="expansionary" />);

    expect(container).toBeEmptyDOMElement();
  });

  it('leaves a neutral row exactly as it was', () => {
    const { container } = render(<PostureMark posture="neutral" />);

    expect(container).toBeEmptyDOMElement();
  });

  it('does not rely on colour alone to say a row is a risk', () => {
    // Colour as the only channel fails a colour-blind reader, and
    // accessibility is a defect class rather than an enhancement (§20c).
    const { container } = render(<PostureMark posture="contractionary" />);

    expect(container.querySelector('svg')).not.toBeNull();
  });

  it('marks nothing when the posture is absent', () => {
    // Posture is null exactly when the leading hypothesis is. A marked row
    // with no reading behind it would be a claim with nothing under it.
    const { container } = render(<PostureMark posture={null} />);

    expect(container).toBeEmptyDOMElement();
  });
});

describe('the list shows what you are working', () => {
  const VIEWER = 'aaaaaaaa-1111-4111-8111-111111111111';
  const COLLEAGUE = 'bbbbbbbb-2222-4222-8222-222222222222';

  it('says nothing about an account nobody has claimed', () => {
    // Most rows, most mornings. A badge on every one of them is noise that
    // trains a reader past the badges that matter.
    const { container } = render(
      <Ownership ownerId={null} stage="tracking" viewerId={VIEWER} />,
    );

    expect(container).toBeEmptyDOMElement();
  });

  it('marks a row the reader took on', () => {
    // **The missing half of the action.** J4 shipped "I'm working this" and
    // the list rendered nothing with it — take an account on, come back, and
    // the row was identical (D40).
    render(<Ownership ownerId={VIEWER} stage="engaged" viewerId={VIEWER} />);

    expect(screen.getByText('Yours')).toBeInTheDocument();
  });

  it('says a colleague has it without naming them', () => {
    // **D23.** The Python tier verifies tokens without ever learning who a
    // person is, so an identifier is all that arrives and "taken" is the
    // honest form of one nobody can read.
    const { container } = render(
      <Ownership ownerId={COLLEAGUE} stage="engaged" viewerId={VIEWER} />,
    );

    expect(screen.getByText('Taken')).toBeInTheDocument();
    expect(container.textContent).not.toContain(COLLEAGUE);
  });

  it('does not claim a row is yours before the session resolves', () => {
    // Announcing "Yours" and then correcting it reads as a bug, and getting
    // ownership wrong is the one thing this badge exists not to do.
    render(<Ownership ownerId={COLLEAGUE} stage="engaged" viewerId={null} />);

    expect(screen.getByText('Taken')).toBeInTheDocument();
    expect(screen.queryByText('Yours')).not.toBeInTheDocument();
  });

  it('says what happened to an account somebody closed without holding', () => {
    // Otherwise the row is indistinguishable from work nobody has looked at,
    // when in fact somebody decided about it.
    render(<Ownership ownerId={null} stage="dismissed" viewerId={VIEWER} />);

    expect(screen.getByText('Dismissed')).toBeInTheDocument();
  });
});

describe('a held account says who holds it — LO-02', () => {
  // **`owner_id` has been on every row since M12.2** and the badge said
  // *Taken* for everybody, because the product could not name a person. TM-01's
  // `member_email` changed that (49-lead-ownership.md §11).

  it('says *Yours* for your own, which is the whole answer a seller needs', () => {
    render(<Ownership ownerId="me" stage="engaged" viewerId="me" />);

    expect(screen.getByText('Yours')).toBeVisible();
  });

  it('names the colleague who holds it', () => {
    // A manager's question is *who holds this*, and it needs the name.
    render(
      <Ownership
        ownerId="ravi"
        ownerName="ravi@acme.com"
        stage="engaged"
        viewerId="me"
      />,
    );

    expect(screen.getByText('ravi@acme.com')).toBeVisible();
  });

  it('falls back to *Taken* when the product cannot name them', () => {
    // A membership added by identifier before invitations existed. Still
    // honest, and now rare.
    render(<Ownership ownerId="ravi" stage="engaged" viewerId="me" />);

    expect(screen.getByText('Taken')).toBeVisible();
  });

  it('prefers *Yours* over your own name', () => {
    // *Yours* answers the question being asked; your own address does not.
    render(
      <Ownership ownerId="me" ownerName="me@acme.com" stage="engaged" viewerId="me" />,
    );

    expect(screen.getByText('Yours')).toBeVisible();
    expect(screen.queryByText('me@acme.com')).toBeNull();
  });

  it('says nothing about an account nobody has taken', () => {
    // Every row on a ranked list is untaken by default; a badge on each would
    // be noise where the absence already says it.
    const { container } = render(
      <Ownership ownerId={null} stage="tracking" viewerId="me" />,
    );

    expect(container).toBeEmptyDOMElement();
  });

  it('never says *Yours* while the session is still resolving', () => {
    // A wrong *Yours* is worse than a late one.
    render(<Ownership ownerId="me" ownerName="me@acme.com" stage="engaged" viewerId={null} />);

    expect(screen.queryByText('Yours')).toBeNull();
    expect(screen.getByText('me@acme.com')).toBeVisible();
  });
});

describe('how long an account has been sitting where it sits — LO-06', () => {
  // **The Friday-afternoon question.** An account taken on this morning and
  // one taken on in March rendered as the same row, so *"what have I been
  // sitting on?"* meant opening briefs one at a time.

  const THREE_WEEKS_AGO = new Date(Date.now() - 21 * 86_400_000).toISOString();

  it('says how long ago somebody took it on', () => {
    render(<HeldSince stage="engaged" since={THREE_WEEKS_AGO} />);

    expect(screen.getByText(/Taken on 3 weeks ago/)).toBeVisible();
  });

  it('never says an account is neglected, stalled or at risk', () => {
    // **The property this whole design turns on.** Signora records workflow
    // decisions and cannot see a call, an email or a meeting — so a seller who
    // spoke to this customer yesterday must not be told they had not, by a
    // product with no way to know. It reports the clock and grades nothing.
    const { container } = render(<HeldSince stage="engaged" since={THREE_WEEKS_AGO} />);

    expect(container.textContent).not.toMatch(/stalled|neglected|at risk|overdue|inactive/i);
  });

  it('carries no tone, because there is no threshold to have an opinion about', () => {
    // A number at which an account becomes *too* old is a per-customer
    // judgement, and the module's policy artifact refuses it — every
    // opportunity records the policy version that qualified it. The threshold
    // arrives with the thing that needs one, which is a notification (M14a).
    const { container } = render(<HeldSince stage="engaged" since={THREE_WEEKS_AGO} />);

    expect(container.querySelector('[class*="danger"], [class*="warning"]')).toBeNull();
  });

  it('says nothing about an account nobody has taken on', () => {
    // A tracked account's age is *Signora's* suggestion ageing, which the
    // brief already states and the evidence badge already grades. This is the
    // clock that starts when a person takes responsibility.
    const { container } = render(<HeldSince stage="tracking" since={THREE_WEEKS_AGO} />);

    expect(container).toBeEmptyDOMElement();
  });

  it('says nothing about a closed account', () => {
    // The clock stopped. Measuring it under "Closed — won" would be reporting
    // a duration that means nothing.
    const { container } = render(<HeldSince stage="closed_won" since={THREE_WEEKS_AGO} />);

    expect(container).toBeEmptyDOMElement();
  });
});
