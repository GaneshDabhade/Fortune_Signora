'use client';

import { useState } from 'react';

import { cn } from '@/lib/design/cn';
import { admitBanners, type BannerKind } from '@/lib/shell/constitution';

/**
 * **The shell's banner region** — [TASK-1408](../../../docs/BACKLOG.md),
 * against `docs/design-snapshot/screens/Fortune Signora App Shell.dc.html`
 * ([D-138](../../../docs/DECISION_REGISTER.md)).
 *
 * > 📁 **Rule 10 — *"At most two banners, environment before commercial."***
 *
 * ## ⚡ The ordering is a safety property, not a layout preference
 *
 * 📁 **The environment banner exists for exactly three states**: *"sandbox,
 * impersonation and read-only maintenance. **Never for marketing.**"* ⛔ **Each
 * one changes what the person believes they are doing** — *"Viewing as J.
 * Okafor · every action is logged"* is the sentence that stops somebody
 * thinking they are themselves.
 *
 * ⚡ **A commercial banner above it would push that sentence down the page**,
 * and on a short viewport off it. **That is why the order is fixed in
 * {@link admitBanners} rather than left to call order**, and why the third
 * banner is dropped rather than stacked.
 *
 * ## ⛔ Two things this region refuses
 *
 * **A risky environment banner has no dismiss control at all** — 📁 *"dismissible
 * only when the state is not risky."* **Not a disabled button: absent.** A
 * control that visibly cannot be used still reads as *"this is optional."*
 *
 * **Commercial banners are suppressed entirely in sandbox** — 📁 *"suppressed
 * entirely inside sandbox"*, ⛔ **not queued for later.** A trial countdown
 * over a copy of production is an upsell against data that is not real, and
 * 📁 the System States rules name *"no upsell to someone without the authority
 * to buy"* as the same family.
 *
 * ## ⛔ What it does not do
 *
 * **It decides nothing about what a banner says.** 📁 **Rule 14**: *"Every new
 * shell capability is an amendment to this document, not a local decision"* —
 * **so the caller supplies the content and this region supplies the law.**
 * ⚠️ **And it owns no navigation**: [D-193](../../../docs/DECISION_REGISTER.md)
 * says modules register capabilities rather than issuing redirects, and
 * [D-194](../../../docs/DECISION_REGISTER.md) already found five modules
 * routing. **A banner's action is a node the caller passes in.**
 */

export interface ShellBanner {
  kind: BannerKind;
  /**
   * ⚠️ **Risky means impersonation or read-only maintenance, not sandbox.**
   * It is the input that decides dismissibility — 📁 *"dismissible only when
   * the state is not risky."*
   */
  risky?: boolean;
  /** 📁 The design's bold lead — *"Sandbox."*, *"Viewing as J. Okafor."* */
  title: string;
  /** 📁 The sentence after it, which carries the consequence. */
  body: string;
  /** 📁 *"One primary action"* — a node, because this region does not route. */
  action?: React.ReactNode;
}

const TONE: Record<'risky' | 'environment' | 'commercial', string> = {
  // 📁 Impersonation is drawn at risk severity: it is the state most costly
  // to forget you are in.
  risky: 'bg-danger-subtle text-danger',
  environment: 'bg-warning-subtle text-warning',
  commercial: 'bg-accent-subtle text-accent',
};

export function ShellBanners({
  banners,
  inSandbox = false,
}: {
  banners: readonly ShellBanner[];
  inSandbox?: boolean;
}) {
  // Session-scoped, per rule: *"dismissible for the session"*. Deliberately
  // component state rather than storage — a banner that stays dismissed
  // across sessions is one the customer never sees again.
  const [dismissed, setDismissed] = useState<Set<number>>(new Set());

  // ⚡ **The law is applied in one place and it is not this file.**
  // `admitBanners` orders, suppresses and caps; this component renders
  // whatever survives that.
  const admitted = admitBanners(banners, inSandbox);

  return (
    <div data-testid="shell-banners">
      {admitted.map(({ banner: source, rule }, i) => {
        if (dismissed.has(i)) return null;

        const tone =
          rule.kind === 'environment' && !rule.dismissible ? 'risky' : rule.kind;

        return (
          <div
            key={`${rule.kind}-${i}`}
            role="status"
            data-kind={rule.kind}
            data-dismissible={rule.dismissible}
            className={cn(
              'flex flex-wrap items-center gap-x-3 gap-y-1 px-4 py-2 text-sm',
              TONE[tone],
            )}
          >
            <span className="font-semibold">{source.title}</span>
            <span className="text-content-muted">{source.body}</span>
            <span className="ml-auto flex items-center gap-3">
              {source.action}
              {/* ⛔ **Absent, not disabled, when the state is risky.** */}
              {rule.dismissible ? (
                <button
                  type="button"
                  onClick={() => setDismissed((d) => new Set(d).add(i))}
                  className="rounded px-1 text-content-subtle transition-colors hover:text-content "
                  aria-label={`Dismiss: ${source.title}`}
                >
                  Dismiss
                </button>
              ) : null}
            </span>
          </div>
        );
      })}
    </div>
  );
}
