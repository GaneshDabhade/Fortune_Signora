'use client';

import { ArrowLeft, Scale } from 'lucide-react';
import Link from 'next/link';
import { useParams } from 'next/navigation';

import { ContestedMark, WhyNow } from '@/components/intelligence/attention';
import {
  ContributionList,
  PostureSplit,
  ReadingValidity,
  ScoreArithmetic,
} from '@/components/intelligence/contributions';
import { EntityName } from '@/components/intelligence/entity-name';
import { EvidenceDrawer, useEvidenceDrawer } from '@/components/intelligence/evidence';
import { NarrativeBlock } from '@/components/intelligence/narration';
import { ResearchPanel } from '@/components/intelligence/research';
import { AccountSequence } from '@/components/intelligence/sequence';
import { ValidationBlock } from '@/components/intelligence/validation';
import {
  ContestedSince,
  OpportunityMomentum,
  WorkflowStage,
} from '@/components/intelligence/opportunity';
import { WorkflowActions } from '@/components/intelligence/workflow';
import { NoWorkspace } from '@/components/workspace/no-workspace';
import { Card, CardBody, EmptyState, SkeletonText } from '@/components/ui';
import { ApiError } from '@/lib/api/client';
import { useSession } from '@/lib/auth/client';
import {
  useAccounts,
  useAccountIdentities,
  useAccountNarration,
  useAccountOpportunity,
  useAccountResearch,
  useAccountScore,
  useAccountValidation,
  useRequestResearch,
} from '@/lib/query/hooks';
import { useWorkspaceContext } from '@/lib/state/workspace-provider';

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
  const { activeWorkspace, isLoading: workspacesLoading } = useWorkspaceContext();
  const workspaceId = activeWorkspace?.id ?? null;
  // Only so the page can say *you* rather than an identifier, and assign an
  // account to the person taking it on. Never an authorization decision —
  // Casbin on the server is that, and always.
  const { data: session } = useSession();
  const viewerId = session?.user.id ?? null;

  const { data: score, isLoading, error } = useAccountScore(workspaceId, accountId);
  const { data: opportunity } = useAccountOpportunity(workspaceId, accountId);
  const { data: narration } = useAccountNarration(workspaceId, accountId);
  const { data: validation } = useAccountValidation(workspaceId, accountId);
  const { data: research } = useAccountResearch(workspaceId, accountId);
  const requestResearch = useRequestResearch(workspaceId, accountId);
  const evidence = useEvidenceDrawer();
  const { data: identities, isLoading: nameLoading } = useAccountIdentities(workspaceId, [
    accountId,
  ]);
  // **The same query the attention page holds**, same cache key, so this costs
  // no request — the brief reads the ranked order rather than fetching it, and
  // *next* therefore means *next most pressing* (D41).
  const { data: list } = useAccounts(workspaceId);
  const ranked = list?.items ?? [];
  const { data: rankedIdentities } = useAccountIdentities(
    workspaceId,
    ranked.map((account) => account.account_id),
  );

  const notScored = error instanceof ApiError && error.status === 404;

  return (
    <div className="mx-auto flex max-w-3xl flex-col gap-6">
      <BackToList />

      <header className="flex items-start justify-between gap-4">
        <div className="min-w-0">
          <EntityName
            identity={identities?.get(accountId)}
            fallbackId={accountId}
            isLoading={nameLoading}
            className="text-lg"
          />
          {/* The workflow line sits under the name rather than in the score
              card: it is about the *account*, not about the number, and a
              seller reads it once on arrival and never again.

              **The decision sits with it**, so workflow lives in exactly one
              place on the screen. An AE who arrived already knowing they are
              working this account should not have to read a brief to say so;
              a reader who is still deciding scrolls, decides, and comes back
              to a control they have already seen. */}
          {opportunity ? (
            <div className="mt-0.5 flex flex-col gap-2.5">
              <WorkflowStage opportunity={opportunity} viewerId={viewerId} />
              <WorkflowActions
                opportunity={opportunity}
                workspaceId={workspaceId}
                viewerId={viewerId}
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
                  is the story, and it is the one figure no other screen has. */}
              {opportunity ? (
                <div className="border-t border-border pt-3">
                  <OpportunityMomentum opportunity={opportunity} />
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
          {narration ? <NarrativeBlock narration={narration} /> : null}

          {score.contested ? <ContestedNote /> : null}
          {opportunity ? (
            <ContestedSince opportunity={opportunity} contestedNow={score.contested} />
          ) : null}

          {/* **Action before evidence.** A reader who is already convinced
              gets what to do next without scrolling past the arithmetic; one
              who is not continues to the ledger below. That is what
              progressive disclosure means on a page — information ordered so
              most of it is never read. */}
          {validation ? <ValidationBlock validation={validation} /> : null}

          {/* **Below the deterministic page, and above the ledger it cites.**
              Research is the only thing here a person starts, and it is the
              only thing that costs anything — so it sits after everything the
              pipeline already knew, where a reader arrives having seen what
              they get for free. The ledger stays last because research's own
              findings point down into it. */}
          <ResearchPanel
            research={research ?? null}
            onRequest={() => requestResearch.mutate()}
            isRequesting={requestResearch.isPending}
          />

          <section className="flex flex-col gap-3">
            <h2 className="text-sm font-semibold text-content">What contributed</h2>
            <Card>
              <CardBody className="py-1">
                <ContributionList score={score} onOpenEvidence={evidence.open} />
              </CardBody>
            </Card>
          </section>

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
    </div>
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
    <EmptyState
      icon={Scale}
      title="Could not load this account"
      description="The explanation is unavailable right now. Nothing has changed about the account — reload to try again."
    />
  );
}
