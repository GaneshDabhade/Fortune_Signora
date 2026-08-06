'use client';

import { ChevronRight } from 'lucide-react';
import { useId, useState } from 'react';

import { Badge } from '@/components/ui';
import type {
  AccountValidation,
  EvidenceState,
  HypothesisValidation,
  SupportingEvent,
} from '@/lib/api/types';
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
 * ### Why one limitation is inline and the rest are not
 *
 * A seller reading this has already decided the account matters and is about to
 * spend an hour on it. **The checks are what they act on; the limitations are
 * what stops them over-reading the score.** Both belong on the page and they do
 * not belong at the same volume: four hypotheses × three caveats is twelve
 * pieces of hedging, and a screen that hedges twelve times reads as a product
 * that does not believe itself.
 *
 * **All twelve were collapsed until R2-02, and that went one step too far.**
 * *"This is the bit I'd want my reps to read, and it's the bit they'll never
 * open."* No competitor tells a seller what their signal cannot prove — it was
 * the most differentiating sentence on the screen and the smallest text on it.
 *
 * **The original reasoning is calibrated rather than reversed.** The first
 * limitation is inline, the rest are one disclosure away. The difference
 * between calibration and hedging is not the volume — it is whether each
 * caveat sits beside the single claim it qualifies.
 *
 * ### Why the checks are not checkboxes
 *
 * They look exactly like a checklist and there is nowhere to store a tick. **A
 * control that forgets is worse than no control**, so these are list markers.
 * When something owns per-user state, they can become real.
 *
 * ### The section is always here once the page has something to say — R2-03
 *
 * It used to render nothing when nothing was live, on the same reasoning that
 * governs narration: *a panel announcing a gap is worse than the gap*. **On
 * this section that reasoning was wrong**, and the difference is worth stating
 * because it decides where the rule applies.
 *
 * A narration that does not exist is Signora having nothing to add. **Nothing
 * live is not nothing to say** — on a page whose subject is an open commitment
 * it means the commitment is running ahead of its evidence, which is the most
 * actionable sentence on the screen. And absence cannot carry it: *"the section
 * just isn't there, so I can't tell if there's nothing to check or if the
 * feature didn't load."* Two very different states rendered identically, as
 * nothing.
 *
 * So this component answers all three — **what to check**, **nothing is
 * current**, and **this did not load** — and they are told apart by what they
 * say rather than by whether they appear.
 */
export function ValidationBlock({
  validation,
  evidence,
  isError = false,
  onOpenEvidence,
}: {
  /** Undefined while the request is in flight. **Not the same as empty**: a
   * page that rendered *"nothing is current"* before the answer arrived would
   * state something it does not yet know. */
  validation: AccountValidation | undefined;
  /** How the evidence behind this account is holding up, when a commitment
   * exists to hold it up *against*. It is the only thing that can explain an
   * empty answer, and it is deliberately optional — an account nobody has
   * taken on has no such reading, and inventing one would be a claim. */
  evidence?: EvidenceState;
  /** The request failed. Rendered as its own sentence rather than as absence,
   * which is the half of R2-03 no empty state can cover. */
  isError?: boolean;
  /** Opens a recorded event in the drawer the ledger already uses. Omitted
   * where there is nowhere to send the reader — the same rule the ledger
   * follows: a control that looks clickable and goes nowhere costs more trust
   * than the missing feature does. */
  onOpenEvidence?: (businessEventId: string) => void;
}) {
  if (!isError && validation === undefined) return null;

  return (
    <section className="flex flex-col gap-3">
      <h2 className="text-sm font-semibold text-content">Before you act</h2>
      {isError ? (
        <Unavailable />
      ) : validation !== undefined && validation.hypotheses.length > 0 ? (
        <ol className="flex flex-col gap-3">
          {validation.hypotheses.map((hypothesis) => (
            <li key={hypothesis.signal_id}>
              <Hypothesis hypothesis={hypothesis} onOpenEvidence={onOpenEvidence} />
            </li>
          ))}
        </ol>
      ) : (
        <NothingCurrent evidence={evidence} />
      )}
    </section>
  );
}

/**
 * Signora is holding nothing about this account — **and that is the answer**.
 *
 * **Stated, never implied by an empty screen.** On a page about an open
 * commitment this is information: what a seller is working is no longer backed
 * by anything current. It is also the case a reader is least equipped to guess
 * at, which is why it says so in a sentence.
 *
 * **Why the wording forks on evidence state.** `stale` is the one case where
 * the product knows *why* there is nothing — the score behind this account is
 * past its validity, or there is no live score at all — and saying so turns an
 * absence into a reason. Everywhere else it says only what it knows and stops:
 * a second sentence guessing at the cause would be exactly the inference this
 * surface exists not to make.
 *
 * **Drawn as calibration, not as a warning**, on the same terms as the
 * limitations below it. Nothing has gone wrong; there is simply nothing to
 * confirm, and an alert would say the opposite.
 */
function NothingCurrent({ evidence }: { evidence?: EvidenceState }) {
  return (
    <div className="rounded-md border border-border bg-surface-raised px-4 py-3.5">
      <p className="text-sm leading-6 text-content-muted">
        {evidence === 'stale'
          ? 'There is nothing to check right now. The evidence behind this account has expired, so the score above is the last reading rather than a current one.'
          : 'There is nothing to check right now. Signora is not holding anything current about this account — nothing has been ruled out, there is simply nothing to confirm.'}
      </p>
    </div>
  );
}

/**
 * The request failed, and says so.
 *
 * **The half of R2-03 that no empty state can cover.** *"The section just isn't
 * there, so I can't tell if there's nothing to check or if the feature didn't
 * load."* Both readings were rendered as nothing, so one sentence had to become
 * two — and this is the one that says an outage is Signora's fault rather than
 * a fact about the account.
 *
 * The wording is the page's own, deliberately: a seller who sees the same
 * sentence in two places learns that it means *try again*, and a second
 * phrasing of one situation is how a product starts sounding uncertain about
 * what happened to it.
 */
function Unavailable() {
  return (
    <div className="rounded-md border border-border bg-surface-raised px-4 py-3.5">
      <p className="text-sm leading-6 text-content-muted">
        Signora could not load what to check on this account. Nothing has changed about
        the account — reload to try again.
      </p>
    </div>
  );
}

/**
 * What this account actually did to earn the hypothesis — **R2-01**.
 *
 * *"It gave me the same advice for two different companies, so I assumed it
 * wasn't really looking at either."*
 *
 * **The advice is generic and stays generic.** A check is a property of the
 * hypothesis type; making it per-account would make it a recommendation, which
 * is a different product with a different burden of proof. So nothing above
 * this line changes — what changes is that the reader can now see the generic
 * guidance is pointed at something specific.
 *
 * **The sentences are the pipeline's**, unedited, and each opens the same
 * evidence drawer the score's ledger opens. Two surfaces, one citation, one
 * wording — a second phrasing of one fact is how a customer catches a product
 * contradicting itself.
 *
 * **Placed after the checks, not before.** A reader who already trusts the
 * hypothesis acts on the checks and never reads this; one who is hesitating
 * looks down. That is what progressive disclosure means here — ordering, not a
 * collapsed panel.
 */
function Observed({
  observed,
  onOpenEvidence,
}: {
  observed: SupportingEvent[];
  onOpenEvidence?: (businessEventId: string) => void;
}) {
  if (observed.length === 0) return null;

  return (
    <div className="flex flex-col gap-1 border-t border-border pt-2.5">
      <p className="text-xs text-content-subtle">What we saw here</p>
      <ul className="flex flex-col gap-1">
        {observed.map((event) => (
          <li key={event.business_event_id} className="text-sm leading-6">
            {onOpenEvidence === undefined ? (
              <span className="text-content-muted">{event.summary}</span>
            ) : (
              <button
                type="button"
                onClick={() => onOpenEvidence(event.business_event_id)}
                className={cn(
                  'text-left text-content-muted underline decoration-dotted underline-offset-4',
                  'transition-colors hover:text-content',
                  'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent',
                )}
              >
                {event.summary}
              </button>
            )}
          </li>
        ))}
      </ul>
    </div>
  );
}

function Hypothesis({
  hypothesis,
  onOpenEvidence,
}: {
  hypothesis: HypothesisValidation;
  onOpenEvidence?: (businessEventId: string) => void;
}) {
  return (
    <div className="flex flex-col gap-2.5 rounded-md border border-border bg-surface-raised px-4 py-3.5">
      <div className="flex flex-wrap items-baseline justify-between gap-x-3 gap-y-1">
        <h3 className="text-md font-medium leading-6 text-content">
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

      <Observed observed={hypothesis.observed} onOpenEvidence={onOpenEvidence} />

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
 * **The first is on the page** (R2-02). The catalog orders them and the first
 * is the strongest — *"investment ahead of growth says nothing about budget for
 * **your** category"* — so showing one is not showing an arbitrary one.
 *
 * **Styled as calibration, not as warning.** No icon, no tone, no border: the
 * same muted prose the hypothesis itself uses. A limitation drawn as an alert
 * would make Signora look unsure of a conclusion it is in fact sure of. What it
 * is unsure of is precisely and only what the sentence says.
 *
 * The rest stay behind **a real disclosure, not a tooltip**, on the same terms
 * as the disputed-name marker: focusable, `aria-expanded`, and rendered
 * `sr-only` rather than `hidden` when closed, so the content is in the
 * accessibility tree and findable by browser search either way.
 *
 * The trigger counts what is still hidden — *"2 more"* rather than *"3"* —
 * because a count that included the sentence already on screen would be
 * counting something the reader can see.
 */
function Limitations({ limitations, title }: { limitations: string[]; title: string }) {
  const detailId = useId();
  const [open, setOpen] = useState(false);

  const [first, ...rest] = limitations;

  if (first === undefined) return null;

  return (
    <div className="flex flex-col gap-1.5 border-t border-border pt-2.5">
      <p className="text-xs leading-5 text-content-muted">
        <span className="text-content-subtle">What this cannot tell you: </span>
        {first}
      </p>

      {rest.length === 0 ? null : (
        <LimitationsDisclosure
          rest={rest}
          title={title}
          open={open}
          onToggle={() => setOpen((was) => !was)}
          detailId={detailId}
        />
      )}
    </div>
  );
}

function LimitationsDisclosure({
  rest,
  title,
  open,
  onToggle,
  detailId,
}: {
  rest: string[];
  title: string;
  open: boolean;
  onToggle: () => void;
  detailId: string;
}) {
  return (
    <>
      <button
        type="button"
        onClick={onToggle}
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
        {rest.length} more {rest.length === 1 ? 'thing' : 'things'} {title} cannot tell
        you
      </button>

      <ul
        id={detailId}
        className={cn('flex flex-col gap-1.5 pl-4.5', open ? 'block' : 'sr-only')}
      >
        {rest.map((limitation) => (
          <li key={limitation} className="text-xs leading-5 text-content-muted">
            {limitation}
          </li>
        ))}
      </ul>
    </>
  );
}
