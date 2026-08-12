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
import { cleanup, render, screen } from '@testing-library/react';
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
const timeline = vi.hoisted(() => vi.fn());
const observations = vi.hoisted(() => vi.fn());

vi.mock('next/navigation', () => ({
  // The attention list and the brief read `?owner=` so a seller's view
  // survives a refresh and travels on the account link (LO-03).
  useSearchParams: () => new URLSearchParams(),
  useParams: () => ({ accountId: '22222222-2222-4222-8222-222222222222' }),
  // The account sequence binds `j`/`k` to move through the ranked list. Not
  // this test's subject, and it needs a router to exist.
  useRouter: () => ({ push: vi.fn(), prefetch: vi.fn() }),
}));

vi.mock('@/lib/state/workspace-provider', () => ({
  useWorkspaceContext: workspaceContext,
}));

vi.mock('@/lib/auth/client', () => ({ useSession: session }));

vi.mock('@/lib/query/hooks/timeline', () => ({ useAccountTimeline: timeline }));

vi.mock('@/lib/query/hooks', () => ({
  useAccountScore: score,
  useAccountOpportunity: opportunity,
  useAccountNarration: narration,
  useAccountValidation: validation,
  useAccountResearch: research,
  useAccounts: accounts,
  useAccountIdentities: identities,
  // TASK-417 wave 1 — what changed, and who says so. Stubbed rather than
  // exercised here: this file is about the brief's own sentences, and the
  // section has its own tests in observations.test.tsx.
  useAccountObservations: observations,
  useRequestResearch: () => ({ mutate: vi.fn(), isPending: false }),
  // A won account has no legal move, so the brief now renders the way
  // back rather than an empty space (LO-05 F-7, LO-07).
  useOpenOpportunity: () => ({ mutate: vi.fn(), reset: vi.fn(), isPending: false, error: null }),
  useRecordDecision: () => ({ mutate: vi.fn(), reset: vi.fn(), isPending: false, error: null }),
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
  observations.mockReturnValue(IDLE);
  timeline.mockReturnValue({
    data: { pages: [{ items: [], next_cursor: null, has_more: false }] },
    hasNextPage: false,
    isLoading: false,
    isFetchingNextPage: false,
    isError: false,
    fetchNextPage: vi.fn(),
  });
});

describe('the brief has a document outline — B-313', () => {
  it('names the account in a level-1 heading', () => {
    // **The screen sellers live on had no `<h1>` at all.** Its two `<h2>`s
    // hung under nothing, so a reader navigating by heading landed on *"What
    // contributed"* without learning which account they were looking at, and
    // the document outline began at level 2.
    render(withQuery(<AccountBriefPage />));

    const headings = screen.getAllByRole('heading', { level: 1 });
    expect(headings).toHaveLength(1);
    expect(headings[0]?.textContent).toBeTruthy();
  });

  it('puts every other heading beneath it', () => {
    // The regression that matters: an outline is only useful if the sections
    // hang off the page's name rather than off nothing.
    render(withQuery(<AccountBriefPage />));

    const levels = screen
      .getAllByRole('heading')
      .map((heading) => Number(heading.tagName.slice(1)));

    expect(Math.min(...levels)).toBe(1);
    expect(levels.filter((level) => level === 1)).toHaveLength(1);
  });
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
    // ⚠️ **This asserted the heading was ABSENT until TASK-1476.** ⛔ B-010's
    // rule is *says neither*, and the heading said neither — 📁 the design
    // paints the header and skeletons only the body, so the absent heading was
    // the page jump rather than the guard.
    render(withQuery(<AccountBriefPage />));

    expect(screen.queryByText(/has not written one/)).toBeNull();
    expect(screen.queryByText(/could not load the explanation/)).toBeNull();
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

describe('the account says what has actually happened to it — C-024', () => {
  // **Timeline's backend, hook and component were complete and mounted
  // nowhere.** Twenty component tests passed the whole time; none of them
  // could ask whether any page rendered it. This is that question.

  it('renders the history section on the brief', () => {
    render(withQuery(<AccountBriefPage />));

    expect(screen.getByRole('heading', { name: 'What has happened' })).toBeVisible();
  });

  it('shows what the pipeline recorded, in the seller’s words', () => {
    timeline.mockReturnValue({
      data: {
        pages: [
          {
            items: [
              // **The real contract, not a convenient one.** `TimelineEntry`
              // has no `summary`: the headline comes from the reviewed
              // catalog in the component and the detail from `detail`. A
              // fixture that invented a field would assert against a shape
              // the API cannot produce — which is what PS-07 found in this
              // very file.
              {
                id: 'e1',
                kind: 'signal_generated',
                occurred_at: '2026-07-30T09:00:00Z',
                source_module: 'signal_engine',
                source_ref: '44444444-4444-4444-8444-444444444444',
                detail: { signal_type: 'hiring_surge' },
              },
            ],
            next_cursor: null,
            has_more: false,
          },
        ],
      },
      hasNextPage: false,
      isLoading: false,
      isFetchingNextPage: false,
      isError: false,
      fetchNextPage: vi.fn(),
    });

    render(withQuery(<AccountBriefPage />));

    expect(screen.getByText('New reason to pay attention')).toBeVisible();
    // `hiring_surge` said aloud — engineering's key never reaches the screen.
    expect(screen.getByText('Hiring surge')).toBeVisible();
  });

  it('says the history is empty rather than rendering nothing', () => {
    // The same rule PS-01 and PS-02 established: an absent section reads as a
    // feature the customer does not have, which is the defect B-006 was.
    render(withQuery(<AccountBriefPage />));

    expect(
      screen.getByText(/Nothing has been recorded about this company yet/i),
    ).toBeVisible();
  });

  it('reports a failed history without removing the section', () => {
    timeline.mockReturnValue({
      data: undefined,
      hasNextPage: false,
      isLoading: false,
      isFetchingNextPage: false,
      isError: true,
      fetchNextPage: vi.fn(),
    });

    render(withQuery(<AccountBriefPage />));

    expect(screen.getByRole('heading', { name: 'What has happened' })).toBeVisible();
    expect(screen.getByText(/could not be loaded/i)).toBeVisible();
  });

  it('sits below the evidence ledger, where the page turns to what occurred', () => {
    const { container } = render(withQuery(<AccountBriefPage />));
    const text = container.textContent ?? '';

    expect(text.indexOf('What contributed')).toBeLessThan(text.indexOf('What has happened'));
  });
});

describe('the brief says how current its evidence is — A4', () => {
  /**
   * **Page-level for the fourth time, and for the reason this file exists.**
   * `Freshness` has its own tests and they would all pass while the brief
   * never called it — which is precisely what R1-04 was. A seller cannot
   * calibrate a score, its contributions or its narration without knowing how
   * old the evidence beneath them is, and the component being correct in
   * isolation does nothing for them.
   */
  function named(lastObservedAt: string | null) {
    return {
      ...IDLE,
      data: new Map([
        [
          ACCOUNT,
          {
            account_id: ACCOUNT,
            name: 'Northwind Traders',
            agreement: 'agreed',
            source_count: 2,
            source: 'apollo',
            observed_at: '2026-01-05T00:00:00Z',
            last_observed_at: lastObservedAt,
          },
        ],
      ]),
    };
  }

  it('carries the line, above everything built on that evidence', () => {
    identities.mockReturnValue(named(new Date(Date.now() - 20 * 86_400_000).toISOString()));

    const { container } = render(withQuery(<AccountBriefPage />));
    const text = container.textContent ?? '';

    expect(screen.getByText(/Latest evidence · 2 weeks ago/)).toBeVisible();
    expect(text.indexOf('Latest evidence')).toBeLessThan(text.indexOf('What contributed'));
  });

  it('says an account has nothing rather than leaving the line out', () => {
    identities.mockReturnValue(named(null));

    render(withQuery(<AccountBriefPage />));

    expect(screen.getByText('No evidence collected yet')).toBeVisible();
  });
});

describe('an account with no data still says what it has no data about — TASK-417', () => {
  /**
   * **Wave 1's acceptance criterion, made executable.** The row asks for *"a
   * designed empty state where a workspace has no data"*, and the whole
   * `beforeEach` above already renders exactly that workspace — every hook
   * idle, every list empty. Until now nothing asserted the page survived it;
   * it merely happened to.
   *
   * **The failure this guards is a section that vanishes.** A brief that drops
   * *What changed* when nothing has changed teaches a reader that the section
   * does not exist, and on the day it fills up they will not know to look. A
   * heading with an explanation beneath it is the difference between *"nothing
   * has happened here"* and *"this product does not do that"*.
   */
  it('keeps every derived section on the page', () => {
    render(withQuery(<AccountBriefPage />));

    for (const heading of ['What contributed', 'What changed', 'What has happened']) {
      expect(screen.getByRole('heading', { name: heading })).toBeVisible();
    }
  });

  it('explains the emptiness rather than leaving a blank', () => {
    render(withQuery(<AccountBriefPage />));

    // The observations section says what it was told, which is not the same
    // claim as nothing having happened at the company.
    expect(screen.getByText(/not the same as nothing having happened/i)).toBeVisible();
  });

  it('omits the competitor list, because that one is a declaration', () => {
    /**
     * **The deliberate exception, asserted so it stays deliberate.** Every
     * other section here is derived *about this account*, so its absence is a
     * fact worth stating. The competitor list is a workspace declaration: a
     * card explaining its own absence would appear on every account of every
     * workspace that has not filled it in, and the place to prompt for a
     * declaration is the page where declarations are made.
     */
    render(withQuery(<AccountBriefPage />));

    expect(screen.queryByText(/who you compete against/i)).not.toBeInTheDocument();
  });
});

/**
 * **A page must say when it could not find out — TASK-442.**
 *
 * *"Absence can never distinguish itself from failure."* — [P-A · Stated
 * absence], ratified 2026-08-05 with **nine recorded instances and zero
 * executable assertions**. This is the first.
 *
 * ### Why it is a page-level test and not a prop
 *
 * **[C-226] was raised by this lane after finding three sections of the brief
 * rendering a failed read as an empty account**, and the fix at TASK-417 was
 * three components each learning to tell the two apart. That fix is correct
 * and it is not a guarantee: **the fourth section added next week starts out
 * unable to tell them apart, and nothing fails.**
 *
 * **[467 §3] endorsed the page-level form for exactly that reason**, and it is
 * the shape `no-mock-data.test.tsx` and `design-tokens.test.tsx` already use —
 * a repository-wide invariant asserted by a test rather than by review.
 *
 * ⚡ **It cannot be silenced by adding a field.** The assertion is about what
 * the *page* says with every read failing, so a new section that renders
 * nothing on error makes the page quieter and the test no happier.
 */
describe('a page must say when it could not find out — P-A, TASK-442', () => {
  /** Every read the brief makes, in the failed state the API can actually
   * produce. `isError` with `data: undefined` is what react-query hands a
   * component when a request rejects. */
  const FAILED = { data: undefined, isLoading: false, isError: true, error: new Error('x') };

  /** **The sentences a customer must never be shown instead.** Each one
   * asserts something the page cannot know when every read has failed: that
   * there is nothing here, that nothing has happened, that all is well. */
  const FALSE_REASSURANCE = [
    /nothing (has )?happened/i,
    /no activity/i,
    /up to date/i,
    /all clear/i,
    /nothing to (show|report|do)/i,
  ];

  function everyReadFails() {
    score.mockReturnValue(FAILED);
    opportunity.mockReturnValue(FAILED);
    narration.mockReturnValue(FAILED);
    validation.mockReturnValue(FAILED);
    research.mockReturnValue(FAILED);
    accounts.mockReturnValue(FAILED);
    identities.mockReturnValue(FAILED);
    observations.mockReturnValue(FAILED);
    timeline.mockReturnValue({
      data: undefined,
      hasNextPage: false,
      isLoading: false,
      isFetchingNextPage: false,
      isError: true,
      fetchNextPage: vi.fn(),
    });
  }

  it('says the read failed, in words, when every read has failed', () => {
    everyReadFails();

    const { container } = render(withQuery(<AccountBriefPage />));

    // **Any of these is a page admitting it does not know.** The wording is
    // each section's; what this asserts is that *something* says so — a page
    // that rendered a screenful of blanks would pass no part of this.
    expect(container.textContent).toMatch(
      /could not|couldn't|unavailable|unable to|try again|reload/i,
    );
  });

  it('never offers reassurance it cannot support', () => {
    /** **The half that matters, and the one C-226 actually found.** A page
     * that says *"nothing has happened here"* when it could not reach the
     * server has not merely failed to inform — it has told the customer
     * something false, and they will act on it. */
    everyReadFails();

    const { container } = render(withQuery(<AccountBriefPage />));

    for (const claim of FALSE_REASSURANCE) {
      expect(container.textContent, `page reassures on a failed read: ${claim}`).not.toMatch(
        claim,
      );
    }
  });

  it('does not render as an empty account', () => {
    /** **The specific defect, asserted against the specific state.** Three
     * sections did this before TASK-417: a failed read produced the same
     * output as an account nothing is known about. The two are opposite
     * facts — one is *ask again*, the other is *there is nothing to ask*. */
    everyReadFails();
    const failed = render(withQuery(<AccountBriefPage />)).container.textContent ?? '';
    cleanup();

    // The same page with every read *succeeding* and returning nothing —
    // a genuinely empty account.
    score.mockReturnValue(IDLE);
    opportunity.mockReturnValue({ ...IDLE, data: committed() });
    narration.mockReturnValue(IDLE);
    validation.mockReturnValue({ ...IDLE, data: { account_id: ACCOUNT, hypotheses: [] } });
    research.mockReturnValue(IDLE);
    accounts.mockReturnValue({ ...IDLE, data: { items: [] } });
    identities.mockReturnValue(IDLE);
    observations.mockReturnValue(IDLE);
    timeline.mockReturnValue({
      data: { pages: [{ items: [], next_cursor: null, has_more: false }] },
      hasNextPage: false,
      isLoading: false,
      isFetchingNextPage: false,
      isError: false,
      fetchNextPage: vi.fn(),
    });
    const empty = render(withQuery(<AccountBriefPage />)).container.textContent ?? '';

    expect(
      failed,
      'a failed read renders identically to an empty account — this is C-226',
    ).not.toBe(empty);
  });

  it('says so even when only some reads fail', () => {
    /** **The realistic outage, and the one a whole-page check would miss.**
     * Services fail one at a time. A page that only admitted failure when
     * *everything* broke would be silent in the case that actually happens. */
    score.mockReturnValue(FAILED);
    narration.mockReturnValue(FAILED);

    const { container } = render(withQuery(<AccountBriefPage />));

    expect(container.textContent).toMatch(
      /could not|couldn't|unavailable|unable to|try again|reload/i,
    );
  });
});
