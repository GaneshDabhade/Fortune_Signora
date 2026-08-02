'use client';

import { ArrowDownRight, ArrowUpRight } from 'lucide-react';

import { howLongAgo } from '@/components/intelligence/dates';
import type { AccountOpportunity, Stage } from '@/lib/api/types';
import { cn } from '@/lib/design/cn';

/**
 * How Signora shows a commitment — what it decided to track, and what has
 * happened since.
 *
 * **The workflow half of the account brief.** Everything else on the page
 * describes what is true *now*; this describes what was true when somebody
 * decided this account was worth watching. A score of 50 means something
 * different on an account opened at 20 than on one opened at 60, and the
 * attention list structurally cannot show that — it only knows about today.
 */

/**
 * What each stage means, said the way a seller would say it.
 *
 * **A translation, never a paraphrase**, on the same terms as the trigger
 * wording: each phrase maps to exactly one recorded stage, so what is on screen
 * can be checked against the record. `dismissed` is deliberately not softened —
 * it means *we should not have been shown this*, which is feedback about
 * Signora's judgement rather than a sales outcome, and blurring it into
 * "closed" would destroy the only signal the platform gets about its own
 * qualification quality.
 */
const STAGE_WORDING: Record<Stage, string> = {
  tracking: 'Signora is tracking this',
  engaged: 'Being worked',
  closed_won: 'Closed — won',
  closed_lost: 'Closed — lost',
  dismissed: 'Dismissed as not a real opportunity',
};

/**
 * Where this stands, and whether anyone has picked it up.
 *
 * **The `tracking` state says nobody has committed, and says it plainly.**
 * *Intelligence suggests; humans commit* is the principle the whole module is
 * shaped around, and a screen that presented Signora's suggestion as though it
 * were a decision somebody made would quietly invert it.
 */
/**
 * Why this account is being tracked at all.
 *
 * **A translation, never a paraphrase.** Each phrase maps to exactly one
 * `Qualification` the domain records, so a reader can check what they were
 * told against what was stored.
 *
 * *"Signora suggested this"* is deliberately not *"Signora decided this"*. The
 * domain's own words: an automatic qualification *"is still only a suggestion —
 * the opportunity opens at `tracking`, which commits nobody."* Wording that
 * implied a decision would overstate what the pipeline did, on the screen whose
 * whole job is to let a seller disagree with it.
 */
const OPENED_BY_WORDING: Record<AccountOpportunity['opened_by'], string> = {
  automatic: 'Signora suggested this',
  manual: 'somebody here added it',
};

export function WorkflowStage({
  opportunity,
  viewerId = null,
}: {
  opportunity: AccountOpportunity;
  /** The signed-in user. **Signora can say *you* and can say nobody else's
   * name**: Better Auth owns user profiles in the Next.js tier and the Python
   * tier verifies tokens without ever learning who a person is (ADR-0026), so
   * an owner arrives here as an identifier and nothing more. *"Held by someone
   * else"* is the honest form of that — a raw identifier on screen would be
   * the same absence dressed as information. Recorded as **D23**. */
  viewerId?: string | null;
}) {
  const unclaimed = opportunity.owner_id === null;

  return (
    <p className="text-sm text-content-muted">
      {STAGE_WORDING[opportunity.stage]}
      {/* **Who put this in front of you** — R1-06. `opened_by` has been on the
          wire since M12.1 and rendered nowhere, and its absence is exactly why
          this line read as furniture: *"Signora is tracking this · nobody has
          taken it yet"*, identical on all twelve briefs. A line constant across
          every instance carries no information at that instance.

          It is also the product's central claim made visible on the one screen
          where it matters. **Intelligence suggests; humans commit** — and until
          now the brief could not tell a reader which of the two had happened
          here. */}
      {' · '}
      <span className="text-content-subtle">{OPENED_BY_WORDING[opportunity.opened_by]}</span>
      {opportunity.stage === 'tracking' && unclaimed ? (
        <>
          {' · '}
          <span className="text-content-subtle">nobody has taken it yet</span>
        </>
      ) : null}
      {!unclaimed ? (
        <>
          {' · '}
          <span className="text-content-subtle">
            {opportunity.owner_id === viewerId ? 'you hold this' : 'held by someone else'}
          </span>
        </>
      ) : null}
    </p>
  );
}

/**
 * What changed since somebody committed.
 *
 * **The first question the brief has to answer**, and the one number no other
 * screen can give: the list knows today's score and today's overnight move,
 * neither of which says whether this account has been climbing for a month.
 *
 * ### Why the last-move delta is not repeated here
 *
 * The list shows `+8` — *what moved overnight*. This shows `+20` — *what has
 * happened since we started watching*. **Showing both on one screen asks the
 * reader to reconcile two numbers that answer different questions**, and the
 * one that belongs on a page about an account's history is the longer arc. The
 * overnight figure stays on the list, where "what moved overnight" is the
 * question being asked.
 */
export function OpportunityMomentum({
  opportunity,
}: {
  opportunity: AccountOpportunity;
}) {
  const change = opportunity.score_change_since_open;
  const since = howLongAgo(opportunity.opened_at);

  return (
    <div className="flex flex-wrap items-baseline gap-x-2 gap-y-1">
      <span className="text-sm text-content-muted">
        Opened at{' '}
        <span className="font-medium tabular-nums text-content">
          {opportunity.score_at_open}
        </span>
        , {since}
      </span>
      <SinceOpen change={change} />
    </div>
  );
}

function SinceOpen({ change }: { change: number | null }) {
  // **Null is not zero, and the distinction is the whole point.** Zero is a
  // reading that has not moved; null is the absence of one, and "no change"
  // on an account whose evidence expired would state the reverse of what
  // happened.
  if (change === null) {
    return (
      <span className="text-sm text-content-subtle">no current score to compare</span>
    );
  }
  if (change === 0) {
    return <span className="text-sm text-content-muted">unchanged since</span>;
  }

  const Icon = change > 0 ? ArrowUpRight : ArrowDownRight;
  return (
    <span
      className={cn(
        'inline-flex items-center gap-1 text-sm tabular-nums',
        change > 0 ? 'text-content' : 'text-content-muted',
      )}
    >
      <Icon aria-hidden className="h-3.5 w-3.5" />
      {change > 0 ? `+${change}` : change} since
    </span>
  );
}

/**
 * The contradiction was already there when this opened — or it was not.
 *
 * Shown only when the two disagree, which is the only case that carries
 * information. **An account that has *become* contested is a different
 * situation from one that always was**: the first is news, the second is the
 * shape of the account. A line saying *"still contested"* on every contested
 * account would be a fact nobody needed.
 */
export function ContestedSince({
  opportunity,
  contestedNow,
}: {
  opportunity: AccountOpportunity;
  contestedNow: boolean;
}) {
  if (opportunity.contested_at_open === contestedNow) return null;

  return (
    <p className="text-sm text-content-muted">
      {contestedNow
        ? 'Your sources did not disagree when this opened. They do now.'
        : 'Your sources disagreed when this opened. They no longer do.'}
    </p>
  );
}
