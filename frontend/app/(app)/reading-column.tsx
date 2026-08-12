import type { ReactNode } from 'react';

import { Column, Columns } from '@/components/ui';

/**
 * **The narrow column nine screens were drawing by hand** —
 * [TASK-1464](../../../docs/BACKLOG.md), against 📁
 * [`Fortune Signora Design System v2.dc.html`](../../../docs/design-snapshot/screens/)
 * `inherited`: ***"12-column grid, 24px gutters, 1600px content maximum."***
 *
 * ## 🔴 What was wrong, and it was not the narrowness
 *
 * ⛔ **Nine route directories opened with the same line** —
 * `mx-auto flex max-w-3xl flex-col gap-6` — **768px, fixed, at every viewport,
 * inside a container the design allows 1600.** ⚡ **The width was not chosen
 * per screen; it was copied.** 📁 **The row's own measurement**: *"768px inside
 * a 1600px container is 48% of the width the design allots."*
 *
 * ⚠️ **A settings form IS legitimately narrow, and the row says so** — *"1600px
 * is a MAXIMUM, not a target; do not widen a form to fill it to prove the
 * migration happened."* 🔴 **So the defect is not that these screens are
 * narrow. It is that their narrowness comes from a `max-w-*` chosen per file
 * rather than from the design's coordinate system.**
 *
 * ## ⚡ Why a span of eight, and why the number is derived rather than picked
 *
 * ⛔ **The Definition of Done requires that *"no screen's rendered content width
 * changes except where the design requires it"***, so the span is **the one
 * nearest today's rendered width at the viewport the row asserts at.**
 *
 * | At 1280 | |
 * |---|---|
 * | The container's inner width | `1280 − 48` gutters = **1232** |
 * | Twelve tracks, eleven 24px gaps | `(1232 − 264) / 12` = **80.7px per track** |
 * | **Span 8** | `8 × 80.7 + 7 × 24` = **≈813px** |
 * | Span 7 | ≈709px · **Span 6** ≈605px |
 * | 📁 **Today** | **768px** |
 *
 * ✅ **Eight is the closest, and it is the closest by measurement rather than
 * by taste.** ⚡ **It widens on a large monitor and narrows on a small one**,
 * which is the whole difference between a coordinate system and a constant —
 * **and it is the change the design requires**, since a fixed 768px was the
 * thing that did not inherit.
 *
 * ## ⛔ One definition, not nine
 *
 * 📁 [§2](../../../CLAUDE.md) — **nine `span={8}` literals would be nine copies
 * of one decision**, and the ninth would be the one nobody updated. ⚠️ **It
 * lives here rather than in `components/ui` because that directory is
 * [TASK-1460](../../../docs/BACKLOG.md)'s and this row's Change Budget
 * excludes it by name.**
 *
 * ⚡ **It also gives [`Columns`](../../components/ui/container.tsx) and
 * `Column` their first real consumers** — 📁 both shipped with none, which is
 * the orphan class this lane has now found six times.
 */
export function ReadingColumn({ children }: { children: ReactNode }) {
  return (
    <Columns>
      <Column span={8} className="flex flex-col gap-6">
        {children}
      </Column>
    </Columns>
  );
}
