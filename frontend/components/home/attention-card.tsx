'use client';

import Link from 'next/link';

import type { Money, Posture, QueueEntry, SignalTypeName } from '@/lib/api/types';
import { formatMoney } from '@/lib/accounts/table';
import { cn } from '@/lib/design/cn';
import { Skeleton } from '@/components/ui';
import { AccountName } from '@/components/intelligence/account-name';
import { CardFailure } from '@/components/home/card-failure';
import { HM_COPY_06 } from '@/lib/home/copy';
import { useCardPhase } from '@/lib/home/loading';
import { TONE } from '@/lib/home/tone';
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
   * queue to render five of it is the wasteful read [§14](../../../CLAUDE.md)
   * calls a defect at write time. */
  const ids = shown.map((entry) => entry.entity_id);
  const names = useAccountIdentities(workspaceId, ids);
  const commercials = useAccountCommercials(workspaceId, ids);

  /** 📁 **`HM-COPY-06` names what was checked** — *"41 accounts and 11 open
   * deals"*. ⚡ **Two separate facts from two owners**: the graph counts
   * accounts, the pipeline counts open deals. ⛔ Neither is inferred from the
   * other. */
  const count = useAccountsCount(workspaceId);
  const pipeline = usePipelineHealth(workspaceId);

  /**
   * 📁 §09's two timed rules — *"under 300ms: **no skeleton at all**"* and *"over
   * 8 seconds: **the card converts to its error state with a retry**"*.
   */
  const phase = useCardPhase(queue.isPending);

  /** 📁 §09 — *"each skeleton uses the card's declared height."* */
  if (queue.isPending && phase !== 'timeout') {
    return (
      <Frame>
        <div role="status" className="flex flex-col gap-3 p-5">
          {/* ⛔ **Nothing drawn for the first 300ms** — 📁 *"a placeholder shown
              and removed inside 300ms reads as a flicker."* ⚡ **The frame still
              holds its footprint**, so nothing reflows when the data lands. */}
          {phase === 'skeleton'
            ? [0, 1, 2].map((i) => (
                <Skeleton key={i} className="h-[46px] rounded-lg" />
              ))
            : null}
          {/* ♿ **Announced from the first frame**, whatever is drawn. A reader
              waiting on a screen reader should not wait 300ms to be told. */}
          <span className="sr-only">Loading what needs you</span>
        </div>
      </Frame>
    );
  }

  /**
   * 📁 **State 08 — the card's error stays inside the card's footprint**, with a
   * correlation id. ⛔ *"Siblings are unaffected."*
   *
   * ⚡ **A timeout lands here too** — 📁 *"the card converts to its error state
   * with a retry"*. ⛔ **The query is not aborted**: the card stops waiting, the
   * read does not, so a response at nine seconds still renders.
   */
  if (queue.isError || phase === 'timeout') {
    /**
     * ⛔ **This card hand-rolled the whole treatment, and it was the closest of
     * the eight to right** — a title, a survivor clause, a real retry and the
     * correlation ID. ⚡ **What it lacked is what the shared panel supplies**:
     * the System States tile and glyph, a COPYABLE identifier, and 📁 the
     * design's dashed frame *"so it is distinguishable from content"*.
     */
    return (
      <CardFailure
        title="What needs you could not be loaded"
        description="Nothing has been missed or dismissed. Everything else on this page is unaffected."
        error={queue.error}
        onRetry={() => void queue.refetch()}
        /* ⛔ **Not `isFetching` on a timeout.** ⚡ The original attempt is still in
           flight, and a permanently-loading button is a retry nobody can press —
           📁 *"with a retry"* means an affordance, not a spinner. */
        retrying={queue.isFetching && phase !== 'timeout'}
      />
    );
  }

  const records = count.data?.total ?? null;
  const openDeals = pipeline.data
    ? pipeline.data.ageing.reduce((total, stage) => total + stage.open_count, 0)
    : null;

  return (
    <Frame>
      <header className="flex flex-wrap items-center gap-2.5 border-b border-border-soft px-5 py-[15px]">
        <h2 className="text-md font-semibold tracking-[-0.014em] text-content">
          Needs you today
        </h2>
        <span className="rounded-sm bg-surface-sunken px-2 py-px text-2xs font-semibold tabular-nums text-content-subtle">
          {entries.length}
        </span>
        {/* 📁 The design's own subtitle. */}
        <span className="ml-auto text-2xs text-content-subtle">
          Ranked by what it costs to ignore
        </span>
      </header>

      {entries.length === 0 ? (
        <div className="p-5">
          {records === 0 ? (
            /* ⚠️ **State 05's half.** ⛔ Not HM-COPY-06 — records are absent, so
             *"nothing needs you"* would be a success message about a workspace
               that has nothing in it. */
            <p className="text-sm leading-[1.6] text-content-muted">
              Signora has no records to work from yet. Connect a source and it starts
              reading straight away.
            </p>
          ) : records === null || openDeals === null ? (
            /* 🔴 **[P-A](../../../docs/DOMAIN_DISCOVERY_REGISTER.md): a read that
               could not happen must not render as a read that happened.** ⛔
               `HM-COPY-06` names *what was checked*, and a sentence naming two
               counts Signora does not have would be the fabrication the design's
               own credibility test exists to prevent. */
            <p className="text-sm leading-[1.6] text-content-muted">
              Nothing needs you this morning. Signora could not say how much it checked.
            </p>
          ) : (
            /* ✅ **State 06b, `HM-COPY-06` verbatim.** 📁 A success state, and it
               names what was checked and when — the design's own credibility test. */
            <p className="text-sm leading-[1.6] text-content-muted">
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
              /**
               * 🔴 **The phone's cut list** — 📁 the 390 × 844 viewport: *"briefing,
               * then **three attention items**, then **a link to the rest**."*
               *
               * ⛔ **CSS rather than a viewport hook**, deliberately. ⚡ A hook
               * reads the width after hydration, so the first paint would show
               * five rows and then drop two — 📁 §09's *"nothing reflows when
               * data lands"* applied to layout rather than to data.
               *
               * ⚠️ **The boundary is the repository's own phone floor** —
               * `tailwind.config.ts` declares *"`phone` is the <640 floor"*, and
               * the design's tablet-portrait row keeps *"full order retained;
               * nothing is cut"* from 768 up. **640–767 is undefined by the
               * design; the repository's floor is what decides it.**
               */
              hiddenOnPhone={index >= PHONE_MAX}
              name={names.data?.get(entry.entity_id)?.name ?? null}
              /* 🔴 **B-290** — ⛔ the identity read settles AFTER the queue, so
                 the fallback was rendering as an answer for over a second. */
              namePending={names.isPending}
              type={catalog.data?.get(entry.signal_type) ?? null}
              posture={postures.data?.get(entry.signal_type) ?? null}
              value={commercials.data?.get(entry.entity_id)?.open_acv ?? null}
            />
          ))}
          {/**
           * 📁 ***"A sixth becomes 'See all 8 in Signals'."*** — and 📁 the phone's
           * *"then a link to the rest"*.
           *
           * ⚡ **The count is the WHOLE queue either way**, so one element serves
           * both bands: what changes is when it is shown. ⛔ **A fourth item
           * hidden on a phone with no link would be a cut**, which is the one
           * thing the design's responsive law forbids — *"cards are never shrunk
           * below their legible minimum; they are **moved or replaced by a
           * link**."*
           */}
          {entries.length > PHONE_MAX ? (
            <Link
              href="/signals"
              className={cn(
                'border-b border-border-soft px-5 py-3 text-label font-semibold text-accent hover:underline ',
                // ⚡ **Above the phone floor the link is the design's sixth-item
                // rule**; at or below it, it stands in for rows four and five.
                entries.length > MAX ? 'block' : 'block phone:hidden',
              )}
            >
              See all {entries.length} in Signals
            </Link>
          ) : null}
          <p className="px-5 py-[13px] text-2xs leading-[1.5] text-content-subtle">
            Home is a starting point, not a queue.
          </p>
        </>
      )}
    </Frame>
  );
}

/** 📁 ***"Maximum five items."*** — the 1440 reference viewport. */
const MAX = 5;
/** 📁 ***"Briefing, then THREE attention items, then a link to the rest"*** — 390. */
const PHONE_MAX = 3;

/**
 * 📁 **One row** — *"left rule, account, tag, value, the reason, one action."*
 *
 * ♿ **Severity uses the left rule, the tag word AND the tint together** — 📁
 * 1.4.1: *"Removing colour leaves the tag and the order intact."*
 */
function Item({
  entry,
  lead,
  hiddenOnPhone,
  name,
  namePending,
  type,
  posture,
  value,
}: {
  entry: QueueEntry;
  lead: boolean;
  /** 📁 **The 390 viewport's cut list** — rows four and five give way to a link. */
  hiddenOnPhone: boolean;
  name: string | null;
  namePending: boolean;
  type: SignalTypeName | null;
  posture: Posture | null;
  value: Money | null;
}) {
  const tone = TONE[posture ?? 'neutral'];

  return (
    <div
      className={cn(
        'flex flex-wrap items-start gap-x-3 gap-y-2.5 border-b border-l-2 border-border-soft px-5 py-[15px]',
        hiddenOnPhone && 'hidden phone:flex',
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
          <AccountName
            name={name}
            pending={namePending}
            absent="Unnamed account"
            className="text-label font-semibold text-content"
          />
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
            <span className="text-2xs font-semibold tabular-nums text-content-subtle">
              {formatMoney(value)}
            </span>
          )}
        </div>
        {/* 📁 **The reason, authored per signal where the reasoning happened.** */}
        <p className="mt-1.5 text-label leading-[1.55] text-content-muted">
          {entry.rationale}
        </p>
      </div>
      <Link
        href={`/accounts/${entry.entity_id}`}
        className={cn(
          'inline-flex items-center rounded-md px-3 text-label font-semibold transition-colors ',
          /**
           * 🔴 **The phone's row anatomy** — 📁 the 390 viewport: *"attention
           * items become full-width rows with the action as a **44px full-width
           * button beneath the reason**."*
           *
           * ⚡ **And `2.5.8` requires it independently**: *"on mobile every
           * primary action is 44px tall."* ⛔ 31px is the desktop control height
           * and is below the touch minimum.
           *
           * ✅ **`flex-wrap` on the row already puts it beneath**; what was
           * missing is the width and the height.
           */
          'h-11 w-full justify-center phone:h-[31px] phone:w-auto phone:flex-none phone:justify-start',
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
 * 📁 The design's *"at 07:00"*.
 *
 * ⚡ **When the read landed, not when the browser painted.** Queue state is
 * derived on the server from the decision in force and the clock, so the moment
 * the response was produced *is* the moment Signora checked — and taking it from
 * the query rather than from `new Date()` keeps the sentence still while the
 * page re-renders.
 */
function checkedAt(at: number): string {
  return new Intl.DateTimeFormat(undefined, {
    hour: '2-digit',
    minute: '2-digit',
  }).format(new Date(at));
}

/** 📁 *"Card 14px --e1"* — the design's own card, from §10's inventory. */
function Frame({ children }: { children: React.ReactNode }) {
  return (
    <div className="overflow-hidden rounded-lg border border-border-soft bg-surface shadow-sm">
      {children}
    </div>
  );
}
