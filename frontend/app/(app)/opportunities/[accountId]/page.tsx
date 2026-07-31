'use client';

import { ArrowLeft, Scale } from 'lucide-react';
import Link from 'next/link';
import { useParams } from 'next/navigation';

import { ContestedMark, ScoreMovement, WhyNow } from '@/components/intelligence/attention';
import {
  ContributionList,
  PostureSplit,
  ReadingValidity,
  ScoreArithmetic,
} from '@/components/intelligence/contributions';
import { EntityName } from '@/components/intelligence/entity-name';
import { Card, CardBody, EmptyState, SkeletonText } from '@/components/ui';
import { ApiError } from '@/lib/api/client';
import { useAccountIdentities, useAccountScore } from '@/lib/query/hooks';
import { useWorkspaceContext } from '@/lib/state/workspace-provider';

/**
 * The account brief — *"why this account?"*
 *
 * The second question of the morning, and the one the list cannot answer. A
 * seller who has decided *which* accounts now has to decide whether they agree,
 * and then defend that to somebody else. **This page exists to be argued with.**
 *
 * ### The route is `/opportunities/[accountId]`, and the segment is named
 *
 * The parameter is an **account** identifier under a section called
 * Opportunities, which is the sort of mismatch that costs the next engineer an
 * hour. Naming the segment `accountId` puts the answer in the URL itself rather
 * than in a comment somebody has to find. The section keeps its name because a
 * seller works a list of opportunities; the brief is about the company one of
 * them is on.
 *
 * ### Composed from two requests, not one aggregate
 *
 * The name comes from the Knowledge Graph and the score from the Buying Score
 * Engine, because no module in the ratified graph reaches both. Composing them
 * here was the option that needed no architectural change
 * (37-product-surface.md §7).
 *
 * ### What is deliberately not here yet
 *
 * The business events and observations beneath each line, and the AI narration
 * and Decision Package, land in later M12 slices. **Nothing on this page hints
 * at them.** A control that looks clickable and is not costs more trust than
 * the missing feature does.
 */
export default function AccountBriefPage() {
  const { accountId } = useParams<{ accountId: string }>();
  const { activeWorkspace } = useWorkspaceContext();
  const workspaceId = activeWorkspace?.id ?? null;

  const { data: score, isLoading, error } = useAccountScore(workspaceId, accountId);
  const { data: identities, isLoading: nameLoading } = useAccountIdentities(workspaceId, [
    accountId,
  ]);

  const notScored = error instanceof ApiError && error.status === 404;

  return (
    <div className="mx-auto flex max-w-3xl flex-col gap-6">
      <BackToList />

      <header className="flex items-start justify-between gap-4">
        <EntityName
          identity={identities?.get(accountId)}
          fallbackId={accountId}
          isLoading={nameLoading}
          className="text-lg"
        />
        {score ? <ContestedMark contested={score.contested} /> : null}
      </header>

      {isLoading ? <Loading /> : null}
      {notScored ? <NeverScored /> : null}
      {error && !notScored ? <Unavailable /> : null}

      {score ? (
        <>
          <Card>
            <CardBody className="flex flex-col gap-4">
              <div className="flex flex-wrap items-end justify-between gap-4">
                <ScoreArithmetic score={score} />
                <div className="flex flex-col items-end gap-1">
                  <WhyNow trigger={score.trigger} />
                  <ScoreMovement trend={score.trend} change={score.score_change} />
                </div>
              </div>
              <ReadingValidity score={score} />
              <PostureSplit score={score} />
            </CardBody>
          </Card>

          {score.contested ? <ContestedNote /> : null}

          <section className="flex flex-col gap-3">
            <h2 className="text-sm font-semibold text-content">What contributed</h2>
            <Card>
              <CardBody className="py-1">
                <ContributionList score={score} />
              </CardBody>
            </Card>
          </section>
        </>
      ) : null}
    </div>
  );
}

function BackToList() {
  return (
    <Link
      href="/opportunities"
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
