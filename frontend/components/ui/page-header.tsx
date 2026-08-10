import type { ReactNode } from 'react';

import { cn } from '@/lib/design/cn';

/**
 * **The page and record headers** — [TASK-1446](../../../docs/BACKLOG.md),
 * against 📁 [Design System v2](../../../docs/design-snapshot/screens/) §08
 * *"Page & record headers"* ([D-138](../../../docs/DECISION_REGISTER.md)).
 *
 * ## 🔴 Shell rule 03 was executable and unenforceable at the same time
 *
 * 📁 [`lib/shell/constitution.ts`](../../lib/shell/constitution.ts) exports it
 * as code: ***"One primary action per view, and it lives in the page
 * header."*** ⛔ **And there was no page header.** ⚠️ **`grep -rl
 * "PageHeader\|RecordHeader" app components` returned zero files** — **a rule
 * constraining where the primary action lives, and no such place.**
 *
 * ⚡ **So the rule is now structural rather than aspirational**: `primaryAction`
 * is **one slot, not a list**. 📁 [§2](../../../CLAUDE.md) prefers a violation
 * that is *unrepresentable* over one that is *discouraged* — **a second primary
 * action does not fail review, it fails to type-check.**
 *
 * ## ⚡ Secondary before primary, which is the design's order and not habit
 *
 * 📁 §08 renders `Export` — outlined, `--line` border — **before** `Log
 * activity` — `--brand` fill, white, `--e1`. ⛔ **Reversing them puts the
 * heaviest control furthest from the eye's landing point on a left-to-right
 * scan**, and the shell already made the same choice for *"help before
 * account, always last."*
 *
 * ## 🔴 §04 is the type authority; §08's pixels are illustrative — [C-1414](../../../docs/LANE_COORDINATION.md)
 *
 * ⚡ **Ruled after this component was written, and it ratifies what it does.**
 * 📁 **§04's entries NAME TOKENS; §08's are inline `font-size:` in a rendered
 * mockup** — ⛔ **a section that names no token cannot be the token authority**,
 * and [D-138](../../../docs/DECISION_REGISTER.md) makes the snapshot the
 * implementation authority without making every pixel in it a requirement.
 *
 * ⚠️ **The scale of the divergence was measured by Lane C and it is larger than
 * this lane reported.** **§08 draws SEVEN distinct sizes — `11.5 · 13 · 14.5 ·
 * 15 · 16 · 24 · 30` — and only `30` matches a §04 role.** ⛔ **So §08 is drawn
 * almost entirely outside the type system**, and anyone migrating a screen
 * against its pixels rather than §04's roles would reproduce exactly the
 * fragmentation [D-218](../../../docs/DECISION_REGISTER.md) §9 measured.
 *
 * ✅ **This component therefore uses `text-title`, `text-sm` and `text-label`** —
 * the named roles — **and none of §08's inline values.**
 *
 * ## ⚠️ A correction this lane owes, because a right answer rested on a wrong measurement
 *
 * 🔴 **This file previously claimed *"the fact LABEL is 12.5px and that is
 * exactly `--text-label`"*. §08 renders it at `11.5px`.** ✅ **Measured directly
 * after [C-1414](../../../docs/LANE_COORDINATION.md) reported it, not taken on
 * trust.**
 *
 * ✅ **The conclusion is unchanged and never needed §08**: 📁 §04's `typeRows`
 * carries `['Label', '--text-label', '12.5 / 1.45 / 600', 12.5, 600, …]`
 * verbatim, **which is the evidence `design-scale.test.ts` already asserts
 * against.** ⛔ **But a correct answer resting on a wrong measurement is one
 * design refresh away from being a wrong answer**, so the evidence is repaired
 * rather than the conclusion defended.
 */

export interface PageHeaderProps {
  /** ⛔ **Required.** 📁 The route's `h1`; a header without one is a strip. */
  title: string;
  /**
   * ⚡ **The breadcrumb slot** — 📁 §08 puts the trail above the title.
   * ⛔ **A slot rather than a `Crumb[]`**: the trail is `Breadcrumb`'s to
   * render, and re-deciding it here would be a second answer to *where am I*.
   */
  eyebrow?: ReactNode;
  /** A sentence under the title. 📁 Optional — §08's page header often has none. */
  description?: ReactNode;
  /**
   * 🔴 **ONE, and the singular is the enforcement.** 📁 Shell rule 03. ⛔ A
   * `ReactNode[]` here would make the rule a convention again.
   */
  primaryAction?: ReactNode;
  /** ⚡ Rendered BEFORE the primary — §08's order. */
  secondaryActions?: ReactNode;
  className?: string;
}

/**
 * 📁 **§08's plane** — *"a surface plane with 24px padding and a soft bottom
 * hairline."* ⛔ **The radius is `--radius-xl` (16px)**, which §05 assigns to
 * *"table plane, dialog, drawer, assistant panel"* and which
 * [TASK-1453](../../../docs/BACKLOG.md) corrected the dialog onto.
 */
const PLANE = 'rounded-xl border border-border bg-surface shadow-sm';

function Actions({
  primaryAction,
  secondaryActions,
}: Pick<PageHeaderProps, 'primaryAction' | 'secondaryActions'>) {
  if (primaryAction === undefined && secondaryActions === undefined) return null;

  return (
    <div className="flex flex-none items-center gap-2">
      {secondaryActions}
      {/* ⚡ **The marker is what makes rule 03 assertable at runtime**, which
          the type alone cannot do for a caller that renders two buttons inside
          one node. 📁 [TASK-1446](../../../docs/BACKLOG.md): *"a second
          primary action fails the test."* */}
      {primaryAction !== undefined ? (
        <div data-primary-action="">{primaryAction}</div>
      ) : null}
    </div>
  );
}

export function PageHeader({
  title,
  eyebrow,
  description,
  primaryAction,
  secondaryActions,
  className,
}: PageHeaderProps) {
  return (
    // 📁 *"24px padding and a soft bottom hairline."*
    <header className={cn(PLANE, 'mb-6 p-6', className)}>
      {eyebrow !== undefined ? <div className="mb-2">{eyebrow}</div> : null}
      <div className="flex items-start gap-4">
        <div className="min-w-0 flex-1">
          {/* 📁 §04's `Title` role — 26px / 1.15 / 700 / −0.026em, all four
              numbers, which is why `text-title` is a tuple in the config. */}
          <h1 className="truncate text-title text-content">{title}</h1>
          {description !== undefined ? (
            <p className="mt-1.5 text-sm leading-6 text-content-muted">{description}</p>
          ) : null}
        </div>
        <Actions primaryAction={primaryAction} secondaryActions={secondaryActions} />
      </div>
    </header>
  );
}

export interface RecordFact {
  label: string;
  value: ReactNode;
}

export interface RecordHeaderProps extends PageHeaderProps {
  /**
   * 📁 *"identity"* — §08's 46px tile. ⛔ **Initials, not an image**: the
   * platform publishes no logo for an account, and a placeholder image is a
   * fact the product does not have.
   */
  initials?: string;
  /** 📁 *"status"* — the chips beside the title. */
  status?: ReactNode;
  /**
   * 📁 *"four key facts as a quiet strip."* ⚠️ **Four is the design's number
   * and it is not enforced here** — a record with three facts is not a defect,
   * and truncating a fifth would hide a fact the module chose to show.
   */
  facts?: readonly RecordFact[];
  /**
   * 📁 *"an AI health line."* ⛔ **Supplied, never derived** — a header that
   * composed its own health sentence would be the frame taking a product
   * decision, which shell rule 01 forbids.
   */
  health?: ReactNode;
}

export function RecordHeader({
  title,
  eyebrow,
  description,
  primaryAction,
  secondaryActions,
  initials,
  status,
  facts,
  health,
  className,
}: RecordHeaderProps) {
  return (
    <header className={cn(PLANE, 'mb-6 p-6', className)}>
      {eyebrow !== undefined ? <div className="mb-3">{eyebrow}</div> : null}

      <div className="flex items-start gap-4">
        {initials !== undefined ? (
          // 📁 §08: 46px, 12px radius, brand tint. ⛔ `rounded-lg` is the 12px
          // token — **not `rounded-full`**, which §05 reserves for the avatar
          // in the top bar. **One circle in the shell**, and this is not it.
          <span
            aria-hidden
            className="grid h-[46px] w-[46px] flex-none place-items-center rounded-lg border border-accent-subtle bg-accent-subtle text-sm font-bold text-accent"
          >
            {initials}
          </span>
        ) : null}

        <div className="min-w-0 flex-1">
          <div className="flex flex-wrap items-center gap-2.5">
            <h1 className="min-w-0 truncate text-title text-content">{title}</h1>
            {status}
          </div>

          {description !== undefined ? (
            <p className="mt-1.5 text-sm leading-6 text-content-muted">{description}</p>
          ) : null}

          {facts !== undefined && facts.length > 0 ? (
            // 📁 *"four key facts as a quiet strip"* — 28px gaps, label above
            // value. ⚡ A `<dl>` because it is pairs, and a screen reader reads
            // them as pairs rather than as eight loose strings.
            <dl className="mt-3.5 flex flex-wrap gap-x-7 gap-y-2">
              {facts.map((fact) => (
                <div key={fact.label}>
                  {/* ✅ `text-label` — §04's `Label` role, 12.5 / 1.45 / 600.
                      ⚡ Added by TASK-1453 because its DoD said *every role*,
                      and missed by that row's own measurement. First caller.
                      ⛔ **§08 draws this at 11.5px and that is not followed** —
                      C-1414: §04 is the type authority. */}
                  <dt className="text-label text-content-subtle">{fact.label}</dt>
                  <dd className="mt-0.5 text-sm font-semibold tabular-nums text-content">
                    {fact.value}
                  </dd>
                </div>
              ))}
            </dl>
          ) : null}
        </div>

        <Actions primaryAction={primaryAction} secondaryActions={secondaryActions} />
      </div>

      {health !== undefined ? (
        <div className="mt-5 flex items-start gap-3 text-sm leading-6 text-content-muted">
          {health}
        </div>
      ) : null}
    </header>
  );
}
