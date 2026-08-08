import { cn } from '@/lib/design/cn';

export interface RailStep {
  /** Stable key, and the value a caller routes on. */
  readonly id: string;
  /** What the person reads. The design names all six. */
  readonly label: string;
}

export interface StepRailProps {
  readonly steps: readonly RailStep[];
  /** The step being shown. Exactly one, and it is `aria-current="step"`. */
  readonly currentId: string;
  /** Everything finished. **A set rather than a count** — see below. */
  readonly completedIds: readonly string[];
  readonly className?: string;
  /**
   * The design's autosave confirmation: *"'Saved' appears in the rail footer
   * for 2s."* Absent means nothing is being claimed, which is the honest
   * default — a permanent *Saved* is a claim about a request nobody made.
   */
  readonly footer?: React.ReactNode;
}

/**
 * **The onboarding rail** — [TASK-469](../../../docs/BACKLOG.md), against
 * `docs/design-snapshot/screens/Fortune Signora Onboarding.dc.html`.
 *
 * ### ⚡ Named steps, not *Step n of 4*
 *
 * ⚠️ **The row asks for a step indicator reading *"Step n of 4"* and the
 * design draws something else**: an ordered list of six named steps, each
 * `done` · `active` · `idle`. **[D-138](../../../docs/DECISION_REGISTER.md)
 * makes the snapshot the implementation authority**, so this follows the
 * design and the difference is recorded rather than reconciled quietly.
 *
 * ⛔ **A count would also be wrong twice over**: the flow has six steps, and
 * *"back is always available"* means position alone cannot say which of the
 * earlier ones are answered.
 *
 * ### 🔴 The state is never carried by colour alone
 *
 * *"Never colour alone — the control mark carries it."* A finished step draws
 * a tick; the current one is `aria-current="step"`. **Both are readable with
 * no colour perception at all**, which is why the tick is an element rather
 * than a green dot.
 *
 * ### ⛔ It renders and it does not navigate
 *
 * **No `onClick`, and that is deliberate.** *"Selecting a choice never
 * advances automatically. The user commits with the primary action."* A rail
 * that moved the person would be a second way through the flow, and the two
 * would eventually disagree about what *advancing* saves.
 */
export function StepRail({
  steps,
  currentId,
  completedIds,
  className,
  footer,
}: StepRailProps) {
  const done = new Set(completedIds);

  return (
    <nav aria-label="Setup progress" className={cn('flex flex-col gap-4', className)}>
      {/* An ordered list, because the steps have an order — WCAG 1.3.1, which
          the design names by number. A stack of divs conveys none of it. */}
      <ol className="flex flex-col gap-1">
        {steps.map((step) => {
          const isCurrent = step.id === currentId;
          const isDone = done.has(step.id) && !isCurrent;

          return (
            <li key={step.id}>
              <div
                aria-current={isCurrent ? 'step' : undefined}
                className={cn(
                  'flex items-center gap-2.5 rounded-md px-2.5 py-2 text-sm',
                  isCurrent && 'bg-accent-subtle font-semibold text-content',
                  !isCurrent && isDone && 'text-content',
                  !isCurrent && !isDone && 'text-content-subtle',
                )}
              >
                <span
                  aria-hidden
                  className={cn(
                    'flex h-4 w-4 shrink-0 items-center justify-center rounded-full border',
                    isDone && 'border-success bg-success text-surface',
                    isCurrent && 'border-accent bg-accent',
                    !isDone && !isCurrent && 'border-border',
                  )}
                >
                  {isDone ? (
                    <svg viewBox="0 0 10 10" className="h-2.5 w-2.5" fill="none">
                      <path
                        d="M2 5.2 4 7.2 8 2.8"
                        stroke="currentColor"
                        strokeWidth="1.6"
                        strokeLinecap="round"
                        strokeLinejoin="round"
                      />
                    </svg>
                  ) : null}
                </span>
                {step.label}
                {/* The state in words, for anybody who cannot see the tick or
                    the tint. `aria-current` covers the active step; this
                    covers the finished ones, which have no ARIA equivalent. */}
                {isDone ? <span className="sr-only">completed</span> : null}
              </div>
            </li>
          );
        })}
      </ol>
      {footer}
    </nav>
  );
}
