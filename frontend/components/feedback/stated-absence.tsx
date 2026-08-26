import type { LucideIcon } from 'lucide-react';

import { Button, Card, CardBody, EmptyState, SystemState } from '@/components/ui';

/**
 * **A read failed, and the surface says so — one implementation, not nine.**
 *
 * [P-A · Stated absence] was ratified 2026-08-05 with **nine recorded
 * instances and zero implementations**, and the Register's own annotation was
 * *"name before the ninth"*. **The ninth arrived as [C-226]** — six at once on
 * one screen, fixed by four different lanes. **Every one of those fixes was
 * correct and local, which is exactly how nine became nine.**
 *
 * ### What was actually duplicated, measured before this was written
 *
 * Six `Unavailable()` functions across `page.tsx`, the account brief,
 * `validation.tsx`, `offering.tsx`, `observations.tsx` and `research.tsx`.
 * **Three different chrome shapes** — a page-level `EmptyState`, a `Card`, and
 * a bare paragraph — **and one sentence pattern repeated verbatim in all six**:
 *
 * > *Signora could not load __ . Nothing has changed — reload to try again.*
 *
 * **So the duplication was never the chrome; it was the sentence.** The three
 * shapes are real and each is right where it sits: a whole page that failed
 * needs an icon and a heading, and a paragraph inside a card must not grow
 * one. **This keeps the three and removes the six.**
 *
 * ### Why the sentence has three obligatory parts
 *
 * **① What could not be loaded**, because *"something went wrong"* tells a
 * seller nothing they can act on. **② What is still true** — *nothing has
 * changed*, *nothing has been lost* — because the fear a failed read creates
 * is that the data is gone, and it is the fear that makes people re-enter
 * work they did not need to. **③ What to do**, which is always *reload*,
 * because that is the only thing that is ever true.
 *
 * ⛔ **It cannot say nothing.** `subject` has no default: a caller with
 * nothing to say about what failed has not thought about it, and the type
 * refuses them rather than rendering a blank (§2, *types should make
 * incorrect architecture impossible*).
 */
export function StatedAbsence({
  subject,
  reassurance = 'Nothing has changed',
  as = 'inline',
  icon,
  title,
  announce = 'polite',
  correlationId,
  onRetry,
}: {
  /** What could not be loaded, in the customer's words and lower case:
   * *"what changed at this account"*, *"your accounts"*. Completes the
   * sentence *Signora could not load __*. */
  subject: string;
  /** What is still true despite the failure. Defaults to the sentence that is
   * true almost everywhere; a surface where something stronger holds — *"nothing
   * your organization has declared has been lost"* — says so. */
  reassurance?: string;
  /** Which of the three shapes. **Not a style choice**: `page` is for a whole
   * screen that failed, `card` for a section that owns its own box, `inline`
   * for a paragraph inside somebody else's. */
  as?: 'page' | 'card' | 'inline';
  /** `page` only. */
  icon?: LucideIcon;
  /** `page` only. Defaults from `subject` so the two cannot disagree. */
  title?: string;
  /** **How a screen reader learns about it.** Politely by default: a page
   * whose sections each failed would otherwise interrupt several times, and
   * `toast.tsx` already established that announcing politely beats
   * interrupting. **`assertive` is for a failure that interrupted something
   * the customer had just done**, where saying nothing until they next move
   * focus is too late.
   *
   * ⚠️ **Added because removing it was a regression.** `segments.tsx` used
   * `role="alert"` and a test asserted it; folding nine implementations into
   * one would have quietly dropped that, and §20c calls an accessibility loss
   * a defect rather than a trade-off. */
  announce?: 'polite' | 'assertive';
  /**
   * 🔴 **📁 System States `rules` ⑤ — *"One primary action: a filled brand
   * button doing the most useful thing available. **'Reload the page' is a
   * last resort, never the first offer.**"***
   *
   * ⛔ **This component offered reload as the ONLY route out, in prose, with
   * no control** — *"— reload to try again"* — **on 29 of the product's 31
   * failure surfaces.** ⚡ **Both layers already had the capability**:
   * [`SystemState`](../ui/system-state.tsx) takes a `primaryAction` and its
   * own docstring quotes the rule verbatim, and
   * [`ErrorState`](../ui/error-state.tsx) has offered `onRetry` all along —
   * **used by exactly one caller.** 📁 [B-299](../../../docs/BUGS.md) ⑩.
   *
   * ⚠️ **And reload is not merely a worse button.** 📁 The same document's
   * rule ② is *"work is preserved: drafts, filters, selection and scroll are
   * held through any recoverable failure"* — ⛔ **and a page reload discards
   * every one of them.** ⚡ **So the prose instruction was telling a customer
   * to destroy their own state to recover a single failed read.**
   *
   * ✅ **Optional, and its absence is honest rather than lazy** — ⛔ **a
   * failure with nothing to retry must not grow a button that does nothing.**
   * ⚡ **Where it IS given, the sentence drops the reload instruction**, so
   * the screen never offers both and never puts the last resort first.
   */
  onRetry?: () => void;
  /**
   * 📁 **The grammar's rule ③** — *"identifiers are copyable: the single thing
   * that makes a support conversation short"* — ⚡ **and it reaches
   * `SystemState`, which owns how one is rendered.**
   *
   * ⚠️ **Added by [TASK-1429](../../../docs/BACKLOG.md) to PRESERVE a
   * behaviour rather than to add one.** ⛔ **`components/feedback/error-boundary.tsx`
   * printed `Reference: {correlationId}` and a test asserted it**; converging
   * that surface onto the ladder without this prop would have silently dropped
   * the identifier — **the class of regression `announce` above was added for,
   * one row later.** ✅ **It arrives copyable, which the retired one was not.**
   *
   * ⛔ **`region` and `card` only.** A `page`-shape absence renders through
   * `EmptyState`, which states an absence rather than a failure and has no
   * identifier to show.
   */
  correlationId?: string;
}) {
  /**
   * ⚡ **The sentence ends differently when there is a control to press.**
   * ⛔ **Never both** — 📁 rule ⑤ makes reload *"a last resort, never the
   * first offer"*, and a sentence saying *reload* above a button saying
   * *Try again* puts the last resort first in reading order.
   */
  const sentence =
    onRetry === undefined
      ? `Signora could not load ${subject}. ${reassurance} — reload to try again.`
      : `Signora could not load ${subject}. ${reassurance}.`;

  if (as === 'page') {
    return (
      /**
       * 🔴 **It announced NOTHING, and 📁 `System States` §4.1.3 leaves no
       * third option**: ***"Region errors and retries announce politely. Only
       * a state that ends the session — 500, maintenance — announces
       * assertively, once."***
       *
       * ⚡ **Polite is unambiguous here even though the SCOPE is not.** 📁
       * `system-state.tsx`'s own `politeness()` gives **region and page the
       * same answer** — `status`/`polite` — and reserves `alert`/`assertive`
       * for `app` and `platform`. **A failed read is neither.**
       *
       * ⚠️ **Found by QE, in a browser, and reported as an observation they
       * had deliberately NOT established.** ⛔ **They were right not to**: the
       * absence of `role="alert"` is correct, and it was the absence of any
       * announcement that was the defect.
       *
       * ⛔ **The `h1` half is NOT fixed here and needs a ruling** — 📁 §1.3.1
       * asks a full-page state for *"an h1 that names what happened"*, and
       * `EmptyState` renders a `<p>` because it is shared with genuine empty
       * states where an `h1` would be wrong. 🔴
       * [C-1557](../../../docs/LANE_COORDINATION.md).
       */
      <div role="status">
        <EmptyState
          icon={icon}
          title={title ?? `Could not load ${subject}`}
          description={sentence}
        />
      </div>
    );
  }

  /**
   * ⚡ **[TASK-1428](../../../docs/BACKLOG.md) — this is now the ladder's
   * region scope rather than a second failed-read implementation.**
   * 📁 **[C-252](../../../docs/LANE_COORDINATION.md)'s ruling**: *"`StatedAbsence`
   * becomes a CALLER of `SystemState` at region scope — neither deleted, one
   * owns the sentence and one owns the scope."*
   *
   * ⛔ **The sentence is unchanged and no caller changed.** ✅ **What arrives
   * is the ladder's**: `role`/`aria-live` derived from the scope rather than
   * chosen here, and one failed-read presentation whether a read returned an
   * error or a component threw.
   */
  const region = (
    <SystemState
      scope="region"
      state="region-error"
      description={sentence}
      {...(correlationId === undefined ? {} : { correlationId })}
      {...(onRetry === undefined
        ? {}
        : {
            /* 📁 **Rule ⑤'s *"filled brand button"*** — `primary` is that, and
               `SystemState` already lays a `primaryAction` out. ⛔ **Nothing
               about the arrangement is decided here**; this passes the control
               and the ladder places it. */
            primaryAction: (
              <Button variant="primary" size="sm" onClick={onRetry}>
                Try again
              </Button>
            ),
          })}
    />
  );

  /**
   * 🔴 **The one caller the ladder cannot yet carry** —
   * [C-258](../../../docs/LANE_COORDINATION.md) ②.
   *
   * 📁 **The ladder's `4.1.3`**: *"only a state that ends the session
   * announces assertively."* ⚠️ **`segments.tsx` interrupts because the
   * failure interrupted something the customer had just done**, which is not
   * a session-ending state and is still worth interrupting for — **and the
   * prop exists because removing it was a regression.**
   *
   * ⛔ **Left as it was rather than downgraded to polite.** **Composing it
   * would fail `segments.test.tsx`, and making that test pass by editing its
   * assertion is the defect, not the fix.** ✅ **It rejoins the ladder the
   * moment [C-258](../../../docs/LANE_COORDINATION.md) ② is ruled.**
   */
  const paragraph =
    announce === 'assertive' ? (
      <p role="alert" className="text-sm leading-6 text-content-muted">
        {sentence}
      </p>
    ) : (
      region
    );

  return as === 'card' ? (
    <Card>
      <CardBody>{paragraph}</CardBody>
    </Card>
  ) : (
    paragraph
  );
}
