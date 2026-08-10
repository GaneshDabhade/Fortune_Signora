'use client';

import { cn } from '@/lib/design/cn';
import { useUtilityPanelPresent } from './utility-panel';

/**
 * **Skip links** — [TASK-1444](../../../docs/BACKLOG.md), 📁 App Shell rule
 * **2.4.1**: *"Skip links: to content, to navigation, to the utility panel —
 * visible on focus."*
 *
 * ## 🔴 There were none, and that is a WCAG A failure rather than a nicety
 *
 * ⛔ **`grep` found zero.** ⚡ **Without them a keyboard user meets the rail's
 * every destination before reaching the content on every single page load** —
 * and the rail is the first thing in the tab order by design.
 *
 * ## ⚡ Visible on focus, which is the whole mechanism
 *
 * ⛔ **A skip link hidden with `display: none` is not focusable and does
 * nothing.** ✅ **This moves it off-screen and brings it back on focus**, which
 * is the only technique that keeps it in the tab order while invisible to a
 * pointer user.
 *
 * ## ✅ Three targets, and the third arrived with its landmark
 *
 * 📁 **The design names content, navigation and the utility panel.**
 * ⚠️ **This block used to say the third *"does not exist"*** — ✅ **it does
 * now**, built by [TASK-1433](../../../docs/BACKLOG.md).
 *
 * 🔴 **But the rule that kept it absent still binds, and it is why the link is
 * CONDITIONAL rather than added**: *a skip link to a missing landmark sends a
 * keyboard user nowhere and is worse than the omission.* ⛔ **The design gives
 * the panel no width below 1024**, so an unconditional third link would be
 * exactly that failure, on every phone. ✅ **`useUtilityPanelPresent` is the
 * one source both this and the panel read**, so they cannot disagree.
 */

/** ⚡ The landmark ids the shell renders, so a link and its target agree. */
export const SKIP_TARGETS = {
  content: 'shell-content',
  navigation: 'shell-navigation',
  utilityPanel: 'shell-utility-panel',
} as const;

/** ⚡ Re-exported so the panel names its own landmark from one place. */
export const UTILITY_PANEL_TARGET = SKIP_TARGETS.utilityPanel;

export function SkipLinks() {
  const panelPresent = useUtilityPanelPresent();

  return (
    // ⛔ **First in the DOM.** A skip link that is not first is a skip link
    // somebody has already tabbed past.
    <div className="absolute left-0 top-0 z-50">
      {[
        { href: `#${SKIP_TARGETS.content}`, label: 'Skip to content' },
        { href: `#${SKIP_TARGETS.navigation}`, label: 'Skip to navigation' },
        // ⛔ **Only when the landmark is there.** See the note above.
        ...(panelPresent
          ? [{ href: `#${SKIP_TARGETS.utilityPanel}`, label: 'Skip to the utility panel' }]
          : []),
      ].map((link) => (
        <a
          key={link.href}
          href={link.href}
          className={cn(
            // ⚡ **Off-screen, not hidden** — `sr-only` keeps it focusable,
            // and `focus:not-sr-only` is what makes rule 2.4.1's *"visible on
            // focus"* true rather than claimed.
            'sr-only focus:not-sr-only',
            'focus:absolute focus:left-2 focus:top-2 focus:z-50',
            'focus:rounded-md focus:bg-surface focus:px-3 focus:py-2',
            'focus:text-sm focus:font-medium focus:text-content focus:shadow-lg',
            // 📁 Rule 2.4.7 — the same 2px ring at 2px offset as everything
            // else in the shell.
            'focus:outline focus:outline-2 focus:outline-offset-2 focus:outline-accent',
          )}
        >
          {link.label}
        </a>
      ))}
    </div>
  );
}
