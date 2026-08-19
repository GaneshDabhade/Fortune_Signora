'use client';

import Link from 'next/link';

import { CardFailure } from '@/components/home/card-failure';
import { useCardPhase, type CardPhase } from '@/lib/home/loading';

import type { ResearchRun } from '@/lib/api/types';
import { cn } from '@/lib/design/cn';
import { useAccountIdentities } from '@/lib/query/hooks';
import { useResearchRuns } from '@/lib/query/hooks/research-runs';
import { useSession } from '@/lib/auth/client';
import { useWorkspaceContext } from '@/lib/state/workspace-provider';

/**
 * 📁 **`card.agentqueue` and `card.agentruns`** ·
 * `Fortune Signora Home.dc.html` §04 registry.
 *
 * > 📁 ***"Signora worked overnight · `card.agentqueue` · SE · OP · Agent
 * > output awaiting a person. Nothing here has been sent or written."***
 * > 📁 ***"Agent runs · `card.agentruns` · OP · Scheduled and triggered runs,
 * > failures first."***
 * > **Both depend on `agents.runs`**, and that is why they share one read.
 *
 * ## 🔴 What `agents.runs` is, measured rather than assumed
 *
 * ⛔ **`action_batch` was the obvious answer and it is the wrong one.** Its
 * `proposed_by` is a required actor and 📁 every producer passes the acting
 * person — *"intelligence suggests; humans commit"* — so today's batches are
 * the bulk tag, assignment and segment edits somebody made on Companies.
 * **Rendering those under *Signora worked overnight* would file a person's own
 * work as the agent's.**
 *
 * ✅ **The research request IS a run**: `requested → running → completed /
 * nothing_to_research / failed`, with who asked, when, why it failed and how
 * much it read. 📁 **The design's own third row is this row** — *"Research on
 * Norvell finished · You requested it Tuesday · 9 sources · Open"*.
 *
 * ⚠️ **Its other two rows have no producer in this repository.** *"2 emails
 * drafted"* needs an agent that proposes a batch and *"renewal sweep
 * completed"* needs a scoring run that records itself; **neither exists, and
 * neither is invented here.** ✅ Both cards render the runs that exist — which
 * is what the design's own empty states are for.
 *
 * ## ⚡ Two cards, two rankings, one query
 *
 * 📁 The queue takes *"agent output awaiting a person"* — **runs with something
 * to read** — and the runs card takes *"failures first"* over **every** run.
 * ⛔ **The server ranks neither**: it returns the order the runs happened, so
 * one card's ranking cannot silently become the other's.
 */
export function AgentQueueCard() {
  const { runs, mine, names } = useRuns();
  /** 📁 §09's timed rules — no skeleton under 300ms, an error state over 8s. */
  const phase = useCardPhase(runs.isPending);

  if (runs.isError || phase === 'timeout') return failed(runs, 'home-agent-queue', phase);
  if (runs.isPending) return <QueueFrame>{skeleton(phase)}</QueueFrame>;

  const all = runs.data ?? [];
  /**
   * 📁 ***"Agent output awaiting a person."*** ⚡ **A completed run names an
   * artifact** — the domain's own invariant — **so a completed run is exactly a
   * run with something to read.**
   *
   * ⛔ **`nothing_to_research` is NOT here.** It finished and produced nothing
   * to open, so it is a run rather than output; 📁 the runs card shows it. ⛔
   * **Nor are failures** — a failure produced no output either, and 📁 *"nothing
   * here has been sent or written"* is a promise about output, not a place to
   * report errors.
   */
  const ready = all.filter((run) => run.status === 'completed').slice(0, 5);

  if (ready.length === 0) {
    /**
     * ⛔ **The two empty causes are NOT one empty state.** 📁 [P-A]: *"a batch
     * that is still running and one that failed to start must never render
     * alike"* — the same distinction here is **working** versus **never
     * asked**, and collapsing them would tell somebody nothing had happened
     * while Signora was mid-run.
     */
    const working = all.filter((run) => run.status === 'requested' || run.status === 'running');
    return (
      <QueueFrame>
        <p className="px-[18px] py-[15px] text-[12.5px] leading-[1.55] text-content-muted">
          {working.length > 0
            ? `Signora is researching ${working.length === 1 ? 'an account' : `${working.length} accounts`}. Nothing is ready to read yet.`
            : 'Signora has not been asked to research anything here yet.'}
        </p>
      </QueueFrame>
    );
  }

  return (
    <QueueFrame>
      {ready.map((run) => (
        <Row
          key={run.request_id}
          tone="pos"
          href={`/accounts/${run.account_id}`}
          title={`Research on ${names.get(run.account_id) ?? 'this account'} finished`}
          meta={[asked(run, mine), sources(run)].filter((part) => part !== null).join(' · ')}
          /** 📁 The drawn row's own word for research output. */
          action="Open"
        />
      ))}
    </QueueFrame>
  );
}

/**
 * 📁 ***"Agent runs · scheduled and triggered runs, failures first."***
 *
 * ⚡ **Every run, including the ones the queue leaves out**: a failure and a
 * run that found nothing are both things an operator is answerable for, and
 * neither is *output*.
 */
export function AgentRunsCard() {
  const { runs, mine, names } = useRuns();
  const phase = useCardPhase(runs.isPending);

  if (runs.isError || phase === 'timeout') return failed(runs, 'home-agent-runs', phase);
  if (runs.isPending) return <RunsFrame>{skeleton(phase)}</RunsFrame>;

  const all = runs.data ?? [];
  /**
   * 📁 ***"Failures first."*** ⚡ **A stable partition, not a sort** — within
   * each half the server's order (newest first) is preserved, so the ranking
   * adds the design's rule without discarding the one underneath it.
   */
  const ordered = [
    ...all.filter((run) => run.status === 'failed'),
    ...all.filter((run) => run.status !== 'failed'),
  ].slice(0, 5);

  if (ordered.length === 0) {
    return (
      <RunsFrame>
        <p className="px-[18px] py-[15px] text-[12.5px] leading-[1.55] text-content-muted">
          Signora has not been asked to research anything here yet.
        </p>
      </RunsFrame>
    );
  }

  return (
    <RunsFrame>
      {ordered.map((run) => (
        <Row
          key={run.request_id}
          tone={TONE[run.status]}
          href={`/accounts/${run.account_id}`}
          title={`${names.get(run.account_id) ?? 'This account'} — ${OUTCOME[run.status]}`}
          /**
           * ⛔ **The failure's own words, never a sentence composed here.** 📁
           * *"A failure with no reason is a state a customer can see and
           * nobody can act on."*
           */
          meta={[asked(run, mine), run.detail ?? sources(run)]
            .filter((part) => part !== null)
            .join(' · ')}
          /** 📁 The registry's primary action for this card, verbatim. */
          action="Open the run"
        />
      ))}
    </RunsFrame>
  );
}

/**
 * ⚡ **One read, shared.** 📁 Both cards depend on `agents.runs`; React Query
 * serves the second card from the first's cache because the key is the same.
 */
function useRuns() {
  const { activeWorkspace } = useWorkspaceContext();
  const workspaceId = activeWorkspace?.id ?? null;
  const { data: session } = useSession();

  const runs = useResearchRuns(workspaceId);
  const identities = useAccountIdentities(
    workspaceId,
    (runs.data ?? []).map((run) => run.account_id),
  );

  return {
    runs,
    /**
     * ⛔ **`null` until the session resolves**, so a row never claims *you*
     * asked for something before it knows who *you* are.
     */
    mine: session?.user.id ?? null,
    names: new Map(
      (identities.data === undefined ? [] : [...identities.data]).map(([id, identity]) => [
        id,
        identity.name,
      ]),
    ),
  };
}

/**
 * 📁 The drawn row's `meta` — *"You requested it Tuesday"*.
 *
 * ⛔ **A colleague is not named, and that is not a choice made here.** 📁
 * [ADR-0026](../../../docs/architecture/adr/0026-jwt-boundary-architecture.md):
 * Better Auth owns identity in the Next.js tier, so **the Python API has no
 * name to give** — `useWorkspaceMembers` says so in terms: *"identities, not
 * names… rendering a readable team list needs a decision this hook
 * deliberately does not make"* ([C-203](../../../docs/LANE_COORDINATION.md)).
 * ✅ **Saying *requested* without a name is honest; inventing one is not.**
 */
function asked(run: ResearchRun, mine: string | null): string {
  const day = when(run.requested_at);
  return mine !== null && run.requested_by === mine
    ? `You requested it ${day}`
    : `Requested ${day}`;
}

/** 📁 The drawn row's *"9 sources"*. **Absent unless the run read something.** */
function sources(run: ResearchRun): string | null {
  if (run.sources === null) return null;
  return `${run.sources} ${run.sources === 1 ? 'source' : 'sources'}`;
}

/**
 * 📁 **The status in the customer's words.**
 *
 * ⚠️ **`nothing_to_research` is not a failure** — the contract says so in
 * terms: *"it means the run finished and found nothing worth comparing, which
 * is a real answer on an account with little evidence and must never be shown
 * as an error."*
 */
const OUTCOME: Readonly<Record<ResearchRun['status'], string>> = Object.freeze({
  requested: 'queued',
  running: 'running',
  completed: 'finished',
  nothing_to_research: 'found nothing to compare',
  failed: 'failed',
});

/**
 * 📁 **The drawn dot's colour, per outcome.** Workflow Automation's run list
 * uses the same three: *"`--pos` completed · `--warn` paused · `--risk` failed
 * / reverted"*.
 */
const TONE: Readonly<Record<ResearchRun['status'], 'pos' | 'warn' | 'risk'>> = Object.freeze({
  requested: 'warn',
  running: 'warn',
  completed: 'pos',
  nothing_to_research: 'pos',
  failed: 'risk',
});

/**
 * 📁 **The drawn row**: *"a 7px dot · the title · its meta · the action,
 * right-aligned"*, wrapping rather than truncating at narrow widths.
 */
function Row({
  tone,
  href,
  title,
  meta,
  action,
}: {
  tone: 'pos' | 'warn' | 'risk';
  href: string;
  title: string;
  meta: string;
  action: string;
}) {
  return (
    <Link
      href={href}
      className="flex flex-wrap items-center gap-x-[11px] gap-y-2 border-b border-border-soft px-[18px] py-3 last:border-b-0 focus-visible:outline focus-visible:outline-2 focus-visible:-outline-offset-2 focus-visible:outline-accent"
    >
      {/* ♿ `aria-hidden`: the outcome is in the title beside it, so a reader
          hears it once rather than as an unnamed colour. */}
      <span
        aria-hidden
        className={cn(
          'h-[7px] w-[7px] flex-none rounded-full',
          tone === 'pos' ? 'bg-success' : tone === 'warn' ? 'bg-warning' : 'bg-danger',
        )}
      />
      <span className="min-w-[8.75rem] flex-1">
        <span className="block text-[12.5px] font-semibold leading-[1.4] text-content">
          {title}
        </span>
        <span className="mt-0.5 block text-[11.5px] text-content-subtle">{meta}</span>
      </span>
      <span className="flex-none text-[12px] font-semibold text-accent">{action}</span>
    </Link>
  );
}

/**
 * 📁 **Contract 13** — *"a card query failing after retries renders that card's
 * error inside its own footprint with the correlation ID; siblings are
 * unaffected."*
 *
 * ⚡ **Shared by both cards, because they share the read.** ⛔ **The promise
 * line does NOT appear over a failure**: *"nothing here was sent or written"*
 * is a claim about output Signora produced, and a card that could not read is
 * not in a position to make it.
 */
function failed(
  runs: { error: unknown; refetch: () => unknown; isFetching: boolean },
  testId: string,
  phase: CardPhase,
) {
  return (
    <CardFailure
      title="Signora could not read what its agents have been doing"
      description="No agent run has been lost or affected. Everything else on this page is unaffected."
      error={runs.error}
      onRetry={() => void runs.refetch()}
      /* ⛔ **Not `isFetching` on a timeout** — the original attempt is still in
         flight, and a permanently-loading button is a retry nobody can press. */
      retrying={runs.isFetching && phase !== 'timeout'}
      testId={testId}
    />
  );
}

/** 📁 **State 07** — *"cards skeletonised at declared footprints."* */
function skeleton(phase: CardPhase) {
  return (
    /* ⛔ **Empty for the first 300ms** — 📁 *"a placeholder shown and removed
       inside 300ms reads as a flicker."* ⚡ The frame keeps its footprint either
       way, so nothing reflows when the data lands. */
    <div aria-hidden className="space-y-3 px-[18px] py-[15px]">
      {phase === 'skeleton' ? (
        <>
          <div className="h-4 w-2/3 animate-pulse rounded bg-surface-sunken" />
          <div className="h-4 w-1/2 animate-pulse rounded bg-surface-sunken" />
        </>
      ) : null}
    </div>
  );
}

function QueueFrame({ children }: { children: React.ReactNode }) {
  return (
    <div
      data-testid="home-agent-queue"
      className="overflow-hidden rounded-xl border border-border-soft bg-surface shadow-e1"
    >
      <h2
        className="border-b border-border-soft px-[18px] py-[14px] text-label font-semibold text-content"
      >
        Signora worked overnight
      </h2>
      {children}
      {/**
       * 📁 **The design's closing line, verbatim, and it is not decoration.**
       * ⛔ *"Nothing here has been sent or written"* is the card's whole
       * promise, and it holds structurally: research reads and derives, and
       * 📁 `source.py` is *"read-only. `fetch` is the only verb."*
       */}
      <p className="px-[18px] py-3 text-[11.5px] leading-[1.5] text-content-subtle">
        Nothing here was sent or written. Agent output waits for a person.
      </p>
    </div>
  );
}

function RunsFrame({ children }: { children: React.ReactNode }) {
  return (
    <div
      data-testid="home-agent-runs"
      className="overflow-hidden rounded-xl border border-border-soft bg-surface shadow-e1"
    >
      <h2
        className="border-b border-border-soft px-[18px] py-[14px] text-label font-semibold text-content"
      >
        Agent runs
      </h2>
      {children}
    </div>
  );
}

/**
 * 📁 Entry §05's `meta` — *"Friday"*, *"Thursday"* — and the design's *"you
 * requested it Tuesday"*. **Shared with `card.recents`' rule**: a weekday
 * inside the last week, a date beyond it, because *"Friday"* eleven days later
 * names the wrong Friday.
 */
function when(iso: string): string {
  const at = new Date(iso);
  const days = Math.floor((Date.now() - at.getTime()) / 86_400_000);
  if (days <= 0) return 'today';
  if (days === 1) return 'yesterday';
  if (days < 7) return new Intl.DateTimeFormat(undefined, { weekday: 'long' }).format(at);
  return new Intl.DateTimeFormat(undefined, { day: 'numeric', month: 'short' }).format(at);
}
