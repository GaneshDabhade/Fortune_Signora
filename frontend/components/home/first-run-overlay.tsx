/**
 * **The first-run overlay** — [TASK-1424](../../../docs/BACKLOG.md), against 📁
 * `Fortune Signora Authenticated Entry.dc.html` rule 20 and
 * `Fortune Signora Home.dc.html`.
 *
 * ## 🔴 It is an overlay, not a composition, and the row's title says otherwise
 *
 * 📁 **Rule 20, verbatim**: *"First login, workspace ready → **Home, with the
 * first-run overlay**: one sentence on what this is, one on what to do,
 * dismissible forever."* 📁 **And Home agrees**: *"Adds the first-run overlay
 * **over whichever composition resolved**."*
 *
 * ⛔ **So this must never become a fifth composition.** ⚡ It renders above
 * whatever rules 1–5 already resolved — executive, seller, operations or
 * activation — **and the cards underneath stay exactly as they were.** A
 * composition that replaced them would make a new person's Home a different
 * screen from the one they return to, which is the opposite of what an
 * orientation is for.
 *
 * ## 🔴 Sentence two must be true of the composition it sits over
 *
 * ⚠️ **It read *"Start by connecting a CRM below"* on every composition**, and
 * 📁 the overlay renders *"over whichever composition resolved"* — **so a seller
 * whose workspace was already connected was told to start with a card that was
 * not on the page.** ⛔ **A first screen that points at something absent is
 * worse than one that says nothing**, and it is the same false-claim class
 * [§2](../../../CLAUDE.md) refuses.
 *
 * ⚠️ **Found in a browser and by nothing else.** The sentence is a string
 * literal; no type, no test and no lint can know that the card it names is
 * filtered out of three of the four compositions.
 *
 * ⚠️ **📁 The copy table has no id for this sentence.** HM-COPY-01…12 cover the
 * states and none covers the overlay, so **the three non-activation sentences
 * below are authored rather than quoted** — 📁 [C-1531](../../../docs/LANE_COORDINATION.md)
 * carries them for ratification. ⛔ **Flagged rather than left false**: the
 * design's own instruction is *"one sentence on what to do"*, and a sentence
 * describing the wrong page does not satisfy it.
 *
 * ## ⛔ Two sentences, and the count is the specification
 *
 * 📁 ***"One sentence on what this is, one on what to do."*** ⚡ **Not a tour,
 * not a checklist, not a modal that traps.** The activation cards are the
 * checklist and they are already on the page; **a second one here would be two
 * lists competing to be first.**
 *
 * ## ✅ Dismissal is server-side, and the design says so twice
 *
 * 📁 ***"Dismissible forever"***, and its sibling activation rule: *"nothing
 * about activation lives in `localStorage`."* ⛔ **A dismissal in a browser is
 * one a person loses when they change machine** — which turns *forever* into
 * *until Tuesday*. ✅ **`POST …/preferences/first-run-dismissal` holds it**, and
 * the moment is the server's.
 */

'use client';

import { X } from 'lucide-react';

import type { Composition } from '@/lib/home/composition';
import { useDismissFirstRun, usePreferences } from '@/lib/query/hooks/preferences';
import { useWorkspaceContext } from '@/lib/state/workspace-provider';

/**
 * 📁 **Sentence two — *"what to do"*, per composition.**
 *
 * ⚡ **Activation's is the design's**, drawn from its own first step. ⚠️ **The
 * other three are authored** and are [C-1531](../../../docs/LANE_COORDINATION.md);
 * each names something that is actually on that composition's page.
 */
const WHAT_TO_DO: Readonly<Record<Composition, string>> = Object.freeze({
  activation:
    'Start by connecting a CRM below — everything on this page fills in from there.',
  seller: 'Start with what needs you today — every item below says why it is there.',
  executive: 'Start with the figures below — each one says what it was derived from.',
  revenue_operations:
    'Start with the health of your connections below — each one says what needs a person.',
});

export function FirstRunOverlay({ composition }: { composition: Composition }) {
  const { activeWorkspace } = useWorkspaceContext();
  const workspaceId = activeWorkspace?.id ?? null;
  const preferences = usePreferences(workspaceId);
  const dismiss = useDismissFirstRun(workspaceId);

  /**
   * ⛔ **Absent until the answer is known, and this is P-A rather than a
   * loading nicety.** 📁 *a failed read must never render as an empty result* —
   * ⚡ **and an unread preference must never render as *not yet dismissed***,
   * because that would show the overlay again to somebody who closed it, on
   * every slow connection.
   *
   * ⚠️ **An error is also silence here, deliberately.** A failed read of a
   * preference is not something to tell a customer about **on the first screen
   * they have ever seen** — and the cost of being wrong is one missing
   * greeting, not a missing capability.
   */
  if (preferences.data === undefined || preferences.data.first_run_dismissed) return null;

  return (
    <section
      // ⚡ **A labelled region, not a dialog.** 📁 The design says *overlay*,
      // and rule 20's own words are two sentences over the composition — ⛔ a
      // `role="dialog"` would trap focus and make an orientation something a
      // person has to escape.
      aria-labelledby="first-run-heading"
      /* 🔴 **`bg-accent-soft` was the wrong role.** ⚠️ **`--accent-soft` is the
         blue ramp's step 300** — 📁 Design System v2's `BLUE[3]` —
       **a FILL for a progress track or a chart band, not a ground for a strip
         of text.** ⛔ Measured on Home at 1440: a solid mid-blue block across the
         content region, against every other strip in the product, which are
         tints.
         ⚡ **`accent-subtle` IS the design's `--brand-tint`**, which
         is what §07 and Home both draw an orientation strip on — and it is the
         same token the border already used, so the strip now reads as one
         object rather than a fill inside an outline. */
      className="flex flex-wrap items-start gap-x-4 gap-y-2 rounded-lg border border-accent-subtle bg-accent-subtle px-4 py-3.5"
    >
      <div className="flex flex-col gap-1">
        <h2 id="first-run-heading" className="text-sm font-semibold text-content">
          {/* 📁 **Sentence one — what this is.** */}
          Signora reads what your systems already record and tells you which accounts need
          you.
        </h2>
        <p className="text-sm leading-6 text-content-muted">
          {/* 📁 **Sentence two — what to do.** ⛔ It names the step below rather
              than repeating it: the activation cards are the checklist. ⚠️ **And
              it names the step that is actually there** — see the header. */}
          {WHAT_TO_DO[composition]}
        </p>
      </div>

      <button
        type="button"
        onClick={() => dismiss.mutate()}
        // ⚠️ **Disabled while the write is in flight**, so a second click
        // cannot start a second request. ⛔ The server is idempotent and would
        // answer the same; this is about the control not lying about what it
        // is doing.
        disabled={dismiss.isPending}
        aria-label="Dismiss"
        className="ml-auto shrink-0 rounded p-1 text-content-subtle transition-colors hover:text-content disabled:cursor-not-allowed"
      >
        <X className="h-4 w-4" aria-hidden />
      </button>
    </section>
  );
}
