'use client';

import { ChevronRight } from 'lucide-react';
import { useId, useState } from 'react';

import { Badge } from '@/components/ui';
import type { AccountValidation, HypothesisValidation } from '@/lib/api/types';
import { cn } from '@/lib/design/cn';

/**
 * What to check before acting, and what the evidence cannot tell you.
 *
 * **The first thing Signora says that is about what a seller should do**, and
 * it needed no model: `limitations` and `suggested_validation` have been in the
 * Signal Catalog since M5A and had never been displayed.
 *
 * ### It is not a recommendation, and the wording protects that
 *
 * Nothing here is about this company. The guidance is a property of the
 * hypothesis *type* — what `expansion_opportunity` fails to prove is identical
 * for every account and every workspace. A recommendation would be specific and
 * inferred; this is neither, which is why it can be shown with no model and no
 * caveat about confidence.
 *
 * ### Why the limitations are collapsed and the checks are not
 *
 * A seller reading this has already decided the account matters and is about to
 * spend an hour on it. **The checks are what they act on; the limitations are
 * what stops them over-reading the score.** Both belong on the page and they do
 * not belong at the same volume: four hypotheses × three caveats is twelve
 * pieces of hedging, and a screen that hedges twelve times reads as a product
 * that does not believe itself.
 *
 * So the checks are open and the caveats are one disclosure away — present,
 * findable, in the accessibility tree whether open or not, and never the first
 * thing read.
 *
 * ### Why the checks are not checkboxes
 *
 * They look exactly like a checklist and there is nowhere to store a tick. **A
 * control that forgets is worse than no control**, so these are list markers.
 * When something owns per-user state, they can become real.
 */
export function ValidationBlock({ validation }: { validation: AccountValidation }) {
  if (validation.hypotheses.length === 0) return null;

  return (
    <section className="flex flex-col gap-3">
      <h2 className="text-sm font-semibold text-content">Before you act</h2>
      <ol className="flex flex-col gap-3">
        {validation.hypotheses.map((hypothesis) => (
          <li key={hypothesis.signal_id}>
            <Hypothesis hypothesis={hypothesis} />
          </li>
        ))}
      </ol>
    </section>
  );
}

function Hypothesis({ hypothesis }: { hypothesis: HypothesisValidation }) {
  return (
    <div className="flex flex-col gap-2.5 rounded-md border border-border bg-surface-raised px-4 py-3.5">
      <div className="flex flex-wrap items-baseline justify-between gap-x-3 gap-y-1">
        <h3 className="text-[0.9375rem] font-medium leading-6 text-content">
          {hypothesis.title}
        </h3>
        <Relevance relevance={hypothesis.relevance} />
      </div>

      {/* The hypothesis in the catalog's own words. **Phrased as a possibility,
          and left that way** — a signal suggests and never asserts, and a
          screen that firmed this into a statement would move the claim past
          what the evidence supports. */}
      <p className="text-sm leading-6 text-content-muted">{hypothesis.hypothesis}</p>

      <ul className="flex flex-col gap-1.5">
        {hypothesis.suggested_validation.map((step) => (
          <li key={step} className="flex gap-2 text-sm leading-6 text-content">
            <span aria-hidden className="select-none text-content-subtle">
              —
            </span>
            {step}
          </li>
        ))}
      </ul>

      <Limitations limitations={hypothesis.limitations} title={hypothesis.title} />
    </div>
  );
}

/**
 * How central this hypothesis is to the workspace's ideal customer profile.
 *
 * Shown only when it is **not** primary. A badge on every entry saying
 * "primary" is noise, and the entries are already ordered by it — the label
 * earns its place exactly when it explains why something is *lower* than the
 * reader expected.
 */
function Relevance({ relevance }: { relevance: HypothesisValidation['relevance'] }) {
  if (relevance === 'primary') return null;
  return <Badge tone="neutral">{relevance}</Badge>;
}

/**
 * What this hypothesis cannot establish.
 *
 * **A real disclosure, not a tooltip**, on the same terms as the disputed-name
 * marker: focusable, `aria-expanded`, and rendered `sr-only` rather than
 * `hidden` when closed so the content is in the accessibility tree and findable
 * by browser search either way.
 *
 * The count is on the trigger because *"three things this cannot tell you"* is
 * itself information — it sets the reader's expectation before they spend the
 * click.
 */
function Limitations({ limitations, title }: { limitations: string[]; title: string }) {
  const detailId = useId();
  const [open, setOpen] = useState(false);

  return (
    <div className="flex flex-col gap-1.5 border-t border-border pt-2.5">
      <button
        type="button"
        onClick={() => setOpen((was) => !was)}
        aria-expanded={open}
        aria-controls={detailId}
        className={cn(
          'inline-flex w-fit items-center gap-1 rounded text-xs text-content-muted',
          'transition-colors hover:text-content',
          'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent',
        )}
      >
        <ChevronRight
          aria-hidden
          className={cn('h-3.5 w-3.5 transition-transform', open && 'rotate-90')}
        />
        What {title} cannot tell you ({limitations.length})
      </button>

      <ul
        id={detailId}
        className={cn('flex flex-col gap-1.5 pl-4.5', open ? 'block' : 'sr-only')}
      >
        {limitations.map((limitation) => (
          <li key={limitation} className="text-xs leading-5 text-content-muted">
            {limitation}
          </li>
        ))}
      </ul>
    </div>
  );
}
