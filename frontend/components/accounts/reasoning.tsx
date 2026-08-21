'use client';

import { Badge, Card, CardHeader, CardTitle, Confidence, SkeletonText } from '@/components/ui';
import { StatedAbsence } from '@/components/feedback/stated-absence';
import { ApiError } from '@/lib/api/client';
import { useAccountDecisionPackage } from '@/lib/query/hooks';
import { cn } from '@/lib/design/cn';

/**
 * 🔴 **Account 360's secondary column — `#reasoning`, and it is the DESIGN'S,
 * not an invention** — 📁 `Design Documents/Fortune Signora Account 360.html`:
 *
 * ```
 * grid-template-columns: minmax(0,1fr) 340px
 *   ├ #risk       Risk indicators
 *   ├ #recs       Recommendations
 *   ├ #reasoning  AI reasoning     ← this file
 *   └ #evidence   Evidence
 * ```
 *
 * ## ⚡ Why this exists now, and it is a correction to this lane's own report
 *
 * ⛔ **The record page's docstring said the Decision Package *"stays unbuilt
 * until `reasoning@1` holds a release"* and that *"nothing on this page hints
 * at it."*** 🔴 **That was STALE and it was load-bearing** — it is why the
 * 340px track was reported as having no producer at all.
 *
 * ✅ **Measured instead of recalled**: `GET
 * /workspaces/{id}/accounts/{id}/decision-package` is routed,
 * `useAccountDecisionPackage` is a shipped hook, `DecisionPackage` is on the
 * contract, and 📁 [`expanded-row.tsx`](../../app/(app)/accounts/expanded-row.tsx)
 * **has been consuming it on the Companies list since it shipped.** ⚡ **The
 * record page was the surface that did not.**
 *
 * ## ⛔ Two of the design's four cards are NOT here, and neither is faked
 *
 * | Card | |
 * |---|---|
 * | **Risk indicators** | ⛔ **No producer.** Nothing in the contract, no hook, no endpoint |
 * | **Recommendations** | ⛔ **No producer**, and a recommendation is the one thing 📁 [§2](../../../CLAUDE.md) is most explicit about not inventing |
 * | **AI reasoning** | ✅ `stated_reasoning` · `support` · `model` |
 * | **Evidence** | ⚠️ **The COUNT only** — see {@link ReasoningCard} |
 *
 * 📁 [§20c](../../../CLAUDE.md): *"screens without a shipped module behind them
 * ship a designed empty state"* — ⛔ **and a fabricated risk list is not one.**
 */
export function ReasoningCard({
  accountId,
  workspaceId,
  className,
}: {
  accountId: string;
  workspaceId: string | null;
  className?: string;
}) {
  const conclusion = useAccountDecisionPackage(workspaceId, accountId);
  // ⚡ **404 is *Signora has not concluded anything yet*, and it is an ANSWER.**
  // ⛔ Anything else is an outage — 📁 [P-A](../../../docs/DOMAIN_DISCOVERY_REGISTER.md),
  // *a failed read must never render as an empty result*.
  const notConcluded = conclusion.error instanceof ApiError && conclusion.error.status === 404;
  const failed = conclusion.error !== null && !notConcluded;
  const decision = conclusion.data;

  return (
    <Card id="reasoning" className={cn('overflow-hidden', className)}>
      <CardHeader className="flex items-center gap-2 p-4">
        {/* 📁 §14's glyph tile — *"a 6px glyph tile, a tint field, a hairline
            in the same family, and a confidence figure."* */}
        <span
          aria-hidden
          className="grid h-5 w-5 flex-none place-items-center rounded-sm bg-ai text-surface"
        >
          <svg
            width="11"
            height="11"
            viewBox="0 0 16 16"
            fill="none"
            stroke="currentColor"
            strokeWidth="1.8"
            strokeLinecap="round"
          >
            <path d="M8 2v2.5M8 11.5V14M2 8h2.5M11.5 8H14" />
          </svg>
        </span>
        <CardTitle className="text-sm">AI reasoning</CardTitle>
        {/* 🔴 **📁 The design's source count** — *"6 sources"*, right-aligned in
            the header on `margin-left:auto`, at `--ai-tint` on `--ai-ink`.
            ⚡ **`Badge tone="ai"` IS that pairing** — 📁 its own docstring:
            *"`ai` … a generated claim"* — **so this is the shared component,
            not a local span.**

            🔴 **CORRECTED.** ⛔ **An earlier pass filed `supporting_evidence` as
            a producer SURPLUS — *"no final design document draws it"*.** ⚠️
            **The design draws it here**, and the miss came from searching the
            document for a section rather than for the count in a header.
            ✅ **It is producer-backed and was rendering nowhere.**

            ⛔ **Absent while pending or unconcluded**, never `0 sources`: a
            package is refused before storage unless it cites something, so a
            zero would describe a state that cannot exist. */}
        {decision !== undefined && decision.supporting_evidence.length > 0 ? (
          <Badge tone="ai" className="ml-auto">
            {decision.supporting_evidence.length === 1
              ? '1 source'
              : `${decision.supporting_evidence.length} sources`}
          </Badge>
        ) : null}
      </CardHeader>

      <div className="p-4">
        {conclusion.isPending ? (
          <SkeletonText lines={3} />
        ) : failed ? (
          <StatedAbsence subject="how Signora reached its reading" />
        ) : notConcluded || decision === undefined ? (
          <p className="text-xs leading-5 text-content-muted">
            Signora has not reached a conclusion about this account yet. One appears here once
            there is enough evidence to argue from.
          </p>
        ) : (
          <>
            <p className="text-xs leading-5 text-content-muted">{decision.summary.text}</p>

            {decision.stated_reasoning.length > 0 ? (
              // 📁 *"position:absolute;left:6px;…;width:1.5px;background:var(--ai-line)"*
              // — ⚡ the design's reasoning chain: one rail, one dot per step.
              // ⛔ `<ol>` because the steps are ORDERED and a screen reader
              // should hear that; the rail is the same fact drawn.
              <ol className="relative mt-3 flex flex-col gap-3 pl-5">
                <span
                  aria-hidden
                  className="absolute bottom-1 left-1 top-1.5 w-px rounded bg-ai-subtle"
                />
                {decision.stated_reasoning.map((step) => (
                  <li key={step.text} className="relative">
                    <span
                      aria-hidden
                      className="absolute -left-[15px] top-1.5 h-2 w-2 rounded-full bg-ai ring-4 ring-ai-subtle"
                    />
                    <p className="text-xs leading-5 text-content">{step.text}</p>
                    {/* ⛔ **Never empty** — an uncited statement is refused
                        before the package is stored, so this is always a real
                        number rather than a hopeful one. */}
                    <p className="mt-0.5 text-2xs text-content-subtle">
                      {step.evidence.length === 1
                        ? '1 cited fact'
                        : `${step.evidence.length} cited facts`}
                    </p>
                  </li>
                ))}
              </ol>
            ) : null}

            <div className="mt-4 flex flex-wrap items-center gap-x-3 gap-y-1 border-t border-border-soft pt-3">
              {/* 📁 §14's fourth term. ⚠️ **`support.level` is the pipeline's
                  own word, not a number** — it is passed through
                  {@link supportPips} rather than parsed into prose, and the
                  SOURCE COUNT is the corroborating providers, which is a
                  measurement rather than a guess. */}
              <Confidence
                level={supportPips(decision.support.level)}
                sources={decision.support.corroborating_providers.length}
              />
              {/* ⚡ **Provenance beside the sentence, never behind a hover** —
                  📁 `AccountNarration`'s rule: *"a customer reading generated
                  language is entitled to know what generated it WHILE THEY ARE
                  READING IT."* */}
              <p className="text-2xs text-content-subtle">
                {decision.model} · prompt {decision.prompt_name} v{decision.prompt_version}
              </p>
            </div>
          </>
        )}
      </div>
    </Card>
  );
}

/**
 * ⚡ **The pipeline's support level as §14's five-point figure.**
 *
 * ⛔ **A lookup, never arithmetic on a string.** 📁 [§2](../../../CLAUDE.md) —
 * *types should make incorrect architecture impossible*; an unknown level
 * returns the middle rather than throwing, because **a confidence figure that
 * crashes the card is worse than one that is cautious.**
 *
 * ⚠️ **`level` is `string` on the contract rather than a union**, so this
 * cannot be exhaustive and does not pretend to be.
 */
function supportPips(level: string): number {
  switch (level.toLowerCase()) {
    case 'strong':
      return 5;
    case 'moderate':
      return 4;
    case 'limited':
      return 2;
    case 'weak':
      return 1;
    default:
      return 3;
  }
}
