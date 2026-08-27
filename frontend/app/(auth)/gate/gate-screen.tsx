/**
 * **One presentation for every refused gate** —
 * [TASK-1423](../../../../docs/BACKLOG.md).
 *
 * ⚡ **One component, not eleven.** 📁 [`SystemState`](../../../components/ui/system-state.tsx)
 * records the same choice a ladder down — *"the one presentation of a system
 * state"* — and **eleven screens differing in two sentences would drift in
 * layout, heading level and focus order.**
 *
 * ⛔ **It renders in the AUTH shell, not the app shell**, and that is not a
 * layout preference: 📁 every gate here fails **before** a workspace is
 * resolved, so **a rail listing destinations inside an organization the person
 * cannot enter would be offering what the screen is refusing.**
 */

'use client';

import Link from 'next/link';
import { useEffect, useId, useRef } from 'react';

import { GATE_COPY, type GateReason } from '@/lib/entry/gates';

export function GateScreen({ reason }: { reason: GateReason }) {
  const copy = GATE_COPY[reason];
  const headingId = useId();
  const headingRef = useRef<HTMLHeadingElement>(null);

  /**
   * 🔴 **📁 `Security Gates` `2.4.3`**: *"Focus moves to the gate heading, then
   * to the first input."*
   *
   * ⛔ **Focus stayed wherever the previous page left it** — usually the
   * document, so a screen-reader user arriving at a refusal was told nothing
   * about why they were refused until they navigated to it themselves.
   *
   * ⚡ **This is also how the gate *announces*.** 📁 `4.1.3` asks a gate to
   * announce once; **a live region added here would announce nothing**, because
   * its content never changes after mount — the same reason
   * [`workspace-switcher.tsx`](../../../components/shell/workspace-switcher.tsx)
   * keeps its announcement outside the menu. **Moving focus to the heading is
   * the announcement on a page that IS the gate.**
   *
   * ⚠️ **The assertive-versus-polite half of `4.1.3` has no subject here** —
   * it distinguishes gates that appear OVER a live page, and every gate this
   * component renders replaces the page.
   */
  useEffect(() => {
    headingRef.current?.focus();
  }, [reason]);

  return (
    /**
     * 🔴 **📁 `1.3.1`**: *"Every gate is a **region with an accessible name**
     * describing the boundary, not the failure."*
     *
     * ⛔ **It was a bare `<div>`** — no landmark, no name — so a screen reader
     * moving by region skipped past the only content on the page.
     * ✅ **`<section>` + `aria-labelledby` is the region**, named by the
     * heading the design already writes from the customer's side.
     */
    <section aria-labelledby={headingId} className="flex flex-col gap-3">
      {/* ⚡ **An `h1`, because this IS the page.** ⛔ A refusal rendered as a
          subordinate heading reads as a note about a page rather than the
          answer to why there isn't one.
          ⚠️ **`tabIndex={-1}` makes it a focus TARGET, never a tab stop.** */}
      <h1
        id={headingId}
        ref={headingRef}
        tabIndex={-1}
        className="text-lg font-semibold text-content"
      >
        {copy.title}
      </h1>

      <p className="text-sm leading-6 text-content-muted">{copy.body}</p>

      {copy.action === null ? null : (
        <Link
          href={copy.action.href}
          className="w-fit rounded bg-accent px-3 py-1.5 text-sm font-medium text-accent-contrast hover:bg-accent-hover "
        >
          {copy.action.label}
        </Link>
      )}
    </section>
  );
}
