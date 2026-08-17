import { cn } from '@/lib/design/cn';

/**
 * **The onboarding rail** — 📁 `docs/design-snapshot/screens/Fortune Signora Onboarding.dc.html`.
 *
 * ## ⛔ Why this is NOT `components/ui/step-rail.tsx`
 *
 * ⚠️ **That component has a second consumer** — the security-enrolment stepper
 * — **and the design draws a different rail here**: a 26px brand mark with the
 * wordmark above the list on Welcome, a *Step n of 4* eyebrow with a 4px
 * progress track on every step after it, an 18px state dot rather than 16, and
 * a 12.5px label rather than 14.
 *
 * ⛔ **Bending the shared one to match would have made it slightly wrong for
 * the screen that already uses it** — 📁 [§20c](../../../../CLAUDE.md): *"never
 * restyle a shared component for one page's benefit."* ✅ **So the rail the
 * design draws lives beside the flow the design draws it for.**
 *
 * ## ⚡ It renders and it does not navigate
 *
 * ⛔ **No `onClick`, deliberately.** 📁 *"Selecting a choice never advances
 * automatically. The user commits with the primary action."*
 *
 * ## 🔴 State is never carried by colour alone
 *
 * 📁 *"Never colour alone — the control mark carries it."* A finished step
 * draws a tick and says *completed*; the current one is `aria-current="step"`.
 */

export interface RailItem {
  readonly id: string;
  readonly label: string;
}

export interface OnboardingRailProps {
  readonly steps: readonly RailItem[];
  readonly currentId: string;
  readonly completedIds: readonly string[];
  /**
   * 📁 **The design's *Step n of 4* eyebrow and its 4px track.** ⛔ Absent on
   * Welcome, which the design gives the brand mark instead — the two are
   * alternatives rather than a stack.
   */
  readonly progress?: { readonly step: number; readonly of: number };
  readonly footer?: React.ReactNode;
}

export function OnboardingRail({
  steps,
  currentId,
  completedIds,
  progress,
  footer,
}: OnboardingRailProps) {
  const done = new Set(completedIds);

  return (
    /* 📁 *"240px rail… background var(--bg-rail), border-right 1px var(--line-soft),
       padding 28px 22px."* ⚡ `bg-surface-raised` IS `--bg-rail` — 253 252 251. */
    <div className="flex flex-col border-border-soft bg-surface-raised px-[22px] py-7 laptop:border-r">
      {progress === undefined ? (
        <div className="flex items-center gap-2.5">
          <span className="grid h-[26px] w-[26px] place-items-center rounded-md bg-accent text-[11px] font-bold text-accent-contrast">
            FS
          </span>
          {/* 📁 **The combined brand, and this is one of the surfaces that may
              carry it** — [§4](../../../../CLAUDE.md): *"`Fortune Signora` is
              the combined brand, reserved for branding surfaces."* ⚡ Onboarding
              is the last screen before the application opens, and the design
              puts it here. */}
          <span className="text-[13px] font-semibold text-content">Fortune Signora</span>
        </div>
      ) : (
        <div>
          <p className="text-[11px] font-semibold uppercase tracking-[0.06em] text-content-subtle">
            Step {progress.step} of {progress.of}
          </p>
          {/* ♿ **A meter, not a decoration.** The eyebrow above already says
              the position in words, so the track is `aria-hidden` rather than
              a second announcement of the same fact. */}
          <div
            aria-hidden
            className="mt-2.5 h-1 overflow-hidden rounded-full bg-surface-sunken"
          >
            <span
              className="block h-full rounded-full bg-accent transition-[width] duration-slow ease-premium"
              style={{ width: `${(progress.step / progress.of) * 100}%` }}
            />
          </div>
        </div>
      )}

      <nav aria-label="Setup progress" className={progress === undefined ? 'mt-[26px]' : 'mt-[22px]'}>
        {/* ♿ An ordered list, because the steps have an order — WCAG 1.3.1. */}
        <ol className="flex flex-col gap-0.5">
          {steps.map((step) => {
            const isCurrent = step.id === currentId;
            const isDone = done.has(step.id) && !isCurrent;

            return (
              <li key={step.id}>
                <div
                  aria-current={isCurrent ? 'step' : undefined}
                  className={cn(
                    'flex items-center gap-2.5 rounded-md px-2 py-[7px] text-[12.5px]',
                    isCurrent && 'bg-accent-subtle font-semibold text-content',
                    !isCurrent && isDone && 'text-content',
                    !isCurrent && !isDone && 'text-content-subtle',
                  )}
                >
                  <span
                    aria-hidden
                    className={cn(
                      'grid h-[18px] w-[18px] shrink-0 place-items-center rounded-full border-[1.5px] text-[9px] font-bold text-accent-contrast',
                      isDone && 'border-success bg-success',
                      isCurrent && 'border-accent bg-accent',
                      !isDone && !isCurrent && 'border-border',
                    )}
                  >
                    {isDone ? '✓' : ''}
                  </span>
                  {step.label}
                  {isDone ? <span className="sr-only">completed</span> : null}
                </div>
              </li>
            );
          })}
        </ol>
      </nav>

      {footer}
    </div>
  );
}

/**
 * 📁 **The rail's footer on Welcome** — *"About 90 seconds. You can leave at
 * any point — everything is saved as you go."* ⚡ **A statement the flow keeps**:
 * every step persists on advance, which is what makes it true rather than
 * reassuring.
 */
export function RailNote({ children }: { children: React.ReactNode }) {
  return (
    <p className="mt-[26px] border-t border-border-soft pt-[18px] text-[11.5px] leading-6 text-content-subtle">
      {children}
    </p>
  );
}
