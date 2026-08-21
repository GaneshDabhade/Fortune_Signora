import type { ReactNode } from 'react';

import { Skeleton } from '@/components/ui/skeleton';
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
  /**
   * ⚡ **Set beside the title, on the title's own baseline** — 📁 the finalized
   * Companies design draws *"Companies  8,412 total · 312 in view"* as one
   * line, and **the counts are part of the heading rather than a sentence
   * under it.**
   *
   * ⛔ **Not folded into `title`.** The `h1` is the route's name and a screen
   * reader announces it; **a heading that read *"Companies 8,412 total 312 in
   * view"* would make the landmark a sentence.** ✅ Two nodes, one line.
   *
   * ⚠️ **A slot rather than `total: number`** — the shape of the meta differs
   * per screen, and a numeric prop here would decide the wording for every
   * caller.
   */
  titleMeta?: ReactNode;
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
const PLANE = 'rounded-xl border border-border-soft bg-surface shadow-sm';

function Actions({
  primaryAction,
  secondaryActions,
}: Pick<PageHeaderProps, 'primaryAction' | 'secondaryActions'>) {
  if (primaryAction === undefined && secondaryActions === undefined) return null;

  return (
    /* ⚡ **`flex-wrap`, and `flex-none` is gone.** ⛔ **`flex-none` was the
       whole of the header's mobile defect**: measured at 390 × 844, the actions
       kept their full width and the title column was left ~150px, so
       *"Companies"* sat beside *"Export"* over a description running at
       twenty-four characters a line. **A header's actions give way before its
       title does** — they wrap under it, and if two of them cannot share a line
       they wrap against each other. */
    <div className="flex flex-wrap items-center gap-2">
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
  titleMeta,
  description,
  primaryAction,
  secondaryActions,
  className,
}: PageHeaderProps) {
  return (
    // 📁 *"24px padding and a soft bottom hairline."*
    <header className={cn(PLANE, 'mb-6 p-6', className)}>
      {eyebrow !== undefined ? <div className="mb-2">{eyebrow}</div> : null}
      {/* 🔴 **The header's layout model, and it is intrinsic rather than
          banded** — this row carried `flex items-start gap-4` with a
          `flex-none` action group, which is a desktop row that never stops
          being one.

          ⚡ **`flex-wrap` plus a `basis` on the title is what makes it
          responsive without a breakpoint**: the title asks for 16rem, and the
          moment the container cannot give it that *and* fit the actions
          alongside, the actions wrap beneath. ⛔ **No media query, so it is
          correct at every width between the design's bands** rather than at the
          four the bands name — and it reacts to the CONTAINER, so a header
          inside a narrow column behaves like a header on a phone. */}
      <div className="flex flex-wrap items-start gap-x-4 gap-y-3">
        <div className="min-w-0 grow basis-64">
          {/* 📁 §04's `Title` role — 26px / 1.15 / 700 / −0.026em, all four
              numbers, which is why `text-title` is a tuple in the config. */}
          {/* ⚡ **One line, two elements** — 📁 the design sets the counts on
              the title's baseline, not beneath it. ⛔ **`items-baseline`, so
              the 26px heading and the 13px meta sit on one optical line**
              rather than being centred against each other. */}
          <div className="flex flex-wrap items-baseline gap-x-3 gap-y-1">
            <h1 className="truncate text-title text-content">{title}</h1>
            {titleMeta !== undefined ? (
              <span className="text-sm text-content-muted">{titleMeta}</span>
            ) : null}
          </div>
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
  /**
   * 🔴 **📁 §08's fact carries a SECOND term and this slot was missing** — the
   * design draws every header fact as a value **and** a qualifier on one
   * baseline: *"$1.24M **−12%**"*, *"12 Oct 2026 **69 days**"*, *"1,240 **91%
   * active**"*.
   *
   * ⚡ **Optional, so every existing caller is unchanged** — ⛔ a fact whose
   * qualifier has no producer renders exactly as it did before, rather than
   * acquiring an empty second line.
   */
  delta?: ReactNode;
  /**
   * ⚠️ **The design colours a delta by judgement — `risk`, `warn`, `pos` — and
   * that judgement is a PRODUCT rule, not a rendering one.**
   *
   * ⛔ **Defaults to neutral deliberately.** 📁 §08 draws *"69 days"* in `warn`,
   * which implies a threshold at which a renewal becomes urgent — **nothing in
   * the product defines one**, and picking a number here would invent the rule
   * rather than render it. ✅ **A caller passes a tone only where a producer
   * establishes the judgement.**
   */
  deltaTone?: 'neutral' | 'positive' | 'caution' | 'critical';
}

/**
 * ⛔ **`titleMeta` is removed rather than inherited, and that is a correction.**
 *
 * 🔴 **`RecordHeaderProps` extended `PageHeaderProps` whole, so `titleMeta` was
 * a legal prop that `RecordHeader` never destructured** — **a caller could pass
 * it, `tsc` would agree, and nothing would render.** 📁 [§2](../../../CLAUDE.md):
 * *types should make incorrect architecture impossible*, and a prop that cannot
 * work is the same defect class as a guard that cannot fail.
 *
 * ⚡ **Removed rather than implemented, because the design has no role for it
 * here.** 📁 `titleMeta` is §08's PAGE header carrying a list's counts —
 * *"8,412 total · 312 in view"* — and §04's RECORD header puts the status pill
 * and the tag chips beside the title instead. **That slot exists and is called
 * {@link RecordHeaderProps.status}.**
 */
export interface RecordHeaderProps extends Omit<PageHeaderProps, 'titleMeta'> {
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
  /**
   * 📁 **§08's line under the actions** — *"Owner **M. Reinhardt** · CSM
   * **P. Lund** · Synced 4m ago."*
   *
   * ⚡ **A slot rather than `owner`/`syncedAt` props**: the facts differ per
   * record type, and a typed pair here would decide the wording — the same
   * reasoning `titleMeta` already carries.
   *
   * ⛔ **Not `description`**, which renders a `<p>`: 📁 the record page's line
   * is itself a paragraph (`Freshness`, `WorkflowStage`), and a `<p>` inside a
   * `<p>` is closed by the parser, so the second half of the header would fall
   * out of the header element.
   */
  meta?: ReactNode;
  /**
   * ⚡ **The name has not arrived yet.** ⛔ **The `<h1>` still renders** — 📁
   * [B-313](../../../docs/BUGS.md) is that a record page with no level-1
   * heading leaves every `<h2>` hanging under nothing, and a heading that
   * appears a moment later is the same defect for as long as it lasts.
   *
   * ⚠️ **Absence is NOT loading.** A record nobody has named passes the
   * identifier as `title`; this is only *the read is in flight*.
   */
  titleLoading?: boolean;
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
  meta,
  titleLoading = false,
  className,
}: RecordHeaderProps) {
  return (
    <header className={cn(PLANE, 'mb-6 p-6', className)}>
      {eyebrow !== undefined ? <div className="mb-3">{eyebrow}</div> : null}

      {/* ⚡ **The same intrinsic model as `PageHeader` above** — the identity
          tile and the title travel together, and the actions wrap beneath them
          when the row cannot hold all three. */}
      <div className="flex flex-wrap items-start gap-x-4 gap-y-3">
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

        <div className="min-w-0 grow basis-64">
          <div className="flex flex-wrap items-center gap-2.5">
            {/* ⚡ **The element is unconditional; only its contents wait.** 📁
                B-313 — the outline must never lose its level 1, not even for
                the moment the identity read is in flight. */}
            <h1 className="min-w-0 truncate text-title text-content">
              {titleLoading ? <Skeleton className="h-7 w-56 max-w-full" /> : title}
            </h1>
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
                  {/* 📁 *"display:flex;align-items:baseline;gap:6px"* — the
                      value and its qualifier share one baseline, so the eye
                      reads them as one fact rather than two stacked lines. */}
                  <dd className="mt-0.5 flex items-baseline gap-1.5">
                    <span className="text-sm font-semibold tabular-nums text-content">
                      {fact.value}
                    </span>
                    {fact.delta === undefined ? null : (
                      <span
                        className={cn(
                          'text-2xs font-semibold',
                          fact.deltaTone === 'positive'
                            ? 'text-success'
                            : fact.deltaTone === 'caution'
                              ? 'text-warning'
                              : fact.deltaTone === 'critical'
                                ? 'text-danger'
                                : 'text-content-subtle',
                        )}
                      >
                        {fact.delta}
                      </span>
                    )}
                  </dd>
                </div>
              ))}
            </dl>
          ) : null}
        </div>

        {/* 📁 **§08 stacks the meta line beneath the actions and shares their
            column** — *"Owner M. Reinhardt · CSM P. Lund · Synced 4m ago."*

            ⛔ **Left-aligned, and §08's right edge is deliberately NOT
            reproduced.** ⚠️ **Measured on Company 360 at 1440**: the header sits
            in a 737px reading column, the title asks for its `basis-64` and
            grows, so **this block wraps onto its own full-width row** — and a
            right-aligned meta line under a left-aligned button row reads as two
            elements that lost each other. ⚡ **`items-end` is only ever correct
            while the block is genuinely the right-hand column**, which flexbox
            cannot tell it, so the alignment that is right at every width wins
            over the one that is right at one. */}
        {meta === undefined ? (
          <Actions primaryAction={primaryAction} secondaryActions={secondaryActions} />
        ) : (
          <div className="flex min-w-0 flex-col items-start gap-2">
            <Actions primaryAction={primaryAction} secondaryActions={secondaryActions} />
            <div className="min-w-0 text-sm text-content-muted">{meta}</div>
          </div>
        )}
      </div>

      {health !== undefined ? (
        <div className="mt-5 flex items-start gap-3 text-sm leading-6 text-content-muted">
          {health}
        </div>
      ) : null}
    </header>
  );
}
