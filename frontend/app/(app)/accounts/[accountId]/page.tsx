'use client';

import { Briefcase, Lock, Scale, SearchX } from 'lucide-react';
import Link from 'next/link';
import { usePathname, useParams, useRouter, useSearchParams } from 'next/navigation';
import { useEffect, useMemo, useRef, type ReactNode } from 'react';

import {
  ContestedMark,
  HeldSince,
  Ownership,
  ScoreMovement,
  EvidenceHealth,
  WhyNow,
} from '@/components/intelligence/attention';
import {
  ContributionList,
  PostureSplit,
  ReadingValidity,
  ScoreArithmetic,
  WhatMovedIt,
} from '@/components/intelligence/contributions';
import { usePublishBreadcrumb } from '@/components/shell/breadcrumb-trail';
import { useUtilityPanel } from '@/components/shell/utility-panel';
import { AccountSegments, membershipFor } from '@/components/accounts/account-segments';
import { AccountTags, tagsFor } from '@/components/accounts/account-tags';
import { AbsentSection, OnThisPage } from '@/components/accounts/sections';
import { ReasoningCard } from '@/components/accounts/reasoning';
import { AccountSectionShell } from '@/components/accounts/section';
import {
  contributionSeverities,
  correlationOf,
  expandedSection,
  withExpanded,
} from '@/lib/accounts/section-state';
import { ACCOUNT_SECTIONS, absent } from '@/lib/accounts/sections';
import { CompetitorContext } from '@/components/intelligence/competitors';
import { StatedAbsence } from '@/components/feedback/stated-absence';
import { SystemState } from '@/components/ui/system-state';
import { NameDispute } from '@/components/intelligence/entity-name';
import { DecisionHistory } from '@/components/intelligence/decision-history';
import { EvidenceDrawer, useEvidenceDrawer } from '@/components/intelligence/evidence';
import { Freshness } from '@/components/intelligence/freshness';
import { NarrativeBlock } from '@/components/intelligence/narration';
import { ObservationList } from '@/components/intelligence/observations';
import { WhatYouSell } from '@/components/intelligence/offering';
import { ResearchPanel } from '@/components/intelligence/research';
import { AccountSequence, nextInSequence } from '@/components/intelligence/sequence';
import { ValidationBlock } from '@/components/intelligence/validation';
import {
  ContestedSince,
  OpportunityMomentum,
  WorkflowStage,
} from '@/components/intelligence/opportunity';
import { WorkflowActions } from '@/components/intelligence/workflow';
import { colleaguesFrom, peopleFrom } from '@/components/team/people';
import { AccountHistory } from '@/components/timeline/feed';
import { NoWorkspace } from '@/components/workspace/no-workspace';
import {
  Card,
  CardBody,
  Column,
  Columns,
  EmptyState,
  RecordHeader,
  SkeletonText,
  initialsFor,
  type RecordFact,
} from '@/components/ui';
import { daysUntil, formatDay } from '@/components/intelligence/dates';
import { formatMoney } from '@/lib/accounts/table';
import { ApiError } from '@/lib/api/client';
import { useSession } from '@/lib/auth/client';
import {
  useAccounts,
  useAccountIdentities,
  useAccountNarration,
  useAccountObservations,
  useAccountOpportunity,
  useAccountResearch,
  useAccountScore,
  useAccountValidation,
  useRequestResearch,
} from '@/lib/query/hooks';
import {
  useBuyingCommittee,
  useCompetitors,
  useProductCatalog,
} from '@/lib/query/hooks/commercial';
import { useAccountTimeline } from '@/lib/query/hooks/timeline';
import {
  useAccountSegmentMemberships,
  useAccountSegments,
} from '@/lib/query/hooks/account-segments';
import {
  useAccountTagAssignments,
  useAccountTags,
} from '@/lib/query/hooks/account-tags';
import { useWorkspaceMembers } from '@/lib/query/hooks/team';
import { useAccountCommercials } from '@/lib/query/hooks/scoring';
import { scopeFrom } from '@/lib/state/owner-scope';
import { useRecordView } from '@/lib/query/hooks/recently-viewed';
import { useWorkspaceContext } from '@/lib/state/workspace-provider';
import { ReadingColumn } from '../../reading-column';

/**
 * 🔴 **Account 360's own layout, and it is the final document's** — 📁
 * `Design Documents/Fortune Signora Account 360.html`:
 *
 * ```
 * display:flex; align-items:flex-start
 * ├── 184px "On this page", position:sticky, align-self:flex-start
 * └── flex:1 min-width:0 the record
 * ```
 *
 * ⛔ **`ReadingColumn` cannot express it** — it is a single `span={8}` and the
 * design puts a second region beside it. ⚡ **So this route composes the grid
 * itself and the other eight `ReadingColumn` screens are untouched**, which is
 * the opposite of bending a shared component to suit one caller
 * ([§20c](../../../../../CLAUDE.md)).
 *
 * ⚡ **`184px`, `1fr` and `340px` are the design's own three numbers** and are
 * used as written. 📁 The rule allows a fixed dimension *"where the final
 * design explicitly defines it"* — ⛔ **and a span was tried first and measured
 * wrong**: `span={2}` is ≈173px at 1440 but **126px at 1024**, where
 * *"Contacts & decision makers"* wraps to three lines. **A nav rail's width is
 * a function of its labels, not of the viewport.**
 *
 * ⚡ **The 340px track carries what the product can actually produce.** 📁 The
 * design fills it with four cards — Risk indicators · Recommendations · AI
 * reasoning · Evidence. 🔴 **This lane previously reported that *"not one of
 * the four has a producer"* and that was WRONG**: `GET
 * …/accounts/{id}/decision-package` is routed, `useAccountDecisionPackage` is
 * shipped, and the Companies list has consumed it since it shipped. ✅ **AI
 * reasoning is built from it** ([`ReasoningCard`](../../../../components/accounts/reasoning.tsx));
 * ⛔ **Risk indicators and Recommendations genuinely have none and are absent
 * rather than faked** ([§20c](../../../../../CLAUDE.md)).
 *
 * ⚠️ **The rail appears from `laptop:` (1280) up, not from 1024.** 📁 The App
 * Shell: *"The shell yields in a fixed order as width disappears: utility panel
 * first, then the rail"*, and the design system's *"chrome yields before
 * data."* ⛔ **At 1024 the shell's own 232px rail is still open, leaving 744px
 * — a 184px page nav there costs a quarter of the record.** ⚡ **Below 1280 it
 * yields to the strip rather than vanishing**, because an anchor nav that
 * disappears takes the record's map with it.
 */
function RecordLayout({
  header,
  rail,
  aside,
  children,
}: {
  header: ReactNode;
  rail: ReactNode;
  aside: ReactNode;
  children: ReactNode;
}) {
  return (
    <Columns>
      {/* 📁 **The record header spans the content region and the rail begins
          beneath it**, which is the order the final document draws. */}
      <Column span={12}>{header}</Column>
      <Column
        span={12}
        className="flex flex-col gap-6 laptop:flex-row laptop:items-start"
      >
        {/* ⚡ **`self-start` is what makes `sticky` mean anything** — a
            stretched flex child is as tall as its row and can never scroll
            within it. ⛔ **`top-6` rather than the design's `top:0`**: that 0
            is measured inside its own scroll region, and this shell scrolls
            the document under a sticky top bar. */}
        <div className="laptop:sticky laptop:top-6 laptop:w-[184px] laptop:flex-none laptop:self-start">
          {rail}
        </div>
        {/* 📁 *"minmax(0,1fr) 340px"* — ⛔ `min-w-0` so a table shrinks the
            track instead of pushing the grid past the viewport. ⚡ **Below
            `laptop:` the aside stacks beneath the record** rather than being
            dropped: it carries the conclusion, and the design system's *"chrome
            yields before data"* protects it rather than sheds it. */}
        <div className="grid min-w-0 flex-1 gap-6 laptop:grid-cols-[minmax(0,1fr)_340px] laptop:gap-4">
          <div className="flex min-w-0 flex-col gap-6">{children}</div>
          <div className="flex min-w-0 flex-col gap-4">{aside}</div>
        </div>
      </Column>
    </Columns>
  );
}

/**
 * The account brief — *"why this account?"*
 *
 * The second question of the morning, and the one the list cannot answer. A
 * seller who has decided *which* accounts now has to decide whether they agree,
 * and then defend that to somebody else. **This page exists to be argued with.**
 *
 * ### The order the questions are answered in
 *
 * *What changed* → *how much attention* → *how long that holds* → *what to do
 * next* → *why* → *what disagrees*. A reader stops as soon as they are convinced, which is what
 * progressive disclosure means on a page rather than in a panel: **information
 * ordered so most of it is never read**, not information hidden behind a
 * control.
 *
 * ### The route is `/accounts/[accountId]`
 *
 * It was `/opportunities/[accountId]` — an *account* identifier under a
 * section named after the workflow record, which M12.2 flagged as *"the sort
 * of mismatch that costs the next engineer an hour"* and worked around by
 * naming the segment. The section is gone (**D38**), so the address can now
 * simply say what the page is about.
 *
 * ### Composed from three requests, not one aggregate
 *
 * The name comes from the Knowledge Graph, the score from the Buying Score
 * Engine, the commitment from the Opportunity Engine — no module in the
 * ratified graph reaches all three. Composing them here was the option that
 * needed no architectural change (37-product-surface.md §7).
 *
 * ### The header is §08's, and it is the approved one
 *
 * 🔴 **This screen hand-rolled its own record header for four milestones while
 * `RecordHeader` sat in the library with ZERO consumers** — 📁
 * [`components/ui/page-header.tsx`](../../../../components/ui/page-header.tsx),
 * and exactly the *"another bespoke version of an existing common component"*
 * [§20c](../../../../../CLAUDE.md) forbids.
 *
 * ⚡ **What arrived with the migration**: §08's identity tile · §04's `Title`
 * role on the name (it was `text-lg`) · the status chips beside the title
 * rather than floated opposite it · §08's *"four key facts as a quiet strip"* ·
 * the meta line beneath the actions.
 *
 * ⛔ **What left**: a *"← All accounts"* link the design does not draw. 📁 §04
 * puts **breadcrumb only** on the left, and this screen already publishes
 * *Accounts / <this company>*. **Two wayfinding controls for one journey** is
 * residue, not redundancy — and six Playwright specs were using the one the
 * design removed as their proof that the page had arrived.
 *
 * ⚠️ **The design draws six facts and two are rendered.** 📁 [ADR-0409](../../../../../docs/architecture/adr/0409-commercial-account-facts.md)
 * §5 — *"absence is never inferred, defaulted or zero-filled"*. **Total
 * contract value, Seats and Employees have no provider behind them**, so the
 * strip is short rather than dashed: 📁 [§20c](../../../../../CLAUDE.md), *an
 * absent fact beats a column of `—`*.
 *
 * ### What is deliberately not here yet
 *
 * 🔴 **CORRECTED 2026-08-20.** This paragraph said the Decision Package
 * *"stays unbuilt until `reasoning@1` holds a release"* and that ***"nothing on
 * this page hints at it."*** ⛔ **Both halves were false**, and the sentence was
 * load-bearing: it is why the design's 340px track was reported as having no
 * producer at all.
 *
 * ✅ **Measured rather than recalled**: `GET
 * …/accounts/{id}/decision-package` is routed, `useAccountDecisionPackage` is
 * a shipped hook, `DecisionPackage` is on the contract, and
 * [`expanded-row.tsx`](../../expanded-row.tsx) has consumed it on the Companies
 * list since it shipped. ⚡ **The record page was simply the surface that did
 * not** — it does now, as
 * [`ReasoningCard`](../../../../components/accounts/reasoning.tsx).
 *
 * ⛔ **What genuinely has no producer**, and is therefore absent rather than
 * faked: 📁 the design's **Risk indicators** and **Recommendations** cards —
 * nothing on the contract, no hook, no endpoint. ⚡ **The original reasoning
 * still holds for those two**: *a control that looks clickable and is not costs
 * more trust than the missing feature does, and a panel that says "coming soon"
 * costs more than both.*
 *
 * ⚠️ **Also absent: §04's seven-tab record navigation.** 📁 The final document
 * draws `Overview · Opportunities · Contacts · Conversations · Activity ·
 * Files · Settings` — **four of the seven have no producer of any kind**, and
 * building a tab bar where four destinations lead nowhere is the same
 * false-affordance class. **This needs a product decision, not an
 * implementation one** — 🔴 **and it is now
 * [C-1563](../../../../../docs/LANE_COORDINATION.md) rather than only this
 * sentence.** ⛔ **A product decision recorded in a code comment is a decision
 * nothing tracks** ([§20e](../../../../../CLAUDE.md)), **and the three tabs that
 * DO have producers — Overview, Opportunities, Activity — are already
 * destinations the rail reaches**, which is the measurement the row carries and
 * this comment did not.
 */
export default function AccountBriefPage() {
  const { accountId } = useParams<{ accountId: string }>();
  const router = useRouter();
  const pathname = usePathname();
  const searchParams = useSearchParams();
  /**
   * 🔴 **The entry engine's 403, rendered where it says to render it** —
   * [TASK-1467](../../../../../docs/BACKLOG.md).
   *
   * 📁 [`lib/entry/rules.ts`](../../../../lib/entry/rules.ts) rule 07,
   * `INTENT_FORBIDDEN`, routes to **`${intent.path}?error=403`** and its own
   * note says why: ***"the 403 page for that object… Not Home, not a silent
   * redirect."***
   *
   * ⛔ **So a 403 is not a route.** ⚡ **It is a state an object's own route
   * renders**, which is what makes it possible to say *this account* rather
   * than *something*. ⚠️ **The engine has produced this URL since it shipped
   * and nothing read the parameter** — **a person following a deep link they
   * could not open got the account screen's ordinary loading and then an
   * outage-shaped failure**, which says the product is broken rather than that
   * the door is closed.
   *
   * ✅ **This is `403`'s first caller.** 📁 The state has been legal in the
   * ladder — `page: ['404', '403', …]` — **with nothing rendering it**, the
   * same law-without-a-surface pattern this repository has now found nine
   * times.
   */
  const forbidden = useSearchParams().get('error') === '403';
  const { activeWorkspace, isLoading: workspacesLoading } = useWorkspaceContext();
  const workspaceId = activeWorkspace?.id ?? null;
  // Only so the page can say *you* rather than an identifier, and assign an
  // account to the person taking it on. Never an authorization decision —
  // Casbin on the server is that, and always.
  const { data: session } = useSession();
  const viewerId = session?.user.id ?? null;
  // ⛔ **The account TYPE is not published to this page, so nothing is
  // guessed.** 📁 `useAccounts` returns `AccountAttention` and
  // `useAccountIdentities` returns `AccountIdentity`; **neither carries
  // `kind`**, and only the Companies list's `ListedAccount` does. ⚡ **A
  // collapse preference keyed under a guessed type is one a rep cannot get
  // back**, so `null` means *persist nothing* rather than *persist wrongly* —
  // [B-261](../../../../docs/BUGS.md).
  const accountKind: string | null = null;

  /**
   * ⚡ **`refetch` is taken because 📁 System States `rules` ⑤ needs it** —
   * *"one primary action… **'Reload the page' is a last resort, never the
   * first offer**"* — and rule ② is *"work is preserved: drafts, filters,
   * selection and scroll are held through any recoverable failure."*
   * ⛔ **A page reload discards every one of those to recover one read.**
   * 📁 [B-299](../../../../docs/BUGS.md) ⑩.
   */
  const {
    data: score,
    isLoading,
    error,
    refetch: refetchScore,
  } = useAccountScore(workspaceId, accountId);

  /**
   * 📁 **Session Continuity tier 4** — *"recently viewed records"*, which is
   * what 📁 Home's `card.recents` offers back as *"pick up where you left
   * off"*.
   *
   * 🔴 **Recorded only once the account has actually resolved.** ⛔ **Writing
   * on mount would record a view of an account that 403'd, 404'd or never
   * loaded** — and the card would then invite somebody to pick up work they
   * were never shown.
   *
   * ⚡ **Fire-and-forget.** 📁 Tier 4 restores *"silent where it only informs a
   * list (recents)"* — **a person opening an account must never wait on the
   * bookkeeping that remembers they did**, and a failure here costs one row in
   * a context card rather than the navigation.
   */
  // ⚡ **`mutate` rather than the mutation object**: it is stable across
  // renders, so the effect below can depend on it honestly instead of
  // suppressing the dependency.
  const { mutate: recordView } = useRecordView(workspaceId);
  const recorded = useRef<string | null>(null);
  useEffect(() => {
    if (workspaceId === null || score === undefined) return;
    // ⛔ **Once per account per mount.** Re-running on every render would write
    // on each poll; the ref is what keeps a view a view.
    if (recorded.current === accountId) return;
    recorded.current = accountId;
    recordView({ entityId: accountId, kind: 'account' });
  }, [workspaceId, accountId, score, recordView]);
  const {
    data: opportunity,
    error: opportunityError,
    refetch: refetchOpportunity,
  } = useAccountOpportunity(workspaceId, accountId);
  // **404 is "nobody has taken this account on"; anything else is an outage.**
  // The third section on this page to need the split, after narration and
  // research. Without it the workflow controls simply vanish, and an account
  // somebody is actively working reads as one nobody has touched.
  const neverTaken =
    opportunityError instanceof ApiError && opportunityError.status === 404;
  const workflowUnavailable = opportunityError !== null && !neverTaken;
  const { data: narration, error: narrationError } = useAccountNarration(
    workspaceId,
    accountId,
  );
  // **404 is an answer here, not a failure** (B-010). Signora has written no
  // explanation for this account — which is a different sentence from *the
  // request failed*, and both used to render as the same blank space.
  const notNarrated = narrationError instanceof ApiError && narrationError.status === 404;
  const { data: validation, isError: validationFailed } = useAccountValidation(
    workspaceId,
    accountId,
  );
  const { data: research, error: researchError } = useAccountResearch(
    workspaceId,
    accountId,
  );
  // **404 is "nobody has asked yet"; anything else is an outage.** The same
  // split the narration block above makes, and for the same reason: without it
  // both render as absence, and absence here is an invitation to start a run
  // that may already exist.
  const neverResearched =
    researchError instanceof ApiError && researchError.status === 404;

  /**
   * 🔴 **Which anchored sections actually RENDER**, and this is a correction to
   * this lane's own previous change — [TASK-1476](../../../../docs/BACKLOG.md).
   *
   * ⛔ **Giving a component an `id` does not make a region appear.**
   * `CompetitorContext` returns `null` when nothing is declared, and
   * `NarrativeBlock` returns `null` while its read is in flight — ⚡ **so the
   * rail gained two entries that can point at nothing.** 📁 **That is exactly
   * the defect `OnThisPage`'s own docstring records** — *"`Account score` and
   * `Summary` were links to nowhere"* — **reintroduced by the change that
   * closed it, one section over.**
   *
   * ✅ **The rail's contract is *"the ids this page ACTUALLY renders"***, so the
   * page answers that question rather than assuming it.
   */
  const requestResearch = useRequestResearch(workspaceId, accountId);
  // Paged rather than fetched whole: an account worked for a year has a long
  // history, and the brief must not wait on all of it to render the rest.
  const timeline = useAccountTimeline(workspaceId, accountId);
  const observations = useAccountObservations(workspaceId, accountId);
  const competitors = useCompetitors(workspaceId);
  const rendersCompetitors =
    competitors.isError || (competitors.data?.competitors.length ?? 0) > 0;
  // **Workspace declarations, not account facts** — the same list on every
  // brief, which is why both read a workspace-scoped query and neither takes
  // an `accountId`. Stage 2 of [C-008](../../../../docs/LANE_COORDINATION.md).
  const catalog = useProductCatalog(workspaceId);
  const committee = useBuyingCommittee(workspaceId);

  /**
   * 🔴 **The account's history, built ONCE and placed by the shell** —
   * [TASK-1433](../../../../docs/BACKLOG.md).
   *
   * ⚡ **`useMemo` is not an optimisation here** — ⛔ **it is what stops the
   * publish effect re-running on every render**, which would republish the
   * same node into the panel forever.
   */
  const historyFeed = useMemo(
    () => (
      <AccountHistory
        entries={timeline.data?.pages.flatMap((page) => page.items) ?? []}
        hasMore={timeline.hasNextPage}
        isLoading={timeline.isLoading}
        isLoadingMore={timeline.isFetchingNextPage}
        isError={timeline.isError}
        onLoadMore={() => void timeline.fetchNextPage()}
      />
    ),
    [
      timeline.data,
      timeline.hasNextPage,
      timeline.isLoading,
      timeline.isFetchingNextPage,
      timeline.isError,
      timeline.fetchNextPage,
    ],
  );

  // 📁 **§13's Activity tab** — ⛔ the panel takes it only where the panel
  // exists; below 1024 `carrying` is false and the section above renders.
  const history = useUtilityPanel('Activity', historyFeed);
  // **The roster, so an account can be handed to a colleague.** The same query
  // the Team page holds, same cache key, so this costs no request — and
  // TM-01's `member_email` is what makes a name renderable at all.
  const { data: roster } = useWorkspaceMembers(workspaceId);
  // **One resolution of a name, read by three surfaces** — the workflow line,
  // the hand-over picker and the decision history. Three copies of *"who is
  // this identifier"* would eventually disagree, and a brief that offers
  // *ana@acme.com* in a picker and then says *"somebody here"* in the trail
  // describes two people to a reader who knows there is one.
  const people = peopleFrom(roster?.items);
  const evidence = useEvidenceDrawer();
  const {
    data: identities,
    isLoading: nameLoading,
    isSuccess: nameSettled,
  } = useAccountIdentities(workspaceId, [accountId]);
  const identity = identities?.get(accountId);

  /**
   * 🔴 **[B-1053](../../../../docs/BUGS.md) — this screen never asked whether
   * the account exists.**
   *
   * ⛔ **QE counted 20 calls to `/api/proxy/**` on this page and not one of
   * them fetched the account.** ⚡ **So `/accounts/00000000-…-000000000000`
   * returned HTTP 200 and rendered a full record**, headed
   * `00000000 — no source has named this account yet` — **a name derived from
   * the URL for a record nothing had confirmed** — with every section showing
   * its designed empty state.
   *
   * ## ✅ The oracle already existed and this page was already calling it
   *
   * 📁 **`/account-identities` says so in its own docstring**: *"An account the
   * workspace does not own is simply **absent** rather than reported, which is
   * the same reason a non-member sees 404."* ⛔ **No new endpoint, no new
   * contract, and no second read** — the identity request is the one this
   * header has always made to get the name.
   *
   * ⚠️ **`isSuccess`, not `!isLoading`.** 🔴 **A FAILED identity read must
   * never render *not found*** — 📁
   * [P-A](../../../../docs/DOMAIN_DISCOVERY_REGISTER.md): *could not find out*
   * and *is not there* are different sentences, and this is the exact
   * distinction [B-207](../../../../docs/BUGS.md)'s withdrawal established one
   * level down for the score.
   *
   * ⚡ **Cross-workspace and non-existent render identically, and that is not an
   * accident of this code** — 📁 [§7](../../../../CLAUDE.md), *404 never 403*:
   * **the endpoint omits both**, so this branch cannot tell them apart even if
   * it wanted to.
   */
  const accountAbsent = nameSettled && identities !== undefined && !identities.has(accountId);

  /**
   * 📁 **§05 — *"Mandatory below the first level, because most sessions start
   * from a deep link in Slack or email."*** 🔴 **This screen had none at all**,
   * and it is the deep-linked one: the design draws *Accounts / Enterprise /
   * Vantage Logistics* in the top bar.
   *
   * ⛔ **Two crumbs rather than the design's three.** ⚠️ **The middle one is a
   * SEGMENT** — *Enterprise* — and 📁 [C-221](../../../../docs/LANE_COORDINATION.md)'s
   * neighbouring rule applies: **nothing publishes an account's segment**, and
   * the table beside it prints *"No segment"* for every row. **A trail cannot
   * name a level the product does not hold.**
   *
   * ⚡ **The current crumb is the account's own name**, which is exactly why
   * the trail is published by the screen and never derived in the shell
   * ([D-193](../../../../docs/DECISION_REGISTER.md)) — **only this module knows
   * it.**
   *
   * ## 🔴 [B-1045](../../../../docs/BUGS.md) — this comment described a rule the
   * line below it did not carry
   *
   * ⛔ **The crumb read `identity?.name ?? 'This account'`**, and the paragraph
   * above it claimed the crumb *waited*, citing
   * [B-290](../../../../docs/BUGS.md) by name. **It did not wait.** ⚠️ **One
   * `??` collapsed the two states B-290 exists to separate** — *the read has
   * not landed* and *nobody has named this account* — **into one string that
   * asserts the second.** ⚡ **A docblock stating behaviour the adjacent
   * expression does not implement is 📁 [§2](../../../../CLAUDE.md)'s
   * Decorative Logic in prose**, and it is worse than no comment: it is what a
   * reader greps for when checking whether B-290's pattern reached this file.
   *
   * ✅ **The identifier is the honest label in BOTH unsettled states**, because
   * `09cdf253` is true of this account before the read lands and after it
   * lands empty. ⛔ **`'This account'` was true of nothing** — it names no
   * record and distinguishes no state.
   *
   * ⚡ **This is exactly what the header 190 lines down already renders**
   * (`title={identity?.name ?? accountId.slice(0, 8)}`), so the two surfaces
   * that name this record on one screen now say the same word — **which is the
   * divergence B-1045 reported.**
   *
   * ⚠️ **A crumb cannot carry `EntityName`'s stated absence.** 📁
   * `Crumb.label` is a `string` ([`lib/shell/breadcrumb.ts`](../../../../lib/shell/breadcrumb.ts)),
   * so *"— no source has named this account yet"* — an `sr-only` span — has
   * **no** representation here without changing a shell primitive. ⛔ **Not
   * changed inside a defect fix**: the identifier is the honest visible label,
   * and the sentence stays where a reader can reach it, on the header.
   */
  usePublishBreadcrumb([
    { label: 'Accounts', kind: 'link', href: '/accounts' },
    { label: identity?.name ?? accountId.slice(0, 8), kind: 'current' },
  ]);
  // **The same query the attention page holds**, same cache key, so this costs
  // no request — the brief reads the ranked order rather than fetching it, and
  // *next* therefore means *next most pressing* (D41).
  // **The same scope the list was showing**, carried on the link that got
  // here. Without it a seller working their own accounts would be offered
  // somebody else's next — one definition of *next*, and it has to be the one
  // they were walking (D41).
  const scope = scopeFrom(useSearchParams().get('owner'));
  const { data: list } = useAccounts(workspaceId, scope);
  const ranked = list?.items ?? [];
  const { data: rankedIdentities } = useAccountIdentities(
    workspaceId,
    ranked.map((account) => account.account_id),
  );

  const notScored = error instanceof ApiError && error.status === 404;

  /**
   * 🔴 **§08's *"four key facts as a quiet strip"*, and only the ones a
   * provider actually supplied** — the same read the Companies table's `acv`
   * and `renewal` columns make, so one company reads identically in the list
   * and on its own page.
   *
   * ⛔ **A fact nobody has stated is ABSENT, never `—`.** 📁 [ADR-0409](../../../../../docs/architecture/adr/0409-commercial-account-facts.md)
   * §5: *"absence is never inferred, defaulted or zero-filled"*, and **a zero
   * ACV is a figure a seller would act on.** ⚠️ The table prints a dash because
   * a grid must keep its columns aligned; **a header strip has no such
   * obligation**, so it simply says less.
   */
  const commercials = useAccountCommercials(workspaceId, [accountId]);
  /**
   * 🔴 **📁 §08's `headerTags`** — the design draws neutral chips beside the
   * title: *Enterprise · EMEA · Denmark · Logistics · Strategic*.
   *
   * ⚡ **The SEGMENT is the one with a producer**, and it was rendering on the
   * Companies list and the context drawer **and nowhere on the record it is
   * about.** ⛔ **Region, industry and tier are firmographics nothing
   * publishes**, so the strip carries what the product knows and states the
   * rest by absence rather than by a placeholder.
   *
   * ⚡ **Same two reads the list already holds**, same cache keys, so opening a
   * record costs no request the list did not already make.
   */
  const segmentMemberships = useAccountSegmentMemberships(workspaceId, [accountId]);
  const segments = useAccountSegments(workspaceId);
  /**
   * 🔴 **📁 §08's `headerTags` draws FOUR chips and this header rendered
   * ONE** — [B-299](../../../../docs/BUGS.md) ⑧.
   *
   * 📁 `['Enterprise', 'EMEA · Denmark', 'Logistics', 'Strategic']` — **a
   * segment, a region, an industry and a customer label.** ⚡ **The customer
   * label is the one with a complete producer**: `useAccountTags` and
   * `useAccountTagAssignments` ship, `AccountTags` ships, **and the Companies
   * list and the context drawer have both consumed them since they landed.**
   * ⛔ **The record page was the only surface that did not** — 📁 the
   * [shipped-backend-with-no-consumer](../../../../../docs/LANE_COORDINATION.md)
   * shape, except the consumer existed and this screen never called it.
   *
   * ⚠️ **The other two are [C-1564](../../../../../docs/LANE_COORDINATION.md)**:
   * `AccountAttributes` publishes `industry` and `country` as a module port
   * with **no HTTP surface at all**, so they are absent for want of a route
   * rather than for want of data.
   *
   * ⚡ **Two reads and no new contract** — the same pair the list already
   * makes, with a one-element list, so the hook's *"disabled on an empty
   * list"* rule holds unchanged.
   */
  const tagVocabulary = useAccountTags(workspaceId);
  const tagAssignments = useAccountTagAssignments(workspaceId, [accountId]);
  const commercial = commercials.data?.get(accountId);
  const facts: RecordFact[] = [];
  if (commercial?.open_acv) {
    facts.push({ label: 'Open ACV', value: formatMoney(commercial.open_acv) });
  }
  if (commercial?.renewal_date) {
    // 📁 **§08 draws the distance beside the date** — *"12 Oct 2026 · 69 days"*.
    // ⚡ **Derived from the date already published**, so no producer is invented.
    // ⛔ **Neutral tone**: the design colours this `warn`, which implies a
    // threshold at which a renewal becomes urgent, and the product defines none.
    const until = daysUntil(commercial.renewal_date);
    facts.push({
      label: 'Renewal',
      value: formatDay(commercial.renewal_date),
      ...(until === null ? {} : { delta: until }),
    });
  }

  // **Where the morning continues, offered at the moment a decision is made**
  // (R10-02). The same ranking the sequence at the foot of the page uses, and
  // the same rule — one definition of *next*, or a reader could be offered two
  // different ones in a single visit.
  const upNext = nextInSequence(ranked, accountId);
  const upNextName = upNext ? rankedIdentities?.get(upNext.account_id)?.name : undefined;

  /**
   * ⛔ **After every hook, never before one** — React's rules, and the reason
   * the read of `?error=403` sits at the top while the branch sits here.
   *
   * ✅ **The refusal replaces the brief rather than sitting inside it.** ⚡ **A
   * banner above the account's data would be a refusal the reader can scroll
   * past** — and 📁 [§20c](../../../../../CLAUDE.md) is explicit that a
   * client-side check is *"a courtesy, never enforcement"*: **Casbin already
   * refused the request, so there is no data here to protect.** ⛔ **What this
   * screen protects is the reader's understanding**, which a half-rendered
   * page destroys.
   */
  /**
   * ⛔ **Before the record header, and that ordering is the fix** — 📁
   * [B-1053](../../../../docs/BUGS.md): *"the screen establishes existence
   * before rendering a record header; never derives a display name from the URL
   * for a record it has not confirmed."*
   *
   * ⚡ **The voice is the product's own 404**, from 📁 `app/not-found.tsx` —
   * ⛔ **not a fifth wording of *nothing here***, and the `SystemState` ladder
   * is what renders it, the same way every other page-level state does.
   *
   * ✅ **Nothing about the score's behaviour moves.** 📁
   * [B-207](../../../../docs/BUGS.md)'s withdrawal vindicated *"a 404 from the
   * score read renders **Nothing has scored this account yet**"* — **that is a
   * statement about an account that EXISTS**, and this branch is reached before
   * the score is ever consulted.
   */
  if (accountAbsent) {
    return (
      <ReadingColumn>
        <SystemState
          scope="page"
          state="404"
          glyph={SearchX}
          title="That company is not here"
          // ⛔ **It asserts no cause.** ⚠️ **`/account-identities` omits an
          // account the workspace does not own for the SAME reason it omits one
          // that does not exist** — 📁 [§7](../../../../CLAUDE.md) — so naming
          // either would be inventing the one thing this screen cannot know.
          // ✅ **And it says what survived**, which is 📁 `3.3.1`'s fourth
          // clause and the sentence `not-found.tsx` already ends on.
          description="Nothing in your organization sits at this link. It may have been removed, or it may never have existed — either way, nothing about your other companies has changed."
          primaryAction={
            <Link
              href="/accounts"
              className="rounded text-sm font-medium text-accent underline decoration-border underline-offset-4 transition-colors hover:decoration-accent "
            >
              Back to the companies you can see
            </Link>
          }
        />
      </ReadingColumn>
    );
  }

  if (forbidden) {
    return (
      <ReadingColumn>
        <SystemState
          scope="page"
          state="403"
          glyph={Lock}
          // 📁 **Named as *this account*, which is the whole reason the engine
          // routes to the object rather than to a shared `/403`.**
          title="You do not have access to this account"
          // ⛔ **It names who can grant it rather than only refusing.** 📁 The
          // rail's own rule: *"a person who is only refused asks for the wrong
          // thing or asks nobody."*
          description="This account is in your organization, and your role does not include it. An owner or an admin can give you access."
          primaryAction={
            <Link
              href="/accounts"
              className="rounded text-sm font-medium text-accent underline decoration-border underline-offset-4 transition-colors hover:decoration-accent "
            >
              Back to the accounts you can see
            </Link>
          }
        />
      </ReadingColumn>
    );
  }

  return (
    <RecordLayout
      header={
        <>
          {/* 🔴 **§08's record header, and it is the APPROVED one** —
              `RecordHeader` in [`components/ui/page-header.tsx`](../../../../components/ui/page-header.tsx).
              ⛔ **This screen hand-rolled its own for four milestones while the
              shared component had ZERO consumers**, which is precisely the
            *"another bespoke version of an existing common component"* §20c
              forbids.

              📁 **§04 draws, in order**: the identity tile · the name at `Title`
              · the status chips beside it · the facts strip · the actions · the
              meta line beneath them.

              ⛔ **The design's six facts are NOT all rendered, and that is
              deliberate.** 📁 [ADR-0409](../../../../../docs/architecture/adr/0409-commercial-account-facts.md)
              — *"absence is never inferred, defaulted or zero-filled"* — and
              [§20c](../../../../../CLAUDE.md): **an absent fact is better than a
              column of `—`.**

              🔴 **This note said *"Total contract value, Seats and Employees
              have no provider behind them"*, and it was wrong twice** —
              [B-299](../../../../docs/BUGS.md) ⑧. ⛔ **It named five of the
              design's six**, omitting *Last touch* entirely, **and it was
              false about *Employees*.**

              | 📁 §08 fact | producer | here |
              |---|---|---|
              | **Open ACV** | ✅ `AccountCommercial.open_acv` | ✅ |
              | **Renewal** | ✅ `AccountCommercial.renewal_date` | ✅ |
              | **Total contract value** | ⛔ no contract lifecycle | ⛔ |
              | **Seats** | ⛔ no product-usage telemetry | ⛔ |
              | **Last touch** | ⛔ **nothing records a contact.** ⚠️ `/approach`
                is *who to approach and why*, a recommendation — **not a record
                of who was** | ⛔ |
              | **Employees** | 🔴 **`AccountAttributes.employee_count` IS
                published as a module port**, and the Playground holds it per
                account and named — *Larkspur Media Cloud 75*, *Brightmoor
                Industrial 12,000*. ⛔ **It has no HTTP surface**, which is
                [C-1564](../../../../../docs/LANE_COORDINATION.md) | ⛔ |

              ⚡ **The distinction the old note collapsed**: *no provider* and
              *no route to the provider* are different findings with different
              owners, **and only the second is buildable.** ⛔ **Nothing is
              rendered for either** — the fix is the truth of the note, not a
              new fact. */}
          <RecordHeader
            // 📁 §08's 46px tile. ⚡ **Derived from the name Signora already
            // holds**, by the library's own helper — ⛔ never a fabricated logo.
            {...(identity?.name ? { initials: initialsFor(identity.name) } : {})}
            // ⛔ **The identifier, never a placeholder** — the same fallback
            // `EntityName` uses everywhere else. **Being told the truth badly
            // beats being told a fiction well.**
            title={identity?.name ?? accountId.slice(0, 8)}
            // ⚡ **B-313's level-1 heading survives the wait.** `RecordHeader`
            // keeps the `<h1>` and skeletons only its text, so every `<h2>` below
            // has a parent from the first paint.
            titleLoading={nameLoading && identity === undefined}
            status={
              <>
                {/* ⚡ **Where §04 puts the chips.** ⛔ Both are silent on the
                    ordinary case — a mark on every record is a mark nobody
                    reads. */}
                {identity ? <NameDispute identity={identity} /> : null}
                {score ? <ContestedMark contested={score.contested} /> : null}
                {/* 📁 **§08's `headerTags`, in the design's position** — after
                    the marks, on the title's line. ⛔ **`AccountSegments`
                    already renders the design's neutral chip**, so this is the
                    shared component rather than a header-local one, and it
                    brings its own *"no segment"* statement with it. */}
                <AccountSegments
                  membership={membershipFor(
                    accountId,
                    segmentMemberships.data?.memberships,
                  )}
                  segments={segments.data?.segments ?? []}
                />
                {/* 📁 **§08's customer label** — *"Strategic"* in the design's
                    own row. ⛔ **`AccountTags` renders NOTHING when an account
                    has none** — its own law: *"the truth is that the customer
                    has not labelled this account, which is a fact about them
                    rather than about Signora, and a placeholder would make it
                    look like a gap the product should fill."* ✅ **So no
                    absence statement belongs here**, unlike a section. */}
                <AccountTags
                  tags={tagsFor(
                    accountId,
                    tagAssignments.data?.assignments,
                    tagVocabulary.data?.tags,
                  )}
                />
              </>
            }
            facts={facts}
            {...(opportunity
              ? {
                  secondaryActions: (
                    <WorkflowActions
                      colleagues={colleaguesFrom(roster?.items, viewerId)}
                      opportunity={opportunity}
                      workspaceId={workspaceId}
                      viewerId={viewerId}
                      // **Named or not offered.** A row whose name has not
                      // resolved would read as *"Next: "* — the sequence below has
                      // the same rule, and an offer that cannot say where it goes
                      // is the affordance this surface refuses everywhere else.
                      {...(upNext && upNextName
                        ? {
                            next: {
                              name: upNextName,
                              go: () => router.push(`/accounts/${upNext.account_id}`),
                            },
                          }
                        : {})}
                    />
                  ),
                }
              : {})}
            meta={
              <>
                {/* **Directly under the actions, because it qualifies the whole
                    page** rather than any one card. Everything below — the score,
                    its contributions, the narration, the validations — is built on
                    evidence, and a reader who does not know how old that evidence
                    is cannot calibrate any of it.

                  **Only once the identity has actually arrived.** Absent means
                  *we do not know yet, or the request failed*; rendering "No
                    evidence collected yet" for either would state something false
                    about the account. */}
                {identity ? <Freshness observedAt={identity.last_observed_at} /> : null}
                {/* **Said, rather than omitted.** The controls must not render —
                    nobody should act on state Signora could not read — but a
                    silent gap tells a seller this account is untouched, which is a
                    claim about their pipeline rather than about our request. */}
                {workflowUnavailable ? (
                  <StatedAbsence
                    subject="where this account stands"
                    reassurance="Nothing has changed about the account"
                    onRetry={() => void refetchOpportunity()}
                  />
                ) : null}
                {/* The workflow line rides with the meta rather than in the score
                    card: it is about the *account*, not about the number, and a
                    seller reads it once on arrival and never again. */}
                {opportunity ? (
                  <WorkflowStage
                    opportunity={opportunity}
                    viewerId={viewerId}
                    people={people}
                  />
                ) : null}
              </>
            }
          />
        </>
      }
      aside={<ReasoningCard accountId={accountId} workspaceId={workspaceId} />}
      rail={
        /**
         * 🔴 **The rail was gated on the score too** —
         * [B-299](../../../../docs/BUGS.md) ③, one level up from the sections.
         *
         * ⛔ **A failing score read removed the map as well as the record**, so
         * a reader could neither see the sections that had answered nor learn
         * that they existed. 📁 *"Always scoped to the smallest failing
         * section; the rest of the record stays live."*
         *
         * ⚡ **`notScored` still removes it, and correctly**: that is the whole
         * page saying this account has never been scored, and there are no
         * sections beneath it to map.
         */
        !notScored ? (
          <OnThisPage
            // 🔴 **📁 The design gives every rail entry a count and this rail
            //    dropped them all** — `pageNav` carries `['Signals timeline',
            //    '#signals', '6']` and each `<a>` renders `{{ p.count }}` at
            //    `margin-left:auto`.
            //
            // ⚡ **Every figure here is already computed on this page** — the
            //    same ones `AccountSectionShell` puts in each section header —
            //    so nothing is derived and nothing is fetched twice.
            // ⛔ **A section whose read has not answered contributes NO key**,
            //    so the rail shows no number rather than a zero: 📁
            //    [B-1054](../../../../docs/BUGS.md), *a count is a
            //    measurement*, and the sections nothing can fill have measured
            //    nothing.
            counts={{
              ...(score?.contributions === undefined
                ? {}
                : { score: score.contributions.length }),
              ...(observations.data === undefined
                ? {}
                : { signals: observations.data.length }),
              ...(rendersCompetitors && competitors.data !== undefined
                ? { compete: competitors.data.competitors.length }
                : {}),
              ...(opportunity === undefined ? {} : { opps: 1 }),
            }}
            /**
             * ⚡ **What this page actually renders, in the design's order.**
             *
             * 🔴 **The absent half is DERIVED — [B-299](../../../../docs/BUGS.md) ⑥.**
             * ⛔ **It was a hand-written list, and it went stale the moment
             * `sections.ts` gained the design's *Emails · Files · Notes ·
             * Tasks · Custom fields · History*** — **six sections that render
             * unconditionally from `absent()` twelve hundred lines below, and
             * that the rail could not reach.**
             *
             * ⚠️ **Which is the failure this rail's own docstring is about**,
             * pointed the other way: *"the section existing and the anchor
             * not."* ✅ **One source now**: whatever `absent()` renders is
             * whatever the rail names, and a seventh absent section cannot
             * arrive unanchored.
             *
             * ⚡ **The supplied ones stay listed, because they are the ones
             * that are CONDITIONAL** — `compete` on a declaration existing,
             * `activity` on the utility panel not carrying it — **and a
             * condition is exactly what a derivation cannot see.**
             */
            anchored={[
              // ⚡ **`summary` is unconditional.** 📁 *"Header, title and counts
              // paint from cache; only the body skeletons"* — **the section
              // renders in all four of its states**, so the rail entry is
              // stable and nothing below it moves when the read lands.
              'summary',
              'score',
              'signals',
              // ⚡ **`research` is unconditional** — `ResearchPanel` always
              // renders its section, because the invitation to start research
              // is itself the content when there is none.
              'research',
              // ⚡ **Unconditional, because `AccountSectionShell` renders in
              // all of its states** — loading, empty, error and populated — so
              // the entry never points at something that is not there.
              'opps',
              ...(rendersCompetitors ? ['compete'] : []),
              ...(history.carrying ? [] : ['activity']),
              // ⛔ **Every section nothing can fill, without exception** — the
              // page renders all of them and the rail names all of them.
              ...absent().map((section) => section.id),
            ]}
            className="phone:flex-row phone:flex-wrap phone:items-center phone:gap-1"
          />
        ) : null
      }
    >
      {/* Same as the list: with no workspace every query is disabled and
          nothing rendered. Reachable directly by URL, so it needs its own
          answer rather than relying on the list to have given one (D36). */}
      {!workspacesLoading && workspaceId === null ? <NoWorkspace /> : null}
      {/* ⚡ **404 is the one answer that IS the whole page** — the account has
          never been scored, and it is deliberately what a caller sees for an
          account in another workspace. ⛔ **Every other score outcome is one
          section's**, and the block below is where that became true. */}
      {notScored ? <NeverScored /> : null}

      {/* 📁 **The design's *"On this page"* rail** —
          [TASK-1415](../../../../docs/BACKLOG.md). ⚡ **Horizontal here rather
          than a right-hand column**, because the right-hand column on this
          screen is the utility panel ([TASK-1433](../../../../docs/BACKLOG.md))
          and two rails competing for one edge is a layout that serves neither.
          ⛔ **It lists every section, including the seven nothing can fill** —
          a map that hides the empty rooms is one nobody can trust. */}

      {/**
        * 🔴 **[B-299](../../../../docs/BUGS.md) — the score read gated the
        * whole record, and the design says the opposite twice.**
        *
        * 📁 ***"Always scoped to the smallest failing section; the rest of the
        * record stays live."*** · 📁 ***"Sections load independently — a slow
        * enrichment never delays the score or the deal."***
        *
        * ⛔ **`{score ? …}` wrapped all seven sections**, so one endpoint
        * failing removed *Signals timeline*, *Recent activity*, *Research*,
        * *Competitors* and *Open opportunities* — **five sections whose own
        * reads had SUCCEEDED** — and replaced the page with a single
        * `StatedAbsence as="page"`. ⚠️ **Slow rather than failing, the same
        * gate hid them behind one page-level skeleton**, while every section
        * already owns the skeleton the design asks for.
        *
        * ⚡ **`lib/system-states/ladder.ts` had already refused this in its own
        * vocabulary**: a primary read failing is a `region-error`, and
        * `region-error` at page scope is not a legal pairing. **The structure
        * was making the pairing the ladder forbids.**
        *
        * ✅ **So the three score outcomes scope to the score's own box, and
        * everything below it renders on its own read.**
        */}
      {notScored ? null : (
        <>
          {isLoading ? (
            <Loading />
          ) : error ? (
            <ScoreUnavailable
              onRetry={() => void refetchScore()}
              {...(correlationOf(error) === undefined
                ? {}
                : { correlationId: correlationOf(error)! })}
            />
          ) : score ? (
          <Card>
            <CardBody className="flex flex-col gap-4">
              <div className="flex flex-wrap items-end justify-between gap-4">
                <ScoreArithmetic score={score} />
                <WhyNow trigger={score.trigger} />
              </div>

              {/* **What changed**, given the same weight as the number itself.
                  A score is a position; the movement since somebody committed
                  is the story, and it is the one figure no other screen has.

                **The evidence badge sits beside it, and it is the list's own
                  component** (R1-04). The list showed *Cooling* on two accounts
                  and the brief never said the word — it rendered `is_current`,
                  which is true of a different fact, so the two screens
                  disagreed about the same account and no reader would ever
                  reconstruct why. *"The list flagged it, the detail page
                  didn't, so I assumed the list was noisy."*

                  Rendering the same component rather than a second phrasing is
                  the point: two wordings for one fact is how a customer catches
                  a product contradicting itself, and this one already had. It
                  says nothing when the evidence is current — *"everything is
                  fine"* is noise that trains people to stop reading badges. */}
              {opportunity ? (
                <div className="flex flex-wrap items-center justify-between gap-x-4 gap-y-2 border-t border-border pt-3">
                  <OpportunityMomentum opportunity={opportunity} />
                  {/* **Only when something else is not already saying it.**
                      `is_current: false` implies `evidence: 'stale'` — the
                      same derivation, one from the score and one from the
                      opportunity — so on an expired account the badge and
                      `ReadingValidity` three lines below stated one fact
                      twice, and the sentence states it better: it names the
                      date and explains the reading is shown as it stood.

                      What the badge alone can say is **cooling**, which no
                      other element on this page knows. Restricting it to that
                      is the rule the component already applies to `current`
                      — *"everything is fine" is noise that trains people to
                      stop reading badges*. */}
                  {score.is_current ? (
                    <EvidenceHealth evidence={opportunity.evidence} />
                  ) : null}
                </div>
              ) : null}

              <ReadingValidity score={score} />
              <PostureSplit score={score} />
            </CardBody>
          </Card>
          ) : null}

          {/* **Prose after the number, never before it.** Deterministic truth
              outranks generated language: a reader meets the score and its
              arithmetic first, and the narration is the bridge between them.
              Rendered only when one exists — absence shows nothing at all,
              because a panel announcing a gap is worse than the gap. */}
          <NarrativeBlock
            id="summary"
            narration={narration}
            notNarrated={notNarrated}
            isError={narrationError !== null && !notNarrated}
            {...(correlationOf(narrationError) === undefined
              ? {}
              : { correlationId: correlationOf(narrationError)! })}
          />

          {/* ⛔ **`score?.` throughout below this line.** ⚡ The score is now one
              section's read among several, so everything that cites it says so
              — **and a citation of a fact nobody obtained renders nothing,
              never a default.** */}
          {score?.contested ? <ContestedNote /> : null}
          {opportunity && score ? (
            <ContestedSince opportunity={opportunity} contestedNow={score.contested} />
          ) : null}

          {/* **Action before evidence.** A reader who is already convinced
              gets what to do next without scrolling past the arithmetic; one
              who is not continues to the ledger below. That is what
              progressive disclosure means on a page — information ordered so
              most of it is never read.

            **Rendered whatever the answer is** (R2-03). *"Nothing is
              currently held about this account"* is actionable on a page whose
              subject is an open commitment, and a failed request is a third
              thing again — the section used to render all three as absence,
              which made an outage indistinguishable from a quiet account.

              `evidence` comes from the opportunity because that is what the
              reading is held up *against*: an account nobody has taken on has
              no such state, and the block is built to say less when so. */}
          <ValidationBlock
            validation={validation}
            evidence={opportunity?.evidence}
            isError={validationFailed}
            onOpenEvidence={evidence.open}
          />

          {/* **Below the deterministic page, and above the ledger it cites.**
              Research is the only thing here a person starts, and it is the
              only thing that costs anything — so it sits after everything the
              pipeline already knew, where a reader arrives having seen what
              they get for free. The ledger stays last because research's own
              findings point down into it. */}
          <ResearchPanel
            id="research"
            research={research ?? null}
            isError={researchError !== null && !neverResearched}
            {...(correlationOf(researchError) === undefined
              ? {}
              : { correlationId: correlationOf(researchError)! })}
            onRequest={() => requestResearch.mutate()}
            isRequesting={requestResearch.isPending}
            viewerId={viewerId}
            kind={accountKind}
            /* 📁 The design: *"keeps the URL so the expanded view is
               shareable."* ⚡ **`withExpanded` and `expandedSection` were built
               with the section law and had NO caller** — this is the first. */
            isExpanded={expandedSection(searchParams, ACCOUNT_SECTIONS) === 'research'}
            onToggleExpanded={(next) => {
              const query = withExpanded(
                new URLSearchParams(searchParams.toString()),
                next ? 'research' : null,
              ).toString();
              router.replace(query === '' ? pathname : `${pathname}?${query}`, {
                scroll: false,
              });
            }}
            /* ⚠️ **`!score`, not `score === null`.** ⛔ `useQuery` publishes
               `undefined` before it publishes anything, **so `=== null` was
               never true** — harmless while this whole block was gated on
               `score`, and wrong the moment it was not. 📁 The absence
               [collapsed into a value](../../../../docs/BUGS.md) again, in a
               comparison that had had no reachable false case. */
            {...(!score
              ? {}
              : {
                  // 📁 The design's *"Open all evidence"*. ⚡ **It opens the
                  // drawer this page already owns** — ⛔ not a second evidence
                  // surface, and absent entirely when there is no ledger line
                  // to open, rather than rendered inert.
                  onOpenEvidence: () => {
                    const first = score.contributions[0];
                    if (first !== undefined) evidence.open(first.business_event_id);
                  },
                })}
          />

          {/* ⚡ **`id="opps"`, which is 📁 the design's own `pageNav` href** —
              [TASK-1483](../../../../docs/BACKLOG.md), [B-299](../../../../docs/BUGS.md) ④.
              📁 `lib/accounts/sections.ts` has marked this section `supplied`
              since [TASK-1476](../../../../docs/BACKLOG.md), and *On this page*
              has linked to it — ⛔ **at nothing.** 🔴 **The anchor existed and
              the section did not**, so a rep clicking *Open opportunities*
              landed wherever the browser gave up.

              ✅ **PRESENTATION ONLY.** ⚡ **`useAccountOpportunity` was already
              imported, already called, and its data already rendered twice
              further down** — so this adds no contract, no endpoint, no read
              and no seed. **It gives the page's own data the section the design
              draws for it.**

              ⛔ **Not the deal record** — 📁 [TASK-1469](../../../../docs/BACKLOG.md)
              is a different screen and is `SEQUENCED` on a `Deals` route that
              does not exist. */}
          <AccountSectionShell
            id="opps"
            heading="Open opportunities"
            // ⛔ **No severity.** ⚡ **An opportunity's stage is not a
            // judgement about the account** — the header folds severities into
            // a summary mark, and inventing one here would put a verdict on a
            // section whose whole content is *where this stands*.
            severities={[]}
            // 🔴 **[B-299](../../../../docs/BUGS.md) — this section read `0`
            // above an opportunity it was displaying.** ⛔ **The count came
            // from `severities`, and this section passes none on purpose**, so
            // *"I make no judgement about these items"* rendered as *"I have no
            // items."*
            // ⚠️ **`null` while the read is in flight and when it failed** — 📁
            // [P-A](../../../../docs/DOMAIN_DISCOVERY_REGISTER.md): a pending or
            // failed read must never publish a measurement.
            count={isLoading || workflowUnavailable ? null : opportunity ? 1 : 0}
            viewerId={viewerId}
            kind={accountKind}
            isLoading={isLoading}
            // ⛔ **The read failing is not the same as nobody working the
            // account**, and the body below has always drawn the split — 📁 the
            // header had not.
            isError={workflowUnavailable}
          >
            {workflowUnavailable ? (
              /* 🔴 **[P-A](../../../../docs/DOMAIN_DISCOVERY_REGISTER.md): a
                 failed read must never render as an empty result.** ⛔ **On
                 this section the empty result reads *nobody is working this
                 account*, which is a statement about the team rather than
                 about the request.**

                 ✅ **`workflowUnavailable` is REUSED rather than a second
                 split** — 📁 it already exists above for exactly this, and a
                 parallel `neverQualified` would have been two answers to one
                 question ([§2](../../../../CLAUDE.md)). */
              <StatedAbsence
                as="card"
                icon={Briefcase}
                subject="this account's opportunity"
                onRetry={() => void refetchOpportunity()}
              />
            ) : opportunity ? (
              <Card>
                <CardBody className="flex flex-wrap items-center gap-x-4 gap-y-2 py-3">
                  <HeldSince stage={opportunity.stage} since={opportunity.opened_at} />
                  <Ownership
                    ownerId={opportunity.owner_id}
                    stage={opportunity.stage}
                    viewerId={viewerId}
                  />
                  {/* ⚠️ **`AccountOpportunity` carries `score_change_since_open`
                      and NO `trend`** — measured, not assumed. ⛔ **So the
                      direction is passed as `null` rather than derived from the
                      sign of the change**: the contract that owns trend is
                      `AccountAttention`'s, and computing one here would be a
                      second author for a field this module does not own
                      ([§2](../../../../CLAUDE.md)). */}
                  <ScoreMovement
                    trend={null}
                    change={opportunity.score_change_since_open}
                  />
                  <ContestedMark contested={opportunity.contested_at_open} />
                </CardBody>
              </Card>
            ) : (
              /* ⚠️ **Empty is *nobody has taken this on*, and it is a real
                 answer rather than a gap.** ⛔ **Distinct from the error above,
                 which is the request failing** — 📁 the 404/outage split this
                 page already draws for narration and research. */
              <EmptyState
                icon={Briefcase}
                title="Nobody is working this account yet"
                description="An opportunity opens when somebody qualifies this account. Until then there is nothing here to track."
              />
            )}

            {/* 🔴 **The tenth invented section on this surface, and the last.**
                ⛔ **This rendered as a PEER of the design's sections, under its
                own `<h2>What has been decided</h2>` — a heading that appears
                ZERO times across the 35-document snapshot**, and a section the
                design does not draw at all.

                ⚠️ **The comment that stood here argued for the placement** —
                *"where the page turns from Signora's argument to the record of
                what people did with it"* — **which is a product decision this
                lane made and the design did not.** 📁 **The design's Account
                360 draws twenty-two sections and none of them is a decision
                history.**

                ✅ **Not deleted, because it is not obsolete, duplicated or
                superseded** ([CLAUDE.md](../../../../CLAUDE.md)). **`Recent
                activity` is fed by `useAccountTimeline` and this by
                `opportunity.history` — two producers, two datasets — so
                removing it would drop producer-backed information a customer
                can read today and nothing else carries.**

                ⚡ **So it moves to where it is already true: detail OF the
                opportunity, inside the design's `Open opportunities` card,
                rather than a page-level section competing with them.** ⛔ **And
                it carries no heading of its own — the design gives this content
                no name, so inventing a quieter one would be the same defect in
                a smaller font.** */}
            {opportunity ? (
              <DecisionHistory
                opportunity={opportunity}
                viewerId={viewerId}
                people={people}
              />
            ) : null}
          </AccountSectionShell>

          {/* ⚡ **`id="score"`** — the design calls this section *Account
              score*, and the rail links to it by that id. */}
          {/* 🔴 **The heading is the DESIGN's, and this one was invented.**
              📁 `Design Documents/Fortune Signora Account 360.html` titles the
              `#score` card ***"Account score"***, which is also what
              [`sections.ts`](../../../../lib/accounts/sections.ts) already
              calls it in the rail. ⛔ **The section heading read *"What
              contributed"***, a phrase that appears **ZERO times in the whole
              final design corpus** — measured across all 17 documents — **so
              the rail and the heading named the same section two different
              things.** ⚡ **Aligning the heading to the rail closes both at
              once.** */}
          <AccountSectionShell
            id="score"
            heading="Account score"
            // ⚡ **A contribution's own direction is its severity** — ⛔ nothing
            // is invented: the ledger already says whether a contribution
            // pushed the score up or down, and the header folds those.
            severities={contributionSeverities(score?.contributions)}
            count={score?.contributions?.length ?? null}
            viewerId={viewerId}
            kind={accountKind}
            isLoading={isLoading}
            // ⛔ **The section that reads the score says so when the read
            // failed** — 📁 *"always scoped to the smallest failing section"*,
            // and this is the smallest one for THIS read.
            isError={error !== null && !notScored}
          >
            {/* ⚡ **The ledger needs the score, so it renders only with one.**
                ⛔ **The shell above already draws the loading and the failed
                header**; ✅ **this is the body's half of the same answer, and
                it states the failure rather than leaving an empty box** —
                📁 [P-A](../../../../docs/DOMAIN_DISCOVERY_REGISTER.md). */}
            {score === undefined ? (
              error !== null && !notScored ? (
                <StatedAbsence
                  as="card"
                  subject="what contributed to this score"
                  reassurance="The rest of this account's record is unaffected"
                  onRetry={() => void refetchScore()}
                  {...(correlationOf(error) === undefined
                    ? {}
                    : { correlationId: correlationOf(error)! })}
                />
              ) : null
            ) : (
            <Card>
              <CardBody className="flex flex-col gap-3 py-3">
                {/* 🔴 **📁 The design draws ONE `#score` card and this page
                    draws TWO blocks, one of them unanchored.**

                    📁 `Design Documents/Fortune Signora Account 360.html`, the
                    `#score` card, in order: **`Account score` · an `AI` badge ·
                    the figure at 36px/700 · `/ 100` · the change chip · the
                    trend · the contributions.** ⛔ **Here the figure and its
                    validity sit in a card ABOVE the summary with no `id` at
                    all, and the contributions sit in `#score`** — so the rail's
                    *Account score* entry lands on half of the thing it names,
                    and the half a reader looks for first is the half it skips.

                    ⚠️ **CORRECTED — an earlier note here said the figure
                    *"rendered nowhere"*.** ⛔ **It renders; the probe that said
                    otherwise was scoped to `#score`** — 📁 the
                    truncation-that-reads-as-a-result failure this lane has met
                    five times now. ✅ **The real finding is the split, not an
                    absence**, and the fix is consolidation rather than another
                    figure. **Recorded as [C-1542](../../../../docs/LANE_COORDINATION.md)
                    with the two producer-backed blocks the design's card has no
                    place for** — `PostureSplit` and `WhyNow` — **because
                    consolidating without deciding those would delete them.** */}
                <ContributionList score={score} onOpenEvidence={evidence.open} />
                {/* 🔴 **📁 *"What moved it"* — Opportunity Intelligence's
                    waterfall, and it rendered NOWHERE in the product.**
                    ⚡ **Every field it needs is already on this page**:
                    `score.contributions` carries `reason`, `points` and
                    `posture`, and the design's `left`/`width` are the running
                    total rather than authored numbers.
                    ⛔ **Here rather than at a new route**: 📁
                    [D38](../../../../../docs/architecture/39-product-review-findings.md)
                    removed *Opportunities* from navigation from first
                    principles, and **a route is how that gets reversed by
                    accident** ([TASK-441](../../../../../docs/BACKLOG.md)).
                    ⚡ **The cockpit's content is this page's** — every one of
                    the nineteen intelligence components renders here and
                    nowhere else, measured. */}
                <WhatMovedIt score={score} />
              </CardBody>
            </Card>
            )}
          </AccountSectionShell>

          {/* **What has actually happened, under what we think about it.**
              [C-024](../../../../docs/LANE_COORDINATION.md): Timeline's
              backend, hook and component were complete and mounted nowhere,
              so a shipped capability reached no customer. Lane B owns the
              feature and may not edit this file; Product Surface owns the
              mount and contributes it. **Below the ledger** because every
              section above argues *why this account matters* and this one
              answers *what has occurred* — the question a reader asks last,
              and usually because they are about to decide.

            **Option A of three, and B was already ruled out**: D38 retired
            *Timeline* as a menu entry, because navigation is journeys
              rather than data. C — a collapsed disclosure — was refused for
              the reason C-024 itself gives: it would hide the one surface
              that answers *what changed since I last looked* (R9-04). */}
          {/* **Last of the argument, before the record of events** (TASK-417).
              A workspace declaration rather than an account fact, so it sits
              after everything Signora derived about *this* company — a reader
              who has not yet seen the evidence should not meet a list of
              names first and carry it into the rest of the page.

              It renders nothing when nothing is declared. A section explaining
              its own absence on every account of a workspace that has not
              filled this in is noise on the screen a seller lives on; the
              declaration page is where that prompt belongs. */}
          {/* **Stage 2 of [C-008](../../../../docs/LANE_COORDINATION.md), and
              it belongs beside the competitor list rather than anywhere else
              on this page.** Both are workspace declarations — identical on
              every account, describing the business rather than this company —
              so grouping them keeps one boundary legible: everything above is
              what Signora derived about *this* account, and these two are what
              the customer told us about themselves.

            **Before competitors**, because *what we sell and who signs for
              it* is the frame a seller reads *who we are up against* inside.

              ⛔ **No ideal customer here, and that is the ruling rather than a
              layout choice.** An ICP rendered beside a real company is a
              comparison a reader completes whether or not the product does,
              and matching is DEFERRED.

              ⚠️ **This used to say matching *"waits on
              [C-002](../../../../docs/LANE_COORDINATION.md)"*, and C-002 is
              `CLOSED`** — Lane C, 2026-08-06,
              [D-116](../../../../docs/DECISION_REGISTER.md). ⛔ **A closed row
              cited as a live blocker is worse here than a stale one is
              elsewhere**: the next reader checks it, finds it answered, and
              concludes matching is free.

              ✅ **It is not.** 📁 **The product owner deferred it** — *"keep
              grouped with [C-322](../../../../docs/LANE_COORDINATION.md), do
              not split, review when Epic B1 begins"* — and
              📁 [TASK-903](../../../../docs/BACKLOG.md) still carries the live
              scope bound in its own words: ***"display the declarations,
              assert no match."*** ⚡ **That is exactly what this renders.**

              `/business` is where a seller reads it and makes that comparison
              knowingly. */}
          <WhatYouSell
            catalog={catalog.data}
            committee={committee.data}
            isError={catalog.isError || committee.isError}
          />

          {/* ⚡ **`id="compete"`, 📁 the design's own `pageNav` href** —
              [TASK-1476](../../../../docs/BACKLOG.md), [B-299](../../../../docs/BUGS.md) ④.
              ⛔ **The component renders no `section` of its own**, so the page
              contributes one rather than the component growing an opinion
              about being a whole section of a screen. ⚠️ **This closes half of
              the limitation the rail's own docstring names** — *"three
              sections have reads and no section on this page yet"*. */}
          {/* ⛔ **No empty region.** ⚡ The wrapper renders only when the
              component will put something inside it — **an anchored `section`
              containing nothing is a rail entry that scrolls a reader to
              blank space**, which is the same defect as a link to a missing
              id and harder to notice. */}
          {rendersCompetitors ? (
            <section id="compete" aria-label="Competitors">
              <CompetitorContext
                competitors={competitors.data}
                isError={competitors.isError}
                {...(correlationOf(competitors.error) === undefined
                  ? {}
                  : { correlationId: correlationOf(competitors.error)! })}
              />
            </section>
          ) : null}

          {/* **Between the ledger and the record of events** (TASK-417, wave 1
              of the approved Account 360). The contribution list above says
            *what Signora weighed*; the timeline below says *what occurred*.
              This is the layer between them — **the raw provider readings the
              weighing rests on, each naming the provider that reported it.**

            **It goes above the timeline rather than beside it** because a
              reader who has just seen a contribution they doubt is asking
            *"says who?"*, and that question has to be answerable without
              scrolling past everything that happened this year.

              The endpoint has shipped since M3B and reached no screen —
              the same shape as [C-024](../../../../docs/LANE_COORDINATION.md),
              which is what wave 1 exists to close. */}
          {/* ⚡ **`id="signals"`** — the design's *Signals timeline*. */}
          {/* 🔴 **📁 The design titles `#signals` *"Signals timeline"***, and so
              does the rail. ⛔ **This heading read *"What changed"*** — 📁 the
              phrase appears in the corpus only in the Design System's own
              changelog and a gap-closure card, **never on Account 360.** */}
          <AccountSectionShell
            id="signals"
            heading="Signals timeline"
            // ⚠️ **No severity is claimed for an observation.** ⛔ An
            // observation is a reading, and whether a reading is bad is
            // `buying_score_engine`'s judgement rather than this screen's — so
            // the header states the COUNT and no status, which `none` is for.
            severities={(observations.data ?? []).map(() => 'none' as const)}
            count={observations.data?.length ?? null}
            viewerId={viewerId}
            kind={accountKind}
            isLoading={observations.isLoading}
            // 🔴 **[B-1054](../../../../docs/BUGS.md)** — with `observations`
            // forced to 500 this heading read *"What changed 0"* above a body
            // saying the read failed. ⛔ **The prose was right and the number
            // was wrong.**
            isError={observations.isError}
          >
            <ObservationList
              observations={observations.data}
              isLoading={observations.isLoading}
              isError={observations.isError}
            />
          </AccountSectionShell>

          {/* 🔴 **The seven sections the design draws and nothing can fill** —
              [TASK-1415](../../../../docs/BACKLOG.md).

              ⛔ **Rendered rather than omitted** ([§20c](../../../../CLAUDE.md)):
              a page that silently left them out would be indistinguishable
              from one with a bug, and a rep who has seen the design would
              assume the screen was broken. ⚡ **Each says what it would show
              and what Signora cannot answer yet** — 📁 the measurement is
              [`lib/accounts/sections.ts`](../../../../lib/accounts/sections.ts),
              not this file's memory. */}
          {absent().map((section) => (
            <AbsentSection key={section.id} section={section} />
          ))}

          {/* 🔴 **The history docks into the panel's Activity tab when there is
              a panel, and renders here when there is not** —
              [TASK-1433](../../../../docs/BACKLOG.md).

              ⛔ **Never both.** 📁 The design gives the panel no width below
              1024, and it never says the CONTENT disappears — only the panel.
              ⚡ **So `carrying` decides the PLACEMENT of one component over one
              data source**, rather than there being two copies to keep in
              step. */}
          {/* ⚡ **`id="activity"`** — the design's *Recent activity*. ⚠️ Only
              anchored when the utility panel is NOT carrying it, which is why
              the rail's `anchored` list asks the same question. */}
          {history.carrying ? null : (
            <AccountSectionShell
              id="activity"
              // 🔴 **📁 *"Recent activity"* — the design's name, and the comment
              // three lines above ALREADY SAID SO while this rendered something
              // else.** ⛔ ***"What has happened"* appears ZERO times across the
              // 35-document snapshot**, and `sections.ts` labels this section
              // *"Recent activity"* in the rail — **so the rail and the heading
              // it points at named one section two different things.**
              // ⚡ **The seventh invented heading on this surface**, found while
              // diagnosing an unrelated `golden-journey` failure rather than by
              // the sweep that found the other six.
              heading="Recent activity"
              // ⚠️ **No severity is claimed for a recorded event.** ⛔ Whether
              // something that happened is bad is a judgement, and the
              // timeline records rather than judges — so the header states a
              // count and no status, which `none` exists for.
              severities={[]}
              /**
               * 🔴 **[B-299](../../../../docs/BUGS.md) — this header read `0`
               * above a timeline holding entries**, for the same reason
               * *Open opportunities* did: the count came from `severities`, and
               * this section claims none.
               *
               * ⛔ **And a LOADED count would be the other half of the same
               * defect.** ⚡ **The timeline is paged** — `CursorPage` carries
               * `items`, `next_cursor` and `has_more`, **and no total** — so
               * while `hasNextPage` is true the only number this page can
               * compute is *how far the reader has scrolled*, ⛔ **which a
               * header states as though it were how much happened.**
               * ⚠️ **`25` beside a *Load more* button is a wrong measurement,
               * not a partial one.**
               *
               * ✅ **So the count is published exactly when the whole list is
               * in hand**, and 📁 whether the endpoint should publish a total
               * is [C-1561](../../../../docs/LANE_COORDINATION.md) rather than
               * a number invented here.
               */
              count={
                timeline.isLoading || timeline.isError || timeline.hasNextPage
                  ? null
                  : (timeline.data?.pages.flatMap((page) => page.items).length ?? null)
              }
              // ⛔ **The header states no count when the read failed** — the
              // body already says so, and 📁 [B-1054](../../../../docs/BUGS.md)
              // is the two disagreeing.
              isError={timeline.isError}
              viewerId={viewerId}
              kind={accountKind}
            >
              {historyFeed}
            </AccountSectionShell>
          )}

          {/* **Where the argument ends.** Every line above is Signora's
              reasoning about a fact; this is the fact. Rendered once for the
              page rather than per line — a dozen mounted dialogs to show one
              is a dozen too many. */}
          <EvidenceDrawer
            workspaceId={workspaceId}
            eventId={evidence.eventId}
            onClose={evidence.close}
          />
        </>
      )}

      {/* **Where the morning continues.** At the bottom because that is where
          a reader finishes, and the only other navigation on this page is at
          the top — where nobody is when they are done (R10-01). */}
      <AccountSequence
        accountId={accountId}
        accounts={ranked}
        identities={rankedIdentities}
      />
    </RecordLayout>
  );
}

/**
 * Both readings are live and neither won.
 *
 * **Stated as a reason to look harder, not as a caveat.** The Buying Score
 * Engine refuses to average opposing readings away precisely because a
 * fought-over account is more interesting than a quiet one; wording that
 * apologised for the disagreement would invert the meaning the pipeline
 * computed.
 */
function ContestedNote() {
  return (
    <Card>
      <CardBody className="flex items-start gap-3 py-3">
        <Scale aria-hidden className="mt-0.5 h-4 w-4 shrink-0 text-accent" />
        <p className="text-sm leading-6 text-content-muted">
          Your evidence points both ways on this account. Signora has not picked a side
          and has not split the difference — both readings are counted, and the lines that
          disagree with the majority are marked below.
        </p>
      </CardBody>
    </Card>
  );
}

function Loading() {
  return (
    <Card>
      <CardBody>
        <SkeletonText lines={5} />
      </CardBody>
    </Card>
  );
}

/**
 * The account exists and nothing has scored it.
 *
 * A real answer rather than an error, and worded so a seller can tell the two
 * apart. It is also what a caller sees for an account in another workspace —
 * deliberately indistinguishable, or account identifiers become enumerable.
 */
function NeverScored() {
  return (
    <EmptyState
      icon={Scale}
      title="Nothing has scored this account yet"
      description="A score appears once evidence about this company reaches Signora and your ideal-customer profile says it matters. Until then there is nothing to explain."
    />
  );
}

/**
 * 🔴 **The score's own failure, in the score's own box** —
 * [B-299](../../../../docs/BUGS.md).
 *
 * 📁 ***"States what is missing versus what is still TRUSTWORTHY, then retry
 * plus a correlation ID."***
 *
 * ⛔ **This was `as="page"` and said *"this account"*, which claimed the whole
 * record had failed** — and, because the page was gated on it, made that claim
 * true. ✅ **`as="card"` is the shape for *"a section that owns its own
 * box"***, and the subject narrows to the one read that failed.
 *
 * ⚡ **The reassurance is the design's second clause, and it is a sentence this
 * page could not honestly have said before**: the rest of the record only
 * stays live because the gate above it went.
 *
 * ⚠️ **This also retires the `as="page"` half of
 * [C-1557](../../../../docs/LANE_COORDINATION.md) on THIS surface.** ⛔ The row
 * stays open — it asks whether a page-scope absence should carry an `h1`, and
 * other callers still pass `as="page"` — **but Account 360 no longer depends on
 * the answer.**
 */
function ScoreUnavailable({
  correlationId,
  onRetry,
}: {
  correlationId?: string;
  onRetry: () => void;
}) {
  return (
    <StatedAbsence
      as="card"
      subject="this account's score"
      reassurance="The rest of this account's record is unaffected"
      onRetry={onRetry}
      {...(correlationId === undefined ? {} : { correlationId })}
    />
  );
}
