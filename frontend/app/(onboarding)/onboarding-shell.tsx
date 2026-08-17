import { cn } from '@/lib/design/cn';

/**
 * **The onboarding frame** — 📁 `docs/design-snapshot/screens/Fortune Signora Onboarding.dc.html`.
 *
 * ## 📁 The design's own figures
 *
 * > *"One frame throughout: a 240px step rail on the left, an 560px content
 * > column on the right, **both inside a 16px-radius plane on the warm
 * > ground**. The rail never changes position, so progress is felt rather than
 * > announced."*
 *
 * 🔴 **The plane is the part the previous implementation did not have.** It
 * rendered the rail and the content directly on the page ground with no
 * surface, no border and no elevation — ⚠️ **structurally a different screen**,
 * not a styling difference, which is why this file was rewritten rather than
 * adjusted.
 *
 * ## ⚡ Tokens, and the consumption checked as well as the value
 *
 * | Design | Token | Value |
 * |---|---|---|
 * | `--bg` — the ground | `bg-canvas` | `250 248 246` |
 * | `--surface` — the plane | `bg-surface` | `255 255 255` |
 * | `--bg-rail` — the rail | `bg-surface-raised` | `253 252 251` |
 * | `--line-soft` — every hairline | `border-border-soft` | `234 229 223` |
 * | `--e2` — the plane's lift | `shadow` | the second elevation |
 *
 * ⛔ **`border-border` is NOT used on the plane**, and that is the mistake the
 * repository has already paid for once: the strong hairline everywhere makes
 * the whole surface read heavier than the design. 📁 The design uses
 * `--line-soft` for the plane, the rail's edge and every divider inside it.
 *
 * ## ⚠️ Below the reference layout
 *
 * 📁 *"Rail collapses to a horizontal progress bar with step name and count
 * above the content."* ⚡ **The rail stays** — it is the only thing saying how
 * much is left — **and stacks above rather than beside.**
 */
export interface OnboardingShellProps {
  /**
   * 📁 The rail, composed by the screen — see `onboarding/rail.tsx`.
   *
   * ⚡ **Optional, because screen `07` has none.** 📁 The design draws Connect
   * as a single `36px 40px` plane: the flow's questions are over, and the
   * rail's job was to say how many were left.
   *
   * 🔴 **This used to be required, and passing `null` silently broke the
   * page.** ⛔ The grid still allocated its `15rem` first column, so the whole
   * screen rendered inside a 240px strip with the connector tiles overlapping
   * each other. **`tsc` was happy — `null` is a valid `ReactNode`** — and only
   * a screenshot showed it.
   */
  readonly rail?: React.ReactNode;
  /**
   * 📁 **The design's step heading**, rendered above the body so every counted
   * step gets the same 24px/700 treatment and the same focus target without
   * restating it.
   */
  readonly title?: string;
  readonly description?: React.ReactNode;
  /** 📁 *"the primary action sits bottom-left of the content column."* */
  readonly actions?: React.ReactNode;
  readonly children: React.ReactNode;
  /**
   * 📁 **Welcome is padded `40px 44px`; every step after it `36px 44px`.** ⚡ A
   * value rather than a class, so the difference is stated once here instead of
   * being re-chosen on each screen.
   */
  readonly roomy?: boolean;
}

export function OnboardingShell({
  rail = null,
  title,
  description,
  actions,
  children,
  roomy = false,
}: OnboardingShellProps) {
  // ⚡ **A rail-less screen is one plane, not a two-column grid with an empty
  // column.** 📁 Screen `07`'s padding is `36px 40px` where a step's is
  // `36px 44px`, because it has no rail to sit beside.
  const railed = rail !== null && rail !== undefined && rail !== false;

  return (
    <div className="min-h-screen bg-canvas px-5 py-10 phone:py-16">
      <div
        className={cn(
          // 📁 *"920px frame"* — 57.5rem.
          'mx-auto w-full max-w-[57.5rem] overflow-hidden rounded-xl',
          'border border-border-soft bg-surface shadow',
          railed && 'grid laptop:grid-cols-[15rem_minmax(0,1fr)]',
        )}
      >
        {rail}
        {/* ♿ **Focus moves here on every step change and the heading carries
            its own position** — WCAG 2.4.3, which the design names by number
            and quotes: *"Step 3 of 4, What do you do at Northwind?"*. */}
        <main className={cn('min-w-0', railed ? 'px-11' : 'px-10', roomy ? 'py-10' : 'py-9')}>
          {title === undefined ? null : (
            <StepHeading title={title}>{description}</StepHeading>
          )}
          <div className={title === undefined ? undefined : 'mt-6'}>{children}</div>
          {actions === undefined ? null : <StepFooter>{actions}</StepFooter>}
        </main>
      </div>
    </div>
  );
}

/**
 * 📁 **The step heading and its supporting line** — *"24px / 700 / -0.026em"*
 * on a step, with the sub-line at 14px on `--ink-2`.
 *
 * ♿ **`tabIndex={-1}`** makes it programmatically focusable without putting it
 * in the tab order, which is the whole of the 2.4.3 pattern.
 */
export function StepHeading({
  title,
  children,
  large = false,
}: {
  title: string;
  children?: React.ReactNode;
  /** 📁 Welcome sets its greeting at 28px; every step after it at 24px. */
  large?: boolean;
  }) {
  return (
    <>
      <h1
        tabIndex={-1}
        className={cn(
          'font-bold text-content outline-none',
          large
            ? 'text-[28px] leading-[1.15] tracking-[-0.028em]'
            : 'text-2xl tracking-[-0.026em]',
        )}
      >
        {title}
      </h1>
      {children === undefined ? null : (
        <p className="mt-2 max-w-[52ch] text-sm leading-relaxed text-content-muted">{children}</p>
      )}
    </>
  );
}

/**
 * 📁 **The step footer** — *"the primary action sits bottom-left of the content
 * column, never floating."* ⚡ Gap 12px, and the secondary is a quiet 13px
 * `--ink-3` label rather than a second button.
 */
export function StepFooter({ children }: { children: React.ReactNode }) {
  return <div className="mt-7 flex flex-wrap items-center gap-3">{children}</div>;
}
