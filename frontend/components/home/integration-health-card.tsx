'use client';

import Link from 'next/link';

import { ApiError } from '@/lib/api/client';
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
 * ## ⛔ *"Including held write queues"* is NOT implemented, and is not invented
 *
 * 🔴 **The repository has no write-queue concept**, and 📁 **the design does not
 * define one** — it never says when a write is held, what a queue contains, or
 * what this card renders about it. **Measured**: `integrations` carries
 * `state · attention · reason · health · connected_at` and nothing resembling a
 * held write.
 *
 * ✅ **So the per-connection state the design specifies is implemented in full,
 * and that one clause is left out rather than guessed.** ⛔ **The card is not
 * redesigned around the gap** and its structure is unchanged; the clause is
 * recorded as the exact outstanding item.
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
  if (systems.isError) {
    const correlation = systems.error instanceof ApiError ? systems.error.correlationId : null;
    return (
      <Frame>
        <p className="px-[18px] py-[15px] text-[12.5px] leading-[1.55] text-content-muted">
          Signora could not read your connections. Everything else on this page is unaffected.
          {correlation === null ? null : (
            <span className="ml-1 font-mono text-2xs text-content-subtle">{correlation}</span>
          )}
        </p>
      </Frame>
    );
  }

  /** 📁 **State 07** — *"cards skeletonised at declared footprints."* */
  if (systems.isPending) {
    return (
      <Frame>
        <div aria-hidden className="space-y-3 px-[18px] py-[15px]">
          <div className="h-4 w-1/2 animate-pulse rounded bg-surface-sunken" />
          <div className="h-4 w-2/3 animate-pulse rounded bg-surface-sunken" />
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
    <section
      aria-labelledby="home-integration-health-heading"
      data-testid="home-integration-health"
      className="overflow-hidden rounded-xl border border-border-soft bg-surface shadow-e1"
    >
      <div className="flex items-center gap-2 border-b border-border-soft px-[18px] py-3">
        <h3
          id="home-integration-health-heading"
          className="text-label font-semibold text-content"
        >
          Integration health
        </h3>
        {count === undefined ? null : (
          <span className="text-2xs font-semibold tabular-nums text-content-subtle">{count}</span>
        )}
      </div>
      {children}
    </section>
  );
}
