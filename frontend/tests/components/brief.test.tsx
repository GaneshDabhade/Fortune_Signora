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
const commercials = vi.hoisted(() => vi.fn());
const decision = vi.hoisted(() => vi.fn());
/** 🔴 [B-1045](../../docs/BUGS.md) — the crumb is published into a context the
 *  shell renders, so it never reaches this tree's DOM. **Capturing the call is
 *  the only way to assert the label** rather than assert around it. */
const publishCrumb = vi.hoisted(() => vi.fn());
/** ⚡ **Hoisted so a test can vary them** — the empty case is the one that
 *  proves the chip is genuinely conditional. */
const tagVocabulary = vi.hoisted(() => vi.fn());
const tagAssignments = vi.hoisted(() => vi.fn());

vi.mock('next/navigation', () => ({
  // The attention list and the brief read `?owner=` so a seller's view
  // survives a refresh and travels on the account link (LO-03).
  useSearchParams: () => new URLSearchParams(),
  useParams: () => ({ accountId: '22222222-2222-4222-8222-222222222222' }),
  // The account sequence binds `j`/`k` to move through the ranked list. Not
  // this test's subject, and it needs a router to exist.
  useRouter: () => ({ push: vi.fn(), prefetch: vi.fn(), replace: vi.fn() }),
  // ⚡ **Research's focus mode writes the expanded section into the URL** — 📁
  // the design: *"keeps the URL so the expanded view is shareable"* — so the
  // page now reads its own path to rebuild the query without losing it.
  usePathname: () => '/accounts/22222222-2222-4222-8222-222222222222',
}));

vi.mock('@/lib/state/workspace-provider', () => ({
  useWorkspaceContext: workspaceContext,
}));

vi.mock('@/lib/auth/client', () => ({ useSession: session }));

vi.mock('@/components/shell/breadcrumb-trail', () => ({
  usePublishBreadcrumb: publishCrumb,
}));

vi.mock('@/lib/query/hooks/timeline', () => ({ useAccountTimeline: timeline }));

// ⚡ **The record header's facts strip** — 📁 §08's *"four key facts as a
// quiet strip"*, read from the same commercial contract the Companies table
// reads. ⛔ Mocked so the strip's ABSENCE rule is exercised deliberately
// rather than by a failed request.
vi.mock('@/lib/query/hooks/scoring', () => ({ useAccountCommercials: commercials }));

/**
 * 🔴 **📁 §08's `headerTags`** — the design draws neutral chips beside the
 * title, and **the segment is the one with a producer.**
 *
 * ⛔ **It rendered on the Companies list and the context drawer and NOWHERE on
 * the record it describes** — producer-backed and unsurfaced, the same class as
 * the Decision Package and ICP Performance.
 */
/**
 * 🔴 **📁 §08's fourth chip — *"Strategic"*, the customer's own label** —
 * [B-299](../../docs/BUGS.md) ⑧.
 *
 * ⛔ **`useAccountTags`, `useAccountTagAssignments` and `AccountTags` all
 * ship**, and the Companies list and the context drawer have consumed them
 * since they landed. ⚠️ **The record page was the only surface that never
 * called them**, and the note beside the assertion below called this chip a
 * *"firmographic nothing publishes"* — **it is a customer label, and the
 * customer publishes it.**
 */
vi.mock('@/lib/query/hooks/account-tags', () => ({
  useAccountTags: tagVocabulary,
  useAccountTagAssignments: tagAssignments,
}));

vi.mock('@/lib/query/hooks/account-segments', () => ({
  useAccountSegments: () => ({
    data: { segments: [{ segment_id: 'seg-1', name: 'Enterprise' }] },
  }),
  useAccountSegmentMemberships: () => ({
    data: { // ⛔ **The literal, not `ACCOUNT`** — `vi.mock` hoists above the const.
      memberships: [{ account_id: '22222222-2222-4222-8222-222222222222', segment_ids: ['seg-1'] }] },
  }),
}));

vi.mock('@/lib/query/hooks', () => ({
  useAccountScore: score,
  useAccountOpportunity: opportunity,
  useAccountNarration: narration,
  useAccountValidation: validation,
  useAccountResearch: research,
  useAccounts: accounts,
  useAccountIdentities: identities,
  // ⚡ **The design's `#reasoning` card in the 340px track.** 📁 The endpoint,
  // the hook and the contract all ship, and the Companies list has consumed
  // them since they did — ⛔ the record page was the surface that did not.
  useAccountDecisionPackage: decision,
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
/**
 * ⚠️ **`isSuccess` is part of `useQuery`'s shape and this fixture omitted it.**
 * ⛔ **A mock that is missing the field under test cannot fail the test** — the
 * same class of gap that let [B-1053](../../../docs/BUGS.md) exist: *not
 * settled yet* and *settled and absent* looked identical to every caller.
 */
const IDLE = {
  data: undefined,
  isLoading: false,
  isError: false,
  isSuccess: false,
  error: null,
};

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
  publishCrumb.mockClear();
  tagVocabulary.mockReturnValue({
    data: { tags: [{ id: 'tag-1', name: 'Strategic', tone: 'neutral' }] },
  });
  tagAssignments.mockReturnValue({ data: { assignments: { [ACCOUNT]: ['tag-1'] } } });
  observations.mockReturnValue(IDLE);
  commercials.mockReturnValue(IDLE);
  // ⛔ **404 is the ordinary state** — Signora has concluded nothing yet, which
  // is an answer rather than a failure.
  decision.mockReturnValue({
    ...IDLE,
    error: new ApiError(404, {
      code: 'not_found',
      message: 'No conclusion for this account.',
      correlation_id: '00000000-0000-4000-8000-000000000000',
    }),
  });
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

describe('the record header is §08\'s, not a bespoke one — Companies 360', () => {
  it('carries the account in the approved record header rather than a hand-rolled one', () => {
    /**
     * 🔴 **The screen hand-rolled its own header while `RecordHeader` had zero
     * consumers**, which is the *"another bespoke version of an existing common
     * component"* §20c forbids. 📁 §08's plane is the tell: the identity tile,
     * the `Title` role and the facts strip all live inside one `<header>`.
     */
    identities.mockReturnValue({
      ...IDLE,
      data: new Map([
        [
          ACCOUNT,
          {
            account_id: ACCOUNT,
            name: 'Vantage Logistics',
            agreement: 'agreed',
            source: 'crm',
            source_count: 1,
            observed_at: '2026-08-01T09:00:00Z',
            last_observed_at: '2026-08-01T09:00:00Z',
          },
        ],
      ]),
    });

    const { container } = render(withQuery(<AccountBriefPage />));

    const heading = screen.getByRole('heading', { level: 1, name: 'Vantage Logistics' });
    // 📁 §04's `Title` role — the approved header applies it; the old one did
    // not, and rendered the name at `text-lg`.
    expect(heading).toHaveClass('text-title');
    // ⚡ **The identity tile the design draws**, derived from the name Signora
    // already holds — ⛔ never a fabricated logo.
    expect(screen.getByText('VL')).toBeInTheDocument();
    expect(container.querySelector('header')?.contains(heading)).toBe(true);
  });

  it('draws no fact nobody has stated — ADR-0409', () => {
    /**
     * ⛔ **§08 draws six facts and the platform supplies two.** 📁 ADR-0409 §5
     * — *"absence is never inferred, defaulted or zero-filled"* — and
     * [§20c](../../../CLAUDE.md): **an absent fact beats a column of `—`.**
     * ⚠️ *Total contract value*, *Seats* and *Employees* have no provider
     * behind them, so the strip must not invent a row for them.
     */
    commercials.mockReturnValue({
      ...IDLE,
      data: new Map([
        [ACCOUNT, { open_acv: { amount: 1_240_000, currency: 'USD' }, renewal_date: null, stage: null }],
      ]),
    });

    render(withQuery(<AccountBriefPage />));

    expect(screen.getByText('Open ACV')).toBeInTheDocument();
    // ⛔ **No renewal was stated, so there is no Renewal fact** — not a dash,
    // not an empty value, not the label on its own.
    expect(screen.queryByText('Renewal')).toBeNull();
    expect(screen.queryByText('—')).toBeNull();
  });

  it('renders no strip at all when no source has said anything', () => {
    render(withQuery(<AccountBriefPage />));

    // ⚡ A record with nothing commercial behind it gets no quiet strip, rather
    // than an empty one.
    expect(screen.queryByText('Open ACV')).toBeNull();
    expect(screen.queryByText('Renewal')).toBeNull();
  });

  it('offers one way back, and it is the breadcrumb the design draws', () => {
    /**
     * 🔴 **The page carried a *"← All accounts"* link the design does not
     * draw.** 📁 §04 puts *"breadcrumb only"* on the left, and the trail
     * *Accounts / <this company>* is published by this screen itself. ⛔ **Two
     * wayfinding controls for one journey** is exactly the residue this
     * migration removes.
     */
    render(withQuery(<AccountBriefPage />));

    expect(screen.queryByRole('link', { name: 'All accounts' })).toBeNull();
  });
});

describe("the record's secondary column carries what the product can produce", () => {
  /**
   * 📁 **`Design Documents/Fortune Signora Account 360.html`** —
   * `minmax(0,1fr) 340px`, and the second track holds **Risk indicators ·
   * Recommendations · AI reasoning · Evidence**.
   *
   * 🔴 **This lane reported that *"not one of the four has a producer"* and it
   * was wrong.** ✅ `GET …/accounts/{id}/decision-package` is routed,
   * `useAccountDecisionPackage` ships, and the Companies list's expanded row
   * has consumed it since it shipped — **the record page was the surface that
   * did not.**
   */
  /**
   * 🔴 **📁 §08's `headerTags`** — *Enterprise · EMEA · Denmark · Logistics ·
   * Strategic*, neutral chips on the title's line.
   *
   * ⚠️ **This note said *"only the SEGMENT has a producer"* and that
   * *"region, industry and TIER are firmographics nothing publishes."***
   * ⛔ **Two of the three were wrong** — [B-299](../../docs/BUGS.md) ⑧.
   *
   * | 📁 chip | producer |
   * |---|---|
   * | **Enterprise** | ✅ segments |
   * | **Strategic** | 🔴 **NOT a firmographic — the customer's own label**, and `useAccountTags` has shipped all along |
   * | **EMEA · Denmark** · **Logistics** | ⚠️ `AccountAttributes` publishes `country` and `industry` as a module port with **no HTTP surface** — [C-1564](../../docs/LANE_COORDINATION.md). **Absent for want of a route, not for want of data** |
   */
  it("🔴 carries the design's segment chip in the header band", () => {
    render(withQuery(<AccountBriefPage />));
    expect(screen.getByText('Enterprise')).toBeInTheDocument();
  });

  /**
   * ⛔ **The customer's label rendered on the Companies list and the context
   * drawer and NOWHERE on the record it describes** — producer-backed and
   * unsurfaced, the same class as the Decision Package and ICP Performance,
   * **and found by counting the design's chips rather than by anything
   * failing.**
   */
  it("🔴 and the customer's own label, which shipped and was never called here", () => {
    render(withQuery(<AccountBriefPage />));
    expect(screen.getByText('Strategic')).toBeInTheDocument();
  });

  /**
   * ⚡ **The half that keeps this honest.** 📁 `AccountTags`' own law: *"the
   * truth is that the customer has not labelled this account, which is a fact
   * about them rather than about Signora — and a placeholder would make it
   * look like a gap the product should fill."*
   *
   * ⛔ **So an unlabelled account renders NOTHING**, not an em dash and not an
   * absence sentence. ⚠️ **A section states its absence; a chip does not**, and
   * conflating the two would put *"no tags"* on the title line of every record
   * a customer has not got round to labelling.
   */
  it('⛔ and renders no chip at all when the customer has labelled nothing', () => {
    // ✅ **The vocabulary still exists** — the workspace has the label and this
    // account does not wear it. ⛔ **Which is the case a placeholder would get
    // wrong**, and the only case that can distinguish a conditional chip from
    // an unconditional one.
    tagAssignments.mockReturnValue({ data: { assignments: {} } });

    render(withQuery(<AccountBriefPage />));

    expect(screen.queryByText('Strategic')).not.toBeInTheDocument();
    // ⛔ **And no placeholder in its place** — not an em dash, not *"None"*.
    const band = screen.getByRole('heading', { level: 1 }).closest('div');
    expect(band?.textContent ?? '').not.toMatch(/—|None|No tags/i);
  });

  it('renders the AI reasoning the design draws, from the shipped contract', () => {
    decision.mockReturnValue({
      ...IDLE,
      data: {
        account_id: ACCOUNT,
        summary: { text: 'Expansion is live and under-served.', evidence: ['event:1'] },
        stated_reasoning: [
          { text: 'Headcount grew 18% in two quarters.', evidence: ['event:1', 'event:2'] },
          { text: 'No competitor has been mentioned.', evidence: ['event:3'] },
        ],
        supporting_evidence: ['event:1', 'event:2', 'event:3'],
        support: {
          level: 'moderate',
          corroborating_providers: ['apollo', 'crunchbase'],
          contributing_events: 3,
          evidence_state: 'current',
          contested: false,
          dissenting_signals: 0,
        },
        model: 'claude-sonnet-5',
        prompt_name: 'reasoning',
        prompt_version: 1,
      },
    });

    render(withQuery(<AccountBriefPage />));

    expect(screen.getByText('AI reasoning')).toBeInTheDocument();
    expect(screen.getByText('Expansion is live and under-served.')).toBeInTheDocument();
    expect(screen.getByText('Headcount grew 18% in two quarters.')).toBeInTheDocument();
    // ⚡ **Provenance beside the sentence, never behind a hover** — 📁 a reader
    // is entitled to know what generated the language WHILE they read it.
    expect(screen.getByText(/claude-sonnet-5/)).toBeInTheDocument();
    // 📁 §14's fourth term, drawn from `corroborating_providers` rather than
    // from a number somebody chose.
    expect(screen.getByText(/Confidence 4 of 5/)).toBeInTheDocument();
    /**
     * 🔴 **📁 The design's source count** — *"6 sources"*, right-aligned in the
     * card header at `--ai-tint` on `--ai-ink`.
     *
     * ⛔ **`supporting_evidence` was rendering NOWHERE**, and an earlier pass
     * filed it as a producer *surplus* — *"no design document draws it"*.
     * ⚠️ **The design draws it in a HEADER rather than as a section**, which is
     * why searching for a section missed it.
     */
    expect(screen.getByText('3 sources')).toBeInTheDocument();
  });

  it('says Signora has concluded nothing rather than drawing an empty panel', () => {
    // ⛔ **404 is an ANSWER** — the account has no conclusion yet, which is a
    // different sentence from *the request failed*.
    render(withQuery(<AccountBriefPage />));

    expect(screen.getByText('AI reasoning')).toBeInTheDocument();
    expect(
      screen.getByText(/has not reached a conclusion about this account yet/),
    ).toBeInTheDocument();
  });

  it('invents neither of the two cards that have no producer', () => {
    /**
     * ⛔ **Risk indicators and Recommendations are drawn by the design and have
     * NO producer** — nothing on the contract, no hook, no endpoint. 📁
     * [§20c](../../../CLAUDE.md): a screen without a shipped module behind it
     * ships a designed absence, **and a fabricated risk list is not one.**
     */
    render(withQuery(<AccountBriefPage />));

    expect(screen.queryByText('Risk indicators')).toBeNull();
    expect(screen.queryByText('Recommendations')).toBeNull();
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

    expect(screen.getByRole('heading', { name: 'Recent activity' })).toBeVisible();
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

    expect(screen.getByRole('heading', { name: 'Recent activity' })).toBeVisible();
    expect(screen.getByText(/could not be loaded/i)).toBeVisible();
  });

  it('sits below the evidence ledger, where the page turns to what occurred', () => {
    const { container } = render(withQuery(<AccountBriefPage />));
    const text = container.textContent ?? '';

    expect(text.indexOf('Account score')).toBeLessThan(text.indexOf('Recent activity'));
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
      isSuccess: true,
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
    expect(text.indexOf('Latest evidence')).toBeLessThan(text.indexOf('Account score'));
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

    for (const heading of ['Account score', 'Signals timeline', 'Recent activity']) {
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
  const FAILED = {
    data: undefined,
    isLoading: false,
    isError: true,
    isSuccess: false,
    error: new Error('x'),
  };

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

/**
 * 🔴 **[B-1053](../../../docs/BUGS.md) — an account that does not exist rendered
 * as an account that exists with no data.**
 *
 * ⛔ **QE navigated to `/accounts/00000000-0000-0000-0000-000000000000` and got
 * HTTP 200 and a full record**, headed `00000000 — no source has named this
 * account yet` — **the raw UUID's first group, presented as the record's name**
 * — with every section showing its designed empty state. **Twenty API calls on
 * the page and not one of them fetched the account.**
 *
 * ⚡ **The evidence needed was already on the page**, which is what makes this a
 * defect rather than a missing capability.
 */
describe('🔴 an account that does not exist says so', () => {
  /** ⚡ **Settled, and this account is not among the identities returned.** */
  function settledWithout() {
    identities.mockReturnValue({ ...IDLE, isSuccess: true, data: new Map() });
  }

  it('⛔ renders a not-found state instead of a record with a name from the URL', () => {
    settledWithout();
    render(withQuery(<AccountBriefPage />));

    expect(screen.getByRole('heading', { level: 1 })).toHaveTextContent(/not here/i);
    // 🔴 **The name derived from the URL** — the first group of the UUID — must
    // be nowhere on the page.
    expect(screen.queryByText(/^22222222/)).toBeNull();
    // ⛔ **And no section's empty state**, which is what made the record look
    // real: *"No evidence collected yet"* about a company that is not there.
    expect(screen.queryByRole('region', { name: 'Signals timeline' })).toBeNull();
  });

  /**
   * ⚠️ **The distinction this must not lose** — 📁
   * [P-A](../../../docs/DOMAIN_DISCOVERY_REGISTER.md) and
   * [B-207](../../../docs/BUGS.md)'s withdrawal: *could not find out* and *is
   * not there* are different sentences.
   */
  it('⛔ a FAILED identity read is never reported as not found', () => {
    identities.mockReturnValue({
      ...IDLE,
      isError: true,
      isSuccess: false,
      error: new Error('x'),
    });
    render(withQuery(<AccountBriefPage />));

    expect(screen.queryByText(/not here/i)).toBeNull();
  });

  it('⛔ nor is a read still in flight', () => {
    identities.mockReturnValue({ ...IDLE, isLoading: true });
    render(withQuery(<AccountBriefPage />));

    expect(screen.queryByText(/not here/i)).toBeNull();
  });

  /**
   * ⚡ **The state names no cause, and it cannot.** 📁 `/account-identities`
   * omits an account the workspace does not own **for the same reason it omits
   * one that does not exist** — 📁 [§7](../../../CLAUDE.md), *404 never 403* —
   * so a member of another organization and a mistyped id reach this identical
   * branch. ⛔ **A sentence claiming either would be inventing it.**
   */
  it('♿ says nothing about access, and offers the way back', () => {
    settledWithout();
    render(withQuery(<AccountBriefPage />));

    const page = screen.getByRole('heading', { level: 1 }).closest('div');
    expect(page?.textContent ?? '').not.toMatch(/access|permission|not allowed|another organization/i);
    expect(screen.getByRole('link', { name: /back to the companies/i })).toHaveAttribute(
      'href',
      '/accounts',
    );
  });

  /**
   * ✅ **The behaviour [B-207](../../../docs/BUGS.md)'s withdrawal vindicated,
   * asserted so this row cannot disturb it**: an account that EXISTS and has
   * never been scored still says *"Nothing has scored this account yet"* — a
   * 404 from the score read is a settled answer about a real record.
   */
  it('✅ an account that EXISTS and has no score is untouched', () => {
    identities.mockReturnValue({
      ...IDLE,
      isSuccess: true,
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
            last_observed_at: null,
          },
        ],
      ]),
    });
    score.mockReturnValue({
      ...IDLE,
      isError: true,
      error: new ApiError(404, {
        code: 'not_found',
        message: 'not found',
        correlation_id: 'corr-1053',
      }),
    });
    render(withQuery(<AccountBriefPage />));

    expect(screen.queryByText(/not here/i)).toBeNull();
    expect(screen.getByRole('heading', { level: 1 })).toHaveTextContent('Northwind Traders');
  });
});


/**
 * 🔴 **[B-1045](../../docs/BUGS.md) — the breadcrumb said *"This account"* where
 * the header said the account is not named yet.**
 *
 * ## ⛔ The comment above the line described a rule the line did not carry
 *
 * ⚠️ **The crumb read `identity?.name ?? 'This account'`**, under a docblock
 * claiming it *waited* and citing 🔴 [B-290](../../docs/BUGS.md) by name. **One
 * `??` collapsed the two states B-290 exists to separate** — *the read has not
 * landed* and *nobody has named this account* — **and asserted the second.**
 *
 * ⚡ **Why this is a guard and not a one-line diff left to review**: the header
 * 190 lines down was already correct, so **one screen named one record two
 * ways**, and neither surface looked wrong on its own. 📁 That is the failure
 * `brief.test.tsx` was created for (D36, B-006) — *"two screens disagreeing is
 * the one failure a component test structurally cannot see"* — which is why
 * this asserts **the crumb and the header together** rather than the crumb
 * alone. ⛔ **A test that pinned only the crumb would pass on the next surface
 * that drifts.**
 */
describe('🔴 B-1045 — the crumb names the record the header names', () => {
  /** The published trail's last segment — 📁 the design's every case ends in
   *  `current`, and it is the one that carries this record's identity. */
  function currentCrumb(): string {
    const calls = publishCrumb.mock.calls;
    expect(calls.length, 'the screen published no trail at all').toBeGreaterThan(0);
    const trail = calls[calls.length - 1]?.[0] as ReadonlyArray<{
      label: string;
      kind: string;
    }>;
    const last = trail[trail.length - 1];
    expect(last?.kind).toBe('current');
    return last?.label ?? '';
  }

  it('says the name once the identity read has landed', () => {
    identities.mockReturnValue({
      ...IDLE,
      isSuccess: true,
      data: new Map([[ACCOUNT, { account_id: ACCOUNT, name: 'Vantage Logistics' }]]),
    });

    render(withQuery(<AccountBriefPage />));

    expect(currentCrumb()).toBe('Vantage Logistics');
  });

  /**
   * ⚡ **The state the row was filed on.** ⛔ **`'This account'` was true of
   * nothing** — it names no record and distinguishes no state. **The identifier
   * is true of this account in both unsettled states**, which is why one label
   * can serve both without either becoming a claim.
   */
  it('says the identifier — never "This account" — while the read is in flight', () => {
    identities.mockReturnValue({ ...IDLE, isLoading: true });

    render(withQuery(<AccountBriefPage />));

    expect(currentCrumb()).toBe(ACCOUNT.slice(0, 8));
    expect(currentCrumb()).not.toBe('This account');
  });

  /**
   * ⚠️ **The unnamed account is an identity PRESENT with a null name** — ⛔ not
   * an absent entry. 📁 An identity the map does not hold at all means the
   * workspace does not own the account, and 🔴
   * [B-1053](../../docs/BUGS.md) makes this screen render *"That company is
   * not here"* for it. ⚡ **Writing this test the obvious way asserted against
   * the 404 branch and never reached the crumb at all** — the two states share
   * a settled read and nothing else.
   */
  it('says the identifier when the read has landed and nobody has named it', () => {
    identities.mockReturnValue({
      ...IDLE,
      isSuccess: true,
      data: new Map([[ACCOUNT, { account_id: ACCOUNT, name: null }]]),
    });

    render(withQuery(<AccountBriefPage />));

    expect(currentCrumb()).toBe(ACCOUNT.slice(0, 8));
  });

  /**
   * 🔴 **The assertion the row actually made**: *two surfaces describe one
   * state differently*. ⚠️ **Neither of the two tests above can see that** —
   * they pin the crumb, and the crumb was never the whole defect.
   */
  it('agrees with the header on the same screen, in the unnamed state', () => {
    identities.mockReturnValue({
      ...IDLE,
      isSuccess: true,
      data: new Map([[ACCOUNT, { account_id: ACCOUNT, name: null }]]),
    });

    render(withQuery(<AccountBriefPage />));

    // 📁 §04's `Title` — the header's visible label for this record.
    const heading = screen.getByRole('heading', { level: 1 }).textContent ?? '';
    expect(heading).toContain(currentCrumb());
  });
});

/**
 * 🔴 **[B-299](../../docs/BUGS.md) — one failing read removed six sections
 * whose own reads had succeeded.**
 *
 * 📁 ***"Always scoped to the smallest failing section; the rest of the record
 * stays live."*** · 📁 ***"Sections load independently — a slow enrichment
 * never delays the score or the deal."***
 *
 * ⛔ **The page was `{score ? <>…all seven sections…</> : null}`**, so a 500 on
 * `…/accounts/{id}/score` replaced *Signals timeline*, *Recent activity*,
 * *Research*, *Open opportunities* and *Competitors* with a single page-level
 * absence — **and the same gate hid them behind one skeleton while the score
 * was merely slow.**
 *
 * ⚠️ **A component test cannot see this**, which is why it is here: every
 * section renders correctly on its own, and what was wrong was the page's
 * decision about when to render them at all.
 */
describe('🔴 a failing score does not take the record with it — B-299', () => {
  it('the sections whose reads succeeded still render', () => {
    score.mockReturnValue({
      ...IDLE,
      data: undefined,
      error: new ApiError(500, {
        code: 'internal_error',
        message: 'nope',
        correlation_id: 'cid-299',
      }),
    });

    render(withQuery(<AccountBriefPage />));

    // ⚡ **Named by their design headings**, not by test ids — 📁 the rail and
    // the heading must agree, and asserting on the heading is what keeps that
    // true.
    expect(screen.getByRole('heading', { name: 'Signals timeline' })).toBeInTheDocument();
    expect(screen.getByRole('heading', { name: 'Recent activity' })).toBeInTheDocument();
    expect(screen.getByRole('heading', { name: 'Open opportunities' })).toBeInTheDocument();
  });

  it('⚡ and the failure is stated in the score\'s own box, with its reference', () => {
    score.mockReturnValue({
      ...IDLE,
      data: undefined,
      error: new ApiError(500, {
        code: 'internal_error',
        message: 'nope',
        correlation_id: 'cid-299',
      }),
    });

    render(withQuery(<AccountBriefPage />));

    // 📁 *"States what is missing versus what is still trustworthy, then retry
    // plus a correlation ID."* — ⛔ **all three clauses, and the third had
    // never been passed on this surface.**
    expect(screen.getAllByText(/could not load this account's score/i).length).toBeGreaterThan(0);
    expect(screen.getAllByText(/rest of this account's record is unaffected/i).length).toBeGreaterThan(0);
    expect(screen.getAllByText(/cid-299/).length).toBeGreaterThan(0);
  });

  it('⛔ and a SLOW score does not hide them either', () => {
    score.mockReturnValue({ ...IDLE, data: undefined, isLoading: true });

    render(withQuery(<AccountBriefPage />));

    expect(screen.getByRole('heading', { name: 'Signals timeline' })).toBeInTheDocument();
    expect(screen.getByRole('heading', { name: 'Recent activity' })).toBeInTheDocument();
  });
});
