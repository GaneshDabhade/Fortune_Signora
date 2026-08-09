'use client';

import { LineChart } from 'lucide-react';
import { useMemo } from 'react';
import Link from 'next/link';
import { useSearchParams } from 'next/navigation';

import {
  AttentionScore,
  STAGE_MARK,
  ContestedMark,
  EvidenceHealth,
  Hypothesis,
  HeldSince,
  Ownership,
  PostureMark,
  ScoreMovement,
} from '@/components/intelligence/attention';
import { DecidedAccounts } from '@/components/intelligence/decided';
import { StatedAbsence } from '@/components/feedback/stated-absence';
import { NeedsIdentity } from '@/components/intelligence/needs-identity';
import { NothingRaises, TriageStrip } from '@/components/intelligence/triage';
import { EntityName } from '@/components/intelligence/entity-name';
import { NoWorkspace } from '@/components/workspace/no-workspace';
import { Card, CardBody, EmptyState, SkeletonText } from '@/components/ui';
import type { AccountAttention, AccountIdentity, SignalTypeName, Stage } from '@/lib/api/types';
import {
  useAccountIdentities,
  useAccounts,
  useDecidedAccounts,
  useSignalCatalog,
} from '@/lib/query/hooks';
import { useSession } from '@/lib/auth/client';
import { useTargetAccounts } from '@/lib/query/hooks/commercial';
import { useWorkspaceMembers } from '@/lib/query/hooks/team';
import {
  SCOPE_WORDS,
  scopeFrom,
  withScope,
  type OwnerScope,
} from '@/lib/state/owner-scope';
import { STANDING_WORDS, standingFrom, withStanding } from '@/lib/state/standing';
import { raisedFrom, raises, triage } from '@/lib/state/triage';
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
  // **From the URL, so the view survives a refresh, browser back and a second
  // tab** — and so it can travel on the account link, which is what keeps the
  // brief's *next* inside the list a seller was working (D41).
  const params = useSearchParams();
  const scope = scopeFrom(params.get('owner'));
  // **Which question the list is narrowed to**, in the URL beside the scope and
  // for the same three reasons: a refresh, a browser back and a second tab.
  const raised = raisedFrom(params.get('raises'));
  // **Where does everything stand** — C-229's answer B, in the URL beside the
  // scope and for the same three reasons. A view over the list already loaded,
  // never a second read.
  const standing = standingFrom(params.get('by'));
  const { data, isLoading, isError } = useAccounts(activeWorkspace?.id ?? null, scope);
  // Names arrive in a second request and the rows do not wait for them: the
  // score and the reason are what a seller triages on, and blocking the list
  // on a name would trade the decision for the label.
  const {
    data: identities,
    isLoading: namesLoading,
    isError: namesFailed,
  } = useAccountIdentities(
    activeWorkspace?.id ?? null,
    (data?.items ?? []).map((account) => account.account_id),
  );
  // The vocabulary, so a row can say *active evaluation* rather than
  // `active_evaluation`. A third request and a cheap one: it is a small
  // versioned artifact, held for the session, and it parallelises with the
  // other two rather than following them.
  const { data: catalog } = useSignalCatalog(activeWorkspace?.id ?? null);
  // **Only to explain an empty list.** Every seller may read the declaration
  // (`policy.csv` grants `member` read on `target_account`), so this asks a
  // question the caller is always permitted to ask.
  const { data: targets } = useTargetAccounts(activeWorkspace?.id ?? null);
  // Only so a row can say *yours* rather than *taken*. Never an authorization
  // decision — Casbin on the server is that, and always.
  const { data: session } = useSession();
  const viewerId = session?.user.id ?? null;
  // **The roster, so a held account says who holds it.** Same query and cache
  // key as the Team page and the brief, so this costs no request — and
  // TM-01's `member_email` is what makes a name renderable at all.
  const { data: roster } = useWorkspaceMembers(activeWorkspace?.id ?? null);
  const owners = useMemo(
    () =>
      new Map(
        (roster?.items ?? []).flatMap((one) =>
          one.member_email ? [[one.user_id, one.member_email] as const] : [],
        ),
      ),
    [roster],
  );
  // The other half of the workflow (R4-04). Fetched alongside rather than
  // behind a control: the section renders nothing when the page is empty, so
  // a reader who never dismisses never learns it exists.
  const { data: decided } = useDecidedAccounts(activeWorkspace?.id ?? null);
  // Their own identity request rather than a union with the list above: the
  // hook keys on the sorted ids, so folding them together would re-fetch every
  // open account's name each time somebody dismisses one. Empty until a
  // decision exists, and the hook asks nothing for an empty set.
  // **Filtered here rather than re-fetched.** The question is a view over the
  // list a seller already has; asking the server again would make a filter cost
  // a round trip and could return a differently-ordered list mid-triage.
  const filtered = useMemo(
    () =>
      raised === null
        ? (data?.items ?? [])
        : (data?.items ?? []).filter((account) => raises(account, raised)),
    [data, raised],
  );

  /**
   * **A6 — unnamed records leave the working list** ([C-321](../../../docs/LANE_COORDINATION.md),
   * ruled 2026-08-05: *appear yes · working list no · score yes · workable
   * never*).
   *
   * **The partition runs only once names have actually arrived**, and that
   * guard is the whole risk in this change rather than a defensive habit. An
   * identity request in flight, or one that failed, makes every account look
   * unnamed — so partitioning eagerly would move the entire working list into
   * *Needs identity* on first paint, and leave it there permanently if the
   * request errored. **A seller would open Signora to an empty call list and a
   * queue of everything**, which is a worse product than the one this fixes.
   *
   * So the rule is: **while names are loading or their read failed, nothing
   * moves.** The list behaves exactly as it did before A6, which is the state
   * this page has shipped in for three milestones.
   */
  const partition = !namesLoading && !namesFailed && identities !== undefined;
  const named = (account: AccountAttention) =>
    !partition || (identities?.get(account.account_id)?.name ?? null) !== null;
  const shown = useMemo(() => filtered.filter(named), [filtered, partition, identities]);
  const unnamed = useMemo(
    () => filtered.filter((account) => !named(account)),
    [filtered, partition, identities],
  );

  const { data: decidedIdentities } = useAccountIdentities(
    activeWorkspace?.id ?? null,
    (decided?.items ?? []).map((account) => account.account_id),
  );

  return (
    <div className="mx-auto flex max-w-4xl flex-col gap-6">
      <header>
        <h1 className="text-xl font-semibold text-content">Attention</h1>
        {/* **The subtitle describes what is on the screen, not what the screen
            is for.** Filtered to one question it was claiming the whole list,
            which is the same defect class as a dashboard describing the
            previous milestone — a sentence a reader has no way to check
            against anything but itself. */}
        <p className="mt-1 text-sm text-content-muted">
          {raised === null
            ? 'Accounts your evidence says are worth a look, most pressing first.'
            : 'Accounts raising one question, in the same order.'}
        </p>
      </header>

      {/*
        ⚡ **The Signal Center's door** — [TASK-439](../../../docs/BACKLOG.md).
        📁 **[D38](../../../docs/architecture/39-product-review-findings.md)
        removed these screens from the rail by name** — *"adding one back is a
        claim that needs defending"* — so the entrance is a link from the
        surface that answers the neighbouring question. **This is the
        recommendation this lane offered on
        [C-229](../../../docs/LANE_COORDINATION.md) and did not implement until
        that item closed.** ⛔ **Not a navigation entry**, and the rail belongs
        to [TASK-1408](../../../docs/BACKLOG.md), not to a feature row.

        🔴 **At PAGE level, and the first draft was not.** It sat inside the
        populated branch, so a workspace with an empty attention list had NO
        DOOR AT ALL — **and that is exactly the reader most likely to want
        one.** ⚠️ **`reachability.py` passed it**, because a static scan sees a
        link in the source and cannot see which branch renders it; **the headed
        walk is what found it** ([B-149](../../../docs/BUGS.md)).
      */}
      <p className="text-sm text-content-muted">
        <Link
          href="/signals"
          className="rounded font-medium text-accent underline decoration-border underline-offset-4 transition-colors hover:decoration-accent focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent"
        >
          Review every signal Signora has raised
        </Link>
      </p>

      {/* **A signed-in reader with no workspace rendered nothing at all**
          until M12.3: the query is disabled, so `isLoading`, `isError` and
          `data` were all falsy and every branch below was skipped (D36). It
          is the state every brand-new account is in, and a blank page is
          indistinguishable from a broken one. */}
      {!workspacesLoading && activeWorkspace === null ? <NoWorkspace /> : null}

      {/* **Three views, as links.** A link is what makes the choice
          bookmarkable, openable in a new tab and reachable by keyboard without
          a widget — and the scope has to live in the URL anyway, so the brief
          can read the list a seller was working (D41).

          **Only once there is an organization**: a filter above an empty
          screen is a control over nothing. */}
      {activeWorkspace !== null ? (
        <div className="flex flex-wrap items-center justify-between gap-2">
          <nav aria-label="Whose work" className="flex items-center gap-1">
            {(['all', 'mine', 'unassigned'] as const).map((one) => (
              <Link
                key={one}
                // **Carries the arrangement.** Changing whose work you are
                // looking at must not silently rearrange the list — that is
                // two changes from one click, and the seller made one.
                href={withStanding('/', one, standing)}
                aria-current={one === scope ? 'page' : undefined}
                className={
                  one === scope
                    ? 'rounded bg-accent-subtle px-2.5 py-1 text-sm font-medium text-accent'
                    : 'rounded px-2.5 py-1 text-sm text-content-muted transition-colors hover:bg-surface-sunken hover:text-content'
                }
              >
                {SCOPE_WORDS[one]}
              </Link>
            ))}
          </nav>
          {/* **C-229's answer B, and deliberately a view rather than a
              destination.** Two links, beside the scope, over the list already
              on screen — no fourth sidebar entry, and no second copy of the
              list (D38). */}
          <nav aria-label="How the list is arranged" className="flex items-center gap-1">
            {(['flat', 'stage'] as const).map((one) => (
              <Link
                key={one}
                href={withStanding('/', scope, one)}
                aria-current={one === standing ? 'page' : undefined}
                className={
                  one === standing
                    ? 'rounded bg-accent-subtle px-2.5 py-1 text-sm font-medium text-accent'
                    : 'rounded px-2.5 py-1 text-sm text-content-muted transition-colors hover:bg-surface-sunken hover:text-content'
                }
              >
                {STANDING_WORDS[one]}
              </Link>
            ))}
          </nav>
        </div>
      ) : null}
      {isLoading ? <Loading /> : null}
      {isError ? <Unavailable /> : null}
      {/* `undefined` while the declaration is still loading, which keeps the
          established wording rather than guessing — announcing *"nobody has
          told Signora anything"* to a workspace that has is the confident
          wrong answer this page already refuses elsewhere. */}
      {/* **Above the list, and absent when the list raises nothing.** A count a
          seller cannot act on is a statistic; each line here narrows the list
          below it, which is a way of working rather than a dashboard. */}
      {data && data.items.length > 0 ? (
        <TriageStrip
          groups={triage(data.items)}
          active={raised}
          scope={scope}
          identities={identities}
        />
      ) : null}

      {data && data.items.length === 0 ? (
        <Quiet
          scope={scope}
          declared={targets === undefined ? undefined : targets.version > 0}
        />
      ) : null}
      {/* **A question nobody raises any more.** Reachable from a shared link, a
          bookmark, or browser-back after the evidence moved: the strip
          correctly hides a question with nothing under it, `Quiet` does not
          fire because the *unfiltered* list is not empty, and the list below
          renders no rows at all. **A page that renders nothing is
          indistinguishable from a broken one** (D36) — so it says so, and
          offers the way back. */}
      {data && data.items.length > 0 && shown.length === 0 && raised !== null ? (
        <NothingRaises raised={raised} scope={scope} />
      ) : null}
      {data && shown.length > 0 ? (
        standing === 'stage' ? (
          <ByStage
            accounts={shown}
            identities={identities}
            namesLoading={namesLoading}
            catalog={catalog}
            viewerId={viewerId}
            owners={owners}
            scope={scope}
          />
        ) : (
          <ol className="flex flex-col gap-2">
            {shown.map((account) => (
              <li key={account.id}>
                <AccountRow
                  account={account}
                  identity={identities?.get(account.account_id)}
                  namesLoading={namesLoading}
                  hypothesis={
                    account.signal_type ? catalog?.get(account.signal_type) : undefined
                  }
                  viewerId={viewerId}
                  owners={owners}
                  scope={scope}
                />
              </li>
            ))}
          </ol>
        )
      ) : null}

      {/* **Below the working list and above what was decided** (A6). This is
          live intelligence a seller cannot act on; the section below is a
          record of what they already did. Both are off the call list, and they
          are off it for opposite reasons — one has nobody to call, the other
          has already been answered. */}
      <NeedsIdentity accounts={unnamed} identities={identities} />

      {/* **Below the list, because that is where a reader finishes.** The
          question this answers — *wait, what did I just dismiss?* — is asked
          after working the list, not before; the same reasoning D41 used to
          put the sequence at the bottom of the brief. */}
      <DecidedAccounts
        accounts={decided?.items ?? []}
        identities={decidedIdentities}
        viewerId={viewerId}
        people={owners}
      />
    </div>
  );
}

/**
 * The attention list, grouped by where each pursuit stands.
 *
 * **[C-229](../../../../docs/LANE_COORDINATION.md)'s answer B.** Not a screen
 * and not a second read — the same `shown` array the flat list renders, over
 * `AccountRow`, arranged by `stage`.
 *
 * ### Every stage present is shown, and empty ones are not invented
 *
 * ⛔ **A group is rendered because the list has accounts in it**, never because
 * the `Stage` union has five members. **A stage with no accounts is not the
 * same claim as a stage a seller has not reached**, and drawing five empty
 * headings would assert the second while meaning neither.
 *
 * **The order is the pipeline's**, not the data's: a seller reads *tracking →
 * being worked → decided*, and sorting groups by size would rearrange the page
 * under them every time an account moved.
 */
function ByStage({
  accounts,
  identities,
  namesLoading,
  catalog,
  viewerId,
  owners,
  scope,
}: {
  accounts: AccountAttention[];
  identities: ReadonlyMap<string, AccountIdentity> | undefined;
  namesLoading: boolean;
  catalog: ReadonlyMap<string, SignalTypeName> | undefined;
  viewerId: string | null;
  owners?: ReadonlyMap<string, string> | undefined;
  scope: OwnerScope;
}) {
  // The pipeline's order, stated once. `STAGE_MARK` supplies the words — a
  // second table here would be a second vocabulary.
  const ORDER: readonly Stage[] = [
    'tracking',
    'engaged',
    'closed_won',
    'closed_lost',
    'dismissed',
  ];

  const groups = ORDER.map((stage) => ({
    stage,
    items: accounts.filter((account) => account.stage === stage),
  })).filter((group) => group.items.length > 0);

  return (
    <div className="flex flex-col gap-6">
      {groups.map((group) => (
        <section key={group.stage} className="flex flex-col gap-2">
          <h2 className="flex items-baseline gap-2 text-sm font-semibold text-content">
            {STAGE_MARK[group.stage]}
            {/* The count is what makes this answer *where does everything
                stand* rather than merely reordering the page. */}
            <span className="text-xs font-normal text-content-subtle">
              {group.items.length}
            </span>
          </h2>
          <ol className="flex flex-col gap-2">
            {group.items.map((account) => (
              <li key={account.id}>
                <AccountRow
                  account={account}
                  identity={identities?.get(account.account_id)}
                  namesLoading={namesLoading}
                  hypothesis={
                    account.signal_type ? catalog?.get(account.signal_type) : undefined
                  }
                  viewerId={viewerId}
                  owners={owners}
                  scope={scope}
                />
              </li>
            ))}
          </ol>
        </section>
      ))}

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
  scope,
  identity,
  namesLoading,
  hypothesis,
  viewerId,
  owners,
}: {
  account: AccountAttention;
  identity: AccountIdentity | undefined;
  namesLoading: boolean;
  /** The catalog's entry for this row's leading hypothesis — its title, and
   * why the type matters. **The whole entry rather than the title alone**
   * (C-204): the explanation existed, reviewed, and reached no screen. */
  hypothesis: SignalTypeName | undefined;
  /** The signed-in reader, so a row they hold can say so. */
  viewerId: string | null;
  /** Who each owner is, by id. **A map rather than a list**: a row asks about
   * one person, and handing it everybody would make every row scan the team.
   * Absent while the roster loads — the badge then says *Taken*, which is what
   * it said before this existed. */
  owners?: ReadonlyMap<string, string> | undefined;
  /** The view this row was reached from, so opening it does not lose it. */
  scope: OwnerScope;
}) {
  return (
    // No card-wide hover. **Only the account name opens the brief**, and a card
    // that lit up under the cursor anywhere would teach a reader the whole row
    // is clickable — then fail them everywhere but one word.
    <Card>
      {/* **Two rows on a phone, one on a laptop.** The block on the right is
          `shrink-0` — four badges and a score, roughly 180px — and at 320px it
          takes more than half the row, squeezing the account name to a few
          characters. **The name leading is the whole hierarchy of this row**
          (below), so the fix is to give it the full width and drop the rest
          onto a second line rather than to shrink either. */}
      <CardBody className="flex flex-col gap-2 py-3.5 sm:flex-row sm:items-start sm:gap-4">
        {/* **The account leads.** A seller scans names, not numbers — the
            number tells them the order, and the order is already the list's.
            A score competing with the name for weight makes every row equally
            loud, which is the same as no hierarchy at all. */}
        <div className="min-w-0 flex-1">
          <EntityName
            identity={identity}
            fallbackId={account.account_id}
            // **Carries the view.** The brief reads the same query to offer
            // *next* (D41); without this a seller filtered to their own work
            // would be handed somebody else's account and dropped out of the
            // list they were working.
            href={withScope(`/accounts/${account.account_id}`, scope)}
            isLoading={namesLoading}
          />
          <div className="mt-1 flex flex-wrap items-center gap-x-3 gap-y-1">
            <Hypothesis signalType={account.signal_type} definition={hypothesis} />
            <ScoreMovement trend={account.trend} change={account.score_change} />
            {/* **Beside what the evidence says, not among the badges.** This
                is what the *seller* did and when; the badges to the right are
                what Signora thinks. Keeping the two apart is why the row is
                still scannable with a fourth fact on it. */}
            <HeldSince stage={account.stage} since={account.since} />
          </div>
        </div>

        {/* `justify-between` only while stacked: the badges stay left and the
            score stays right, so **the score is still the rightmost thing on
            the row** at either width and the column property below survives
            the reflow. */}
        <div className="flex shrink-0 items-center justify-between gap-3 sm:justify-start sm:pt-0.5">
          <div className="flex items-center gap-2">
            {/* **What the seller did, beside what the evidence says.** The
                one action Signora offers had no visible consequence on the
                surface a seller opens every morning (D40). */}
            <Ownership
              ownerId={account.owner_id}
              ownerName={owners?.get(account.owner_id ?? '')}
              stage={account.stage}
              viewerId={viewerId}
            />
            <ContestedMark contested={account.contested} />
            <EvidenceHealth evidence={account.evidence} />
            {/* **Last in the lane, so it is the thing next to the number.**
                The confusion this exists to end is with a *score* — a
                contraction risk ranks beside the weakest opportunities and
                means the opposite of one — so the correction belongs where the
                eye lands after the digits, not in the running text on the
                left. */}
            <PostureMark posture={account.posture} />
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
/**
 * The list is empty, and **why** it is empty.
 *
 * **One sentence used to cover two very different situations.** *"Nothing
 * needs your attention"* is true of a workspace Signora has been watching for
 * weeks and found nothing hot in today. It is **not** true of a workspace that
 * has never told Signora which companies to watch — there, the product was
 * reporting an empty *result* where the truth was an empty *input*, and a new
 * customer reading it would reasonably conclude Signora had looked.
 *
 * **The product already knows which it is**: a target account list at version
 * 0 has never been declared. Asking the customer to work that out from an
 * empty screen is exactly the effort this surface exists to remove.
 *
 * **It says what is true and stops there.** No button, no *"get started"*, no
 * promise about what happens after declaring — the guided first run is
 * [C-007](../../../docs/LANE_COORDINATION.md) and is deliberately not
 * scheduled, and a call to action here would answer part of it by accident.
 * An owner already has Settings in the navigation; a member cannot declare
 * one, so a control offering it would be a control they cannot use.
 */
function Quiet({
  scope,
  declared,
}: {
  scope: OwnerScope;
  declared: boolean | undefined;
}) {
  // **An empty *view* is not an empty workspace, and LO-03 made the two look
  // identical.** Filtered to *Mine* while holding nothing, a seller was told
  // *"Nothing needs your attention"* — which may be false twenty times over,
  // and is exactly the confident wrong answer this page refuses when the
  // target declaration has not loaded. The filter is the reason the list is
  // empty, so the filter is what the sentence has to be about.
  //
  // **And it offers the way back.** A dead end a reader arrived at by
  // clicking is the one kind this surface should never leave them in.
  if (scope !== 'all') {
    return (
      <EmptyState
        icon={LineChart}
        title={
          scope === 'mine'
            ? 'You are not working any accounts'
            : 'Every account here has somebody on it'
        }
        description={
          scope === 'mine'
            ? 'Nothing on your list is held by you. Other accounts may still need attention — this view is showing only yours.'
            : 'Nobody has left an account unclaimed. This view is showing only accounts nobody has taken on.'
        }
        action={<Link href="/">Show everything</Link>}
      />
    );
  }

  if (declared === false) {
    return (
      <EmptyState
        icon={LineChart}
        title="Signora does not know which companies to watch yet"
        description="Your accounts appear here once you tell Signora which companies matter to you. Until then there is nothing for it to look at — this list is empty because it has not been asked, not because it found nothing."
      />
    );
  }

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
    <StatedAbsence as="page" icon={LineChart} subject="your accounts" />
  );
}
