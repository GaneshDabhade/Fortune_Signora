'use client';

import { LineChart } from 'lucide-react';

import {
  AttentionScore,
  ContestedMark,
  EvidenceHealth,
  Hypothesis,
  Ownership,
  ScoreMovement,
} from '@/components/intelligence/attention';
import { DecidedAccounts } from '@/components/intelligence/decided';
import { EntityName } from '@/components/intelligence/entity-name';
import { NoWorkspace } from '@/components/workspace/no-workspace';
import { Card, CardBody, EmptyState, SkeletonText } from '@/components/ui';
import type { AccountAttention, AccountIdentity } from '@/lib/api/types';
import {
  useAccountIdentities,
  useAccounts,
  useDecidedAccounts,
  useSignalCatalog,
} from '@/lib/query/hooks';
import { useSession } from '@/lib/auth/client';
import { useWorkspaceContext } from '@/lib/state/workspace-provider';

/**
 * The morning workspace — *"which accounts should I work on today?"*
 *
 * **This is `/`.** It replaced an Overview page that promised an integration
 * capability a milestone away and showed three permanently-empty counters,
 * reviewed from first principles and retired at M12.3 (**D38**). A seller's
 * first screen should be their morning's work rather than a dashboard about
 * it — and none of the six customer journeys was ever *"give me a summary."*
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
export default function AttentionPage() {
  const { activeWorkspace, isLoading: workspacesLoading } = useWorkspaceContext();
  const { data, isLoading, isError } = useAccounts(activeWorkspace?.id ?? null);
  // Names arrive in a second request and the rows do not wait for them: the
  // score and the reason are what a seller triages on, and blocking the list
  // on a name would trade the decision for the label.
  const { data: identities, isLoading: namesLoading } = useAccountIdentities(
    activeWorkspace?.id ?? null,
    (data?.items ?? []).map((account) => account.account_id),
  );
  // The vocabulary, so a row can say *active evaluation* rather than
  // `active_evaluation`. A third request and a cheap one: it is a small
  // versioned artifact, held for the session, and it parallelises with the
  // other two rather than following them.
  const { data: catalog } = useSignalCatalog(activeWorkspace?.id ?? null);
  // Only so a row can say *yours* rather than *taken*. Never an authorization
  // decision — Casbin on the server is that, and always.
  const { data: session } = useSession();
  const viewerId = session?.user.id ?? null;
  // The other half of the workflow (R4-04). Fetched alongside rather than
  // behind a control: the section renders nothing when the page is empty, so
  // a reader who never dismisses never learns it exists.
  const { data: decided } = useDecidedAccounts(activeWorkspace?.id ?? null);
  // Their own identity request rather than a union with the list above: the
  // hook keys on the sorted ids, so folding them together would re-fetch every
  // open account's name each time somebody dismisses one. Empty until a
  // decision exists, and the hook asks nothing for an empty set.
  const { data: decidedIdentities } = useAccountIdentities(
    activeWorkspace?.id ?? null,
    (decided?.items ?? []).map((account) => account.account_id),
  );

  return (
    <div className="mx-auto flex max-w-4xl flex-col gap-6">
      <header>
        <h1 className="text-xl font-semibold text-content">Attention</h1>
        <p className="mt-1 text-sm text-content-muted">
          Accounts your evidence says are worth a look, most pressing first.
        </p>
      </header>

      {/* **A signed-in reader with no workspace rendered nothing at all**
          until M12.3: the query is disabled, so `isLoading`, `isError` and
          `data` were all falsy and every branch below was skipped (D36). It
          is the state every brand-new account is in, and a blank page is
          indistinguishable from a broken one. */}
      {!workspacesLoading && activeWorkspace === null ? <NoWorkspace /> : null}
      {isLoading ? <Loading /> : null}
      {isError ? <Unavailable /> : null}
      {data && data.items.length === 0 ? <Quiet /> : null}
      {data && data.items.length > 0 ? (
        <ol className="flex flex-col gap-2">
          {data.items.map((account) => (
            <li key={account.id}>
              <AccountRow
                account={account}
                identity={identities?.get(account.account_id)}
                namesLoading={namesLoading}
                hypothesis={
                  account.signal_type ? catalog?.get(account.signal_type) : undefined
                }
                viewerId={viewerId}
              />
            </li>
          ))}
        </ol>
      ) : null}

      {/* **Below the list, because that is where a reader finishes.** The
          question this answers — *wait, what did I just dismiss?* — is asked
          after working the list, not before; the same reasoning D41 used to
          put the sequence at the bottom of the brief. */}
      <DecidedAccounts
        accounts={decided?.items ?? []}
        identities={decidedIdentities}
        viewerId={viewerId}
      />
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
function AccountRow({
  account,
  identity,
  namesLoading,
  hypothesis,
  viewerId,
}: {
  account: AccountAttention;
  identity: AccountIdentity | undefined;
  namesLoading: boolean;
  /** The catalog's title for this row's leading hypothesis. */
  hypothesis: string | undefined;
  /** The signed-in reader, so a row they hold can say so. */
  viewerId: string | null;
}) {
  return (
    // No card-wide hover. **Only the account name opens the brief**, and a card
    // that lit up under the cursor anywhere would teach a reader the whole row
    // is clickable — then fail them everywhere but one word.
    <Card>
      <CardBody className="flex items-start gap-4 py-3.5">
        {/* **The account leads.** A seller scans names, not numbers — the
            number tells them the order, and the order is already the list's.
            A score competing with the name for weight makes every row equally
            loud, which is the same as no hierarchy at all. */}
        <div className="min-w-0 flex-1">
          <EntityName
            identity={identity}
            fallbackId={account.account_id}
            href={`/accounts/${account.account_id}`}
            isLoading={namesLoading}
          />
          <div className="mt-1 flex flex-wrap items-center gap-x-3 gap-y-1">
            <Hypothesis
              signalType={account.signal_type}
              posture={account.posture}
              title={hypothesis}
            />
            <ScoreMovement trend={account.trend} change={account.score_change} />
          </div>
        </div>

        <div className="flex shrink-0 items-center gap-3 pt-0.5">
          <div className="flex items-center gap-2">
            {/* **What the seller did, beside what the evidence says.** The
                one action Signora offers had no visible consequence on the
                surface a seller opens every morning (D40). */}
            <Ownership
              ownerId={account.owner_id}
              stage={account.stage}
              viewerId={viewerId}
            />
            <ContestedMark contested={account.contested} />
            <EvidenceHealth evidence={account.evidence} />
          </div>
          {/* Right-aligned and tabular so the column reads as a column: at a
              glance the eye follows the digits down the page without the
              layout shifting under a three-digit score. */}
          <div className="w-9 text-right">
            <AttentionScore score={account.score} />
          </div>
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
