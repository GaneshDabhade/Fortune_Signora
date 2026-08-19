'use client';

import { useEffect, useState } from 'react';

import { cn } from '@/lib/design/cn';
import { useReadiness, servicesOf, type ServiceState } from '@/lib/query/hooks/readiness';
import { statusLabelVisible } from '@/lib/shell/top-bar';

/**
 * **Is Signora degraded** — [TASK-1484](../../../docs/BACKLOG.md) ⓑ, against
 * 📁 `Fortune Signora App Shell.dc.html` **§07**.
 *
 * > 📁 ***"System status is a persistent pill in the top bar rather than a
 * > banner — degradation is a fact about the product, not an interruption, and
 * > it expands into detail on click."***
 *
 * ## 🔴 A sibling of `OfflineStatus`, not a replacement for it
 *
 * ✅ **[`offline-status.tsx`](offline-status.tsx) is CORRECT and stays.** ⚡ It
 * cites §07 to justify its placement and the citation is right — ⛔ **but it
 * answers *is this browser online* and §07 asks *is Signora degraded*.**
 * ⚠️ **Two different facts were sharing one slot, and the shipped one was the
 * narrower.**
 *
 * ## ⚠️ Five services are drawn and two are published
 *
 * 📁 The design's panel lists **Application · CRM sync · Scoring service ·
 * Conversation ingest · Exports**. ⛔ **`GET /ready` reports the database and
 * the authentication subsystem, and nothing else does.** ✅ **So two rows are
 * rendered** — 📁 TASK-1484's own bound: *"render what `/ready` returns and
 * nothing else"*, and *"do not invent a service the payload does not report."*
 *
 * ⚡ **The rows are DERIVED from the payload rather than declared**, so a
 * service the API stops reporting stops being listed instead of leaving a row
 * that is always green.
 *
 * ## ⛔ What it does not do
 *
 * **No status-page link, no incident feed, no history, no subscription** — 📁
 * the row forbids each by name, and every one of them is a promise about
 * something the product does not operate.
 */

/** 📁 *"Green shows a dot only below 1280px; amber and red always keep their label."* */
const HIDE_LABEL_BELOW = 1280;

export function SystemStatus({ className }: { className?: string }) {
  const readiness = useReadiness();
  const [open, setOpen] = useState(false);
  /**
   * ⛔ **Not read during render.** The server has no `window`, so reading its
   * width in the render body disagrees with the markup Next produced — the same
   * hydration rule `offline-status.tsx` and `use-rail-collapse.ts` document.
   */
  const [width, setWidth] = useState(HIDE_LABEL_BELOW);
  useEffect(() => {
    const sync = () => setWidth(window.innerWidth);
    sync();
    window.addEventListener('resize', sync);
    return () => window.removeEventListener('resize', sync);
  }, []);

  /**
   * ⛔ **Silent while it does not know.** ⚡ A pill that said *"degraded"*
   * because a read had not returned would report an outage on every cold load —
   * 📁 [P-A](../../../docs/DOMAIN_DISCOVERY_REGISTER.md) is the same rule for an
   * empty result, and 🔴 [B-290](../../../docs/BUGS.md) is what rendering a
   * fallback as a settled fact costs one surface over.
   *
   * ⚠️ **And silent when the READ ITSELF failed**, which is a different fact
   * from a degraded product: 📁 `offline-status.tsx` already owns *"you cannot
   * reach anything"*, and two pills saying it would be two answers to one
   * question.
   */
  if (readiness.data === undefined) return null;

  const services = servicesOf(readiness.data);
  const degraded = readiness.data.status === 'degraded';
  const down = services.some((service) => service.state === 'unavailable');
  const tone = down ? 'down' : degraded ? 'degraded' : 'healthy';
  const labelVisible = statusLabelVisible(tone, width);

  /** 📁 The design's own words for the pill's two states. */
  const label = down
    ? 'Service unavailable'
    : degraded
      ? 'Partial degradation'
      : 'All systems normal';

  return (
    <div className={cn('relative', className)}>
      <button
        type="button"
        onClick={() => setOpen((was) => !was)}
        aria-expanded={open}
        // ♿ **The name never hides**, whatever the viewport does to the label:
        // 📁 the design hides a green pill's TEXT below 1280px, which is a
        // statement about pixels and never about who is told.
        aria-label={label}
        data-status={tone}
        data-testid="system-status"
        className={cn(
          'flex items-center gap-2 rounded-full border px-3 py-1 text-xs font-medium',
          'transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent',
          tone === 'down'
            ? 'border-danger/30 bg-danger-subtle text-danger'
            : tone === 'degraded'
              ? 'border-warning/30 bg-warning-subtle text-warning'
              : 'border-border bg-surface-sunken text-content-muted',
        )}
      >
        {/* 📁 *"a dot"* — ⚡ and below 1280px on a healthy product it is the
            whole pill, which is what the rule is for. */}
        <span
          aria-hidden
          className={cn(
            'h-2 w-2 shrink-0 rounded-full',
            tone === 'down' ? 'bg-danger' : tone === 'degraded' ? 'bg-warning' : 'bg-success',
          )}
        />
        {labelVisible ? <span>{label}</span> : null}
      </button>

      {/* 📁 *"it expands into detail on click"* — the design's 360px panel. */}
      {open ? (
        <div
          role="status"
          data-testid="system-status-detail"
          className="absolute right-0 z-20 mt-2 w-[360px] rounded-lg border border-border bg-surface shadow-lg"
        >
          <div className="flex items-center gap-2.5 border-b border-border-soft px-4 py-3">
            <span
              aria-hidden
              className={cn(
                'h-2 w-2 shrink-0 rounded-full',
                tone === 'down' ? 'bg-danger' : tone === 'degraded' ? 'bg-warning' : 'bg-success',
              )}
            />
            <span className="text-sm font-semibold text-content">{label}</span>
            {/* ⛔ **Not the design's *"Updated 2m ago"*.** ⚡ The pill re-reads on
                a fixed interval, so *"just now"* is true for most of it and
                false for the rest — **a relative time nothing recomputes is the
                one thing on this panel that could lie.** ✅ Said as the
                interval, which is a fact about the product. */}
            <span className="ml-auto text-2xs text-content-subtle">Checked every 30s</span>
          </div>
          <ul>
            {services.map((service) => (
              <Row key={service.name} service={service} />
            ))}
          </ul>
        </div>
      ) : null}
    </div>
  );
}

/** 📁 The design's row — *"a dot · the name · its state, right-aligned."* */
function Row({ service }: { service: ServiceState }) {
  const ok = service.state === 'ok';
  return (
    /* ⚠️ **`flex-wrap`, and it was missing.** ⛔ Without it the detail's
       `basis-full` did not start a new line — **the API's sentence sat beside
       the state instead of under the row**, and the state stopped being
       right-aligned. ⚡ Found by looking at the rendered panel, not by a test:
       every assertion about it was about the TEXT. */
    <li className="flex flex-wrap items-center gap-2.5 border-b border-border-soft px-4 py-2.5 text-xs last:border-b-0">
      <span
        aria-hidden
        className={cn(
          'h-[7px] w-[7px] shrink-0 rounded-full',
          service.state === 'unavailable'
            ? 'bg-danger'
            : ok
              ? 'bg-success'
              : 'bg-warning',
        )}
      />
      <span className="text-content">{service.name}</span>
      <span
        className={cn(
          'ml-auto font-semibold',
          service.state === 'unavailable'
            ? 'text-danger'
            : ok
              ? 'text-success'
              : 'text-warning',
        )}
      >
        {ok ? 'Normal' : service.state === 'unavailable' ? 'Unavailable' : 'Degraded'}
      </span>
      {/* ⚡ **The API's own sentence, when it sent one** — 📁 `/ready` carries
          `authentication_detail`, and paraphrasing it here would be a second
          vocabulary for one fact. */}
      {service.detail === null ? null : (
        <span className="basis-full text-2xs text-content-subtle">{service.detail}</span>
      )}
    </li>
  );
}
