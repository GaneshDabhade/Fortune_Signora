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
