/**
 * **Home's `card.pipeline`** — [TASK-1425](../../../docs/BACKLOG.md), against
 * 📁 `Fortune Signora Home.dc.html`, registry entry
 * ***"Pipeline health · `card.pipeline` · EX · Coverage, stage distribution,
 * movement"***.
 *
 * ## 🔴 The two design rules this file exists to obey
 *
 * 📁 ***"Cards degrade individually. Each card renders its own empty, error or
 * forbidden state inside its own footprint. The composition never changes shape
 * because one card has nothing."*** ⛔ **So this component never returns
 * `null`** — a card that vanishes reshapes the grid around it, which is the one
 * thing that sentence forbids.
 *
 * 📁 ***"Emptiness is legible. Every empty card names what was checked and
 * when. 'Nothing to do' is only credible if the system says what it looked
 * at."*** ⚡ **`movements_since` is echoed by the API for exactly this**, so the
 * empty state can say *since when* without inventing a boundary.
 *
 * ## ⛔ What is deliberately NOT drawn
 *
 * 🔴 **Coverage.** The design's entry names *"coverage, stage distribution,
 * movement"* and **two of the three have a source.** ⚠️ **Coverage is pipeline
 * measured against a target, and nothing in this product holds a target** — ⛔ a
 * computed figure would be a number with no author, and a zero would read as
 * *"you have no coverage"*, which is a different claim and a false one. 📁 **The
 * backend already makes this exact refusal one layer down** about the screen's
 * fifth section: *"a zero would read as 'no accounts match your ICP' — which is
 * a different claim, and a false one."*
 *
 * ⚡ **Stated on the card rather than omitted** ([§20c](../../../CLAUDE.md)): a
 * section a reader expects and cannot find reads as a bug.
 */

'use client';

import { Card, CardBody, CardHeader, CardTitle, EmptyState, SkeletonText } from '@/components/ui';
import { StatedAbsence } from '@/components/feedback/stated-absence';
import { LineChart } from 'lucide-react';
import { formatDay } from '@/components/intelligence/dates';
import { correlationOf } from '@/lib/accounts/section-state';
import { usePipelineHealth } from '@/lib/query/hooks/commercial';
import { useWorkspaceContext } from '@/lib/state/workspace-provider';

export function PipelineHealthCard() {
  const { activeWorkspace } = useWorkspaceContext();
  const health = usePipelineHealth(activeWorkspace?.id ?? null);

  return (
    <Card>
      <CardHeader>
        <CardTitle>Pipeline health</CardTitle>
      </CardHeader>
      <CardBody>
        <Body health={health} />
      </CardBody>
    </Card>
  );
}

function Body({ health }: { health: ReturnType<typeof usePipelineHealth> }) {
  // ⚠️ **Error before empty** — 📁 [P-A](../../../docs/DOMAIN_DISCOVERY_REGISTER.md):
  // *a failed read must never render as an empty result.*
  if (health.isError) {
    return (
      <StatedAbsence
        subject="how your pipeline is moving"
        reassurance="Nothing about your deals has changed"
        {...(correlationOf(health.error) === undefined
          ? {}
          : { correlationId: correlationOf(health.error)! })}
      />
    );
  }

  if (health.isLoading || health.data === undefined) {
    return <SkeletonText lines={3} />;
  }

  const { ageing, movements, movements_since } = health.data;
  const open = ageing.reduce((total, stage) => total + stage.open_count, 0);

  if (open === 0) {
    return (
      <EmptyState
        icon={LineChart}
        title="No open deals to measure"
        /* 📁 ***"Every empty card names what was checked and when."*** ⚡ The
           stage count is what was checked; `movements_since` is the when, and
           it comes from the API rather than from this component's clock. */
        description={`Signora checked every stage of your pipeline and found nothing open. Movement has been read since ${formatDay(movements_since)}.`}
      />
    );
  }

  return (
    <div className="flex flex-col gap-3">
      <p className="text-sm text-content">
        <span className="font-semibold">{open}</span> open{' '}
        {open === 1 ? 'deal' : 'deals'} across {ageing.length}{' '}
        {ageing.length === 1 ? 'stage' : 'stages'}
      </p>

      <ul className="flex flex-col gap-1.5">
        {ageing.map((stage) => (
          <li key={stage.stage} className="flex items-baseline justify-between gap-3 text-sm">
            <span className="text-content-muted">{stage.stage}</span>
            <span className="tabular-nums text-content">
              {stage.open_count}
              {/* ⚡ **The age is the point of this row, not the count.** A stage
                  holding four deals for two days and one holding four for
                  ninety are the same number and a different pipeline. */}
              {stage.open_count > 0 ? (
                <span className="ml-2 text-2xs text-content-subtle">
                  median {Math.round(stage.median_days)}d
                </span>
              ) : null}
            </span>
          </li>
        ))}
      </ul>

      <p className="text-2xs text-content-subtle">
        {movements.length === 0
          ? `Nothing has moved since ${formatDay(movements_since)}.`
          : `${movements.length} ${movements.length === 1 ? 'change' : 'changes'} since ${formatDay(movements_since)}.`}
      </p>

      {/* ⛔ **The absent third, named rather than omitted.** 📁 The design's
          entry says *coverage*; nothing holds a target to measure against, and
          a figure invented here would have no author. */}
      <p className="text-2xs text-content-subtle">
        Coverage against a target is not shown — Signora does not hold a target to
        measure your pipeline against.
      </p>
    </div>
  );
}
