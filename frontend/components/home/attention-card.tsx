'use client';

import Link from 'next/link';

import { ApiError } from '@/lib/api/client';
import type { Money, Posture, QueueEntry, SignalTypeName } from '@/lib/api/types';
import { formatMoney } from '@/lib/accounts/table';
import { cn } from '@/lib/design/cn';
import { HM_COPY_06 } from '@/lib/home/copy';
import { useAccountIdentities, useSignalCatalog } from '@/lib/query/hooks';
import { useAccountsCount } from '@/lib/query/hooks/accounts-count';
import { usePipelineHealth } from '@/lib/query/hooks/commercial';
import { useAccountCommercials, useScoringModel } from '@/lib/query/hooks/scoring';
import { useWorkspaceTriage } from '@/lib/query/hooks/triage';
import { useWorkspaceContext } from '@/lib/state/workspace-provider';

/**
 * 📁 **`card.attention` — *"Needs you today"*** ·
 * `Fortune Signora Home.dc.html` §04 and §06.
 *
 * > 📁 ***"Up to five ordered items, each with a reason and a cost of ignoring
 * > it."*** · ***"Ranked by what it costs to ignore."***
 *
 * ## 🔴 The registry's dependency is `signals + deals`, and this card now reads exactly that
 *
 * ⚠️ **This card was built on `AccountAttention`** — `GET /accounts`, the
 * Opportunity Engine's ranked open work — **and the product owner ruled that
 * out of Home on 2026-08-17.** ⛔ **The endpoint itself is untouched**: Account
 * 360, Companies, Triage and the Intelligence surfaces read it and it is
 * independently authoritative for them. **Home simply no longer depends on it.**
 *
 * ⚡ **What replaced it is what the registry always named**, composed at the
 * frontend edge under 📁 **U-04's interim ruling** — *"composed client-side from
 * separate signal and deal queries… the order must be seeded deterministically
 * so a refresh does not reshuffle."*
 *
 * | Half | Read | What it supplies |
 * |---|---|---|
 * | **signals** | `GET /triage?state=open` | the row, and **`rationale` — the reason, authored per signal** |
 * | | `GET /signal-catalog` | the tag word, from the one place a type is named |
 * | | `GET /scoring-model` | **posture → severity**, from the module that owns the judgement |
 * | **deals** | `GET /account-commercials` | **Open ACV — the design's `$2.11M`** |
 * | | `GET /account-identities` | the account's name |
 *
 * ⚡ **The old row could not name the company.** It rendered
 * `account_id.slice(0, 8)` — eight characters of a UUID where the design shows
 * *"Corrigan Health"* — because the Opportunity Engine is forbidden from
 * reaching entity names. **The identity batch is the composition that fixes it.**
 *
 * ## ⛔ Deterministic order, and it is the server's
 *
 * 📁 The queue is keyset-paged on `(occurred_at, id)` — **newest first, and
 * stable across a refresh**, which is precisely what U-04 requires of a
 * client-composed list. ⛔ **Nothing here re-sorts**: a browser ranking would be
 * a second ranking, free to disagree with the one the platform computed.
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
 * ## ⚠️ Every item carries a reason, and Signora does not invent one
 *
 * 📁 P-08: *"Every attention item carries a reason. And a cost of ignoring it."*
 *
 * ✅ **`rationale` is that reason and it is real** — 📁 the contract's own words:
 * *"why this matters HERE, and what it rests on… **per signal, not per type**:
 * the catalog's `why_it_matters` is a fact about the TYPE, so rendering that as
 * the summary would put the same sentence under every row."* ⚠️ **The design's
 * examples additionally cite a comparable-deal population** — *"in 412
 * comparable deals this pattern cost 23 days"* — **which nothing publishes**;
 * 📁 [C-1529](../../../docs/LANE_COORDINATION.md) carries that gap.
 */
export function AttentionCard() {
  const { activeWorkspace } = useWorkspaceContext();
  const workspaceId = activeWorkspace?.id ?? null;

  const queue = useWorkspaceTriage(workspaceId, 'open');
  const catalog = useSignalCatalog(workspaceId);
  const postures = useScoringModel(workspaceId);

  const entries = queue.data?.items ?? [];
  const shown = entries.slice(0, MAX);
  /** ⚡ **Only the rows on screen are joined.** ⛔ Naming and pricing the whole
   *  queue to render five of it is the wasteful read [§14](../../../CLAUDE.md)
   *  calls a defect at write time. */
  const ids = shown.map((entry) => entry.entity_id);
  const names = useAccountIdentities(workspaceId, ids);
  const commercials = useAccountCommercials(workspaceId, ids);

  /** 📁 **`HM-COPY-06` names what was checked** — *"41 accounts and 11 open
   *  deals"*. ⚡ **Two separate facts from two owners**: the graph counts
   *  accounts, the pipeline counts open deals. ⛔ Neither is inferred from the
   *  other. */
  const count = useAccountsCount(workspaceId);
  const pipeline = usePipelineHealth(workspaceId);

  /** 📁 §09 — *"each skeleton uses the card's declared height."* */
  if (queue.isPending) {
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
  if (queue.isError) {
    const correlation = queue.error instanceof ApiError ? queue.error.correlationId : '';
    return (
      <Frame>
        <div className="p-[18px]">
          <p role="alert" className="text-sm font-semibold text-content">
            What needs you could not be loaded
          </p>
          <p className="mt-1.5 text-xs leading-[1.5] text-content-muted">
            Everything else on this page is unaffected.
          </p>
          <div className="mt-3 flex flex-wrap items-center gap-3">
            <button
              type="button"
              onClick={() => void queue.refetch()}
              className="inline-flex h-control-sm items-center rounded-md border border-border px-3 text-xs font-semibold text-content transition-colors hover:border-accent hover:text-accent focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-accent"
            >
              Retry
            </button>
            {/* 📁 Contract item 13 — *"with the correlation ID"*. ⛔ Rendered only
                when the response carried one; an empty reference is worse than
                none, because support would search for it. */}
            {correlation ? (
              <span className="font-mono text-2xs text-content-subtle">{correlation}</span>
            ) : null}
          </div>
        </div>
      </Frame>
    );
  }

  const records = count.data?.total ?? null;
  const openDeals = pipeline.data
    ? pipeline.data.ageing.reduce((total, stage) => total + stage.open_count, 0)
    : null;

  return (
    <Frame>
      <header className="flex flex-wrap items-center gap-2.5 border-b border-border-soft px-[18px] py-[15px]">
        <h2 className="text-md font-semibold tracking-[-0.014em] text-content">Needs you today</h2>
        <span className="rounded-sm bg-surface-sunken px-2 py-px text-2xs font-semibold tabular-nums text-content-subtle">
          {entries.length}
        </span>
        {/* 📁 The design's own subtitle. */}
        <span className="ml-auto text-[11.5px] text-content-subtle">
          Ranked by what it costs to ignore
        </span>
      </header>

      {entries.length === 0 ? (
        <div className="p-[18px]">
          {records === 0 ? (
            /* ⚠️ **State 05's half.** ⛔ Not HM-COPY-06 — records are absent, so
               *"nothing needs you"* would be a success message about a workspace
               that has nothing in it. */
            <p className="text-[13px] leading-[1.6] text-content-muted">
              Signora has no records to work from yet. Connect a source and it starts reading
              straight away.
            </p>
          ) : records === null || openDeals === null ? (
            /* 🔴 **[P-A](../../../docs/DOMAIN_DISCOVERY_REGISTER.md): a read that
               could not happen must not render as a read that happened.** ⛔
               `HM-COPY-06` names *what was checked*, and a sentence naming two
               counts Signora does not have would be the fabrication the design's
               own credibility test exists to prevent. */
            <p className="text-[13px] leading-[1.6] text-content-muted">
              Nothing needs you this morning. Signora could not say how much it checked.
            </p>
          ) : (
            /* ✅ **State 06b, `HM-COPY-06` verbatim.** 📁 A success state, and it
               names what was checked and when — the design's own credibility test. */
            <p className="text-[13px] leading-[1.6] text-content-muted">
              {HM_COPY_06(records, openDeals, checkedAt(queue.dataUpdatedAt))}
            </p>
          )}
        </div>
      ) : (
        <>
          {shown.map((entry, index) => (
            <Item
              key={entry.signal_id}
              entry={entry}
              /* 📁 §10 — *"the primary action of the answer card is the first tab
                 stop after the heading"*, and the mock fills only the first row's
                 button. */
              lead={index === 0}
              name={names.data?.get(entry.entity_id)?.name ?? null}
              type={catalog.data?.get(entry.signal_type) ?? null}
              posture={postures.data?.get(entry.signal_type) ?? null}
              value={commercials.data?.get(entry.entity_id)?.open_acv ?? null}
            />
          ))}
          {/* 📁 ***"A sixth becomes 'See all 8 in Signals'."*** */}
          {entries.length > MAX ? (
            <Link
              href="/signals"
              className="block border-b border-border-soft px-[18px] py-3 text-[12.5px] font-semibold text-accent hover:underline focus-visible:outline focus-visible:outline-2 focus-visible:-outline-offset-2 focus-visible:outline-accent"
            >
              See all {entries.length} in Signals
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
function Item({
  entry,
  lead,
  name,
  type,
  posture,
  value,
}: {
  entry: QueueEntry;
  lead: boolean;
  name: string | null;
  type: SignalTypeName | null;
  posture: Posture | null;
  value: Money | null;
}) {
  const tone = TONE[posture ?? 'neutral'];

  return (
    <div
      className={cn(
        'flex flex-wrap items-start gap-x-3 gap-y-2.5 border-b border-l-2 border-border-soft px-[18px] py-[15px]',
        tone === 'risk'
          ? 'border-l-danger'
          : tone === 'warn'
            ? 'border-l-warning'
            : 'border-l-success',
      )}
    >
      <div className="min-w-[13rem] flex-1">
        <div className="flex flex-wrap items-center gap-x-2.5 gap-y-1.5">
          {/* ⚠️ **The name, or a stated absence — never eight characters of a
              UUID.** 📁 A name is a resolved claim, so *"nobody has named this
              account"* is a real answer the identity surface can give. */}
          <span className="text-label font-semibold text-content">
            {name ?? 'Unnamed account'}
          </span>
          {/* 📁 **The tag word, from the catalog** — ⛔ never a title composed
              here, which would be the second vocabulary the catalog exists to
              prevent. */}
          {type === null ? null : (
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
              {type.title}
            </span>
          )}
          {/* 📁 The design's `$2.11M`. ⛔ **Omitted rather than zero-filled when
              no source has stated one** — ADR-0409 §5, and a `$0` beside an
              account name is a figure a seller would act on. */}
          {value === null ? null : (
            <span className="text-[11.5px] font-semibold tabular-nums text-content-subtle">
              {formatMoney(value)}
            </span>
          )}
        </div>
        {/* 📁 **The reason, authored per signal where the reasoning happened.** */}
        <p className="mt-1.5 text-[12.5px] leading-[1.55] text-content-muted">{entry.rationale}</p>
      </div>
      <Link
        href={`/accounts/${entry.entity_id}`}
        className={cn(
          'inline-flex h-[31px] flex-none items-center rounded-md px-3 text-[12.5px] font-semibold transition-colors focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-accent',
          lead
            ? 'border border-accent bg-accent text-accent-contrast hover:bg-accent-hover'
            : 'border border-border text-content hover:border-accent hover:text-accent',
        )}
      >
        Open the account
      </Link>
    </div>
  );
}

/**
 * 📁 **Posture is the severity**, and the map is one line rather than a
 * judgement.
 *
 * ⛔ **The posture itself is NOT decided here** — it is Signora's, published by
 * the Buying Score Engine per hypothesis type. **This turns a domain word into a
 * colour, which is the only part of it a screen owns.**
 */
const TONE: Readonly<Record<Posture, 'risk' | 'warn' | 'pos'>> = Object.freeze({
  contractionary: 'risk',
  neutral: 'warn',
  expansionary: 'pos',
});

/**
 * 📁 The design's *"at 07:00"*.
 *
 * ⚡ **When the read landed, not when the browser painted.** Queue state is
 * derived on the server from the decision in force and the clock, so the moment
 * the response was produced *is* the moment Signora checked — and taking it from
 * the query rather than from `new Date()` keeps the sentence still while the
 * page re-renders.
 */
function checkedAt(at: number): string {
  return new Intl.DateTimeFormat(undefined, { hour: '2-digit', minute: '2-digit' }).format(
    new Date(at),
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
