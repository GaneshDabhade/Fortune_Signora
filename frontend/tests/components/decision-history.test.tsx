/**
 * What happened to this account before you opened it.
 *
 * **The one record in Signora that nothing can reproduce.** Every score,
 * signal, narration and finding can be recomputed from evidence; a decision
 * cannot — and `history` has travelled on every brief since M12.1 with no
 * screen ever reading it.
 *
 * These assert the rules that keep an audit trail honest: that it is shown in
 * the order it was recorded, that nobody is named whom the product cannot
 * name, and that Signora's own opening entry is never mistaken for a person's.
 */
import { render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';

import { DecisionHistory } from '@/components/intelligence/decision-history';
import type { AccountOpportunity, WorkflowState } from '@/lib/api/types';

const ME = 'aaaaaaaa-1111-4111-8111-111111111111';
const COLLEAGUE = 'bbbbbbbb-2222-4222-8222-222222222222';

const OPENED: WorkflowState = {
  stage: 'tracking',
  owner_id: null,
  decided_by: null,
  reason: 'Qualified by Signora on the buying score.',
  occurred_at: '2026-06-01T09:00:00Z',
};

function opportunity(history: WorkflowState[]): AccountOpportunity {
  return {
    id: 'cccccccc-3333-4333-8333-333333333333',
    account_id: 'dddddddd-4444-4444-8444-444444444444',
    stage: 'dismissed',
    owner_id: null,
    opened_at: '2026-06-01T09:00:00Z',
    opened_by: 'automatic',
    score_at_open: 35,
    contested_at_open: false,
    score: 50,
    score_change_since_open: 15,
    evidence: 'current',
    history,
    allowed_next: [],
  };
}

const TOOK_ON: WorkflowState = {
  stage: 'engaged',
  owner_id: COLLEAGUE,
  decided_by: COLLEAGUE,
  reason: 'Met their VP at a conference.',
  occurred_at: '2026-06-14T09:00:00Z',
};

const DISMISSED: WorkflowState = {
  stage: 'dismissed',
  owner_id: null,
  decided_by: ME,
  reason: "Wrong segment — they're SMB.",
  occurred_at: '2026-07-02T09:00:00Z',
};

describe('the account remembers what was decided, and why', () => {
  it('leads with the reason, because the reason is the record', () => {
    // "Wrong segment — they're SMB" is the whole value. The stage is how the
    // product filed it, and a trail that led with vocabulary would read as a
    // status log rather than a colleague's note.
    render(<DecisionHistory opportunity={opportunity([OPENED, DISMISSED])} viewerId={ME} />);

    expect(screen.getByText("Wrong segment — they're SMB.")).toBeVisible();
  });

  it('shows every entry, including the one Signora authored', () => {
    render(
      <DecisionHistory
        opportunity={opportunity([OPENED, TOOK_ON, DISMISSED])}
        viewerId={ME}
      />,
    );

    expect(screen.getByText(/Qualified by Signora/)).toBeVisible();
    expect(screen.getByText('Met their VP at a conference.')).toBeVisible();
    expect(screen.getByText("Wrong segment — they're SMB.")).toBeVisible();
  });

  it('keeps the order the record was written in', () => {
    // **The screen does not re-sort.** The same rule the ledger follows, for a
    // stronger reason: a trail reordered by a browser is a trail that can
    // disagree with the record it claims to show.
    const { container } = render(
      <DecisionHistory
        opportunity={opportunity([OPENED, TOOK_ON, DISMISSED])}
        viewerId={ME}
      />,
    );

    const text = container.textContent ?? '';
    expect(text.indexOf('Qualified by Signora')).toBeLessThan(
      text.indexOf('Met their VP'),
    );
    expect(text.indexOf('Met their VP')).toBeLessThan(text.indexOf('Wrong segment'));
  });
});

describe('nobody is named whom the product cannot name', () => {
  it('says *you* for your own decision', () => {
    render(<DecisionHistory opportunity={opportunity([OPENED, DISMISSED])} viewerId={ME} />);

    expect(screen.getByText(/^You ·/)).toBeVisible();
  });

  it('says *somebody here* for a colleague, never an identifier', () => {
    // **D23.** Better Auth owns user profiles in the Next.js tier and the
    // Python tier verifies tokens without learning who anybody is, so a raw
    // identifier would be the same absence dressed as information.
    const { container } = render(
      <DecisionHistory opportunity={opportunity([OPENED, TOOK_ON])} viewerId={ME} />,
    );

    expect(screen.getByText(/Somebody here ·/)).toBeVisible();
    expect(container.textContent).not.toContain(COLLEAGUE);
  });

  it('never prints an identifier for anybody', () => {
    const { container } = render(
      <DecisionHistory
        opportunity={opportunity([OPENED, TOOK_ON, DISMISSED])}
        viewerId={ME}
      />,
    );

    expect(container.textContent).not.toContain(ME);
    expect(container.textContent).not.toContain(COLLEAGUE);
  });

  it("credits Signora for the entry it authored, not a person", () => {
    // The distinction the whole product rests on: intelligence suggests,
    // humans commit — and the record already knows which this was.
    render(<DecisionHistory opportunity={opportunity([OPENED, DISMISSED])} viewerId={ME} />);

    expect(screen.getByText(/^Signora ·/)).toBeVisible();
  });
});

describe('the trail names people, now that the product can', () => {
  // **TM-01 changed the fact underneath D23**, and this is where that shows:
  // a membership carries the address it was created with, so the roster the
  // brief already holds can turn an identifier into a person.
  const PEOPLE = new Map([[COLLEAGUE, 'ravi@acme.com']]);

  it('names a colleague when the roster can name them', () => {
    render(
      <DecisionHistory
        opportunity={opportunity([OPENED, TOOK_ON])}
        viewerId={ME}
        people={PEOPLE}
      />,
    );

    expect(screen.getByText(/ravi@acme\.com ·/)).toBeVisible();
  });

  it('still says *somebody here* for a membership with no address', () => {
    // **A name the roster does not hold is a fact about today**, and the
    // record is about then — somebody who has since left still decided this.
    render(
      <DecisionHistory
        opportunity={opportunity([OPENED, TOOK_ON])}
        viewerId={ME}
        people={new Map()}
      />,
    );

    expect(screen.getByText(/Somebody here ·/)).toBeVisible();
  });

  it('never prints an identifier, even when it cannot resolve one', () => {
    const { container } = render(
      <DecisionHistory
        opportunity={opportunity([OPENED, TOOK_ON])}
        viewerId={ME}
        people={new Map()}
      />,
    );

    expect(container.textContent).not.toContain(COLLEAGUE);
  });
});

describe('a hand-over reads as a hand-over', () => {
  const PEOPLE = new Map([
    [ME, 'ana@acme.com'],
    [COLLEAGUE, 'ravi@acme.com'],
  ]);

  const I_TOOK_IT_ON: WorkflowState = {
    stage: 'engaged',
    owner_id: ME,
    decided_by: ME,
    reason: 'Met their VP at a conference.',
    occurred_at: '2026-06-14T09:00:00Z',
  };

  const I_HANDED_IT_OVER: WorkflowState = {
    stage: 'engaged',
    owner_id: COLLEAGUE,
    decided_by: ME,
    reason: 'On leave until March.',
    occurred_at: '2026-06-20T09:00:00Z',
  };

  it('does not say *took it on* about somebody giving an account away', () => {
    // **The defect this rendering exists to prevent.** The stage on that row
    // is `engaged`, and reading the stage alone would have told a seller that
    // Ana took on an account she had just handed to Ravi.
    render(
      <DecisionHistory
        opportunity={opportunity([OPENED, I_TOOK_IT_ON, I_HANDED_IT_OVER])}
        viewerId={ME}
        people={PEOPLE}
      />,
    );

    expect(screen.getByText(/handed it to ravi@acme\.com/)).toBeVisible();
    expect(screen.getAllByText(/took it on/)).toHaveLength(1);
  });

  it('says who took it over, and from whom', () => {
    const TOOK_IT_OVER: WorkflowState = {
      stage: 'engaged',
      owner_id: ME,
      decided_by: ME,
      reason: 'Agreed at the pipeline review.',
      occurred_at: '2026-06-25T09:00:00Z',
    };

    render(
      <DecisionHistory
        opportunity={opportunity([OPENED, I_TOOK_IT_ON, I_HANDED_IT_OVER, TOOK_IT_OVER])}
        viewerId={ME}
        people={PEOPLE}
      />,
    );

    expect(screen.getByText(/took it over from ravi@acme\.com/)).toBeVisible();
  });

  it('reads the first owner arriving as taking it on, not as a hand-over', () => {
    // Ownership moved here too — from nobody. **There was no previous holder
    // to be handed from**, and inventing one would be the trail describing an
    // act that did not happen.
    render(
      <DecisionHistory
        opportunity={opportunity([OPENED, I_TOOK_IT_ON])}
        viewerId={ME}
        people={PEOPLE}
      />,
    );

    expect(screen.getByText(/took it on/)).toBeVisible();
  });

  it('lets the close lead when a close also moved the owner', () => {
    // **Ownership leads only where it is the news.** A win that also
    // reassigned is a win; the assignment beside it is bookkeeping.
    const WON: WorkflowState = {
      stage: 'closed_won',
      owner_id: COLLEAGUE,
      decided_by: ME,
      reason: 'Signed the three-year deal.',
      occurred_at: '2026-07-02T09:00:00Z',
    };

    render(
      <DecisionHistory
        opportunity={opportunity([OPENED, I_TOOK_IT_ON, WON])}
        viewerId={ME}
        people={PEOPLE}
      />,
    );

    expect(screen.getByText(/closed it won/)).toBeVisible();
    expect(screen.queryByText(/handed it to/)).toBeNull();
  });

  it('says *you* rather than your own address', () => {
    // A reader recognises themselves before they read anything else, and
    // seeing your own email in a trail you wrote is the product failing to
    // notice who is looking.
    const HANDED_TO_ME: WorkflowState = {
      stage: 'engaged',
      owner_id: ME,
      decided_by: COLLEAGUE,
      reason: 'Your territory now.',
      occurred_at: '2026-06-28T09:00:00Z',
    };

    const { container } = render(
      <DecisionHistory
        opportunity={opportunity([OPENED, TOOK_ON, HANDED_TO_ME])}
        viewerId={ME}
        people={PEOPLE}
      />,
    );

    expect(screen.getByText(/handed it to you/)).toBeVisible();
    expect(container.textContent).not.toContain('ana@acme.com');
  });
});

describe('it is silent when it has nothing to say', () => {
  it('renders nothing on an account nobody has decided anything about', () => {
    // Every account has an opening entry, so a section rendered for that alone
    // would appear on every brief carrying nothing — which is exactly what
    // made the workflow line furniture (R1-06).
    const { container } = render(
      <DecisionHistory opportunity={opportunity([OPENED])} viewerId={ME} />,
    );

    expect(container).toBeEmptyDOMElement();
  });

  it('renders nothing when there is no history at all', () => {
    const { container } = render(
      <DecisionHistory opportunity={opportunity([])} viewerId={ME} />,
    );

    expect(container).toBeEmptyDOMElement();
  });

  it('appears as soon as one real decision exists', () => {
    render(<DecisionHistory opportunity={opportunity([OPENED, TOOK_ON])} viewerId={ME} />);

    expect(
      screen.getByRole('heading', { name: 'What has been decided' }),
    ).toBeVisible();
  });
});
