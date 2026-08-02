/**
 * Whether the brief agrees with the list about the same account.
 *
 * **A page-level test, deliberately, and for the third time** (D36, B-006).
 * R1-04 was never a broken component: `EvidenceHealth` has rendered *Cooling*
 * correctly on the attention list since M12.2, and its own tests passed
 * throughout. The defect was that **the brief never called it** — it rendered
 * `is_current`, which is true of a different fact, so the list said *"this is
 * going off the boil"* and the detail page said *"exactly correct until Sep 20,
 * 2026"* about the same company on the same afternoon.
 *
 * *"The list flagged it, the detail page didn't, so I assumed the list was
 * noisy."* Two screens disagreeing is the one failure a component test
 * structurally cannot see, because neither component is wrong.
 *
 * R1-04 and R2-03 — the same plumbing, and the reason they were done together.
 */
import { render, screen } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import type { ReactElement } from 'react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import { ApiError } from '@/lib/api/client';
import type { AccountOpportunity, AccountScore } from '@/lib/api/types';

const workspaceContext = vi.hoisted(() => vi.fn());
const session = vi.hoisted(() => vi.fn());
const score = vi.hoisted(() => vi.fn());
const opportunity = vi.hoisted(() => vi.fn());
const narration = vi.hoisted(() => vi.fn());
const validation = vi.hoisted(() => vi.fn());
const research = vi.hoisted(() => vi.fn());
const accounts = vi.hoisted(() => vi.fn());
const identities = vi.hoisted(() => vi.fn());

vi.mock('next/navigation', () => ({
  useParams: () => ({ accountId: '22222222-2222-4222-8222-222222222222' }),
  // The account sequence binds `j`/`k` to move through the ranked list. Not
  // this test's subject, and it needs a router to exist.
  useRouter: () => ({ push: vi.fn(), prefetch: vi.fn() }),
}));

vi.mock('@/lib/state/workspace-provider', () => ({
  useWorkspaceContext: workspaceContext,
}));

vi.mock('@/lib/auth/client', () => ({ useSession: session }));

vi.mock('@/lib/query/hooks', () => ({
  useAccountScore: score,
  useAccountOpportunity: opportunity,
  useAccountNarration: narration,
  useAccountValidation: validation,
  useAccountResearch: research,
  useAccounts: accounts,
  useAccountIdentities: identities,
  useRequestResearch: () => ({ mutate: vi.fn(), isPending: false }),
  useBusinessEvent: () => ({ data: undefined, isLoading: false, isError: false }),
}));

import AccountBriefPage from '@/app/(app)/accounts/[accountId]/page';

const WORKSPACE = 'aaaaaaaa-1111-4111-8111-111111111111';
const ACCOUNT = '22222222-2222-4222-8222-222222222222';
const IDLE = { data: undefined, isLoading: false, isError: false, error: null };

const SCORE: AccountScore = {
  account_id: ACCOUNT,
  value: 35,
  possible: 120,
  contested: false,
  trigger: 'signal_generated',
  is_current: true,
  valid_until: '2026-09-20T00:00:00Z',
  attention_by_posture: { expansion: 35 },
  contributions: [],
  computed_at: '2026-08-01T09:00:00Z',
} as unknown as AccountScore;

function committed(overrides: Partial<AccountOpportunity> = {}): AccountOpportunity {
  return {
    id: '33333333-3333-4333-8333-333333333333',
    account_id: ACCOUNT,
    stage: 'tracking',
    owner_id: null,
    opened_at: '2026-07-01T09:00:00Z',
    opened_by: 'automatic',
    score_at_open: 50,
    contested_at_open: false,
    score: 35,
    score_change_since_open: -15,
    evidence: 'cooling',
    history: [],
    allowed_next: [],
    ...overrides,
  } as unknown as AccountOpportunity;
}

function withQuery(node: ReactElement) {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return <QueryClientProvider client={client}>{node}</QueryClientProvider>;
}

beforeEach(() => {
  workspaceContext.mockReturnValue({
    workspaces: [{ id: WORKSPACE }],
    activeWorkspace: { id: WORKSPACE },
    isLoading: false,
  });
  session.mockReturnValue({ data: { user: { id: 'user-1' } } });
  score.mockReturnValue({ ...IDLE, data: SCORE });
  opportunity.mockReturnValue({ ...IDLE, data: committed() });
  narration.mockReturnValue(IDLE);
  validation.mockReturnValue({ ...IDLE, data: { account_id: ACCOUNT, hypotheses: [] } });
  research.mockReturnValue(IDLE);
  accounts.mockReturnValue({ ...IDLE, data: { items: [] } });
  identities.mockReturnValue(IDLE);
});

describe('the brief and the list say the same thing about the same account — R1-04', () => {
  it('shows the cooling badge the list has always shown', () => {
    render(withQuery(<AccountBriefPage />));

    expect(screen.getByText('Cooling')).toBeVisible();
  });

  it('shows it beside the movement, where the two are one story', () => {
    // "Opened at 50, −15 since" and "cooling" are the same fact told twice,
    // which is the point: the number is what happened and the badge is that it
    // crossed a threshold Signora considers material.
    render(withQuery(<AccountBriefPage />));

    expect(screen.getByText(/-15 since|−15 since/)).toBeVisible();
    expect(screen.getByText('Cooling')).toBeVisible();
  });

  it('says nothing when the evidence is current', () => {
    // "Everything is fine" is noise that trains people to stop reading badges,
    // and the list has taken that position since M12.2. Two screens, one rule.
    opportunity.mockReturnValue({ ...IDLE, data: committed({ evidence: 'current' }) });

    render(withQuery(<AccountBriefPage />));

    expect(screen.queryByText('Cooling')).toBeNull();
    expect(screen.queryByText('Evidence current')).toBeNull();
  });

  it('does not repeat "expired" when the reading already says so', () => {
    // **`is_current: false` implies `evidence: 'stale'`** — one derivation
    // read from the score, the other from the opportunity — so the badge and
    // `ReadingValidity` three lines below were stating one fact twice. The
    // sentence states it better: it names the date.
    //
    // **This test previously asserted an unreachable state.** Its fixture
    // paired `stale` with `is_current: true`, which the pipeline cannot
    // produce: `evidence_state` is only `stale` when the score is absent or
    // past its validity, and a brief showing an `AccountScore` with
    // `is_current: true` is neither. It passed, and asserted nothing.
    score.mockReturnValue({ ...IDLE, data: { ...SCORE, is_current: false } });
    opportunity.mockReturnValue({
      ...IDLE,
      data: committed({ evidence: 'stale', score: null, score_change_since_open: null }),
    });

    render(withQuery(<AccountBriefPage />));

    expect(screen.queryByText('Evidence expired')).toBeNull();
    expect(screen.getByText(/This reading expired/)).toBeVisible();
  });

  it('still marks a cooling account, which nothing else says', () => {
    // The badge's whole remaining job. `cooling` is derived from the drop
    // since the opportunity opened, and no other element on this page knows
    // it — which is why R1-04 put it here in the first place.
    render(withQuery(<AccountBriefPage />));

    expect(screen.getByText('Cooling')).toBeVisible();
  });

  it('says nothing about evidence on an account nobody has taken on', () => {
    // No commitment, so there is nothing for the reading to be holding up
    // *against*. A badge here would be a state the product never computed.
    opportunity.mockReturnValue(IDLE);

    render(withQuery(<AccountBriefPage />));

    expect(screen.queryByText('Cooling')).toBeNull();
    expect(screen.queryByText('Evidence expired')).toBeNull();
  });
});

describe('the brief distinguishes a quiet account from a broken one — R2-03', () => {
  it('says there is nothing to check, rather than dropping the section', () => {
    render(withQuery(<AccountBriefPage />));

    expect(screen.getByRole('heading', { name: 'Before you act' })).toBeVisible();
    expect(screen.getByText(/nothing to check right now/)).toBeVisible();
  });

  it('names expired evidence as the reason, when that is the reason', () => {
    opportunity.mockReturnValue({
      ...IDLE,
      data: committed({ evidence: 'stale', score: null, score_change_since_open: null }),
    });

    render(withQuery(<AccountBriefPage />));

    expect(screen.getByText(/evidence behind this account has expired/)).toBeVisible();
  });

  it('says the request failed, in different words', () => {
    // The whole finding: "the section just isn't there, so I can't tell if
    // there's nothing to check or if the feature didn't load."
      validation.mockReturnValue({ ...IDLE, isError: true });

    render(withQuery(<AccountBriefPage />));

    expect(screen.getByText(/could not load what to check/)).toBeVisible();
    expect(screen.queryByText(/nothing to check right now/)).toBeNull();
  });

  it('says neither while the answer is still being fetched', () => {
    // Announcing "nothing to check" during the first paint is a confident
    // wrong answer, and it is the failure the list's own empty state avoids.
    validation.mockReturnValue(IDLE);

    render(withQuery(<AccountBriefPage />));

    expect(screen.queryByRole('heading', { name: 'Before you act' })).toBeNull();
  });
});

describe('the brief tells three narration states apart — B-010, TASK-004', () => {
  it('says nothing has been written when there is no narration', () => {
    // A 404 here is an answer: Signora has written no explanation for this
    // account. It used to render as the same blank space as a broken request.
    narration.mockReturnValue({
      ...IDLE,
      isError: true,
      error: notFound(),
    });

    render(withQuery(<AccountBriefPage />));

    expect(screen.getByRole('heading', { name: 'In plain language' })).toBeVisible();
    expect(screen.getByText(/has not written one for this account yet/)).toBeVisible();
  });

  it('says the request failed when it actually failed', () => {
    narration.mockReturnValue({
      ...IDLE,
      isError: true,
      error: new Error('network down'),
    });

    render(withQuery(<AccountBriefPage />));

    expect(screen.getByText(/could not load the explanation/)).toBeVisible();
    expect(screen.queryByText(/has not written one/)).toBeNull();
  });

  it('says neither while the answer is still in flight', () => {
    render(withQuery(<AccountBriefPage />));

    expect(screen.queryByRole('heading', { name: 'In plain language' })).toBeNull();
  });
});

/** What the API returns for an account nothing has narrated. */
function notFound(): ApiError {
  return new ApiError(404, {
    code: 'not_found',
    message: 'No narration for this account.',
    correlation_id: '00000000-0000-4000-8000-000000000000',
  });
}
