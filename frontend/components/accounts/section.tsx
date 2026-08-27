/**
 * **A section of Account 360, in every state the design gives it** —
 * [TASK-1476](../../../docs/BACKLOG.md), against 📁
 * `Fortune Signora Account 360.dc.html` §*States*.
 *
 * ⚡ **The rules live in
 * [`lib/accounts/section-state.ts`](../../lib/accounts/section-state.ts) and
 * this file obeys them.** ⛔ **Nothing about worst-status folding, the
 * persistence key or the skeleton row count is decided here** — a rule
 * duplicated between a law file and a component is a rule that will disagree
 * with itself ([§2](../../../CLAUDE.md)).
 *
 * ## ⛔ What this deliberately does not build
 *
 * 🔴 **The design's *Expanded* state — *"widens to the full content region with
 * filters, grouping and export"*.** ⚠️ **Filters, grouping and export are per
 * section and each needs a field to act on**, and 📁 the fields most sections
 * would group by are [C-210](../../../docs/LANE_COORDINATION.md)'s and
 * [C-1425](../../../docs/LANE_COORDINATION.md)'s. ⛔ **A control that widens a
 * region and offers three affordances that do nothing is the false-affordance
 * class** — **so the URL contract is built and the widened view is not, and
 * that is stated rather than hidden.** ✅ **What an anchor DOES do is open a
 * collapsed section**, which is the half of the rule that has a subject.
 */

'use client';

import { ChevronDown } from 'lucide-react';
import { useEffect, useState, type ReactNode } from 'react';

import { cn } from '@/lib/design/cn';
import {
  collapseKey,
  collapsedHeader,
  expansionFromAnchor,
  skeletonRows,
  type SectionSeverity,
} from '@/lib/accounts/section-state';
import { ACCOUNT_SECTIONS } from '@/lib/accounts/sections';
import { SkeletonText } from '@/components/ui';

/** ⚡ **The header's status dot** — 📁 tokens only, never a literal colour
 * ([§20c](../../../CLAUDE.md)). */
const SEVERITY_DOT: Record<SectionSeverity, string> = {
  none: 'bg-border-strong',
  good: 'bg-success',
  watch: 'bg-warning',
  risk: 'bg-danger',
};

const SEVERITY_LABEL: Record<SectionSeverity, string> = {
  none: '',
  good: 'nothing of concern',
  watch: 'worth watching',
  risk: 'a risk',
};

export function AccountSectionShell({
  id,
  heading,
  /**
   * 🔴 **One severity per item, in the section's own order.** ⚡ The header
   * folds them — 📁 *"the header keeps the count and the worst status, so
   * collapsing cannot hide a risk."*
   */
  severities,
  /**
   * 🔴 **How many items this section holds, as far as this page knows** —
   * [B-299](../../../docs/BUGS.md).
   *
   * ⛔ **`null` is *nobody counted*, and it is a THIRD answer** — not `0`.
   * ⚡ A read in flight on a first visit, and a read that failed, both report
   * `null`; ✅ **a read that succeeded and found nothing reports `0`.**
   *
   * ⚠️ **This replaced `lastKnownCount`, which was the same fact under a
   * narrower name.** ⚡ **Every call site computed both from one expression**
   * — `data?.length ?? null` — **so they were one prop wearing two.** 📁 And
   * the design says why they must be: *"header, title and counts paint from
   * CACHE; only the body skeletons"* — **the cached count IS the skeleton row
   * count**, so a section that knows how tall it was also knows what number to
   * show while it reloads.
   */
  count,
  /** ⚠️ **Whose preference this is.** `null` while the session is unknown, and
   * then nothing is persisted rather than persisted under a wrong owner. */
  viewerId,
  /**
   * 📁 **The account TYPE, never the record** — the design's own words.
   *
   * ⛔ **`null` when the type is not known**, and then NOTHING is persisted.
   * ⚠️ **This page does not know it today**: `useAccounts` returns
   * `AccountAttention` and `useAccountIdentities` returns `AccountIdentity`,
   * and **neither publishes `kind`** — only the Companies list's
   * `ListedAccount` does. ⚡ **Storing under a guessed type would put a rep's
   * preference somewhere they cannot get it back from**, and adding a whole
   * list read to key a collapse toggle is disproportionate. **The gap is
   * recorded rather than papered over** —
   * [B-261](../../../docs/BUGS.md).
   */
  kind,
  isLoading,
  isError = false,
  children,
}: {
  id: string;
  heading: string;
  severities: readonly SectionSeverity[];
  count: number | null;
  viewerId: string | null;
  kind: string | null;
  isLoading?: boolean;
  /**
   * 🔴 **[B-1054](../../../docs/BUGS.md) — a failed read rendered its count as
   * `0` beside a body correctly saying the read failed.**
   *
   * ⛔ **`0` is a MEASUREMENT and no measurement was obtained.** ⚡ **A reader
   * scanning headings — which is what a count beside a heading is FOR — read
   * *nothing changed at this account*, the exact inference the sentence below
   * it was written to prevent.** 🔴 **The section contradicted itself and the
   * half that was wrong was the half read first.**
   *
   * ⚠️ **This does not soften the rule the count exists for.** 📁 *"A positive
   * empty is good news, not a gap"* — ✅ **a read that SUCCEEDS and returns
   * nothing still says `0`.** ⛔ **What changes is only the case where nobody
   * counted anything.**
   */
  isError?: boolean;
  children: ReactNode;
}) {
  const [open, setOpen] = useState(true);
  // ⛔ **A failed read publishes no count** — [B-1054](../../../docs/BUGS.md).
  // ⚡ **The two absences meet here and become one**: nobody counted.
  const header = collapsedHeader(isError ? null : count, severities);

  const key = viewerId === null || kind === null ? null : collapseKey(viewerId, kind, id);

  // ⚠️ **Read after mount, never during render.** ⛔ `localStorage` is not
  // available on the server, and a value read during render would make the
  // first client paint disagree with the server's.
  useEffect(() => {
    if (key === null) return;
    setOpen(window.localStorage.getItem(key) !== 'collapsed');
  }, [key]);

  // 📁 ***"Anchor links from the page nav auto-expand the target section."***
  // ⚡ **Both on arrival and on a later click**, because a rail link to the
  // section a reader is already on changes the hash and nothing else.
  useEffect(() => {
    const openIfTargeted = () => {
      if (expansionFromAnchor(window.location.hash, ACCOUNT_SECTIONS) === id)
        setOpen(true);
    };
    openIfTargeted();
    window.addEventListener('hashchange', openIfTargeted);
    return () => window.removeEventListener('hashchange', openIfTargeted);
  }, [id]);

  const toggle = () => {
    const next = !open;
    setOpen(next);
    // ⛔ **Written under the type's key and never the record's.** ⚡ The key is
    // the law's; this component cannot construct another shape.
    if (key !== null) window.localStorage.setItem(key, next ? 'open' : 'collapsed');
  };

  return (
    <section
      id={id}
      // 📁 ***"Every section is a labelled region with a heading, reachable by
      // landmark navigation"*** — and that holds in EVERY state, collapsed
      // included.
      aria-labelledby={`${id}-heading`}
      className="flex flex-col gap-3"
    >
      <div className="flex flex-wrap items-center gap-2">
        {/* 🔴 **The heading is an `h2` and the button lives INSIDE it** — the
            standard disclosure pattern, and it is a correction rather than a
            preference. ⛔ **The first version made the heading a `span` inside
            the button**, which removed every section from the document outline
            — 📁 the design's *"every section is a labelled region WITH A
            HEADING, reachable by landmark navigation"* stops being true, and a
            screen-reader user loses the ability to jump between sections.
            ⚠️ **Caught by an existing TASK-417 assertion** that asks for the
            heading by role, **not by a new test** — which is the assertion
            doing exactly what it was written for. */}
        <h2 id={`${id}-heading`} className="text-sm font-semibold text-content">
          <button
            type="button"
            onClick={toggle}
            aria-expanded={open}
            aria-controls={`${id}-body`}
            /* ♿ 📁 **Design System v2 §17 `2.5.8`** — *"Targets ≥ 24px with
               8px separation; the 26px compact button keeps a 32px hit
               area."* ⚠️ **Measured at `159 × 21` on Company 360, and
               identically at 1440 and 390** — a line box and nothing more.
               ⛔ **`min-h-6` rather than a height**: the design's treatment
               here is a heading, not a button, so the control keeps its type
               and gains only the floor it was under. ⚡ **`coarse:min-h-11` is
               the pointer rule** — 📁 the same variant the top bar, the team
               page and the session panel already use, and a section heading
               is a control a thumb has to hit on a phone. */
            className={cn(
              'flex min-h-6 items-center gap-1.5 rounded text-left coarse:min-h-11',
            )}
          >
            <ChevronDown
              aria-hidden
              className={cn('h-3.5 w-3.5 transition-transform', open ? '' : '-rotate-90')}
            />
            {heading}
          </button>
        </h2>

        {/* 🔴 **The count and the worst status, and they stay while collapsed.**
            ⛔ **This is the design's safety rule, not a decoration**: a section
            folded to its heading alone can hide a risk, and that is the one
            outcome collapsing must never produce. */}
        {/* ⛔ **No count when the read failed** — 📁
            [B-1054](../../../docs/BUGS.md). ⚡ **Nothing here, rather than a
            zero**: 📁 [P-A](../../../docs/DOMAIN_DISCOVERY_REGISTER.md) in its
            quietest form — *a failed read must never render as an empty
            result*, and **`0` IS the empty result rendered as a fact.**
            ⚠️ **And no stale count either**: the number comes from this
            render's `severities`, so a previous render's figure cannot survive
            into a failure. */}
        {/* ⛔ **`null` renders nothing at all** — 📁 [B-299](../../../docs/BUGS.md).
            ⚡ **The header still keeps its heading, its chevron and its
            position**, which is 📁 *"header, title and counts paint from
            cache"*: what is missing is the one figure nobody measured, not the
            row it sits in. */}
        {header.count === null ? null : (
        <span className="flex items-center gap-1.5 text-2xs text-content-subtle">
          <span>{header.count}</span>
          {header.worst === 'none' ? null : (
            <>
              <span
                aria-hidden
                className={cn('h-1.5 w-1.5 rounded-full', SEVERITY_DOT[header.worst])}
              />
              {/**
                * 🔴 **This was `sr-only`, and that is 📁 §17 `1.4.1` failing** —
                * ***"Status keeps its dot AND its word. Tint alone never
                * carries meaning."***
                *
                * ⛔ **A screen-reader user heard *"a risk"*; a sighted user got
                * a coloured dot and nothing else.** ⚡ **`1.4.1` is about the
                * VISUAL channel** — an `sr-only` word does not satisfy it, and
                * this is the one criterion an `aria-` attribute cannot answer.
                *
                * ⚠️ **And the design carries this status as WORDS, not
                * colour.** 📁 Its collapsed header is `{name} {summary} ▸` with
                * **no dot at all**, and `stateCollapsed`'s summaries are
                * *"14 detected · 1 competitor present"*, *"6 · all healthy"*.
                *
                * ⛔ **Not replaced with the design's phrasing**, because those
                * summaries are per-section prose derived from each section's
                * own content — **a shell cannot compute them**, and inventing
                * one per section is the thing this file refuses everywhere
                * else. ✅ **Making the existing word visible moves toward the
                * design without authoring new copy**, and it is the same word
                * a screen reader already heard.
                */}
              <span>{SEVERITY_LABEL[header.worst]}</span>
            </>
          )}
        </span>
        )}
      </div>

      <div id={`${id}-body`} hidden={!open}>
        {isLoading ? (
          // 📁 ***"Skeleton row count matches the expected result so the page
          // height is stable."*** ⚡ The count is the law's, not a literal.
          <div className="flex flex-col gap-2" aria-hidden>
            {Array.from({ length: skeletonRows(count) }, (_, row) => (
              <SkeletonText key={row} />
            ))}
          </div>
        ) : (
          children
        )}
      </div>
    </section>
  );
}
