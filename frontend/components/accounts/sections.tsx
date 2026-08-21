/**
 * **Account 360's section rail, and the sections nothing can fill** —
 * [TASK-1415](../../../docs/BACKLOG.md), against 📁
 * `Fortune Signora Account 360.dc.html`.
 *
 * ## 🔴 Why an absent section is RENDERED rather than omitted
 *
 * 📁 **[§20c](../../../CLAUDE.md)**: *"screens without a shipped module behind
 * them ship a designed empty state."* ⛔ **And an omission is not one.**
 *
 * ⚠️ **Seven of the design's fifteen sections have nothing behind them**
 * ([`lib/accounts/sections.ts`](../../lib/accounts/sections.ts) is the
 * measurement). **A page that simply left them out would be
 * indistinguishable from a page with a bug** — a rep who has seen the design
 * would assume the screen was broken, and the next lane could not tell which
 * it was either.
 *
 * ✅ **So each says what it would show and what Signora cannot answer yet.**
 * ⛔ **Never *"coming soon"*** — 📁 the rail already paid for that once: *"at
 * M12.3, three of six said `coming soon` on the screen a customer sees
 * first."*
 */

'use client';

import { cn } from '@/lib/design/cn';
import { onThisPage, type AccountSection } from '@/lib/accounts/sections';

/**
 * 📁 **The design's *"On this page"* rail** — 📁 `Design Documents/Fortune
 * Signora Account 360.html`, and this is now built to its own geometry rather
 * than as a strip.
 *
 * ## 🔴 What the final document actually specifies
 *
 * ```
 * width:184px; flex:none; position:sticky; top:0; align-self:flex-start
 * label 10.5px / 600 / 0.07em / uppercase / --ink-4
 * entry display:flex; gap:8px; padding:5px 8px; border-radius:7px; 12px
 * active --brand-ink on --brand-tint, 600 hover --sunken
 * ```
 *
 * ⛔ **It was rendered as a horizontal chip strip at every width**, on the
 * reasoning that *"the right-hand column on this screen is the utility panel
 * and two rails competing for one edge serves neither."* ⚠️ **That reasoning
 * confused two regions**: 📁 the App Shell's utility panel *"docks to the right
 * of content"* and is **shell chrome**, while this rail is **inside** the
 * content region on its left. **They never met.**
 *
 * ## ⚡ Why a `Column` span rather than `width:184px`
 *
 * ⛔ **A literal 184px would be an arbitrary dimension in a product whose
 * design opens with *"12-column grid, 24px gutters, 1600px content maximum."***
 * ✅ **A span of two is ≈200px at 1440 and it BREATHES** — 📁 the same argument
 * [`ReadingColumn`](../../app/(app)/reading-column.tsx) makes for eight, and it
 * keeps the record's reading width **unchanged** rather than widening it to
 * fill the space the rail used to sit above.
 *
 * ## ⚠️ One landmark, two orientations
 *
 * ⛔ **Not two components and not two renders** — a second
 * `nav[aria-label="On this page"]` would be a duplicate landmark a screen
 * reader has to disambiguate. ⚡ **One element whose axis changes**: 📁 the App
 * Shell's *"the shell yields in a fixed order as width disappears"* and the
 * design system's *"chrome yields before data"* — **below 1024 the rail yields
 * to a strip rather than vanishing**, because an anchor nav that disappears
 * takes the record's map with it.
 *
 * ⚡ **Every section, including the ones that cannot be filled**, because the
 * rail is a map of the record and a map that hides the empty rooms is one
 * nobody can trust — 📁 the same reasoning `rail.ts` records for a restricted
 * navigation destination: *"a hidden destination teaches a person the feature
 * does not exist, so they ask for the wrong thing or ask nobody."*
 *
 * ⛔ **The design draws a count on each entry and none is rendered.** ⚠️ Only
 * two of the eighteen have a count this page could state, and 📁
 * [§20c](../../../CLAUDE.md) prefers an absent figure to a fabricated one —
 * **a rail of blanks would be worse than a rail of labels.**
 */
export function OnThisPage({
  anchored,
  className,
}: {
  /**
   * 🔴 **The ids this page actually renders**, and the rail links to nothing
   * else.
   *
   * ⚠️ **Found in a headed review**: the first version linked every section by
   * id while only the ABSENT ones carried one — ⛔ **so *Account score* and
   * *Summary* were links to nowhere**, which is precisely the defect this
   * component was written to prevent, one level up.
   *
   * ⚡ **`supplied` means a READ exists, not that this page renders it.**
   *
   * ⚠️ **This said three sections were unanchored — *Open opportunities*,
   * *Contacts & decision makers* and *Competitors*. ✅ Two are closed by
   * [TASK-1476](../../../docs/BACKLOG.md)** and the third is corrected rather
   * than merely ticked off:
   *
   * - **Competitors** now carries an `id` the page contributes, and
   * **Summary** and **Deeper research** carry one their own components
   * accept. ⛔ **They rendered here all along and simply had no anchor.**
   * - **Contacts & decision makers** is `absent` now and anchored as one —
   * 🔴 **it was never supplied**: its source was the workspace's ICP
   * committee, which is the same answer on every account.
   * - ⛔ **Open opportunities is still unanchored, and honestly so**: the
   * opportunity is rendered in the record's header rather than as a section
   * of its own, **so there is no region for the rail to reach.**
   */
  anchored: readonly string[];
  className?: string;
}) {
  const sections = onThisPage().filter((section) => anchored.includes(section.id));

  return (
    <nav
      aria-label="On this page"
      className={cn(
        // ⚡ **A strip below 1024 and the design's rail from 1024 up** — one
        // element, one landmark, and the axis is the only thing that changes.
        'flex flex-row flex-wrap items-center gap-1',
        'smalllaptop:flex-col smalllaptop:flex-nowrap smalllaptop:items-stretch smalllaptop:gap-0.5',
        className,
      )}
    >
      {/* 📁 *"10.5px / 600 / 0.07em / uppercase"* — ⚡ `text-2xs` is the
          nearest role on §04's scale and the tracking is the design's own.
          ⛔ The 8px lead-in only exists once the entries are stacked. */}
      <p
        className={cn(
          'text-2xs font-semibold uppercase tracking-[0.07em] text-content-subtle',
          'smalllaptop:px-2 smalllaptop:pb-2',
        )}
      >
        On this page
      </p>
      {sections.map((section) => (
        <a
          key={section.id}
          href={`#${section.id}`}
          // ⛔ **A dimmed entry, never a hidden one.** ⚡ The design's own
          // treatment for a destination that exists and cannot be entered.
          //
          // ♿ 📁 §17 `2.5.8` — *"Targets ≥ 24px."* ⚡ The design's own
          // `5px 8px` around 12px type is 27px, so the floor is what the
          // design already draws rather than something added to it.
          className={cn(
            'flex min-h-6 items-center gap-2 rounded-md px-2 py-1 text-2xs transition-colors',
            'coarse:min-h-11',
            section.supply === 'supplied'
              ? 'text-content-muted hover:bg-surface-sunken hover:text-content'
              : 'text-content-subtle hover:text-content-muted',
          )}
        >
          {section.label}
        </a>
      ))}
    </nav>
  );
}

/**
 * ⛔ **A section the platform cannot fill.**
 *
 * 🔴 **This is NOT an empty state and the difference is the whole component.**
 * 📁 [P-A](../../../docs/DOMAIN_DISCOVERY_REGISTER.md) applied one level up:
 * **an empty section means *this account has none*; an absent one means
 * *Signora cannot answer the question at all*** — and a rep who reads the
 * first when the second is true concludes their account is quiet, which is a
 * commercial decision made on a false reading.
 */
export function AbsentSection({ section }: { section: AccountSection }) {
  if (section.supply !== 'absent') return null;

  return (
    <section
      id={section.id}
      aria-labelledby={`${section.id}-heading`}
      className="flex flex-col gap-2"
    >
      <h2 id={`${section.id}-heading`} className="text-sm font-semibold text-content">
        {section.label}
      </h2>
      <div className="rounded-lg border border-dashed border-border-strong bg-surface px-4 py-4">
        {/* ⛔ **The sentence is the deliverable.** 📁 It says what the section
            would show and what is missing — never that it is *"coming soon"*,
            which tells somebody to wait without saying for what. */}
        <p className="text-sm leading-6 text-content-muted">{section.absence}</p>
      </div>
    </section>
  );
}
