'use client';

import { useId, useState, type ReactNode } from 'react';

import { formatDay } from '@/components/intelligence/dates';
import { cn } from '@/lib/design/cn';

import { Confidence } from './confidence';

/**
 * **The AI attribution strip** — [TASK-1411](../../../docs/BACKLOG.md).
 *
 * ## 🔴 One component, because three designs draw the same line
 *
 * 📁 **Account 360**: *"Show reasoning · 6 sources · Confidence 4 of 5 ·
 * Generated 09:14"*. 📁 **Reports**: *"Confidence 4 of 5 · 3 sources"*.
 * 📁 **AI Research**: *"14 sources · 3 excluded · Confidence 4 of 5"*.
 *
 * ⛔ **Three workflows reaching this separately build three of these, and they
 * will disagree about what *4 of 5* means.** ⚡ **The row's named risk is
 * building it for Account 360 and generalising later** — so `excluded` is here
 * from the first line rather than added by the third consumer.
 *
 * ## ⛔ It never renders a confidence the model did not produce
 *
 * ⚠️ **The row's first slice was a READ, and this lane performed it before
 * claiming**: 📁 **`ai_platform/public/` exports `Infer`, the inference types,
 * `ExplanationSource`, `EvidenceFact`, `EvidenceRef` and `EvidenceSet` — and
 * NO confidence value.** 📁 **The only `confidence` on any endpoint is
 * `workspace_tenancy`'s `confidence_floor`, a threshold the CUSTOMER sets.**
 *
 * ✅ **So `confidence` is optional and its absence is STATED**, which is the
 * row's own instruction: *"if `ai_platform` publishes no confidence, this
 * component renders its ABSENCE, it does not compute one."*
 *
 * 🔴 **Specifically it is never `0 of 5`.** ⛔ **`0 of 5` reads as *certainly
 * wrong* where the truth is *not known*** — the two are opposite claims, and
 * the pips would draw the first one. **[C-267](../../../docs/LANE_COORDINATION.md)
 * is open on exactly this figure and this component is what refuses it.**
 *
 * ⚠️ ***Confidence not stated* is the shortest true sentence, and it is not
 * [`StatedAbsence`](../feedback/stated-absence.tsx).** **That component's
 * sentence ends *"reload to try again"*, which would be a false instruction
 * here**: nothing failed to load, and reloading produces the same absence
 * forever. 📁 **[P-A](../../../docs/DOMAIN_DISCOVERY_REGISTER.md) is *a failed
 * read must never render as an empty result* — this is the mirror case, and
 * borrowing the failed-read wording would misreport a working system.**
 *
 * ## 🔴 A source the reader may not open is not listed
 *
 * ⛔ **The row's Security Invariant, and it is the same disclosure rule as
 * [C-245](../../../docs/LANE_COORDINATION.md).** ⚡ **`readable: false` removes
 * a source from the list AND from the count** — listing one the reader cannot
 * open discloses that it exists, which is the leak; ⚠️ **and counting one that
 * is not listed would make the count a false claim about the evidence, which
 * is the same defect the responsive rule below names.**
 *
 * ## ⚠️ Excluded is not the same as unreadable, and both are kept
 *
 * 📁 **AI Research's *"3 excluded"*** — *"excluded citations are shown as
 * withheld rather than removed, so the argument stays auditable."* ✅ **An
 * excluded source stays visible with its reason**; an unreadable one was never
 * this reader's to see. **Two different facts, never collapsed into one.**
 */

export interface AttributionSource {
  /** Stable across renders. Whatever the calling surface already keys by. */
  id: string;
  /** What the source is, in the customer's words. */
  title: string;
  /** Where it came from and when — 📁 the design's `{{ e.meta }}`. */
  meta?: string;
  /**
   * ⚡ **Why the answer did NOT use it.** 📁 AI Research's *"3 excluded"* —
   * **present means excluded, and the string is the reason.** ⛔ **A reason is
   * mandatory when excluding**: *"3 excluded"* with no reason is an
   * unfalsifiable claim, and the type refuses it by carrying no boolean.
   */
  excluded?: string;
  /**
   * 🔴 **Whether THIS reader may open it.** ⛔ **`false` means the source is
   * not listed and not counted** — see above. ✅ **Required rather than
   * defaulted**: a caller that has not thought about who may read a citation
   * has not thought about the citation.
   */
  readable: boolean;
  /** Opens the source at the cited moment. Absent where nothing opens yet. */
  onOpen?: () => void;
}

export interface AttributionStripProps {
  /**
   * **1–5, and undefined where the platform publishes none.** ⛔ **Never
   * computed here and never a percentage** — 📁 Design System v2 §03:
   * *"Confidence is stated as pips plus a plain-language basis. Never a
   * synthetic percentage."*
   */
  confidence?: number;
  /** Everything the answer stands on, excluded entries included. */
  sources: AttributionSource[];
  /** When the answer was produced, ISO. */
  generatedAt?: string;
  /**
   * ⚡ **What keeps it current** — 📁 Account 360's *"updates on new
   * evidence"*. **Omitted where nothing does**, because the phrase is a
   * promise about behaviour rather than decoration.
   */
  note?: string;
  /**
   * 📁 **The reasoning chain, *"collapsed by default"*.** **Undefined renders
   * no disclosure at all** — ⛔ **a *Show reasoning* button that opens an empty
   * panel is the affordance-with-nothing-behind-it this repository has
   * refused since the narration's fact count.**
   */
  reasoning?: ReactNode;
  className?: string;
}

export function AttributionStrip({
  confidence,
  sources,
  generatedAt,
  note,
  reasoning,
  className,
}: AttributionStripProps) {
  const [showReasoning, setShowReasoning] = useState(false);
  const [showSources, setShowSources] = useState(false);
  const reasoningId = useId();
  const sourcesId = useId();

  // 🔴 The Security Invariant, applied once and before anything counts.
  const listed = sources.filter((source) => source.readable);
  const excluded = listed.filter((source) => source.excluded !== undefined);

  return (
    <div className={cn('flex flex-col gap-2', className)}>
      {/* ⚡ **`flex-wrap` and no `truncate`** — 📁 the row's responsive rule:
        *"the attribution strip wraps rather than truncating; a truncated
          source count is a false claim about evidence."* */}
      <div className="flex flex-wrap items-center gap-x-3 gap-y-1.5 text-xs text-content-muted">
        {reasoning === undefined ? null : (
          <Disclosure
            id={reasoningId}
            open={showReasoning}
            onToggle={() => setShowReasoning((was) => !was)}
            label="Show reasoning"
          />
        )}

        {listed.length === 0 ? null : (
          <Disclosure
            id={sourcesId}
            open={showSources}
            onToggle={() => setShowSources((was) => !was)}
            label={`${listed.length} ${listed.length === 1 ? 'source' : 'sources'}`}
          />
        )}

        {excluded.length === 0 ? null : (
          // 📁 AI Research states the exclusions on the strip, not only inside
          // the list — a reader deciding whether to open it needs to know
          // there is something withheld before they do.
          <span className="tabular-nums">{excluded.length} excluded</span>
        )}

        {confidence === undefined ? (
          <span>Confidence not stated</span>
        ) : (
          <Confidence level={confidence} />
        )}

        {generatedAt === undefined ? null : (
          <span>
            Generated {formatDay(generatedAt)}
            {note === undefined ? null : ` · ${note}`}
          </span>
        )}
      </div>

      {showReasoning ? (
        <div id={reasoningId} className="text-sm leading-6 text-content">
          {reasoning}
        </div>
      ) : null}

      {showSources ? <SourceList id={sourcesId} sources={listed} /> : null}
    </div>
  );
}

/**
 * ♿ **A disclosure, not a link.** 📁 The row: *"Show reasoning is a disclosure
 * button with `aria-expanded`"* — and the source count is the same control
 * doing the same thing, so it is the same component rather than two.
 */
function Disclosure({
  id,
  open,
  onToggle,
  label,
}: {
  id: string;
  open: boolean;
  onToggle: () => void;
  label: string;
}) {
  return (
    <button
      type="button"
      onClick={onToggle}
      aria-expanded={open}
      aria-controls={id}
      className={cn(
        'rounded font-medium tabular-nums text-ai',
        'underline decoration-dotted underline-offset-4',
        'transition-all hover:decoration-solid',
      )}
    >
      {label}
    </button>
  );
}

/**
 * 📁 *"Numbered sources with the cited excerpt"* — Design System v2 §04.
 *
 * ⚡ **The numbering is the citation.** A claim carrying `2` in the answer and
 * a list whose second entry is something else has broken the only link that
 * makes the answer checkable, so the index is positional and never sorted here.
 *
 * ⚠️ **The list opens in place rather than in a docked panel.** 📁 The design
 * docks it beside the answer — **that surface is the utility panel, which is
 * [TASK-1433](../../../docs/BACKLOG.md)'s and does not exist yet.** ⛔ **A
 * primitive must not invent it**, and the individual source still opens at the
 * cited moment through `onOpen`, which is where the citation actually ends.
 */
function SourceList({ id, sources }: { id: string; sources: AttributionSource[] }) {
  return (
    <ol id={id} className="flex flex-col gap-2 border-t border-border pt-2">
      {sources.map((source, index) => (
        <li key={source.id} className="flex items-baseline gap-2.5 text-xs">
          <span aria-hidden className="tabular-nums text-content-subtle">
            {index + 1}
          </span>
          <span className="flex flex-col gap-0.5">
            <span className="flex flex-wrap items-baseline gap-x-2 gap-y-0.5">
              {source.onOpen === undefined ? (
                <span className="text-content">{source.title}</span>
              ) : (
                <button
                  type="button"
                  onClick={source.onOpen}
                  className={cn(
                    'rounded text-left text-content',
                    'underline decoration-dotted underline-offset-4',
                    'transition-all hover:decoration-solid',
                  )}
                >
                  {source.title}
                </button>
              )}
              {source.meta === undefined ? null : (
                <span className="text-content-subtle">{source.meta}</span>
              )}
            </span>
            {source.excluded === undefined ? null : (
              // 📁 *"shown as withheld rather than removed, so the argument
              // stays auditable"* — ⛔ **the reason is on the row, because
              // *excluded* without one is not auditable, it is just absent.**
              <span className="text-content-muted">Excluded — {source.excluded}</span>
            )}
          </span>
        </li>
      ))}
    </ol>
  );
}
