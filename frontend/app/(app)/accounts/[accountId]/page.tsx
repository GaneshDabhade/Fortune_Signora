'use client';

import { ArrowLeft, Lock, Scale } from 'lucide-react';
import Link from 'next/link';
import { useParams, useRouter, useSearchParams } from 'next/navigation';
import { useMemo } from 'react';

import {
  ContestedMark,
  EvidenceHealth,
  WhyNow,
} from '@/components/intelligence/attention';
import {
  ContributionList,
  PostureSplit,
  ReadingValidity,
  ScoreArithmetic,
} from '@/components/intelligence/contributions';
import { useUtilityPanel } from '@/components/shell/utility-panel';
import { AbsentSection, OnThisPage } from '@/components/accounts/sections';
import { AccountSectionShell } from '@/components/accounts/section';
import { contributionSeverities, correlationOf } from '@/lib/accounts/section-state';
import { absent } from '@/lib/accounts/sections';
import { CompetitorContext } from '@/components/intelligence/competitors';
import { StatedAbsence } from '@/components/feedback/stated-absence';
import { SystemState } from '@/components/ui/system-state';
import { EntityName } from '@/components/intelligence/entity-name';
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
import { Card, CardBody, EmptyState, SkeletonText } from '@/components/ui';
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
import { useWorkspaceMembers } from '@/lib/query/hooks/team';
import { scopeFrom } from '@/lib/state/owner-scope';
import { useWorkspaceContext } from '@/lib/state/workspace-provider';
import { ReadingColumn } from '../../reading-column';

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
 * ### What is deliberately not here yet
 *
 * The Decision Package —
 * which stays unbuilt until `reasoning@1` holds a release, because UI around an
 * unavailable capability is a panel that cannot be filled. **Nothing on this
 * page hints at it.** A control that looks clickable and is not costs more
 * trust than the missing feature does — and a panel that says *"coming soon"*
 * costs more than both.
 */
export default function AccountBriefPage() {
  const { accountId } = useParams<{ accountId: string }>();
  const router = useRouter();
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

  const { data: score, isLoading, error } = useAccountScore(workspaceId, accountId);
  const { data: opportunity, error: opportunityError } = useAccountOpportunity(
    workspaceId,
    accountId,
  );
  // **404 is "nobody has taken this account on"; anything else is an outage.**
  // The third section on this page to need the split, after narration and
  // research. Without it the workflow controls simply vanish, and an account
  // somebody is actively working reads as one nobody has touched.
  const neverTaken = opportunityError instanceof ApiError && opportunityError.status === 404;
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
  const { data: research, error: researchError } = useAccountResearch(workspaceId, accountId);
  // **404 is "nobody has asked yet"; anything else is an outage.** The same
  // split the narration block above makes, and for the same reason: without it
  // both render as absence, and absence here is an invitation to start a run
  // that may already exist.
  const neverResearched = researchError instanceof ApiError && researchError.status === 404;

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
  const { data: identities, isLoading: nameLoading } = useAccountIdentities(workspaceId, [
    accountId,
  ]);
  const identity = identities?.get(accountId);
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
              className="rounded text-sm font-medium text-accent underline decoration-border underline-offset-4 transition-colors hover:decoration-accent focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent"
            >
              Back to the accounts you can see
            </Link>
          }
        />
      </ReadingColumn>
    );
  }

  return (
    <ReadingColumn>
      <BackToList />

      {/* **The name gets the width it needs before the score takes any.** A
          company name is the longest thing on this page and the one a reader
          is looking for; at 320px, sharing the row with the score block leaves
          it a few characters. Stacked below `sm`, side by side above it. */}
      <header className="flex flex-col gap-3 phone:flex-row phone:items-start phone:justify-between phone:gap-4">
        <div className="min-w-0">
          {/* **The page's only level-1 heading** (B-313). The brief had none,
              so its two `<h2>`s hung under nothing and a reader navigating by
              structure landed on *"What contributed"* without learning which
              account they were looking at.

              **The heading is here rather than inside `EntityName`**, which is
              shared with the attention list — a name that is a page title on
              one screen and a row label on another cannot be one element, and
              bending the component to suit this caller would make it slightly
              wrong for every other (§20c). The `<h1>` carries no styling of
              its own: preflight resets it, so the name looks exactly as it
              did. */}
          <h1 className="min-w-0">
            <EntityName
              identity={identity}
              fallbackId={accountId}
              isLoading={nameLoading}
              className="text-lg"
            />
          </h1>
          {/* **Directly under the name, because it qualifies the whole page**
              rather than any one card. Everything below — the score, its
              contributions, the narration, the validations — is built on
              evidence, and a reader who does not know how old that evidence is
              cannot calibrate any of it.

              **Outside the heading**, deliberately: freshness qualifies the
              page, but it is not part of the page's name, and a document
              outline that read "Northwind Health — collected 3 days ago"
              would be an outline entry that changes under the reader.

              **Only once the identity has actually arrived.** Absent means
              *we do not know yet, or the request failed*; rendering "No
              evidence collected yet" for either would state something false
              about the account, which is the one thing this line exists not
              to do. It also keeps two skeletons off the page on arrival. */}
          {identity ? <Freshness observedAt={identity.last_observed_at} /> : null}
          {/* The workflow line sits under the name rather than in the score
              card: it is about the *account*, not about the number, and a
              seller reads it once on arrival and never again.

              **The decision sits with it**, so workflow lives in exactly one
              place on the screen. An AE who arrived already knowing they are
              working this account should not have to read a brief to say so;
              a reader who is still deciding scrolls, decides, and comes back
              to a control they have already seen. */}
          {workflowUnavailable ? (
            /* **Said, rather than omitted.** The controls must not render —
               nobody should act on state Signora could not read — but a silent
               gap tells a seller this account is untouched, which is a claim
               about their pipeline rather than about our request. */
            <StatedAbsence subject="where this account stands" reassurance="Nothing has changed about the account" />
          ) : null}

          {opportunity ? (
            <div className="mt-0.5 flex flex-col gap-2.5">
              <WorkflowStage opportunity={opportunity} viewerId={viewerId} people={people} />
              <WorkflowActions
                colleagues={colleaguesFrom(roster?.items, viewerId)}
                opportunity={opportunity}
                workspaceId={workspaceId}
                viewerId={viewerId}
                // **Named or not offered.** A row whose name has not resolved
                // would read as *"Next: "* — the sequence below has the same
                // rule, and an offer that cannot say where it goes is the
                // affordance this surface refuses everywhere else.
                {...(upNext && upNextName
                  ? {
                      next: {
                        name: upNextName,
                        go: () => router.push(`/accounts/${upNext.account_id}`),
                      },
                    }
                  : {})}
              />
            </div>
          ) : null}
        </div>
        {score ? <ContestedMark contested={score.contested} /> : null}
      </header>

      {/* Same as the list: with no workspace every query is disabled and
          nothing rendered. Reachable directly by URL, so it needs its own
          answer rather than relying on the list to have given one (D36). */}
      {!workspacesLoading && workspaceId === null ? <NoWorkspace /> : null}
      {isLoading ? <Loading /> : null}
      {notScored ? <NeverScored /> : null}
      {error && !notScored ? <Unavailable /> : null}

      {/* 📁 **The design's *"On this page"* rail** —
          [TASK-1415](../../../../docs/BACKLOG.md). ⚡ **Horizontal here rather
          than a right-hand column**, because the right-hand column on this
          screen is the utility panel ([TASK-1433](../../../../docs/BACKLOG.md))
          and two rails competing for one edge is a layout that serves neither.
          ⛔ **It lists every section, including the seven nothing can fill** —
          a map that hides the empty rooms is one nobody can trust. */}
      {score ? (
        <OnThisPage
          // ⚡ **What this page actually renders**, in the design's order.
          // ⛔ **`score`, `signals` and `activity` are the supplied sections
          // that have a section here**; the seven absent ones all carry an id.
          // ⚠️ **`activity` only when the utility panel is not carrying it**,
          // which is why `history.carrying` decides it.
          anchored={[
            // ⚡ **`summary`, `research` and `competitors` join the rail** —
            // [TASK-1476](../../../../docs/BACKLOG.md). ⛔ **They rendered on
            // this page all along and carried no `id`**, so the rail could not
            // link to them and its docstring recorded that as a limitation.
            // ✅ **The limitation is closed rather than restated.**
            // ⚡ **`summary` is unconditional now.** 📁 *"Header, title and
            // counts paint from cache; only the body skeletons"* — **the
            // section renders in all four of its states**, so the rail entry
            // is stable and nothing below it moves when the read lands.
            'summary',
            'score',
            'health',
            'intent',
            'signals',
            // 🔴 **`contacts` joins the rail — TASK-1476.** ⚠️ It was
            // classified `supplied` and had no section here, so the rail could
            // never anchor it. **It is `absent` now and states why**, which is
            // the treatment §20c requires and the one every other unfillable
            // section already gets.
            'contacts',
            // ⚡ **`research` is unconditional** — `ResearchPanel` always
            // renders its section, because the invitation to start research is
            // itself the content when there is none.
            'research',
            ...(rendersCompetitors ? ['competitors'] : []),
            'org-chart',
            'relationships',
            'tech-stack',
            'market',
            ...(history.carrying ? [] : ['activity']),
            'meetings',
          ]}
          className="phone:flex-row phone:flex-wrap phone:items-center phone:gap-1"
        />
      ) : null}

      {score ? (
        <>
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

          {score.contested ? <ContestedNote /> : null}
          {opportunity ? (
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
            onRequest={() => requestResearch.mutate()}
            isRequesting={requestResearch.isPending}
          />

          {/* **After the reasoning, before the evidence.** Somebody asking
              what happened here before them is asking a different question
              from *why does this score say what it says* — and usually asking
              it because they are about to decide something themselves. It
              sits where the page turns from Signora's argument to the record
              of what people did with it. */}
          {opportunity ? (
            <DecisionHistory opportunity={opportunity} viewerId={viewerId} people={people} />
          ) : null}

          {/* ⚡ **`id="score"`** — the design calls this section *Account
              score*, and the rail links to it by that id. */}
          <AccountSectionShell
            id="score"
            heading="What contributed"
            // ⚡ **A contribution's own direction is its severity** — ⛔ nothing
            // is invented: the ledger already says whether a contribution
            // pushed the score up or down, and the header folds those.
            severities={contributionSeverities(score?.contributions)}
            viewerId={viewerId}
            kind={accountKind}
            isLoading={isLoading}
            lastKnownCount={score?.contributions?.length ?? null}
          >
            <Card>
              <CardBody className="py-1">
                <ContributionList score={score} onOpenEvidence={evidence.open} />
              </CardBody>
            </Card>
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
              and matching waits on
              [C-002](../../../../docs/LANE_COORDINATION.md). `/business` is
              where a seller reads it and makes that comparison knowingly. */}
          <WhatYouSell
            catalog={catalog.data}
            committee={committee.data}
            isError={catalog.isError || committee.isError}
          />

          {/* ⚡ **`id="competitors"`** — [TASK-1476](../../../../docs/BACKLOG.md).
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
            <section id="competitors" aria-label="Competitors">
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
          <AccountSectionShell
            id="signals"
            heading="What changed"
            // ⚠️ **No severity is claimed for an observation.** ⛔ An
            // observation is a reading, and whether a reading is bad is
            // `buying_score_engine`'s judgement rather than this screen's — so
            // the header states the COUNT and no status, which `none` is for.
            severities={(observations.data ?? []).map(() => 'none' as const)}
            viewerId={viewerId}
            kind={accountKind}
            isLoading={observations.isLoading}
            lastKnownCount={observations.data?.length ?? null}
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
            <section id="activity" className="flex flex-col gap-3">
              <h2 className="text-sm font-semibold text-content">What has happened</h2>
              {historyFeed}
            </section>
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
      ) : null}

      {/* **Where the morning continues.** At the bottom because that is where
          a reader finishes, and the only other navigation on this page is at
          the top — where nobody is when they are done (R10-01). */}
      <AccountSequence
        accountId={accountId}
        accounts={ranked}
        identities={rankedIdentities}
      />
    </ReadingColumn>
  );
}

function BackToList() {
  return (
    <Link
      href="/"
      className="inline-flex w-fit items-center gap-1.5 rounded text-sm text-content-muted transition-colors hover:text-content focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent"
    >
      <ArrowLeft aria-hidden className="h-3.5 w-3.5" />
      All accounts
    </Link>
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

function Unavailable() {
  return (
    <StatedAbsence
      as="page"
      icon={Scale}
      subject="this account"
    />
  );
}
