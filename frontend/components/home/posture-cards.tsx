'use client';

import Link from 'next/link';

import { CardFailure } from '@/components/home/card-failure';
import { useCardPhase } from '@/lib/home/loading';

import type { Money, Posture, QueueEntry, SignalTypeName } from '@/lib/api/types';
import { formatMoney } from '@/lib/accounts/table';
import { cn } from '@/lib/design/cn';
import { CARD_POSTURE, TONE } from '@/lib/home/tone';
import { useAccountIdentities, useSignalCatalog } from '@/lib/query/hooks';
import { useAccountCommercials, useScoringModel } from '@/lib/query/hooks/scoring';
import { useWorkspaceTriage } from '@/lib/query/hooks/triage';
import { useWorkspaceContext } from '@/lib/state/workspace-provider';

/**
 * 📁 **`card.risks` and `card.opps` — the Executive composition's two ranked
 * lists** · `Fortune Signora Home.dc.html` §05 registry.
 *
 * > 📁 ***"Top risks · Ranked risks with the population each was derived
 * > from."***
 * > 📁 ***"Top opportunities · Ranked positive signals with their window."***
 *
 * ## 🔴 These were recorded as having no producer, and the record was wrong
 *
 * ⚠️ **A previous audit concluded `signals.risk` and `signals.opportunity` had
 * no backing capability.** ⛔ **It searched `signal_engine` alone** — whose
 * catalog carries `key · title · hypothesis · why_it_matters ·
 * detection_strategy · limitations`, **and no polarity** — and stopped there.
 *
 * ✅ **The classification exists, is ratified, and is already published**:
 * `scoring_model@1.json` assigns every one of the ten types a `posture`, and
 * `GET /workspaces/{id}/scoring-model` has been serving it all along. 📁 The
 * artifact settles that it is not a matter of taste: *"posture is not
 * configurable — whether `CONTRACTION_RISK` reads as contractionary is a fact
 * about the English language, not a preference."*
 *
 * ⚡ **So no product decision was required and none was invented.** **The two
 * cards partition one queue by a judgement the platform already owns.**
 *
 * ## ⛔ One queue, two readings — never two rankings
 *
 * 📁 **U-04's interim ruling**: *"assume the service returns a ranked list; if
 * it does not, the order must be seeded deterministically so a refresh does not
 * reshuffle."* ⚡ `GET /triage` is keyset-paged on `(occurred_at, id)`, **so the
 * order is the server's and stable.** ⛔ **Nothing here re-sorts** — a browser
 * ranking would be a second ranking, free to disagree with the platform's.
 *
 * ## ⚠️ `neutral` appears in neither card, deliberately
 *
 * 📁 `card.opps` asks for *"ranked **positive** signals"*.
 * **`consolidation_underway` and `new_decision_maker` are the two postures the
 * model declines to call either way** — ⛔ **filing them under either heading
 * would assert a commercial reading the domain explicitly refuses to make.**
 */
export function TopRisksCard() {
  return (
    <PostureCard
      title="Top risks"
      posture={CARD_POSTURE.risks}
      /** 📁 The registry's own words for this card's empty answer. */
      quiet="Nothing on your book is contracting. Signora checked every open signal."
      testId="home-top-risks"
    />
  );
}

export function TopOpportunitiesCard() {
  return (
    <PostureCard
      title="Top opportunities"
      posture={CARD_POSTURE.opportunities}
      quiet="No expansionary signal is open. Signora checked every open signal."
      testId="home-top-opportunities"
    />
  );
}

/** 📁 *"Ranked risks"* — the design shows four; five is the Home-wide ceiling
 * contract item 17 sets for a ranked list, and the two cards obey the same one
 * rather than inventing a second number. */
const MAX = 5;

function PostureCard({
  title,
  posture,
  quiet,
  testId,
}: {
  title: string;
  posture: Posture;
  quiet: string;
  testId: string;
}) {
  const { activeWorkspace } = useWorkspaceContext();
  const workspaceId = activeWorkspace?.id ?? null;

  const queue = useWorkspaceTriage(workspaceId, 'open');
  const catalog = useSignalCatalog(workspaceId);
  const postures = useScoringModel(workspaceId);

  /**
   * 🔴 **The partition happens only once the model has answered.** ⛔ **An
   * unresolved posture map would put every signal in the `?? 'neutral'` bucket
   * and render BOTH cards empty**, which is state 06b's *"a success state"*
   * copy shown for what is actually still loading — 📁 contract item 4's
   * distinction, one card over.
   */
  const resolved = postures.data ?? null;
  const mine =
    resolved === null
      ? []
      : (queue.data?.items ?? []).filter((entry) => resolved.get(entry.signal_type) === posture);
  const shown = mine.slice(0, MAX);

  /**
   * ⚡ **Batched, and only for the rows this card actually shows** — 📁 the
   * identity surface is the one place an account may be named, and asking it
   * for the whole queue would fetch four fifths of a page nobody renders.
   */
  const ids = shown.map((entry) => entry.entity_id);
  const identities = useAccountIdentities(workspaceId, ids);
  const commercials = useAccountCommercials(workspaceId, ids);

  /**
   * 📁 **Contract item 13** — *"a card query failing after retries renders that
   * card's error inside its own footprint with the correlation ID; siblings are
   * unaffected."*
   */
  /** 📁 §09's timed rules — no skeleton under 300ms, an error state over 8s.
   *  ⚡ **Both reads**, because the card waits on the slower of the two. */
  const phase = useCardPhase(queue.isPending || postures.isPending);

  /* ⚡ **A timeout lands here too** — 📁 *"the card converts to its error state
     with a retry."* */
  if (queue.isError || postures.isError || phase === 'timeout') {
    return (
      <CardFailure
        title={`${title} could not be read`}
        /* ⚡ **Two reads feed this card and either can fail** — the queue and
           the posture the scoring model publishes. ⛔ **Neither is named
           here**: which of two internal reads failed is not a fact a customer
           can act on, and the correlation ID is what carries it to support. */
        description="Nothing has been lost, and the rest of this page is unaffected."
        error={queue.isError ? queue.error : postures.error}
        onRetry={() => {
          void queue.refetch();
          void postures.refetch();
        }}
        retrying={(queue.isFetching || postures.isFetching) && phase !== 'timeout'}
        testId={testId}
      />
    );
  }

  if (queue.isPending || postures.isPending) {
    /** 📁 State 07 — *"cards skeletonised at declared footprints."* ⛔ Never a
     * page-level spinner, and never an empty state standing in for a load.
     * ⛔ **And nothing at all for the first 300ms**, which 📁 §09 calls a flicker. */
    return (
      <Frame title={title} testId={testId}>
        <div aria-hidden className="space-y-3 px-[18px] py-[15px]">
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
    <Frame title={title} testId={testId} count={mine.length}>
      {mine.length === 0 ? (
        /** 📁 **State 06b, `HM-COPY-06`'s shape** — *"a success state… never
         * mistaken for a failure."* ⛔ Distinct copy per card, because a shared
         * empty component is contract item 4's named violation. */
        <p
          className="px-[18px] py-[15px] text-[12.5px] leading-[1.55] text-content-muted"
          data-testid={`${testId}-quiet`}
        >
          {quiet}
        </p>
      ) : (
        <>
          {shown.map((entry, i) => (
            <Row
              key={entry.signal_id}
              entry={entry}
              lead={i === 0}
              posture={posture}
              name={identities.data?.get(entry.entity_id)?.name ?? null}
              type={catalog.data?.get(entry.signal_type) ?? null}
              value={commercials.data?.get(entry.entity_id)?.open_acv ?? null}
            />
          ))}
          {/**
           * 📁 **Contract item 17's rule, applied to this card's own overflow**
           * — *"a sixth is replaced by a single link to Signals."*
           */}
          {mine.length > MAX ? (
            <Link
              href="/signals"
              className="block px-[18px] py-3 text-[12.5px] font-semibold text-accent hover:text-accent-hover focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-accent"
            >
              See all {mine.length} in Signals
            </Link>
          ) : null}
        </>
      )}
    </Frame>
  );
}

/**
 * 📁 **One row** — *"account, tag, value, the reason, one action."*
 *
 * ♿ **Severity is carried by the left rule, the tag word AND the tint
 * together**, so 📁 1.4.1 holds: removing colour leaves the tag and the order
 * intact.
 */
function Row({
  entry,
  lead,
  posture,
  name,
  type,
  value,
}: {
  entry: QueueEntry;
  lead: boolean;
  posture: Posture;
  name: string | null;
  type: SignalTypeName | null;
  value: Money | null;
}) {
  const tone = TONE[posture];

  return (
    <div
      className={cn(
        'flex flex-wrap items-start gap-x-3 gap-y-2.5 border-b border-l-2 border-border-soft px-[18px] py-[15px]',
        tone === 'risk' ? 'border-l-danger' : tone === 'warn' ? 'border-l-warning' : 'border-l-success',
      )}
    >
      <div className="min-w-[13rem] flex-1">
        <div className="flex flex-wrap items-center gap-x-2.5 gap-y-1.5">
          <span className="text-label font-semibold text-content">{name ?? 'Unnamed account'}</span>
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
          {/* ⛔ **Omitted rather than zero-filled** — ADR-0409 §5. A `$0` beside
              an account name is a figure an executive would act on. */}
          {value === null ? null : (
            <span className="text-[11.5px] font-semibold tabular-nums text-content-subtle">
              {formatMoney(value)}
            </span>
          )}
        </div>
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
        Open the deal
      </Link>
    </div>
  );
}

function Frame({
  title,
  testId,
  count,
  children,
}: {
  title: string;
  testId: string;
  count?: number;
  children: React.ReactNode;
}) {
  return (
    <section
      aria-labelledby={`${testId}-heading`}
      data-testid={testId}
      className="overflow-hidden rounded-xl border border-border-soft bg-surface shadow-e1"
    >
      <div className="flex items-center gap-2 border-b border-border-soft px-[18px] py-3">
        <h3 id={`${testId}-heading`} className="text-label font-semibold text-content">
          {title}
        </h3>
        {/* 📁 *"with the population each was derived from"* — ⚡ the size of the
            set this card ranked, not the number of rows it drew. */}
        {count === undefined ? null : (
          <span className="text-2xs font-semibold tabular-nums text-content-subtle">{count}</span>
        )}
      </div>
      {children}
    </section>
  );
}
