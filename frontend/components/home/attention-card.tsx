'use client';

import Link from 'next/link';

import { cn } from '@/lib/design/cn';
import { HM_COPY_06 } from '@/lib/home/copy';
import type { AccountAttention } from '@/lib/api/types';
import { useAccounts } from '@/lib/query/hooks';
import { useAccountsCount } from '@/lib/query/hooks/accounts-count';
import { useWorkspaceContext } from '@/lib/state/workspace-provider';

/**
 * 📁 **`card.attention` — *"Needs you today"*** ·
 * `Fortune Signora Home.dc.html` §04 and §06.
 *
 * > 📁 ***"Up to five ordered items, each with a reason and a cost of ignoring
 * > it."*** · ***"Ranked by what it costs to ignore."***
 *
 * ## ⛔ Five, and the sixth is a link
 *
 * 📁 ***"Maximum five items. A sixth becomes 'See all 8 in Signals' — Home is a
 * starting point, not a queue."*** ⚡ **P-07 gives the reason**: a ranked list
 * with no ceiling is a queue, and Signals is the surface designed for triage.
 *
 * ## 🔴 State 05 and state 06b are different states, and this card decides between them
 *
 * 📁 §03 draws the distinction and contract item 4 makes it a merge condition:
 * ***"a single shared empty component is a contract violation."***
 *
 * | | Test | Reads |
 * |---|---|---|
 * | **06b `no-results`** | records > 0 **and** attention == 0 | ✅ **a success state** — `HM-COPY-06` |
 * | **05 `no-business-data`** | records == 0 | ⚠️ **a setup condition** — 📁 owned by the STRIP, not this card |
 *
 * ⚠️ **State 05's copy names the source that returned nothing**, which is a fact
 * about integrations rather than about attention — 📁 so this card renders the
 * *no-results* half and says *"Signora has no records yet"* for the other,
 * leaving the source name to the surface that knows it.
 *
 * ## ⚠️ Every item carries a reason, and Signora will not invent one
 *
 * 📁 P-08: *"Every attention item carries a reason. And a cost of ignoring it. A
 * ranked list with no stated reason is a list people learn to scroll past."*
 *
 * ⛔ **The design's example reasons are prose a model wrote** — *"In 412
 * comparable deals this pattern cost 23 days"* — **and nothing here produces
 * that.** ⚡ **What the contract does publish is the FACT each row rests on**:
 * the signal type, whether the reading is contested, how long since anything
 * happened. **So the reason is the fact, stated plainly, and the cost is the one
 * the contract can support — elapsed time.** 📁 [C-1529](../../../docs/LANE_COORDINATION.md)
 * carries the gap between a stated fact and the design's reasoned sentence.
 */
export function AttentionCard() {
  const { activeWorkspace } = useWorkspaceContext();
  const workspaceId = activeWorkspace?.id ?? null;
  const accounts = useAccounts(workspaceId);
  const count = useAccountsCount(workspaceId);

  /** 📁 §09 — *"each skeleton uses the card's declared height."* */
  if (accounts.isPending) {
    return (
      <Frame>
        <div role="status" className="flex flex-col gap-3 p-[18px]">
          {[0, 1, 2].map((i) => (
            <div key={i} className="h-[46px] animate-pulse rounded-lg bg-surface-sunken" />
          ))}
          <span className="sr-only">Loading what needs you</span>
        </div>
      </Frame>
    );
  }

  /**
   * 📁 **State 08 — the card's error stays inside the card's footprint**, with a
   * correlation id. ⛔ *"Siblings are unaffected."*
   */
  if (accounts.isError) {
    return (
      <Frame>
        <div className="p-[18px]">
          <p role="alert" className="text-sm font-semibold text-content">
            What needs you could not be loaded
          </p>
          <p className="mt-1.5 text-xs leading-[1.5] text-content-muted">
            Everything else on this page is unaffected.
          </p>
          <button
            type="button"
            onClick={() => void accounts.refetch()}
            className="mt-3 inline-flex h-control-sm items-center rounded-md border border-border px-3 text-xs font-semibold text-content transition-colors hover:border-accent hover:text-accent focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-accent"
          >
            Retry
          </button>
        </div>
      </Frame>
    );
  }

  const rows = accounts.data?.items ?? [];
  const records = count.data?.total ?? null;
  const shown = rows.slice(0, MAX);

  return (
    <Frame>
      <header className="flex flex-wrap items-center gap-2.5 border-b border-border-soft px-[18px] py-[15px]">
        <h2 className="text-md font-semibold tracking-[-0.014em] text-content">Needs you today</h2>
        <span className="rounded-sm bg-surface-sunken px-2 py-px text-2xs font-semibold tabular-nums text-content-subtle">
          {rows.length}
        </span>
        {/* 📁 The design's own subtitle. */}
        <span className="ml-auto text-[11.5px] text-content-subtle">
          Ranked by what it costs to ignore
        </span>
      </header>

      {rows.length === 0 ? (
        <div className="p-[18px]">
          {records === 0 ? (
            /* ⚠️ **State 05's half.** ⛔ Not HM-COPY-06 — records are absent, so
               *"nothing needs you"* would be a success message about a workspace
               that has nothing in it. */
            <p className="text-[13px] leading-[1.6] text-content-muted">
              Signora has no records to work from yet. Connect a source and it starts reading
              straight away.
            </p>
          ) : (
            /* ✅ **State 06b, `HM-COPY-06` verbatim.** 📁 A success state, and it
               names what was checked and when — the design's own credibility test. */
            <p className="text-[13px] leading-[1.6] text-content-muted">
              {HM_COPY_06(records ?? 0, rows.length, checkedAt())}
            </p>
          )}
        </div>
      ) : (
        <>
          {shown.map((row) => (
            <Item key={row.id} row={row} />
          ))}
          {/* 📁 ***"A sixth becomes 'See all 8 in Signals'."*** */}
          {rows.length > MAX ? (
            <Link
              href="/signals"
              className="block border-b border-border-soft px-[18px] py-3 text-[12.5px] font-semibold text-accent hover:underline focus-visible:outline focus-visible:outline-2 focus-visible:-outline-offset-2 focus-visible:outline-accent"
            >
              See all {rows.length} in Signals
            </Link>
          ) : null}
          <p className="px-[18px] py-[13px] text-[11.5px] leading-[1.5] text-content-subtle">
            Home is a starting point, not a queue.
          </p>
        </>
      )}
    </Frame>
  );
}

/** 📁 ***"Maximum five items."*** */
const MAX = 5;

/**
 * 📁 **One row** — *"left rule, account, tag, value, the reason, one action."*
 *
 * ♿ **Severity uses the left rule, the tag word AND the tint together** — 📁
 * 1.4.1: *"Removing colour leaves the tag and the order intact."*
 */
function Item({ row }: { row: AccountAttention }) {
  const tone = row.contested ? 'risk' : row.evidence === 'stale' ? 'warn' : 'pos';

  return (
    <div
      className={cn(
        'flex flex-wrap items-start gap-x-3 gap-y-2.5 border-b border-border-soft px-[18px] py-[15px] border-l-2',
        tone === 'risk' ? 'border-l-danger' : tone === 'warn' ? 'border-l-warning' : 'border-l-success',
      )}
    >
      <div className="min-w-[13rem] flex-1">
        <div className="flex flex-wrap items-center gap-x-2.5 gap-y-1.5">
          <span className="text-[13.5px] font-semibold text-content">
            {row.account_id.slice(0, 8)}
          </span>
          <span
            className={cn(
              'rounded-sm px-2 py-px text-2xs font-semibold',
              tone === 'risk'
                ? 'bg-danger-subtle text-danger'
                : tone === 'warn'
                  ? 'bg-warning-subtle text-warning'
                  : 'bg-success-subtle text-success',
            )}
          >
            {row.contested ? 'Contested' : row.evidence === 'stale' ? 'Reading is stale' : 'Open'}
          </span>
          {row.score === null ? null : (
            <span className="text-[11.5px] tabular-nums text-content-subtle">
              Score {row.score}
            </span>
          )}
        </div>
        {/* 📁 **The reason.** ⛔ A fact, never a diagnosis — 📁 `AccountAttention`'s
            own rule: *"Signora records workflow decisions and cannot see a call,
            an email or a meeting, so it must not say an account is neglected."* */}
        <p className="mt-1.5 text-[12.5px] leading-[1.55] text-content-muted">{reason(row)}</p>
      </div>
      <Link
        href={`/accounts/${row.account_id}`}
        className="inline-flex h-[31px] flex-none items-center rounded-md border border-border px-3 text-[12.5px] font-semibold text-content transition-colors hover:border-accent hover:text-accent focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-accent"
      >
        Open the record
      </Link>
    </div>
  );
}

/**
 * ⛔ **What the contract can support, and nothing beyond it.**
 *
 * 📁 The design's reasons cite comparable-deal counts a model produced. ⚡ **These
 * state the fact the row rests on and how long it has stood** — which is a
 * reason a reader can check against the record, and 📁 the *"cost of ignoring"*
 * this product can honestly express.
 */
function reason(row: AccountAttention): string {
  const since = days(row.since);
  if (row.contested) {
    return `Your sources disagree about this account, and nothing has resolved it in ${since}.`;
  }
  if (row.evidence === 'stale') {
    return `The evidence behind this reading has gone stale. Nothing new in ${since}.`;
  }
  if (row.trend === 'falling') {
    return `The score has been falling, and nothing has been recorded against it in ${since}.`;
  }
  return `Nothing has been recorded against this account in ${since}.`;
}

function days(since: string): string {
  const ms = Date.now() - new Date(since).getTime();
  const d = Math.max(0, Math.floor(ms / 86_400_000));
  if (d === 0) return 'today';
  return `${d} ${d === 1 ? 'day' : 'days'}`;
}

/** 📁 The design's *"at 07:00"*. ⚡ The time the read landed, in the reader's zone. */
function checkedAt(): string {
  return new Intl.DateTimeFormat(undefined, { hour: '2-digit', minute: '2-digit' }).format(
    new Date(),
  );
}

/** 📁 *"Card 14px --e1"* — the design's own card, from §10's inventory. */
function Frame({ children }: { children: React.ReactNode }) {
  return (
    <div className="overflow-hidden rounded-lg border border-border-soft bg-surface shadow-sm">
      {children}
    </div>
  );
}
