import type { CommercialStage } from '@/lib/api/types';
import { cn } from '@/lib/design/cn';

/**
 * **What a commercial cell shows when no source has said anything.**
 *
 * 🔴 **The single most dangerous cell on the Companies screen**, because every
 * wrong answer here is plausible. ⛔ **Not `0`, not `$0`, not *"None"*, not an
 * empty cell** — 📁 [ADR-0409](../../../docs/architecture/adr/0409-commercial-account-facts.md)
 * §5: *"absence is never inferred, defaulted or zero-filled."*
 *
 * ⚡ **Why a dash is honest here and would not have been last week.** 📁
 * [`table.ts`](../../lib/accounts/table.ts)'s law is that *"a column of `—` is
 * worse than an absent column: it says Signora looked and found nothing, when
 * the truth is that nothing was ever asked."* ✅ **The read path now asks** —
 * ADR-0409 is ratified, the attributes are canonical, and the graph reads
 * them — **so the dash means exactly what it looks like it means.**
 *
 * ♿ **The screen reader gets a sentence rather than a punctuation mark.** A
 * dash announced as *"em dash"* forty times is noise; **the fact is that
 * nothing has been reported**, and that is what is said.
 */
export function NothingSaid() {
  return (
    <span className="text-content-subtle">
      <span aria-hidden="true">—</span>
      <span className="sr-only">Not reported</span>
    </span>
  );
}

/**
 * **Where a relationship stands — in the customer's own word.**
 *
 * 📁 [ADR-0409](../../../docs/architecture/adr/0409-commercial-account-facts.md)
 * §5: *"the tenant's stage label is provenance and is never reasoned over.
 * Reasoning reads the canonical position. **A screen may show the customer's
 * word.**"* ⚡ **So the label is what renders, always** — and this component
 * never branches on it.
 *
 * ## ⚠️ Unmapped is a state the product shows
 *
 * 📁 **The CRM Integrations design states the case:** *"Salesforce added 'Legal
 * review' and 'Procurement' to StageName last week. **214 opportunities now sit
 * in stages Signora treats as unmapped**, and their velocity metrics are
 * excluded until mapped."*
 *
 * ⛔ **So a stage with no canonical position is NOT hidden and NOT guessed at.**
 * ⚡ **It renders the customer's word with a stated caveat**, because the
 * alternative — coercing *"Legal review"* into *Negotiating* — is precisely the
 * invention ADR-0409 was written to prevent.
 */
export function StageBadge({ stage }: { stage: CommercialStage }) {
  const mapped = stage.position !== null;
  return (
    <span
      className={cn(
        'inline-flex items-center rounded-md px-1.5 py-0.5 text-xs font-semibold',
        mapped
          ? 'bg-surface-sunken text-content-muted'
          : // ⚠️ **A different surface, not a warning colour.** Unmapped is a
            // configuration state the customer can fix, not a risk — and
            // painting it red would make every new CRM stage look like a
            // problem with the account rather than with the mapping.
            'border border-dashed border-border text-content-subtle',
      )}
      title={
        mapped
          ? undefined
          : 'Signora has not mapped this stage yet, so it is excluded from reasoning.'
      }
    >
      {stage.label}
      {mapped ? null : <span className="sr-only"> — not mapped</span>}
    </span>
  );
}
