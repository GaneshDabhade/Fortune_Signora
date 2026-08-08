'use client';

import Link from 'next/link';

import { OnboardingShell } from '../onboarding-shell';
import { RAIL_STEPS } from './steps';

/**
 * **Screens `01 Welcome` and `02 Product introduction`** —
 * [TASK-469](../../../../docs/BACKLOG.md), Workflow 8, against
 * `docs/design-snapshot/screens/Fortune Signora Onboarding.dc.html`.
 *
 * ### ⚡ One screen, because the design draws one
 *
 * The row lists `01` and `02` separately and **the design's flow table has a
 * single step 1**: *"Welcome · Skippable · 10s · **Nothing.** States what the
 * product does and what the next 90 seconds will cover."* The four capability
 * cards are what *"states what the product does"* means, so they are this
 * screen's body rather than a second screen with its own advance.
 *
 * ⚠️ **Recorded rather than reconciled quietly** ([D-138](../../../../docs/DECISION_REGISTER.md)
 * makes the snapshot the authority): a second screen would add a click to a
 * flow whose stated selling point is ninety seconds.
 *
 * ### ⛔ It asks nothing
 *
 * *"Nothing already known is asked again: name, email, domain and region come
 * from the account and are shown as read-only context"* (WCAG 3.3.7). **The
 * first name is the only inferred value on this screen and it is greeted, not
 * requested.**
 */
export function OnboardingWelcome({ firstName }: { firstName: string | null }) {
  return (
    <OnboardingShell
      steps={RAIL_STEPS}
      currentId="welcome"
      // ⚠️ **The organization step reads as done, and that is not a shortcut.**
      // Onboarding runs *on* a workspace — `workspace_id` is what the run is
      // keyed by — so by the time anybody sees this screen the organization
      // exists. **The design creates it at step 2 because it draws the flow
      // starting before there is one**; here the flow starts after, and a rail
      // offering to create what already exists would be the false step.
      // TASK-468's screen `03` is where that half is built, and this row
      // routes past it rather than rebuilding it.
      completedIds={['workspace']}
      title={firstName ? `Welcome, ${firstName}` : 'Welcome to Signora'}
      description="Four questions, about ninety seconds. Everything is saved as you go, so you can leave at any point and pick it up where you left it."
      actions={
        <>
          {/* A link rather than a `Button`, because it navigates. `Button`
              renders a `<button>` and has no `asChild`; wrapping one around a
              link would give a control two roles, and only one of them is
              what a keyboard would do with it. */}
          <Link
            href="/onboarding/company"
            className="inline-flex h-control-md items-center justify-center rounded bg-accent px-4 text-sm font-medium text-accent-contrast transition-colors hover:bg-accent-hover focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent focus-visible:ring-offset-2"
          >
            Get started
          </Link>
          {/* ⛔ **Skip is offered here and is not a dark pattern.** The design
              makes every step but the workspace skippable, and hiding the exit
              on the first screen would be the *"second ask"* it forbids one
              screen later. */}
          <Link
            href="/onboarding/company"
            className="text-sm text-content-muted underline underline-offset-4 hover:text-content"
          >
            Skip the tour
          </Link>
        </>
      }
    >
      <ul className="flex flex-col gap-3">
        {CAPABILITIES.map((capability) => (
          <li
            key={capability.title}
            className="flex flex-col gap-1 rounded-md border border-border-soft bg-surface p-4"
          >
            <span className="text-sm font-semibold text-content">{capability.title}</span>
            <span className="text-sm leading-6 text-content-muted">{capability.body}</span>
          </li>
        ))}
      </ul>
    </OnboardingShell>
  );
}

/**
 * The design's four cards, verbatim.
 *
 * ⚠️ **The fourth is the one that must not be softened**: *"Read-only to
 * start. Nothing is written without your approval."* It is a commitment about
 * what the product will do to a customer's CRM, and screen `07` repeats it
 * beside the actual consent — **two places, one sentence, and neither is the
 * place to improve the wording.**
 */
const CAPABILITIES = [
  {
    title: 'See what moved',
    body: 'Every change since you last looked, ranked by what it costs you.',
  },
  {
    title: 'Evidence, always',
    body: 'Each claim cites the call, email or field change behind it.',
  },
  {
    title: 'Forecast you can defend',
    body: "The model's number, the rep's number, and the gap explained.",
  },
  {
    title: 'Reads your CRM',
    body: 'Read-only to start. Nothing is written without your approval.',
  },
] as const;
