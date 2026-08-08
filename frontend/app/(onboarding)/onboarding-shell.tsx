import { StepRail, type RailStep } from '@/components/ui';

/**
 * **The onboarding container** — [TASK-469](../../../docs/BACKLOG.md), and
 * *"the one genuinely new layout in Workflows 1–8"*, named in the row rather
 * than improvised.
 *
 * ### ⛔ Not the authentication shell, and not the App Shell
 *
 * **Onboarding runs after authentication and before the App Shell.** The
 * `(auth)` shell is a 400px card for a person who is not yet anybody; this is
 * a 920px frame for somebody who now owns a workspace. **Reusing either would
 * bend a shared component to suit one caller** ([§20c](../../../CLAUDE.md)),
 * which is the thing the frozen foundation exists to prevent.
 *
 * ### The frame the design specifies, in its own figures
 *
 * > *"920px frame, 240px rail, 560px content column. Rail visible throughout;
 * > the primary action sits bottom-left of the content column, never
 * > floating."*
 *
 * ⚠️ **Below `lg` the rail becomes a bar above the content** — the design's
 * tablet row — because a 240px column beside a 560px one does not fit, and
 * dropping the rail entirely would remove the only thing telling somebody how
 * much is left.
 */
export interface OnboardingShellProps {
  readonly steps: readonly RailStep[];
  readonly currentId: string;
  readonly completedIds: readonly string[];
  readonly title: string;
  readonly description?: React.ReactNode;
  readonly children: React.ReactNode;
  /** The primary action, and anything beside it. **Bottom-left of the content
   * column, never floating** — the design says so in terms. */
  readonly actions?: React.ReactNode;
  readonly railFooter?: React.ReactNode;
}

export function OnboardingShell({
  steps,
  currentId,
  completedIds,
  title,
  description,
  children,
  actions,
  railFooter,
}: OnboardingShellProps) {
  return (
    <div className="min-h-screen bg-canvas px-5 py-10 sm:py-16">
      <div className="mx-auto flex w-full max-w-[57.5rem] flex-col gap-8 lg:flex-row lg:gap-12">
        <StepRail
          steps={steps}
          currentId={currentId}
          completedIds={completedIds}
          footer={railFooter}
          className="lg:w-60 lg:shrink-0"
        />

        <main className="flex w-full flex-col gap-6 lg:max-w-[35rem]">
          {/*
            **Focus moves here on every step change and the heading carries
            its own position** — WCAG 2.4.3, which the design names by number
            and quotes: *"Step 3 of 4, What do you do at Northwind?"*.
            `tabIndex={-1}` makes it programmatically focusable without
            putting it in the tab order, which is the whole of that pattern.
          */}
          <header className="flex flex-col gap-2">
            <h1 tabIndex={-1} className="text-xl font-semibold tracking-tight text-content">
              {title}
            </h1>
            {description ? (
              <p className="text-sm leading-6 text-content-muted">{description}</p>
            ) : null}
          </header>

          {children}

          {actions ? <div className="flex items-center gap-3 pt-2">{actions}</div> : null}
        </main>
      </div>
    </div>
  );
}
