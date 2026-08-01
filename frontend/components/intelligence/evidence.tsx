'use client';

import { useState } from 'react';

import { formatDay } from '@/components/intelligence/dates';
import { Dialog, SkeletonText } from '@/components/ui';
import type { BusinessEventEvidence, EvidenceObservation } from '@/lib/api/types';
import { useBusinessEvent } from '@/lib/query/hooks';
import { cn } from '@/lib/design/cn';

/**
 * Where a citation ends.
 *
 * **Every other surface says something *about* a fact.** The signal interprets
 * it, the score weighs it, the narration describes it — and all three are
 * Signora's own reasoning. The readings in here are the only content the
 * platform did not write, which is why a citation has to end at them rather
 * than at another summary.
 *
 * ### Why this is a modal and not an inline expansion
 *
 * The disputed-name disclosure expands inline, deliberately, because it is one
 * sentence attached to the row it qualifies. This is not that: it is a
 * different subject entirely — a provider's record — reached from the middle of
 * a long page, and inlining it would push everything below out from under the
 * reader's finger. The native `<dialog>` gives focus trapping, background
 * inertness and Escape for free, which is the whole reason the design system
 * has one.
 *
 * ### Why the request happens on open
 *
 * A brief has a dozen ledger lines and most are never followed. Loading all
 * their evidence with the page would be a dozen requests answering a question
 * nobody asked.
 */
export function EvidenceDrawer({
  workspaceId,
  eventId,
  onClose,
}: {
  workspaceId: string | null;
  eventId: string | null;
  onClose: () => void;
}) {
  const { data, isLoading, isError } = useBusinessEvent(workspaceId, eventId);

  return (
    <Dialog
      open={eventId !== null}
      onClose={onClose}
      title={data ? data.summary : 'The evidence behind this'}
      description={
        data
          ? `Reported by ${describeProviders(data.corroborating_providers)} · ${formatDay(data.occurred_at)}`
          : undefined
      }
    >
      {isLoading ? <SkeletonText lines={3} /> : null}
      {isError ? (
        // **A citation that cannot resolve is a visible error, never a silent
        // omission** (M12.3's definition of done). Saying nothing here would
        // let a reader believe they had checked something they had not.
        <p className="text-sm leading-6 text-content-muted">
          This evidence could not be loaded. That is a fault in Signora, not a missing
          record — the citation is valid.
        </p>
      ) : null}
      {data ? <Readings observations={data.observations} /> : null}
    </Dialog>
  );
}

/**
 * The provider readings, oldest first.
 *
 * A change reads forwards: `29,000 → 34,000`. Newest-first would deliver every
 * movement backwards.
 */
function Readings({ observations }: { observations: EvidenceObservation[] }) {
  if (observations.length === 0) {
    return (
      <p className="text-sm leading-6 text-content-muted">
        Signora recorded this and kept no readings for it. That is a defect worth
        reporting — nothing should appear here without the readings that produced it.
      </p>
    );
  }

  return (
    <ol className="flex flex-col">
      {observations.map((observation, index) => (
        <li
          key={`${observation.provider}:${observation.observed_at}:${index}`}
          className="flex flex-wrap items-baseline justify-between gap-x-4 gap-y-1 border-b border-border py-2.5 last:border-b-0"
        >
          <span className="text-sm text-content">
            <Movement observation={observation} />
          </span>
          <span className="text-xs text-content-subtle">
            {observation.provider} · {formatDay(observation.observed_at)}
          </span>
        </li>
      ))}
    </ol>
  );
}

/**
 * What the provider reported, and what it was before.
 *
 * **Both halves or neither.** A current value alone cannot be argued with; the
 * previous one is what makes a change checkable. When there is no previous
 * value this is a first sighting, and saying *"first reported"* is more honest
 * than implying a movement from nothing.
 */
function Movement({ observation }: { observation: EvidenceObservation }) {
  const from = render(observation.previous_value);
  const to = render(observation.current_value);

  return (
    <>
      <span className="text-content-muted">{humanise(observation.attribute)}</span>{' '}
      {from === null ? (
        <>
          first reported as <span className="font-medium tabular-nums">{to}</span>
        </>
      ) : (
        <>
          <span className={cn('tabular-nums text-content-muted')}>{from}</span>
          <span aria-hidden className="px-1.5 text-content-subtle">
            →
          </span>
          <span className="font-medium tabular-nums">{to}</span>
        </>
      )}
    </>
  );
}

/**
 * Who reported this, said the way a person would.
 *
 * **"Reported by CoreSignal" and "reported by CoreSignal and Apollo" are
 * different claims**, and the second is the stronger one. Naming them rather
 * than counting them lets a reader who distrusts one source see when it is the
 * one talking.
 */
function describeProviders(providers: string[]): string {
  if (providers.length === 0) return 'no provider on record';
  if (providers.length === 1) return providers[0]!;
  return `${providers.slice(0, -1).join(', ')} and ${providers.at(-1)}`;
}

/** `employee_count` → `employee count`. The wire carries the pipeline's key;
 * a reader should not have to. Nothing is renamed — only unpunctuated. */
function humanise(attribute: string): string {
  return attribute.replaceAll('_', ' ');
}

/**
 * A provider value as text.
 *
 * Providers report numbers, strings and structures, and the drawer must show
 * whatever arrived. **Nothing is reformatted** — a thousands separator or a
 * rounded decimal added here would be Signora editing a provider's claim inside
 * the one view that exists to show it unedited.
 */
function render(value: unknown): string | null {
  if (value === null || value === undefined) return null;
  if (typeof value === 'object') return JSON.stringify(value);
  return String(value);
}

/**
 * Opens the evidence for one business event.
 *
 * **The affordance deliberately withheld until now.** A citation drawn as
 * clickable and going nowhere costs more trust than the missing feature does,
 * so the ledger showed its reasons flat and the narration showed a fact count.
 * This is the same content, now that it opens.
 */
export function useEvidenceDrawer() {
  const [eventId, setEventId] = useState<string | null>(null);
  return { eventId, open: setEventId, close: () => setEventId(null) };
}

export type { BusinessEventEvidence };
