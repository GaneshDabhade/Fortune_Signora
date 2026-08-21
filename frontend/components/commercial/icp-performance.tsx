'use client';

import { Badge, Card, CardHeader, CardTitle, SkeletonText } from '@/components/ui';
import { StatedAbsence } from '@/components/feedback/stated-absence';
import type { CriterionLift, IcpMeasurement, ProductCatalog } from '@/lib/api/types';
import { useIcpPerformance } from '@/lib/query/hooks/commercial';
import { cn } from '@/lib/design/cn';

/**
 * 🔴 **The sentence the ICP Builder design opens with, made true** — 📁 `Design
 * Documents/Fortune Signora ICP Builder.html`:
 *
 * > ***"Every criterion is scored against closed-won evidence, not opinion."***
 *
 * ## ⚡ Why this exists, and it is the same orphan twice
 *
 * ⛔ **`GET /workspaces/{id}/icp-performance` shipped with no consumer.** The
 * endpoint, `MeasureIcp`, `CriterionLift` and their tests are all on `main`,
 * and **no screen read them** — so a customer could declare an ideal customer
 * and was never told whether it predicted anything. ⚠️ **[`IcpEditor`](./icp.tsx)'s
 * docstring still said *"it describes; it never matches… this screen has no
 * verdict to show and no field that could carry one"***, which stopped being
 * true when the measurement shipped.
 *
 * ⚡ **The backend was built against this very design** — its schema quotes the
 * screen back: *"the threshold the ICP Builder itself states: '2.2× lift on
 * only 22 deals; treat as directional, not settled.'"*
 *
 * ## ⛔ What the design draws and this deliberately does NOT
 *
 * | Design | |
 * |---|---|
 * | `Must` · `Should` · `Bonus` · `Exclude` tiers | ⛔ **No tier on the contract.** `ProductIcp` has no field that could carry one |
 * | Seven criterion groups, 29 criteria | ⛔ **Three kinds exist** — `industry`, `country`, `employees` |
 * | Scoring weights, `Refit on last 8 quarters` | ⛔ **No producer** |
 * | Preview, TAM funnel, templates, AI suggestions | ⛔ **No producer** |
 *
 * 📁 [§20c](../../../CLAUDE.md) — **a screen without a shipped module behind it
 * ships a designed absence, never a control that does nothing.**
 */
export function IcpPerformance({
  catalog,
  workspaceId,
}: {
  catalog: ProductCatalog;
  workspaceId: string | null;
}) {
  const measured = useIcpPerformance(workspaceId);

  return (
    <Card className="overflow-hidden">
      <CardHeader className="flex flex-wrap items-center gap-x-3 gap-y-1 p-4">
        <CardTitle className="text-sm">Does this description predict a win?</CardTitle>
        {/* 📁 The design's own subtitle, and it is the claim this panel makes. */}
        <p className="text-xs text-content-muted">
          Every criterion scored against closed-won evidence, not opinion
        </p>
      </CardHeader>

      {measured.isPending ? (
        <div className="p-4">
          <SkeletonText lines={3} />
        </div>
      ) : measured.isError ? (
        // ⛔ **A failed read is never an empty result** — 📁 [P-A](../../../docs/DOMAIN_DISCOVERY_REGISTER.md).
        <div className="p-4">
          <StatedAbsence subject="whether these criteria predict a win" />
        </div>
      ) : (measured.data ?? []).length === 0 ? (
        // ⚡ **The endpoint's own words**: *"Empty when no ICP has been declared
        // — not an error. A workspace that has not described who buys from it
        // is in a state to wait in, and the surface says so rather than showing
        // zeroes."*
        <p className="p-4 text-xs leading-5 text-content-muted">
          Nothing to measure yet. Describe who buys a product above, and once deals have been
          won or lost this says which parts of that description actually predicted the wins.
        </p>
      ) : (
        <ul className="flex flex-col">
          {(measured.data ?? []).map((measurement) => (
            <ProductMeasurement
              key={measurement.product_id}
              measurement={measurement}
              catalog={catalog}
            />
          ))}
        </ul>
      )}
    </Card>
  );
}

function ProductMeasurement({
  measurement,
  catalog,
}: {
  measurement: IcpMeasurement;
  catalog: ProductCatalog;
}) {
  /* ⛔ **The measurement carries a `product_id` and never a name** — 📁 its own
     contract: *"This module never learned what a product is called."* ⚡ **And
     a product removed from the catalog still leaves the row readable**, which
     is the rule `IcpSegmentSummary` states for the same reason. */
  const product = catalog.products.find((candidate) => candidate.id === measurement.product_id);

  return (
    <li className="border-b border-border-soft last:border-b-0">
      <div className="flex flex-wrap items-baseline gap-x-3 gap-y-1 px-4 pb-2 pt-3">
        <p className="text-xs font-semibold text-content">
          {product?.name ?? 'A product no longer in the catalog'}
        </p>
        {/* 🔴 **The honest denominator, and it comes first.** 📁 *"if this is
            small, nothing below it is settled."* */}
        <p className="text-2xs text-content-subtle">
          {measurement.decided === 1
            ? 'measured on 1 decided account'
            : `measured on ${measurement.decided} decided accounts`}
        </p>
      </div>

      <ul className="flex flex-col">
        {measurement.criteria.map((criterion) => (
          <Criterion key={criterion.criterion} lift={criterion} />
        ))}
      </ul>
    </li>
  );
}

/** 📁 The design's own words for each criterion kind. */
const KIND_LABEL: Record<string, string> = {
  industry: 'Industry',
  country: 'Country',
  employees: 'Employees',
};

function Criterion({ lift }: { lift: CriterionLift }) {
  return (
    /* 📁 **The design's criterion row** — `minmax(0,1.15fr) … minmax(0,1fr)`,
       label on the left and the lift figure with its evidence on the right.
       ⛔ **The `Must`/`Should`/`Bonus`/`Exclude` badge is NOT rendered**: the
       contract has no tier, and a badge that always read the same would be
       decoration ([§2](../../../CLAUDE.md)). */
    <li className="grid grid-cols-[minmax(0,1fr)_auto] items-center gap-3 px-4 py-2">
      <span className="truncate text-xs font-semibold text-content">
        {KIND_LABEL[lift.criterion] ?? lift.criterion}
      </span>

      <span className="flex flex-wrap items-center justify-end gap-x-2 gap-y-1">
        <LiftFigure lift={lift} />
        {/* ⚡ **The sample size travels with the multiple, always** — 📁 *"read
            it before the multiple."* */}
        <span className="text-2xs tabular-nums text-content-subtle">
          {lift.satisfied_won} of {lift.satisfied} won
        </span>
        {/* 📁 *"treat as directional, not settled"* — ⚠️ **only where the
            endpoint says so**, never computed here: the threshold is the
            measurement's and a second copy would eventually disagree. */}
        {lift.is_directional && lift.lift !== null ? (
          <Badge tone="warning">Directional</Badge>
        ) : null}
      </span>
    </li>
  );
}

/**
 * ⛔ **`null` is rendered as *not measured*, never as `1.0`.** 📁 The contract
 * says so in as many words, and the two mean opposite things: **1.0 is *"this
 * tells you nothing"*, null is *"nobody could check."***
 *
 * ⚡ **Below 1.0 is the useful case** — 📁 *"below 1.0 it is selecting against
 * you… the most useful thing this can say and the one nobody expects"* — so it
 * is toned as a risk rather than hidden.
 */
function LiftFigure({ lift }: { lift: CriterionLift }) {
  if (lift.lift === null) {
    return (
      <span className="text-2xs text-content-subtle">
        Not measured
        {lift.unmeasured > 0 ? ` · ${lift.unmeasured} accounts undescribed` : ''}
      </span>
    );
  }

  const predicts = lift.lift >= 1.5;
  const against = lift.lift < 1;

  return (
    <span
      className={cn(
        'text-xs font-semibold tabular-nums',
        against ? 'text-danger' : predicts ? 'text-success' : 'text-warning',
      )}
    >
      {lift.lift.toFixed(1)}× {against ? 'against' : 'lift'}
    </span>
  );
}
