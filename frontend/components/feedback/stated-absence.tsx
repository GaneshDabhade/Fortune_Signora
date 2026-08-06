import type { LucideIcon } from 'lucide-react';

import { Card, CardBody, EmptyState } from '@/components/ui';

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
}) {
  const sentence = `Signora could not load ${subject}. ${reassurance} — reload to try again.`;

  if (as === 'page') {
    return (
      <EmptyState
        icon={icon}
        title={title ?? `Could not load ${subject}`}
        description={sentence}
      />
    );
  }

  const paragraph = (
    <p
      role={announce === 'assertive' ? 'alert' : 'status'}
      className="text-sm leading-6 text-content-muted"
    >
      {sentence}
    </p>
  );

  return as === 'card' ? (
    <Card>
      <CardBody>{paragraph}</CardBody>
    </Card>
  ) : (
    paragraph
  );
}
