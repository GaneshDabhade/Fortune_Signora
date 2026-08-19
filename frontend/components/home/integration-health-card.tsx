'use client';

import Link from 'next/link';

import { CardFailure } from '@/components/home/card-failure';
import { useCardPhase } from '@/lib/home/loading';

import type { Connection, ConnectionHealth } from '@/lib/api/types';
import { cn } from '@/lib/design/cn';
import { useIntegrations } from '@/lib/query/hooks/integrations';
import { useWorkspaceContext } from '@/lib/state/workspace-provider';

/**
 * 📁 **`card.inthealth` — *"Integration health"*** ·
 * `Fortune Signora Home.dc.html` §04 registry.
 *
 * > 📁 ***"Per-connection state, including held write queues."***
 * > 📁 Compositions **`OP` · `EX`** · footprint `1.2fr × auto` · dependency
 * > `integrations.health` · primary action ***"Open the integration"***.
 *
 * ## ⛔ *"Including held write queues"* waits on E2, and the earlier reason here was wrong
 *
 * ⚠️ **This comment first said the design does not define a held write. It
 * does.** 📁 **CRM Integrations** — the approved screen for this capability —
 * specifies it exactly: **`Held writes · 41 · queued · "Retained until
 * permissions verify"`**, *"writes are held, **not discarded**"*, the log line
 * `write.opp held=41 reason=INSUFFICIENT_ACCESS retry_in=15m`, and a recovery
 * step *"drain the 41 held writes in order"*.
 *
 * 🔴 **The real reason is that Signora cannot hold a write, because Signora
 * cannot write.** 📁 `integrations/domain/source.py:177` — ***"Read-only.
 * `fetch` is the only verb, and write-back is E2's territory."***
 *
 * 📁 **E2 is a ratified epic that is deliberately unbuilt** —
 * [`406-epic-e2-crm-write-back.md`](../../../docs/architecture/406-epic-e2-crm-write-back.md):
 * ***"Prepared by Lane C — Product Office. No code was written and none should
 * be."*** ⛔ **It owns write-back entirely**, and its guardrail is structural:
 * *"no write path without an `actor_id`"*, because *"a machine-authored
 * commitment in a customer's CRM is [**intelligence suggests, humans commit**]
 * being broken in somebody else's database."*
 *
 * ✅ **So this is a dependency, not a gap and not a product question.** ⛔
 * **Building a write queue inside a Home slice would take E2's territory and
 * breach its guardrail.** **The count appears here when E2 lands**; until then
 * there is nothing to count, and a `0` would imply a capability that does not
 * exist.
 *
 * ## ✅ Per-connection, not per-system
 *
 * 📁 The design says *"per-CONNECTION state"*, and a system may hold several.
 * ⛔ **Rolling them up to one row per integration would lose the fact the card
 * exists to show** — a workspace with two Salesforce connections, one revoked,
 * reads as *"Salesforce: needs attention"* and says nothing about which.
 */
export function IntegrationHealthCard() {
  const { activeWorkspace } = useWorkspaceContext();
  const systems = useIntegrations(activeWorkspace?.id ?? null);

  /**
   * 📁 **Contract 13** — *"a card query failing after retries renders that
   * card's error inside its own footprint with the correlation ID; siblings are
   * unaffected."*
   */
  /** 📁 §09's timed rules — no skeleton under 300ms, an error state over 8s. */
  const phase = useCardPhase(systems.isPending);

  /* ⚡ **A timeout lands in the error branch** — 📁 *"the card converts to its
     error state with a retry."* ⛔ The query is not aborted; the card stops
     waiting, so a late response still renders. */
  if (systems.isError || phase === 'timeout') {
    return (
      <CardFailure
        title="Signora could not read your connections"
        /* ⛔ **What survived, named** — 📁 `3.3.1`. A person reading *"could not
           read your connections"* has to be told the sources are still
           connected; the failure is the READ, not the connection. */
        description="Nothing has been disconnected. Everything else on this page is unaffected."
        error={systems.error}
        onRetry={() => void systems.refetch()}
        retrying={systems.isFetching && phase !== 'timeout'}
        testId="home-integration-health"
      />
    );
  }

  /** 📁 **State 07** — *"cards skeletonised at declared footprints"*, ⛔ **and
   *  nothing for the first 300ms**, which the design calls a flicker. */
  if (systems.isPending) {
    return (
      <Frame>
        <div aria-hidden className="space-y-3 px-[18px] py-[15px]">
          {phase === 'skeleton' ? (
            <>
              <div className="h-4 w-1/2 animate-pulse rounded bg-surface-sunken" />
              <div className="h-4 w-2/3 animate-pulse rounded bg-surface-sunken" />
            </>
          ) : null}
        </div>
      </Frame>
    );
  }

  const connections = (systems.data ?? []).flatMap((system) => system.connections);

  return (
    <Frame count={connections.length}>
      {connections.length === 0 ? (
        /**
         * ⛔ **Not *"No data available"*** — 📁 that string is on the design's
         * banned list. ✅ **It names what was looked for**, which is §03's test
         * for whether an empty state is credible.
         */
        <p className="px-[18px] py-[15px] text-[12.5px] leading-[1.55] text-content-muted">
          {/* ⛔ **Not *"workspace"*** — 📁 [ADR-0034](../../../docs/architecture/adr):
              *a customer says "organization", the platform says "workspace"*.
              ⚡ **Caught by `vocabulary.test.tsx`, not by review.** */}
          No system is connected yet.
        </p>
      ) : (
        connections.map((connection) => <Row key={connection.id} connection={connection} />)
      )}
    </Frame>
  );
}

/**
 * 📁 **Health is the row's severity**, and it is the connection's own word —
 * ⛔ **never recomputed here.** `ConnectionHealth` is `healthy | degraded |
 * unknown`, decided when the read is served.
 */
const TONE: Readonly<Record<ConnectionHealth, 'pos' | 'warn' | 'muted'>> = Object.freeze({
  healthy: 'pos',
  degraded: 'warn',
  unknown: 'muted',
});

function Row({ connection }: { connection: Connection }) {
  const tone = TONE[connection.health];

  return (
    <div
      className={cn(
        'flex flex-wrap items-start gap-x-3 gap-y-2 border-b border-l-2 border-border-soft px-[18px] py-[13px]',
        tone === 'pos' ? 'border-l-success' : tone === 'warn' ? 'border-l-warning' : 'border-l-border',
      )}
    >
      <div className="min-w-[11rem] flex-1">
        <div className="flex flex-wrap items-center gap-x-2.5 gap-y-1.5">
          <span className="text-label font-semibold text-content">{connection.label}</span>
          {/* 📁 **The connection's own state**, verbatim from the contract. */}
          <span
            className={cn(
              'rounded-sm px-2 py-px text-2xs font-semibold',
              tone === 'pos'
                ? 'bg-success-subtle text-success'
                : tone === 'warn'
                  ? 'bg-warning-subtle text-warning'
                  : 'bg-surface-sunken text-content-subtle',
            )}
          >
            {connection.state}
          </span>
        </div>
        {/* ⚡ **The reason, only when the read supplies one.** ⛔ Never a
            sentence composed here to fill the space. */}
        {connection.reason === null ? null : (
          <p className="mt-1.5 text-[12.5px] leading-[1.55] text-content-muted">
            {connection.reason}
          </p>
        )}
      </div>
      {/* 📁 The registry's primary action for this card, verbatim. */}
      <Link
        href="/settings/connections"
        className="inline-flex h-[31px] flex-none items-center rounded-md border border-border px-3 text-[12.5px] font-semibold text-content transition-colors hover:border-accent hover:text-accent focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-accent"
      >
        Open the integration
      </Link>
    </div>
  );
}

function Frame({ count, children }: { count?: number; children: React.ReactNode }) {
  return (
    <div
      data-testid="home-integration-health"
      className="overflow-hidden rounded-xl border border-border-soft bg-surface shadow-e1"
    >
      <div className="flex items-center gap-2 border-b border-border-soft px-[18px] py-3">
        <h2
          className="text-label font-semibold text-content"
        >
          Integration health
        </h2>
        {count === undefined ? null : (
          <span className="text-2xs font-semibold tabular-nums text-content-subtle">{count}</span>
        )}
      </div>
      {children}
    </div>
  );
}
