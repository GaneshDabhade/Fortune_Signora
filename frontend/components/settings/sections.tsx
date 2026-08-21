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
              design's own, the same pairing the Account 360 rail uses. */}
          <p className="px-2 pb-1.5 text-2xs font-semibold uppercase tracking-[0.07em] text-content-subtle">
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
                'flex min-h-6 items-center gap-2 rounded-md px-2 py-1.5 text-2xs transition-colors',
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
      <Card>
        <CardHeader className="flex flex-col gap-0.5">
          <CardTitle id={`${section.id}-heading`}>{section.title}</CardTitle>
          {/* 📁 The design's meta line, beneath the title on every section. */}
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
