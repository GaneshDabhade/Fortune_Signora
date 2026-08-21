'use client';

import Link from 'next/link';

import { OnboardingShell, StepFooter, StepHeading } from '../onboarding-shell';
import { OnboardingRail, RailNote } from './rail';
import { RAIL_STEPS } from './steps';

/**
 * **Screen `01 · Welcome`** — 📁 `docs/design-snapshot/screens/Fortune Signora Onboarding.dc.html`.
 *
 * ## ⛔ It asks nothing
 *
 * 📁 *"Welcome · Skippable · 10s · **Nothing.** States what the product does
 * and what the next 90 seconds will cover."* ♿ WCAG 3.3.7 — *"nothing already
 * known is asked again"* — **so the first name is greeted rather than
 * requested**, and when the account has none the greeting is impersonal rather
 * than blank.
 *
 * ## ⚡ The verified badge is a fact, not decoration
 *
 * 📁 The design draws *Email verified* above the greeting. ⛔ **It renders only
 * when the session says the address IS verified.** A badge that always appeared
 * would be a claim about a security state nobody checked — and this flow
 * arrives directly from Authentication, where that check is the whole screen.
 *
 * ## 📁 The four cards, verbatim
 *
 * ⚠️ **The fourth must not be softened**: *"Read-only to start. Nothing is
 * written without your approval."* It is a commitment about what the product
 * will do to a customer's CRM, and screen `07` repeats it beside the actual
 * consent — **two places, one sentence, and neither is the place to improve
 * the wording.**
 */
export function OnboardingWelcome({
  firstName,
  emailVerified,
}: {
  firstName: string | null;
  emailVerified: boolean;
}) {
  return (
    <OnboardingShell
      roomy
      rail={
        <OnboardingRail
          steps={RAIL_STEPS}
          currentId="welcome"
          completedIds={[]}
          footer={
            <RailNote>
              About 90 seconds. You can leave at any point — everything is saved as you
              go.
            </RailNote>
          }
        />
      }
    >
      {emailVerified ? (
        <span className="mb-4 inline-flex items-center gap-1.5 rounded-md bg-success-subtle px-2.5 py-0.5 text-2xs font-semibold text-success">
          Email verified
        </span>
      ) : null}

      <StepHeading
        large
        title={firstName === null ? 'Welcome to Signora' : `Welcome, ${firstName}`}
      >
        Signora reads your CRM, calls and email to tell you which deals are moving, which
        are stalling, and why. Four questions and it will be reading yours.
      </StepHeading>

      {/* 📁 *"grid-template-columns:1fr 1fr; gap:12px; margin-top:28px"*, each
          card `padding:16px; border-radius:12px; background:var(--sunken)`.
          ⛔ **`--sunken`, not `--surface`** — the cards are recessed into the
          plane rather than raised off it, which is why they carry no border and
          no shadow. */}
      <ul className="mt-7 grid gap-3 smalllaptop:grid-cols-2">
        {CAPABILITIES.map((capability) => (
          <li key={capability.title} className="rounded-lg bg-surface-sunken p-4">
            <span className="grid h-[26px] w-[26px] place-items-center rounded-md bg-surface text-accent">
              {capability.icon}
            </span>
            <span className="mt-3 block text-sm font-semibold text-content">
              {capability.title}
            </span>
            <span className="mt-1 block text-xs leading-relaxed text-content-muted">
              {capability.body}
            </span>
          </li>
        ))}
      </ul>

      <StepFooter>
        {/* ⛔ **A link rather than a `Button`, because it navigates.** `Button`
            renders a `<button>` and has no `asChild`; wrapping one around a
            link would give a control two roles, and only one of them is what a
            keyboard would do with it. ⚡ 40px is the design's height here and
            `--control-md` is exactly that. */}
        <Link
          href="/onboarding/introduction"
          /* ⛔ **A link, so it cannot be [`Button`](../../../components/ui/button.tsx)** —
             that component renders a `<button>` and has no `asChild`, and wrapping
             one around an anchor would give the control two roles. ⚡ **It takes
             the canonical control's own geometry rather than restating a
             literal**: the `md` height token, `rounded` (the design's 8px step,
             not `rounded-md`), `px-4`, and 📁 `2.5.8`'s touch floor. */
          className="inline-flex h-control-md shrink-0 items-center justify-center whitespace-nowrap rounded bg-accent px-4 text-sm font-semibold text-accent-contrast shadow-sm transition-colors hover:bg-accent-hover coarse:min-h-11 "
        >
          Get started
        </Link>
        <Link
          href="/onboarding/introduction"
          className="text-sm font-semibold text-content-subtle hover:text-content "
        >
          Take the tour first
        </Link>
        {/* 📁 The design's *"↵ to continue"*. ♿ `aria-hidden`: it describes a
            pointer-free shortcut to sighted readers and would otherwise be
            announced as a stray glyph. */}
        <span aria-hidden className="ml-auto text-xs text-content-subtle">
          ↵ to continue
        </span>
      </StepFooter>
    </OnboardingShell>
  );
}

function Glyph({ d }: { d: string }) {
  return (
    <svg
      width="14"
      height="14"
      viewBox="0 0 16 16"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.6"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden
    >
      <path d={d} />
    </svg>
  );
}

const CAPABILITIES = [
  {
    title: 'See what moved',
    body: 'Every change since you last looked, ranked by what it costs you.',
    icon: <Glyph d="M1.5 8h3l2-4.5L9 12l2-4h3.5" />,
  },
  {
    title: 'Evidence, always',
    body: 'Each claim cites the call, email or field change behind it.',
    icon: <Glyph d="M8 1.5 3 3.5v4c0 3 2.2 5.4 5 6.5 2.8-1.1 5-3.5 5-6.5v-4L8 1.5Z" />,
  },
  {
    title: 'Forecast you can defend',
    body: "The model's number, the rep's number, and the gap explained.",
    icon: <Glyph d="M3 13V7M8 13V3M13 13V9" />,
  },
  {
    title: 'Reads your CRM',
    body: 'Read-only to start. Nothing is written without your approval.',
    icon: (
      <Glyph d="M6.5 9.5 9.5 6.5M6 4.5 7.5 3a2.8 2.8 0 0 1 4 4L10 8.5M6 7.5 4.5 9a2.8 2.8 0 0 0 4 4L10 11.5" />
    ),
  },
] as const;
