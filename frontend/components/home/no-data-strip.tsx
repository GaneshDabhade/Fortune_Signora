'use client';

import { systemName } from '@/components/integrations/connection-center';
import { HM_COPY_05 } from '@/lib/home/copy';
import type { IntegrationSystem } from '@/lib/api/types';

/**
 * 📁 **Home's state 05 — `state.nodata`, *"no meaningful business data"***.
 *
 * > *"Sync succeeded AND record count is zero. **Distinct from state 06b.**
 * > Composition renders with every card in its no-data state, plus **one strip
 * > naming which source returned nothing** and when. **Not the activation
 * > composition — setup is complete.**"*
 *
 * ### 🔴 Why this is a separate component from the no-results card
 *
 * 📁 **Contract item 4 makes it a violation to share one**: *"`state.nodata` and
 * `state.noresults` are separate branches with separate copy IDs. A single
 * shared empty component is a contract violation."* 📁 And **P-02** gives the
 * reason: *"different cause, different copy, different tint, different action.
 * Conflating them sends someone to review a pipeline that does not exist, or
 * implies a setup problem on a quiet Tuesday."*
 *
 * ⚡ **So state 06b lives in the attention card** — a success, green, *"review
 * your pipeline"* — **and state 05 lives here**: a strip, warn tint, *"check
 * what is synced"*. **Neither imports the other.**
 *
 * ### ⚠️ *"Sync succeeded"* is read as *"a working connection"*, and that is stronger
 *
 * ⛔ **No contract publishes a sync outcome.** 📁 `IntegrationSystem.working` is
 * *"at least one connection Signora can currently use — not merely present"*,
 * which is **a stronger claim than a sync having finished**, not a weaker one:
 * a connection whose credential silently lost a permission reads `false` here
 * and would have read *"succeeded"* on a stored sync flag. **Same reading the
 * activation module already takes for completion.**
 *
 * ### ⛔ Not on the activation composition
 *
 * 📁 The design says so twice — *"setup is complete"*. ⚡ A workspace that has
 * connected nothing has no source to name, and the activation composition is
 * already telling that person exactly what to do.
 */
export interface NoDataStripProps {
  readonly systems: readonly IntegrationSystem[];
  /** The workspace's own record count. `null` while unknown. */
  readonly accounts: number | null;
  /** ⛔ **Suppressed on activation** — the design excludes it by name. */
  readonly activation: boolean;
  readonly loading: boolean;
}

export function NoDataStrip({
  systems,
  accounts,
  activation,
  loading,
}: NoDataStripProps) {
  // ⛔ **Silent until both facts are known.** ⚡ A strip saying *"it returned no
  // opportunities"* while the count is still in flight would accuse a working
  // integration of emptiness on every slow connection — and it is the strip a
  // person would act on by opening their CRM.
  if (loading || activation || accounts === null) return null;

  const working = systems.filter((system) => system.working);
  // 📁 *"Sync succeeded"* — nothing has succeeded if nothing is connected. That
  // workspace is state 01, and the activation composition is already saying so.
  if (working.length === 0) return null;
  // 📁 *"…AND record count is zero."* ⛔ **Zero exactly.** A workspace with one
  // account is state 06, however thin it looks.
  if (accounts !== 0) return null;

  const source = working[0]!;

  return (
    /**
     * ♿ **`role="status"`** — 📁 the same rule the disconnected strip follows:
     * a fact about the product, not an interruption, and out of the assertive
     * queue the greeting already occupies (4.1.3, one announcement per entry).
     */
    <div
      role="status"
      className="flex flex-wrap items-center gap-x-3 gap-y-2 rounded-lg border border-warning-line bg-warning-subtle px-4 py-3"
    >
      {/* 📁 The design's own mark for this state — `!` on a surface chip, warn
          tinted, distinct from the disconnected strip's danger tint. */}
      <span
        aria-hidden
        className="grid h-5 w-5 flex-none place-items-center rounded-sm bg-surface text-xs font-bold text-warning"
      >
        !
      </span>
      <p className="text-label leading-[1.5] text-content">
        {/* 📁 `HM-COPY-05`, verbatim, with the source named from what actually
            connected. ⛔ **`syncedAgo` is `null`** — nothing publishes when a
            connection last synced, and `connected_at` is when the relationship
            began rather than when data last arrived. */}
        {HM_COPY_05(systemName(source.integration), null)}
      </p>
      {/* 📁 The design's action for this state is *"Check what is synced"*, and
          ⛔ **it belongs to CRM Integrations rather than to Home** — *"activation
          and health cards link into it and never restate a connection step"*. */}
      <a
        href="/settings/connections"
        className="ml-auto inline-flex h-control-sm items-center rounded-md border border-border bg-surface px-3 text-2xs font-semibold text-content transition-colors hover:border-accent hover:text-accent "
      >
        Check what is synced
      </a>
      {/* ⛔ **No dismiss.** 📁 The design gives a dismiss only to state 11, the
          degraded strip, *"because the product is fully usable"*. **This one is
          a setup condition and stays until records arrive.** */}
    </div>
  );
}
