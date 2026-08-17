'use client';

import { useRouter } from 'next/navigation';
import { useState } from 'react';

import { MultiChoiceCards } from '@/components/ui';
import { chooseGoals, type Goal } from '@/lib/api/onboarding';

import { OnboardingShell } from '../onboarding-shell';
import { OnboardingRail } from './rail';
import { OnboardingSkeleton } from './company-form';
import { GOALS, MAX_GOALS, COUNTED_STEPS, COUNTED_TOTAL, isGoal, positionOf } from './steps';
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
  const router = useRouter();
  const { run, error, isLoading, isSaving, save, advance } = useOnboarding();
  const [chosen, setChosen] = useState<readonly string[] | null>(null);

  if (isLoading) return <OnboardingSkeleton />;

  const selected = chosen ?? run?.goals ?? [];

  /**
   * ⚡ **This no longer finishes the run, and that is the design's flow rather
   * than a change of mind.**
   *
   * ⚠️ **It used to.** 📁 Screen `07 Connect` did not exist, so a `Continue`
   * routing to it would have been the *"control that goes nowhere"* [B-255](../../../../docs/BUGS.md)
   * refuses, and finishing here was the honest alternative. ✅ **`07` exists
   * now**, and 📁 the design is explicit about which screen closes the run:
   * **Goals' primary reads *"Finish setup"* and Connect's reads *"Connect and
   * finish"***. **Connect finishes; this hands over to it.**
   *
   * ⛔ **So `useOnboardingExit` is gone from this screen** — it decides where
   * somebody *lands after onboarding*, and this screen is no longer the last
   * one. 📁 It moves to `connect-form.tsx`, unchanged.
   */
  const submit = async () => {
    const goals = selected.filter(isGoal) as Goal[];
    await save((id) => chooseGoals(id, goals));
    await advance('connect');
    router.push('/onboarding/connect');
  };

  return (
    <OnboardingShell
      rail={
        <OnboardingRail
          steps={COUNTED_STEPS}
          currentId="goals"
          completedIds={[...(run?.completed_steps ?? []), 'workspace']}
          progress={{ step: positionOf('goals'), of: COUNTED_TOTAL }}
          footer={
            <>
              {/* 📁 The design's own note, verbatim, in a `--sunken` card:
                  *"This is the last question · Connecting your CRM comes after
                  — you can do it now or from Settings."* ⚡ **It is what makes
                  the next screen feel optional before somebody reaches it.** */}
              <div className="mt-[22px] rounded-lg bg-surface-sunken p-3">
                <p className="text-[11.5px] font-semibold text-content">
                  This is the last question
                </p>
                <p className="mt-[5px] text-[11.5px] leading-[1.5] text-content-muted">
                  Connecting your CRM comes after — you can do it now or from Settings.
                </p>
              </div>
              <SkipSetup
                completedIds={run?.completed_steps ?? []}
                industry={run?.industry?.value ?? null}
              />
            </>
          }
        />
      }
      title="What are you trying to fix?"
      description="Choose up to three. These decide what your home page leads with and which insights Signora produces first."
      actions={
        <>
          <button
            type="button"
            onClick={submit}
            disabled={isSaving}
            className="inline-flex h-control-md items-center rounded-md bg-accent px-[18px] text-[13.5px] font-semibold text-accent-contrast shadow-sm transition-colors hover:bg-accent-hover disabled:opacity-40 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-accent"
          >
            {isSaving ? 'Saving…' : 'Finish setup'}
          </button>
          <button
            type="button"
            onClick={async () => {
              // 📁 *"Skipping entirely is permitted."* ⛔ **And skipping this
              // question is not leaving onboarding** — it advances to Connect
              // with no goals recorded, exactly as skipping Company advances
              // to You. **The run is closed by Connect either way.**
              await advance('connect');
              router.push('/onboarding/connect');
            }}
            className="text-[13px] font-semibold text-content-subtle hover:text-content focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-accent"
          >
            Skip for now
          </button>
          {/* 📁 *"`margin-left:auto` · tabular-nums · 3 of 3 selected"*.
              ♿ **A status, not an alert** — *"progress changes and autosave
              confirmations are status messages… they do not interrupt"*
              (4.1.3). The count changes on every click, and an alert would
              talk over somebody choosing quickly.
              ⚡ **`tabular-nums` because the design says so**: proportional
              figures make the line jump as the count changes. */}
          <p
            role="status"
            className="ml-auto text-[11.5px] tabular-nums text-content-subtle"
          >
            {selected.length} of {MAX_GOALS} selected
          </p>
        </>
      }
    >
      <div>
        <MultiChoiceCards
          legend="Your goals"
          legendHidden
          name="goals"
          choices={GOALS}
          value={selected}
          onChange={(next) => {
            // ⚡ **Held locally for the click, then persisted immediately.**
            setChosen(next);
            // 🔴 **The save is what makes the card below real.** 📁 The design
            // shows *"Based on these, Signora will switch on…"* while somebody
            // is still choosing, and the goal→capability mapping lives on the
            // server ([§2](../../../../CLAUDE.md)) — ⛔ **so without a save
            // there is nothing to say, and the card never appeared during the
            // step it belongs to.**
            //
            // ⚠️ **Found in a screenshot with three goals picked and the card
            // absent.** ✅ It also matches this flow's own promise —
            // *"every step saves on advance and on blur"* — for a step whose
            // only input is a click.
            void save((id) => chooseGoals(id, next.filter(isGoal) as Goal[]));
          }}
          max={MAX_GOALS}
        />

        <GoalConsequence
          on={run === null ? [] : reachable(run.features)}
          off={run === null ? [] : reachable(run.features_off)}
        />

        {error !== null ? (
          <p role="alert" className="mt-4 text-sm text-danger">
            {error}
          </p>
        ) : null}
      </div>
    </OnboardingShell>
  );
}

/**
 * 📁 **What the goals just bought, in the design's own card.**
 *
 * > *"Based on these, Signora will switch on **Forecast, Signal Center and
 * > Renewal risk**, and leave **Marketing attribution** off. Change any of it
 * > in Settings."*
 *
 * ### ⚡ Both halves come from the server
 *
 * `features` and `features_off` are derived from the goal table on every read.
 * ⛔ **The complement is not computed here**, because a client deriving *off*
 * would need its own copy of the table to know what the universe is — 📁
 * [§2](../../../../CLAUDE.md) — and it would be the copy nobody updates.
 *
 * ### 🔴 It names only what a person can actually reach
 *
 * 📁 [B-256](../../../../docs/BUGS.md). ⛔ **The design's own example cannot
 * be rendered**: it leads with *Forecast*, and `forecast` has no route on any
 * branch — `buying_score_engine` refuses it as domain law, *"no probability,
 * no likelihood, no prediction."* ⚡ **So both lists pass through `reachable`**,
 * and a clause with nothing left in it is **absent rather than empty**: *say
 * something true or say nothing, never something hopeful.*
 *
 * ⚠️ **Which means this card can carry one clause, two, or none at all**, and
 * that is the honest range rather than a degraded version of the mock.
 */
function GoalConsequence({ on, off }: { on: readonly string[]; off: readonly string[] }) {
  if (on.length === 0 && off.length === 0) return null;

  return (
    // 📁 *"padding:13px 15px; border-radius:12px; background:var(--ai-tint);
    //     border:1px solid var(--ai-line)"*.
    <div className="mt-[22px] flex items-center gap-3 rounded-lg border border-ai/30 bg-ai-subtle px-[15px] py-[13px]">
      {/* 📁 The design's 20px tile with its four-point spark. ♿ `aria-hidden`
          — the sentence beside it says everything. */}
      <span
        aria-hidden
        className="grid h-5 w-5 flex-none place-items-center rounded-sm bg-ai"
      >
        <svg
          width="11"
          height="11"
          viewBox="0 0 16 16"
          fill="none"
          stroke="currentColor"
          strokeWidth="1.7"
          strokeLinecap="round"
          className="text-accent-contrast"
        >
          <path d="M8 2v2.5M8 11.5V14M2 8h2.5M11.5 8H14" />
        </svg>
      </span>
      <p className="text-[12.5px] leading-[1.55] text-content">
        Based on these, Signora will
        {on.length > 0 ? (
          <>
            {' '}
            switch on <Named of={on} />
          </>
        ) : null}
        {on.length > 0 && off.length > 0 ? ',' : null}
        {off.length > 0 ? (
          <>
            {' '}
            {on.length > 0 ? 'and leave' : 'leave'} <Named of={off} /> off
          </>
        ) : null}
        . Change any of it in Settings.
      </p>
    </div>
  );
}

/** 📁 The design emphasises the capability names inside the sentence. ⚡ **An
 *  Oxford-free list with *and* before the last** — the design writes *"Forecast,
 *  Signal Center and Renewal risk"*. */
function Named({ of }: { of: readonly string[] }) {
  const text =
    of.length === 1
      ? of[0]
      : `${of.slice(0, -1).join(', ')} and ${of[of.length - 1]}`;
  return <span className="font-semibold">{text}</span>;
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
