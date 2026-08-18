'use client';

import Link from 'next/link';

import { CardFailure } from '@/components/home/card-failure';
import { useCardPhase } from '@/lib/home/loading';

import type { ViewedRecord } from '@/lib/api/types';
import { useAccountIdentities } from '@/lib/query/hooks';
import { useRecentlyViewed } from '@/lib/query/hooks/recently-viewed';
import { useWorkspaceContext } from '@/lib/state/workspace-provider';

/**
 * 📁 **`card.recents` — *"Pick up where you left off"*** ·
 * `Fortune Signora Home.dc.html` §04 registry.
 *
 * > 📁 ***"Last five records touched. Context, never urgent."*** ·
 * > compositions **`SE` · `OP` · `EX`** · footprint `1fr × 160px` ·
 * > primary action ***"Open the record"***.
 *
 * ## 📁 The rendering is the Authenticated Entry document's
 *
 * ⚠️ **Home names this card but does not draw it** — its `HM-01` renders the
 * briefing, attention, meetings and the agent queue. ✅ 📁 **Authenticated
 * Entry §05 draws it**: an uppercase eyebrow, then rows of *"a 20px initial
 * tile · the record's name · the day, right-aligned"*.
 *
 * ⛔ **So the treatment is not invented here.** Home's own reconciliation
 * adopts Entry *"verbatim"* for what its rules render, and this is one of them.
 *
 * ## 🔴 *"Touched"* is *viewed*, and Home did not decide that
 *
 * 📁 **Session Continuity tier 4** — *"recently **viewed** records"* — and its
 * restore rule names the same list: *"silent where it only informs a list
 * (recents)"*. ⛔ **Never *edited* or *created***: those are different facts
 * and would need their own source.
 *
 * ## ⛔ Names come from the identity surface, never from the record of the view
 *
 * 📁 An account's name is the Knowledge Graph's to state and moves without this
 * fact hearing about it — **storing it beside the view would be a second
 * representation of something that changes** ([§2](../../../CLAUDE.md)). ✅ The
 * attention card resolves names the same way.
 */
export function RecentsCard() {
  const { activeWorkspace } = useWorkspaceContext();
  const workspaceId = activeWorkspace?.id ?? null;

  const recents = useRecentlyViewed(workspaceId);
  const records = recents.data ?? [];
  const identities = useAccountIdentities(
    workspaceId,
    records.map((record) => record.entity_id),
  );

  /**
   * 📁 **Contract 13** — *"a card query failing after retries renders that
   * card's error inside its own footprint with the correlation ID."*
   *
   * ⛔ **And it never says there were none.** 📁 Session Continuity's tier-4
   * failure rule is exactly that: *"recents unavailable… **no fabricated
   * history**"* — **an empty list and an unread list are different answers.**
   */
  /** 📁 §09's timed rules — no skeleton under 300ms, an error state over 8s. */
  const phase = useCardPhase(recents.isPending);

  /* ⚡ **A timeout lands in the error branch** — 📁 *"the card converts to its
     error state with a retry."* ⛔ The query is not aborted; the card stops
     waiting, so a late response still renders. */
  if (recents.isError || phase === 'timeout') {
    /**
     * ⛔ **NOT inside `Frame`, and the 160px footprint is deliberately not
     * imposed here.** 📁 The registry's height is what a LOADED card occupies
     * and what its skeleton reserves — *"each card skeleton uses the height
     * declared in the registry, so nothing reflows when data lands."* ⚡ **A
     * failure panel clipped to 160px would hide its own retry**, and the
     * design's drawn error card is card-sized rather than row-sized.
     */
    return (
      <CardFailure
        title="Signora could not read what you opened recently"
        /* 📁 Session Continuity tier 4's failure rule: *"recents unavailable…
           **no fabricated history**"* — ⛔ **an empty list and an unread list
           are different answers**, and this is the one that says which. */
        description="Nothing you opened has been lost. Everything else on this page is unaffected."
        error={recents.error}
        onRetry={() => void recents.refetch()}
        retrying={recents.isFetching && phase !== 'timeout'}
        testId="home-recents"
      />
    );
  }

  /** 📁 **State 07** — skeletonised at the declared footprint. ⛔ **And nothing at
   *  all for the first 300ms** — 📁 *"a placeholder shown and removed inside 300ms
   *  reads as a flicker."* */
  if (recents.isPending) {
    return (
      <Frame>
        <div aria-hidden className="mt-2.5 space-y-3">
          {phase === 'skeleton' ? (
            <>
              <div className="h-4 w-2/3 animate-pulse rounded bg-surface-sunken" />
              <div className="h-4 w-1/2 animate-pulse rounded bg-surface-sunken" />
            </>
          ) : null}
        </div>
      </Frame>
    );
  }

  return (
    <Frame>
      {records.length === 0 ? (
        /**
         * ⛔ **Not *"No data available"*** — 📁 that string is banned on Home.
         * ⚡ **Nothing synthetic either**: 📁 *"if a tier has no record, the
         * screen renders empty rather than reconstructing a plausible state.
         * Fabricated continuity is worse than none."*
         */
        <p className="mt-2.5 text-[12.5px] leading-[1.55] text-content-muted">
          Nothing opened yet in this organization.
        </p>
      ) : (
        <div className="mt-2.5 flex flex-col">
          {records.map((record) => (
            <Row
              key={record.entity_id}
              record={record}
              name={identities.data?.get(record.entity_id)?.name ?? null}
            />
          ))}
        </div>
      )}
    </Frame>
  );
}

function Row({ record, name }: { record: ViewedRecord; name: string | null }) {
  const label = name ?? 'Unnamed account';

  return (
    <Link
      href={`/accounts/${record.entity_id}`}
      className="flex items-center gap-[11px] border-b border-border-soft py-2 last:border-b-0 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-accent"
    >
      {/* 📁 Entry §05's *"20px initial tile"*. ♿ `aria-hidden`: the name beside
          it already carries the meaning, so a reader hears it once. */}
      <span
        aria-hidden
        className="grid h-5 w-5 flex-none place-items-center rounded-md bg-surface-sunken text-[8.5px] font-bold text-content-muted"
      >
        {initials(label)}
      </span>
      <span className="min-w-0 truncate text-[12.5px] text-content">{label}</span>
      <span className="ml-auto flex-none text-[11px] text-content-subtle">
        {when(record.viewed_at)}
      </span>
    </Link>
  );
}

/** 📁 Entry §05's `abbr` — *"VL"*, *"NE"*. */
function initials(name: string): string {
  return name
    .split(/\s+/)
    .slice(0, 2)
    .map((word) => word[0] ?? '')
    .join('')
    .toUpperCase();
}

/**
 * 📁 Entry §05's `meta` — *"Friday"*, *"Thursday"*.
 *
 * ⚡ **A weekday inside the last week, a date beyond it.** ⛔ *"Friday"* eleven
 * days later names the wrong Friday, which is the one way this line can lie.
 */
function when(iso: string): string {
  const at = new Date(iso);
  const days = Math.floor((Date.now() - at.getTime()) / 86_400_000);
  if (days <= 0) return 'Today';
  if (days === 1) return 'Yesterday';
  if (days < 7) return new Intl.DateTimeFormat(undefined, { weekday: 'long' }).format(at);
  return new Intl.DateTimeFormat(undefined, { day: 'numeric', month: 'short' }).format(at);
}

/**
 * 📁 **Footprint `1fr × 160px`**, from the registry. ⛔ **A fixed height, so a
 * shorter list does not reflow the grid** — contract 12's rule for skeletons is
 * the same property at load.
 */
function Frame({ children }: { children: React.ReactNode }) {
  return (
    <section
      aria-labelledby="home-recents-heading"
      data-testid="home-recents"
      className="h-[160px] overflow-hidden rounded-xl border border-border-soft bg-surface p-[18px] shadow-e1"
    >
      {/* 📁 Entry §05's uppercase eyebrow, not a card title bar. */}
      <h3
        id="home-recents-heading"
        className="text-2xs font-semibold uppercase tracking-[0.05em] text-content-subtle"
      >
        Pick up where you left off
      </h3>
      {children}
    </section>
  );
}
