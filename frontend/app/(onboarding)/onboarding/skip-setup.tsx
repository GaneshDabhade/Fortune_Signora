'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';

import { Button, Dialog } from '@/components/ui';

import { onboardingExit } from './exit';
import { RAIL_STEPS } from './steps';

/**
 * **Screen `08 · Skip, resume, and the three interruption states`** —
 * [TASK-469](../../../../docs/BACKLOG.md) milestone 2, against
 * `docs/design-snapshot/screens/Fortune Signora Onboarding.dc.html`
 * ([D-138](../../../../docs/DECISION_REGISTER.md)).
 *
 * ## ⛔ The design's note is the specification, not a decoration
 *
 * > 📁 ***"States the consequence in product terms and lets them go. No dark
 * > pattern, no second ask."***
 *
 * **Three things follow from that sentence and each is a rule this file
 * keeps:**
 *
 * **①** ⛔ **`Skip` leaves. It does not re-prompt, re-word or re-offer.** A
 * confirmation that argues twice is the dark pattern the note forbids.
 * **②** ⚡ **The consequence is stated in product terms** — what Signora will
 * do differently — **never in the language of an incomplete form.** *"You have
 * 2 steps remaining"* is a fact about the software; *"the home page will show
 * everything rather than your priorities"* is a fact about their day.
 * **③** ✅ **`Finish setup` is the primary action and it merely closes.** The
 * person is already on the step they were on, so continuing is the absence of
 * a redirect rather than a navigation.
 *
 * ## ⚠️ Nothing here is skipped *for* the person
 *
 * ⛔ **Skipping records nothing.** The run keeps exactly the answers already
 * given — the same rule `company-form.tsx` states for a single step, applied
 * to the whole flow: *"a skip that quietly confirmed four guesses"* is an
 * answer nobody gave. **The resume banner then offers the run back**, which is
 * why leaving is safe to make this easy.
 */

/**
 * **Seconds per unanswered step, derived from the design's own figure.**
 *
 * 📁 The resume banner reads *"Two questions left — about 40 seconds"* and the
 * skip dialog's primary action reads *"Finish setup — 40s"* on the same run.
 * ⚡ **Twenty seconds a step is that arithmetic, not an invention** — and it is
 * a constant here so the two surfaces cannot drift into two estimates of one
 * thing.
 *
 * ⚠️ **A rounded estimate is the honest shape.** The design writes *"about 40
 * seconds"*, and a countdown implying precision the product does not have
 * would be the `research.tsx` mistake — *"a spinner is a promise about
 * duration"*.
 */
export const SECONDS_PER_STEP = 20;

/** `40s` — the design prints seconds, and never a bare *"2 steps left"*. */
export function formatSetupEstimate(remainingSteps: number): string {
  return `${remainingSteps * SECONDS_PER_STEP}s`;
}

export interface SkipSetupProps {
  /**
   * Step ids already answered. ⚡ **Ids rather than a count**, because the
   * estimate must not shrink when somebody revisits a step they finished.
   */
  readonly completedIds: readonly string[];
  /**
   * The industry the person confirmed on screen `04`, and `null` when they
   * have not reached it or skipped it. ⛔ **Never inferred** — see below.
   */
  readonly industry?: string | null;
}

/**
 * **The consequence sentence, and the one judgement in this file.**
 *
 * 📁 The design writes it against its own example workspace: *"general
 * benchmarks instead of ones matched to **logistics companies your size**"*.
 * **Northwind is a logistics company, so *logistics* is that run's answer to
 * screen `04` rather than a word in the product.**
 *
 * ⛔ **Hardcoding *logistics* would ship the design's fixture as copy** —
 * exactly what `no-mock-data.test.tsx` exists to catch, and what
 * `SIZE_BANDS` was renamed for.
 *
 * ✅ **So the sentence is templated from the run**, and ⚠️ **falls back to the
 * generic form when the person has not answered screen `04`** — which is
 * precisely the case where somebody is most likely to be skipping. **The
 * fallback is the common path, not the edge.**
 */
export function consequence(industry: string | null | undefined): string {
  const matched =
    industry === null || industry === undefined || industry === ''
      ? 'ones matched to companies like yours'
      : `ones matched to ${industry.toLowerCase()} companies your size`;
  return (
    `Your workspace is already live. Signora will use general benchmarks instead of ${matched}, ` +
    `and the home page will show everything rather than your priorities.`
  );
}

/**
 * **Skip the rest of setup.** Lives in the onboarding rail's footer, so it is
 * reachable from every step and competes with nothing — 📁 the design keeps
 * the primary action *"bottom-left of the content column"*, and an exit beside
 * it would read as the other half of a pair.
 */
export function SkipSetup({ completedIds, industry }: SkipSetupProps) {
  const [open, setOpen] = useState(false);
  const router = useRouter();

  // ⚡ **`welcome` is not a question**, so it is not counted. The design's
  // banner says *"two questions left"* on a run with the workspace made and
  // company, you and goals outstanding — the steps that ask something.
  const remaining = RAIL_STEPS.filter(
    (step) => step.id !== 'welcome' && !completedIds.includes(step.id),
  ).length;

  return (
    <>
      <button
        type="button"
        onClick={() => setOpen(true)}
        className="rounded text-left text-sm text-content-subtle underline underline-offset-4 transition-colors hover:text-content focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent"
      >
        Skip setup
      </button>

      <Dialog
        open={open}
        onClose={() => setOpen(false)}
        title="Skip the rest of setup?"
        description={consequence(industry)}
        footer={
          <div className="flex flex-wrap items-center gap-3">
            {/* ✅ **Primary, and it only closes.** They are already on the step
                they were on, so continuing is the absence of a navigation. */}
            <Button onClick={() => setOpen(false)}>
              Finish setup — {formatSetupEstimate(remaining)}
            </Button>
            {/* ⛔ **This leaves, and asks nothing further.** *No second ask.* */}
            <Button variant="secondary" onClick={() => router.push(onboardingExit())}>
              Skip
            </Button>
          </div>
        }
      />
    </>
  );
}
