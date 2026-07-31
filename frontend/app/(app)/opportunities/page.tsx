'use client';

import { LineChart } from 'lucide-react';

import {
  AttentionScore,
  ContestedMark,
  EvidenceHealth,
  ScoreMovement,
  WhyNow,
} from '@/components/intelligence/attention';
import { Card, CardBody, EmptyState, SkeletonText } from '@/components/ui';
import type { AccountAttention } from '@/lib/api/types';
import { useAccounts } from '@/lib/query/hooks';
import { useWorkspaceContext } from '@/lib/state/workspace-provider';

/**
 * The morning workspace — *"which accounts should I work on today?"*
 *
 * **Not a dashboard.** There is no chart, no KPI tile, no summary of totals.
 * A dashboard reports on a period; this answers a question a person is about
 * to act on, which is a different job and a different shape: one ordered
 * list, read top-down, stopping when they have enough to start.
 *
 * The order of information on a row is deliberate — **what, why, how much it
 * moved, how far it can be trusted.** A seller decides from the first two and
 * only reads the rest when the first two make them hesitate.
 *
 * **Everything on this screen is deterministic.** The score, the movement,
 * the reason and the evidence state are all computed by the pipeline from
 * recorded facts; no model wrote any of it. That is deliberate for the daily
 * surface: the screen a person opens every morning should be the one they
 * never have to second-guess. AI arrives on the account brief, where its
 * claims can be read beside the evidence they cite.
 */
export default function OpportunitiesPage() {
  const { activeWorkspace } = useWorkspaceContext();
  const { data, isLoading, isError } = useAccounts(activeWorkspace?.id ?? null);

  return (
    <div className="mx-auto flex max-w-4xl flex-col gap-6">
      <header>
        <h1 className="text-xl font-semibold text-content">Opportunities</h1>
        <p className="mt-1 text-sm text-content-muted">
          Accounts your evidence says are worth a look, most pressing first.
        </p>
      </header>

      {isLoading ? <Loading /> : null}
      {isError ? <Unavailable /> : null}
      {data && data.items.length === 0 ? <Quiet /> : null}
      {data && data.items.length > 0 ? (
        <ol className="flex flex-col gap-2">
          {data.items.map((account) => (
            <li key={account.id}>
              <AccountRow account={account} />
            </li>
          ))}
        </ol>
      ) : null}
    </div>
  );
}

/**
 * One account, as a row.
 *
 * Two lines and a number. The account and its reason carry the decision; the
 * movement and evidence badges are there for the moment a seller pauses over
 * one, which is what progressive disclosure means on a list — **not a
 * collapsed panel, but information ordered so most of it is never read.**
 */
function AccountRow({ account }: { account: AccountAttention }) {
  return (
    <Card>
      <CardBody className="flex items-center gap-4 py-3">
        <div className="w-12 shrink-0 text-right">
          <AttentionScore score={account.score} />
        </div>

        <div className="min-w-0 flex-1">
          <p className="truncate font-medium text-content">
            {/* The company name lives in the Knowledge Graph and has no
                endpoint yet, so the account is named by its identifier
                rather than by a placeholder that would read as a real name.
                Resolving it is the first thing M12.2 does. */}
            <span className="font-mono text-sm text-content-muted">
              {account.account_id.slice(0, 8)}
            </span>
          </p>
          <div className="mt-0.5 flex flex-wrap items-center gap-x-3 gap-y-1">
            <WhyNow trigger={account.trigger} />
            <ScoreMovement trend={account.trend} change={account.score_change} />
          </div>
        </div>

        <div className="flex shrink-0 items-center gap-2">
          <ContestedMark contested={account.contested} />
          <EvidenceHealth evidence={account.evidence} />
        </div>
      </CardBody>
    </Card>
  );
}

function Loading() {
  return (
    <Card>
      <CardBody>
        <SkeletonText lines={4} />
      </CardBody>
    </Card>
  );
}

/**
 * Nothing needs attention — a legitimate answer, not a failure.
 *
 * Worded so a seller can tell it apart from a broken screen: it says what
 * would put an account here, so the absence is informative rather than
 * ambiguous.
 */
function Quiet() {
  return (
    <EmptyState
      icon={LineChart}
      title="Nothing needs your attention"
      description="Accounts appear here when your evidence says they are worth a look — a new signal, a change in what your ideal customer looks like, or a score that moved."
    />
  );
}

function Unavailable() {
  return (
    <EmptyState
      icon={LineChart}
      title="Could not load your accounts"
      description="The list is unavailable right now. Nothing has changed about your accounts — reload to try again."
    />
  );
}
