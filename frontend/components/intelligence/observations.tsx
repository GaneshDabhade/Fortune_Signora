import { ArrowDownRight, ArrowUpRight, Minus } from 'lucide-react';

import { howLongAgo } from '@/components/intelligence/dates';
import { Card, CardBody, CardHeader, CardTitle, EmptyState, SkeletonText } from '@/components/ui';
import type { AccountObservation } from '@/lib/api/types';

/**
 * How this company has changed, and who says so.
 *
 * **The layer beneath a claim the brief makes in one line.** The header says
 * *"grew headcount 15% over 32 days"* and nothing behind it; a seller who
 * wants to repeat that on a call has to know whether it is one provider's
 * guess or three providers agreeing.
 *
 * ### The provider is named, and that is the point of the section
 *
 * Everywhere else on this page Signora speaks in its own voice — a score, a
 * signal, a conclusion. **This is the one section that shows the raw material
 * and attributes it.** Two providers can disagree about headcount, and a
 * reader deciding whether to believe a change needs to know whose change it
 * is. Collapsing them into *"headcount increased"* would be the product
 * laundering a single unverified reading into a fact.
 *
 * ### A first sighting is not a change from nothing
 *
 * `previous_value` is `null` the first time a provider reports an attribute.
 * That is **not** a transition, and rendering `— → 400` would invent a history
 * the pipeline never saw: it would read as *"they grew to 400"* when what
 * happened is *"we learned they are 400"*. Those are different sentences and
 * only one of them is true.
 *
 * ### Magnitude is rendered only where it means something
 *
 * A change of country has no magnitude and the API returns `null`. Printing
 * `1` there would give a reader a number they could sort by, and sorting by it
 * would rank a country change above a 15% headcount rise.
 *
 * ### Vocabulary lives here, at the edge (ADR-0034)
 *
 * `employee_count` is the pipeline's word. **A customer never sees it.** The
 * labels below are this section's only job beyond layout, and they are
 * deliberately not exhaustive over the enum — see `attributeLabel`.
 */

/**
 * What each recorded attribute is called on a screen.
 *
 * **Not exhaustive over `ClaimAttribute`, and deliberately so.** A `Record<>`
 * covering every member would have to be edited by whoever adds an attribute
 * to the pipeline — a module they may not own — and the compiler would send
 * them here to invent customer copy for it. The fallback below is honest for
 * an unmapped key, so a new attribute renders readably on the day it ships and
 * gets its proper wording when somebody who knows the product writes one.
 */
const ATTRIBUTE_LABELS: Record<string, string> = {
  employee_count: 'Headcount',
  revenue_band: 'Revenue',
  industry: 'Industry',
  founded_year: 'Founded',
  country: 'Country',
  legal_name: 'Legal name',
  technology_detected: 'Technology adopted',
  technology_removed: 'Technology retired',
  funding_round: 'Funding',
  acquisition: 'Acquisition',
  headcount_change: 'Headcount change',
  open_roles: 'Open roles',
  role_change: 'Role change',
  intent_topic_surge: 'Research activity',
};

/**
 * `employee_count` → `Employee count` when nothing above matches.
 *
 * **Readable rather than right.** It is not the words a product writer would
 * choose, and it never claims to be — but it is a great deal better than the
 * raw key, and it fails in the direction that costs a customer nothing.
 */
export function attributeLabel(attribute: string): string {
  const known = ATTRIBUTE_LABELS[attribute];
  if (known !== undefined) return known;
  const spaced = attribute.replace(/_/g, ' ');
  return spaced.charAt(0).toUpperCase() + spaced.slice(1);
}

function DirectionMark({ direction }: { direction: string }) {
  if (direction === 'increased') {
    return <ArrowUpRight aria-hidden className="size-4 text-success" />;
  }
  if (direction === 'decreased') {
    return <ArrowDownRight aria-hidden className="size-4 text-warning" />;
  }
  return <Minus aria-hidden className="size-4 text-content-subtle" />;
}

/**
 * How a value is written on this screen.
 *
 * The API types `previous_value` and `current_value` as `unknown` because the
 * pipeline stores whatever the provider reported — a number, a string, a year.
 * **Rendering it means narrowing it, and narrowing it here is honest**: an
 * object would be a shape this section was never designed for, and printing
 * `[object Object]` at a customer is worse than saying nothing.
 */
function readable(value: unknown): string | null {
  if (value === null || value === undefined) return null;
  if (typeof value === 'string') return value;
  if (typeof value === 'number') return value.toLocaleString();
  if (typeof value === 'boolean') return value ? 'yes' : 'no';
  return null;
}

function ObservationRow({ observation }: { observation: AccountObservation }) {
  const previous = readable(observation.previous_value);
  const current = readable(observation.current_value);
  const percent =
    observation.magnitude === null ? null : `${Math.round(observation.magnitude * 100)}%`;

  return (
    <li className="flex items-start gap-3 border-b border-border py-3 last:border-0">
      <DirectionMark direction={observation.direction} />
      <div className="min-w-0 flex-1">
        <p className="text-sm text-content">
          <span className="font-medium">{attributeLabel(observation.attribute)}</span>{' '}
          {/* A first sighting has no transition to show. */}
          {previous === null ? (
            <span className="text-content-muted">recorded as {current ?? 'a new value'}</span>
          ) : (
            <span className="text-content-muted">
              {previous} → {current ?? 'a new value'}
            </span>
          )}
          {percent !== null && <span className="text-content-subtle"> ({percent})</span>}
        </p>
        <p className="mt-0.5 text-xs text-content-subtle">
          {/* **Observed, not checked.** `observed_at` is when the provider says
              the value became true, which is the only per-account freshness
              fact the pipeline holds — the same distinction `Freshness` makes
              and for the same reason. */}
          {observation.provider} · observed {howLongAgo(observation.observed_at)}
        </p>
      </div>
    </li>
  );
}

/**
 * **A failed fetch is not an empty account**, and the section must not say it
 * is. Rendering an outage as *"nothing recorded yet"* tells a reader the
 * company is quiet when what happened is that Signora could not answer — and
 * the sentence they take away is a claim about their customer.
 *
 * `ValidationBlock` learned this on the same page: *"the section used to
 * render all three as absence, which made an outage indistinguishable from a
 * quiet account."* The wording here follows its `Unavailable` treatment rather
 * than inventing a second way of saying the same thing.
 */
function Unavailable() {
  return (
    <p className="text-sm leading-6 text-content-muted">
      Signora could not load what changed at this account. Nothing has changed about the
      account — reload to try again.
    </p>
  );
}

export function ObservationList({
  observations,
  isLoading,
  isError = false,
}: {
  observations: AccountObservation[] | undefined;
  isLoading: boolean;
  isError?: boolean;
}) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>What changed, and who says so</CardTitle>
      </CardHeader>
      <CardBody>
        {isLoading && <SkeletonText lines={3} />}
        {!isLoading && isError && <Unavailable />}
        {!isLoading && !isError && (observations === undefined || observations.length === 0) && (
          /* **An answer, not a failure.** An account no provider has reported a
             change about is an ordinary state — most accounts, most weeks — and
             an error-shaped empty state would teach a reader to distrust the
             page on the days it is right. */
          <EmptyState
            title="Nothing recorded yet"
            description="No provider has reported a change to this company. That is not the same as nothing having happened — it is what Signora has been told."
          />
        )}
        {!isLoading && !isError && observations !== undefined && observations.length > 0 && (
          <ul className="-my-3">
            {observations.map((observation) => (
              <ObservationRow key={observation.id} observation={observation} />
            ))}
          </ul>
        )}
      </CardBody>
    </Card>
  );
}
