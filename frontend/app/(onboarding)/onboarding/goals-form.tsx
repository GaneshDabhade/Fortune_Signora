'use client';

import { useState } from 'react';

import { Button, MultiChoiceCards } from '@/components/ui';
import { chooseGoals, finishOnboarding, type Goal } from '@/lib/api/onboarding';

import { OnboardingShell } from '../onboarding-shell';
import { OnboardingSkeleton } from './company-form';
import { useOnboardingExit } from './exit';
import { GOALS, MAX_GOALS, RAIL_STEPS, isGoal } from './steps';
import { SkipSetup } from './skip-setup';
import { useOnboarding } from './use-onboarding';

/**
 * **Screen `06 Goals`** — [TASK-469](../../../../docs/BACKLOG.md).
 *
 * > *"Up to three outcomes. These order the home page and pick the first
 * > insights. Inferred: **feature preferences follow from the goals — no
 * > separate step.**"*
 *
 * ### ⚡ This screen is why there is no feature menu
 *
 * *"Users can't rank features they haven't used, but they know what is going
 * wrong. Three outcomes map deterministically onto modules, so the
 * feature-preferences step disappears."*
 *
 * ⛔ **The mapping is the server's and is not repeated here.** `run.features`
 * comes back derived; a copy in this file would be a second representation of
 * one rule, and the one on the screen is the one that would be stale
 * ([§2](../../../../CLAUDE.md)).
 *
 * ### ⛔ The fourth is disabled with the reason stated
 *
 * *"The fourth selection is disabled, not silently ignored"*, and *"dims to
 * 55% **with the reason stated in the footer count**"*. **A control that stops
 * working without saying why reads as a bug.**
 */
export function GoalsForm() {
  // ⛔ **No `useRouter` here any more.** 📁 The flow does not choose where
  // somebody lands; `useOnboardingExit` asks the engine. See `exit.ts`.
  const { exit } = useOnboardingExit();
  const { run, error, isLoading, isSaving, save } = useOnboarding();
  const [chosen, setChosen] = useState<readonly string[] | null>(null);

  if (isLoading) return <OnboardingSkeleton />;

  const selected = chosen ?? run?.goals ?? [];

  /**
   * ⚠️ **This finishes the run, and in milestone 2 it will not.**
   *
   * **Screen `07 Connect & AI personalisation` is milestone 2's** and does not
   * exist yet. ⛔ **So this does not route to it.** A `Continue` that landed on
   * a missing page would be the *"control that goes nowhere"* the shell already
   * refuses one workflow over — and `vocabulary.test.tsx` catches it, which is
   * how this line came to be written twice.
   *
   * ⛔ **And it does not choose where the person lands** — that goes through
   * `onboardingExit`, which exists because the coordination source forbids
   * this flow from deciding it. See `exit.ts`.
   *
   * ✅ **Finishing here is honest rather than a stub**: everything the run can
   * currently record has been recorded, and *"an abandoned onboarding still
   * produces a customer"* applies just as well to one the product has not
   * finished building. **When `07` lands, this advances to it instead.**
   */
  const submit = async () => {
    const goals = selected.filter(isGoal) as Goal[];
    await save((id) => chooseGoals(id, goals));
    await save((id) => finishOnboarding(id));
    exit();
  };

  return (
    <OnboardingShell
      steps={RAIL_STEPS}
      currentId="goals"
      completedIds={run?.completed_steps ?? []}
      railFooter={
        <SkipSetup
          completedIds={run?.completed_steps ?? []}
          industry={run?.industry?.value ?? null}
        />
      }
      title="What are you trying to fix?"
      description="Pick up to three. They order your home page and choose the first things Signora looks at — you are not choosing features."
      actions={
        <>
          <Button onClick={submit} loading={isSaving}>
            Continue
          </Button>
          <button
            type="button"
            onClick={async () => {
              // *"Skipping entirely is permitted."* An empty selection is a
              // valid answer and is not the same as never being asked — the
              // goals are simply left as they were and the run closes.
              await save((id) => finishOnboarding(id));
              exit();
            }}
            className="text-sm text-content-muted underline underline-offset-4 hover:text-content"
          >
            Skip this step
          </button>
        </>
      }
    >
      <div className="flex flex-col gap-6">
        <MultiChoiceCards
          legend="Your goals"
          legendHidden
          name="goals"
          choices={GOALS}
          value={selected}
          onChange={setChosen}
          max={MAX_GOALS}
          countLabel={(count, max) =>
            count >= max
              ? `${count} of ${max} chosen. Unpick one to swap it for another.`
              : `${count} of ${max} chosen.`
          }
        />

        {/* ⚡ **What the goals bought, in the product's own words.** Derived
            server-side and shown so the step visibly does something — a
            selection whose effect is invisible is the feature menu the design
            replaced, wearing different clothes. */}
        {/* 🔴 **[B-256](../../../../docs/BUGS.md): only destinations that
            EXIST are named.** ⛔ **This said *"Signora will open on Forecast,
            the Executive Dashboard"* to whoever picked the first goal**, and
            neither has a route. ⚡ **When a goal's features are all unbuilt the
            sentence is absent** rather than shortened to nothing — 📁 the same
            rule [`StatedAbsence`](../../../components/feedback/stated-absence.tsx)
            keeps: **say something true or say nothing, never something
            hopeful.** */}
        {run !== null && reachable(run.features).length > 0 ? (
          <p className="text-sm text-content-muted">
            Signora will open on{' '}
            <span className="font-medium text-content">
              {reachable(run.features).join(', ')}
            </span>
            .
          </p>
        ) : null}

        {error !== null ? (
          <p role="alert" className="text-sm text-danger">
            {error}
          </p>
        ) : null}
      </div>
    </OnboardingShell>
  );
}

/**
 * A capability name, in the customer's vocabulary.
 *
 * ⚠️ **The server returns identifiers and a customer never reads one**
 * ([ADR-0034](../../../../docs/architecture/adr/0034-ubiquitous-language.md):
 * *the translation lives at the frontend edge and never travels inward*).
 *
 * 🔴 **[B-256](../../../../docs/BUGS.md): the name is not enough — a
 * destination has to EXIST.** ⛔ **Five of these ten had no route**, and the
 * sentence said *"Signora will open on Forecast, the Executive Dashboard"* to
 * anybody who picked the first goal on the screen. **Neither exists.**
 *
 * ⚡ **So the map answers *where*, not *what it is called***, and `null` is a
 * real answer rather than a missing entry. ⛔ **A `Record<string, string>`
 * could not express *"this is named and unreachable"***, which is why the
 * absent ones were indistinguishable from the shipped ones.
 */
const DESTINATIONS: Record<string, { readonly label: string; readonly href: string | null }> = {
  // ✅ Shipped, and reachable from the rail.
  signals: { label: 'Signals', href: '/signals' },
  companies: { label: 'Companies', href: '/accounts' },
  reports: { label: 'Reports', href: '/reports' },
  team_management: { label: 'your team', href: '/settings/team' },
  // ⚡ **The Copilot is a room that says it cannot answer yet**
  // ([TASK-482](../../../../docs/BACKLOG.md)) — ✅ **it exists and is honest**,
  // which is a destination, not a promise.
  ai_copilot: { label: 'the Copilot', href: null },
  // ⛔ **No route, on any branch.** 📁 `forecast` is refused as domain law —
  // `buying_score_engine` states *"no probability, no likelihood, no
  // prediction… it does not forecast a purchase"* — and the other three are
  // unbuilt screens with their own rows.
  forecast: { label: 'Forecast', href: null },
  executive_dashboard: { label: 'the Executive Dashboard', href: null },
  opportunity_intelligence: { label: 'Opportunity Intelligence', href: null },
  account_360: { label: 'Account 360', href: null },
  ai_research: { label: 'Research', href: null },
};

/**
 * ⛔ **An unknown identifier is titled rather than dropped** — a feature going
 * missing because the map was not updated is worse than one appearing in
 * slightly plain English. ⚠️ **But an identifier this file has never heard of
 * is not evidence that a screen exists**, so it is named and not promised.
 */
export function reachable(features: readonly string[]): string[] {
  return features
    .filter((feature) => DESTINATIONS[feature]?.href != null)
    .map((feature) => DESTINATIONS[feature]?.label ?? feature.replaceAll('_', ' '));
}
