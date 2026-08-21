'use client';

import { systemName } from '@/components/integrations/connection-center';
import { cn } from '@/lib/design/cn';
import { HM_COPY_09 } from '@/lib/home/copy';
import type { IntegrationSystem } from '@/lib/api/types';

/**
 * 📁 **Home's states 10 and 11** — a source that stopped, and a source that is
 * behind.
 *
 * | State | Design's rule | Here |
 * |---|---|---|
 * | `10 disconnected` | *"A persistent strip above the greeting… **No card silently shows old numbers as current**"* | ✅ **not dismissible** |
 * | `11 degraded` | *"A **dismissible** strip stating the lag in plain time"* | ⚠️ **no producer** — see below |
 *
 * ### ⛔ Above the greeting, and that is the design's order
 *
 * 📁 Hierarchy 2 puts the strip above everything, because it changes how every
 * figure below it should be read.
 *
 * ### ⚠️ State 11 is not drawn, and the reason is a missing fact rather than a choice
 *
 * 📁 The design's copy is *"Salesforce is about 6 hours behind"* — ⛔ **and no
 * contract publishes a sync lag.** `Connection` carries `state`, `health` and
 * `connected_at`; **nothing says how far behind a working connection is.**
 * ⚡ **Inventing a duration would be the fabricated figure [§20c](../../../CLAUDE.md)
 * forbids**, and *"about 6 hours"* is precisely the kind of number a customer
 * would act on. 📁 `HM_COPY_10` is kept in the copy table so the string is ready
 * when a producer exists.
 */
export interface SourceStripProps {
  readonly systems: readonly IntegrationSystem[];
  readonly loading: boolean;
}

export function SourceStrip({ systems, loading }: SourceStripProps) {
  if (loading) return null;

  /**
   * ⚡ **A source that was connected and is not working now.** 📁 State 10's
   * entry condition: *"A previously connected source now has a revoked or expired
   * token."* ⛔ **`needs_attention` is the contract's own word for it**, and a
   * system with no connections at all is state 01 rather than state 10.
   */
  const broken = systems.filter((s) => s.connections.length > 0 && s.needs_attention);
  if (broken.length === 0) return null;

  const first = broken[0]!;
  const connection = first.connections[0];
  const stoppedOn =
    connection?.connected_at === undefined || connection.connected_at === null
      ? 'an earlier date'
      : new Intl.DateTimeFormat(undefined, { day: 'numeric', month: 'long' }).format(
          new Date(connection.connected_at),
        );

  return (
    /**
     * ♿ **`role="status"`, not `alert`** — 📁 the App Shell's rule that
     * degradation *"is a fact about the product, not an interruption"*. ⚡ It also
     * keeps the strip out of the assertive queue the greeting already uses.
     */
    <div
      role="status"
      className={cn(
        'flex flex-wrap items-center gap-x-3 gap-y-2 rounded-lg px-4 py-3',
        'border border-danger-line bg-danger-subtle',
      )}
    >
      <span aria-hidden className="grid h-5 w-5 flex-none place-items-center rounded-sm bg-surface text-xs font-bold text-danger">
        !
      </span>
      <p className="text-label leading-[1.5] text-content">
        {/* 📁 `HM-COPY-09`, verbatim. */}
        {HM_COPY_09(systemName(first.integration), stoppedOn, 'and are marked as such below')}
      </p>
      {/* ⛔ **No dismiss.** 📁 State 10's strip is *"not dismissible"* — the
          figures under it are stale for as long as the source is. */}
      <span className="ml-auto text-2xs font-semibold text-content-subtle">
        Reconnect from Settings → Connections
      </span>
      {/* ⛔ **No dismiss state is held here at all.** ⚠️ A `dismissed` flag with
          nothing able to set it is the decorative branch [§2](../../../CLAUDE.md)
          names — *"a guard that cannot fail is documentation pretending to be
          code"*. **It arrives with the lag producer, not before it.** */}
    </div>
  );
}
