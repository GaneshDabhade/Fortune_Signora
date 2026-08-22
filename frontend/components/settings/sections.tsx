'use client';

import Link from 'next/link';

import { Card, CardBody, CardHeader, CardTitle } from '@/components/ui';
import { cn } from '@/lib/design/cn';
import { SETTINGS_NAV, type SettingsSection } from '@/lib/settings/sections';

/**
 * **The Settings navigation and its sections** — 📁 `Design Documents/Fortune
 * Signora Settings.html`.
 *
 * ⛔ **No `Settings*` fork of anything.** `Card`, `CardHeader`, `CardTitle` and
 * `CardBody` are the library's; the section shell below is twelve lines of
 * composition rather than a variant of
 * [`AccountSectionShell`](../accounts/section.tsx), **because that component
 * carries collapse state, severities and a per-account-type persistence key,
 * and none of the three means anything here.** ⚡ **Reusing it would have meant
 * passing `severities={[]}` and `kind={null}` on every call** — 📁 the shape
 * [§20c](../../../CLAUDE.md) calls bending a component to suit one caller.
 */

/**
 * 📁 **The design's grouped navigation** — four groups over eleven anchors.
 *
 * ⚠️ **It renders in the CONTENT column, not in the application rail**, and
 * that is a deliberate limit on this slice. 📁 **The design draws it at
 * `width:238px` in the rail's own position**, which would make the primary
 * navigation contextual — **a change to the App Shell, 🔴 under
 * [§20e](../../../CLAUDE.md)'s Change Budget**, and already in front of the
 * product owner as QE's **D13-B** (*App Shell 232px vs Settings 238px*).
 * ✅ **Recorded rather than taken**; everything else about the navigation is
 * the design's.
 */
/**
 * ⛔ **The design draws an ACTIVE item and this renders none, deliberately.**
 *
 * 📁 **The design states the appearance exactly** — `color: var(--brand-ink)`,
 * `background: var(--brand-tint)`, `weight: 600`, against `--ink-2` /
 * transparent / 400 for the rest. ⚠️ **It does not state what MAKES an item
 * active**, and the two candidate rules are a scroll observer and the URL
 * fragment — neither of which the design mentions.
 *
 * 🔴 **And the design's own navigation makes any anchor-derived rule ambiguous**:
 * *SSO* and *SCIM* both point at `#sso`, *API keys* and *Webhooks* both at
 * `#api`. **Any rule reading the anchor marks TWO items active**, and the
 * design shows one.
 *
 * ⚡ **So the appearance is specified and the behaviour is not** — inventing the
 * rule would be reinterpreting the design rather than implementing it. **The
 * same absence exists on Account 360's `OnThisPage` rail**, whose docstring
 * records `active --brand-ink on --brand-tint, 600` and which renders no active
 * entry either. ✅ **Recorded here rather than guessed at; if it is wanted, it
 * wants a ruling on the rule, not a component.**
 */
export function SettingsNav({ className }: { className?: string }) {
  return (
    <nav
      aria-label="Settings sections"
      className={cn('flex flex-col gap-4', className)}
    >
      {SETTINGS_NAV.map((group) => (
        <div key={group.label} className="flex flex-col">
          {/* 📁 *"10.5px / 600 / 0.07em / uppercase / --ink-4"* — ⚡ `text-2xs`
              is the nearest role §04 publishes and the tracking is the
              design's own, the same pairing the Account 360 rail uses.

              🔴 **`text-content-faint`, not `-subtle`** — 📁 the design draws this
              label in `--ink-4` and the product's content ramp had no fourth
              step ([B-1064](../../../docs/BUGS.md), QE). ⛔ **It rendered one
              step too dark on every Settings section, and nothing could see it
              because the ramp was SHORT rather than wrong.**

              ⚡ **QE's audit of `main` settles the SIZE in the system's favour
              too**: 📁 §04 `Column head` is `11 / 1.4 / 600 / upper`, so
              `text-2xs` at 11px is correct and **this screen's `10.5px` is the
              outlier** — the same shape as its 16px card radius, and covered by
              the same [C-1547](../../../docs/LANE_COORDINATION.md).

              ⚠️ **TWO DOCUMENTS DISAGREE BY 0.01em AND THIS FOLLOWS THE SCREEN.**
              📁 **Design System v2 §04 `typeRows` gives `Column head` as
              `11 / 1.4 / 600 / +0.06em / upper`**; 📁 **this screen and Account
              360 both draw `0.07em`.** ⛔ **Not silently reconciled**: moving to
              `0.06em` here would make Settings disagree with the Account 360
              rail, which is the worse of the two inconsistencies.
              ⚡ **`onboarding/rail.tsx` already uses `0.06em`**, so the product
              currently carries both — recorded rather than resolved in code. */}
          <p className="px-2 pb-1.5 text-2xs font-semibold uppercase tracking-[0.07em] text-content-faint">
            {group.label}
          </p>
          {group.items.map((item) => (
            <a
              key={item.label}
              href={`#${item.section}`}
              // 📁 *"padding:6px 9px; border-radius:8px; font-size:12.5px"*,
              // hover `--sunken`. ♿ 📁 §17 `2.5.8` — the design's own 6px
              // around 12.5px type is 25px, so the floor is what it already
              // draws rather than something added to it.
              className={cn(
                // 🔴 **`text-xs`, not `text-2xs`.** 📁 **The design sets the
                // ITEM at `12.5px` and the GROUP LABEL at `10.5px`** — two
                // sizes, and this rendered both at `--text-2xs` (11px), which
                // flattened the hierarchy the nav is built on.
                //
                // ✅ **§04 NAMES THIS ROLE AND IT IS `Caption` — `12 / 1.5 / 400`.**
                // 📁 **`--text-xs` is 12px**, so the token is the role rather
                // than an approximation of a different one.
                //
                // ⛔ **NOT `text-label`, though that token is exactly 12.5px**:
                // `--text-label` carries the whole `Label` role — `12.5 / 1.45 /
                // 600` — and the design draws this item at the default weight,
                // so taking it would state a role this element does not have
                // and render it bold.
                //
                // ⚠️ **This comment used to argue to 12/400 from *"12 against
                // 12.5 is invisible; 400 against 600 is not"*** — 🔴 **true, and
                // it was a derivation standing where an authority exists.** ⚡
                // **QE's audit of §04 found the role.** ⛔ **A reasoned guess
                // that happens to be right still teaches the next reader to
                // guess.**
                'flex min-h-6 items-center gap-2 rounded-md px-2 py-1.5 text-xs transition-colors',
                'coarse:min-h-11',
                'text-content-muted hover:bg-surface-sunken hover:text-content',
              )}
            >
              {item.label}
            </a>
          ))}
        </div>
      ))}
    </nav>
  );
}

/**
 * 📁 **One section of the Settings page**, in the design's composition: a title
 * at `14.5px/600`, a meta line at `11.5px` on `--ink-3`, and the body beneath.
 *
 * ♿ **A labelled region with a heading**, which is the same rule Account 360's
 * sections follow — 📁 *"every section is a labelled region with a heading,
 * reachable by landmark navigation."*
 */
export function SettingsSectionShell({
  section,
  children,
}: {
  section: SettingsSection;
  children: React.ReactNode;
}) {
  return (
    <section id={section.id} aria-labelledby={`${section.id}-heading`} className="scroll-mt-4">
      {/* ⚠️ **The card is 12px and the Settings design draws 16px — and 12px is
          CORRECT.** 📁 **Design System v2 §05 `radii` assigns `12px --r-lg` to
          *"Card, menu, popover, toast, chart container"* and `16px --r-xl` to
          *"Table plane, dialog, drawer, assistant panel"***, so this screen's
          16px contradicts the system's own scale. ⚡ **§09 `Cards` states it in
          words too — *"12px radius"* — and draws `padding:20px`, which is what
          `CardHeader` renders.**

          ⛔ **So this is NOT a divergence to fix, and `components/ui/card.tsx`
          must not be restyled for this screen** ([§20c](../../CLAUDE.md)).
          🔴 **Recorded as [C-1547](../../../docs/LANE_COORDINATION.md) because
          an auditor comparing this screen to its own document will read 12 vs
          16 as a defect** — which is exactly what happened here before the
          system document was checked. */}
      <Card>
        {/* 🔴 **This was `flex-col`, and the comment beside it asserted the
            design put the meta *"beneath the title"*. ⛔ It does not.** 📁 The
            design's section header is ONE row — `display:flex;
            align-items:center; gap:10px; flex-wrap:wrap` — with the meta beside
            the title, not under it. ⚠️ **A comment citing the design while
            describing the implementation is the worst kind of wrong**, because
            it stops the next reader checking.

            ⚡ **`flex-wrap` is the design's own**, so a long meta wraps to its
            own line on a narrow screen rather than crushing the title. */}
        <CardHeader className="flex flex-wrap items-center gap-2.5">
          <CardTitle id={`${section.id}-heading`}>{section.title}</CardTitle>
          <p className="text-2xs text-content-subtle">{section.meta}</p>
        </CardHeader>
        <CardBody>{children}</CardBody>
      </Card>
    </section>
  );
}

/**
 * ⛔ **A Settings capability this product does not have.**
 *
 * 🔴 **This is NOT an empty state, and the difference is the whole component** —
 * 📁 the same distinction [`AbsentSection`](../accounts/sections.tsx) draws one
 * screen over: **an empty section means *you have none of these*; an absent one
 * means *Signora cannot do this at all*.** ⚡ **A reader who takes the first for
 * the second goes looking for a control that was never built.**
 *
 * ⛔ **No control, no figure, no placeholder input.** 📁 The instruction this
 * implements: *"do not create placeholder functionality that makes an
 * unavailable capability appear operational."*
 */
export function AbsentSettings({ section }: { section: SettingsSection }) {
  if (section.supply !== 'absent') return null;

  return (
    <p className="rounded-md border border-dashed border-border px-4 py-3.5 text-sm leading-6 text-content-muted">
      {section.absence}
    </p>
  );
}

/**
 * ⚡ **A section whose detail lives on its own route**, with the sentence that
 * says so.
 *
 * 📁 **The Experience Map names `…/settings/team` and `…/settings/integrations`
 * as canonical routes**, and the Settings design draws their content inline.
 * ⚠️ **Both are final documents and they disagree**, which is recorded as a
 * conflict rather than resolved here — 📁
 * [C-1545](../../../docs/LANE_COORDINATION.md).
 *
 * ⛔ **The link is not a placeholder**: it goes to a screen that exists and
 * works today, so it is a real affordance rather than one implying a capability
 * the product lacks.
 */
export function ElsewhereSettings({
  children,
  href,
  label,
}: {
  children: React.ReactNode;
  href: string;
  label: string;
}) {
  return (
    <div className="flex flex-col gap-3">
      <p className="text-sm leading-6 text-content-muted">{children}</p>
      <Link
        href={href}
        className="inline-block self-start rounded text-sm font-medium text-accent underline decoration-border underline-offset-4 transition-colors hover:decoration-accent"
      >
        {label}
      </Link>
    </div>
  );
}
