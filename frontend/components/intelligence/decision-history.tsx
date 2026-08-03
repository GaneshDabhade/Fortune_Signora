'use client';

import { formatDay } from '@/components/intelligence/dates';
import { nameOf } from '@/components/team/people';
import type { AccountOpportunity, WorkflowState } from '@/lib/api/types';

/** One instance, so a default parameter is not a new object every render. */
const EMPTY: ReadonlyMap<string, string> = new Map();

/**
 * What has been decided about this account, and why.
 *
 * **The one record in Signora that nothing can reproduce.** Every score,
 * signal, narration and finding can be recomputed from evidence; a decision
 * cannot. It is append-only, never rewritten, and until now it was **on the
 * wire and rendered nowhere** — `history` has travelled on every brief since
 * M12.1 and no screen has ever read it.
 *
 * ### The question it answers
 *
 * *"What happened here before me?"* A seller opening an account a colleague
 * worked last month sees the current stage and nothing else — not that it was
 * taken on and given up, not why. **The product knew and did not say.**
 *
 * It is also what a reader needs when the colleague is themselves: a rep who
 * dismissed an account in March and finds it back on the list in June should
 * not have to remember their own reasoning.
 *
 * ### Rendered in the order it arrived
 *
 * Oldest first, exactly as the API sends it. **The screen does not re-sort** —
 * the same rule the ledger follows, for a stronger reason here: this is an
 * audit trail, and a trail reordered by a browser is a trail that can disagree
 * with the record it claims to show.
 *
 * ### Nobody is named, and that is honest rather than a gap
 *
 * `decided_by` is an identifier. Better Auth owns user profiles in the Next.js
 * tier and the Python tier verifies tokens without learning who anybody is
 * (ADR-0026), so *"somebody here"* is the truthful form — the same wording the
 * workflow line has used since **D23**. A raw identifier would be the same
 * absence dressed as information. When [C-024](../../../docs/LANE_COORDINATION.md)
 * settles how the product resolves a name, this reads it and nothing else
 * changes.
 */
export function DecisionHistory({
  opportunity,
  viewerId = null,
  people = EMPTY,
}: {
  opportunity: AccountOpportunity;
  /** The signed-in reader, so their own decisions read as theirs. */
  viewerId?: string | null;
  /** Everybody who can be named, so the trail says who rather than *somebody*.
   *
   * **The comment above predicted this and was wrong about the mechanism**: it
   * expected [C-024](../../../docs/LANE_COORDINATION.md) to settle how a name
   * is resolved, and TM-01 settled it first by giving a membership an address.
   * Empty still reads exactly as it did before. */
  people?: ReadonlyMap<string, string>;
}) {
  // **Silent when it has nothing to say.** Every account has an opening entry,
  // so a section rendered for one row would appear on every brief and carry
  // nothing — which is what made the workflow line furniture (R1-06).
  const decisions = opportunity.history.filter((state) => state.decided_by !== null);
  if (decisions.length === 0) return null;

  return (
    <section className="flex flex-col gap-3">
      <h2 className="text-sm font-semibold text-content">What has been decided</h2>
      <ol className="flex flex-col gap-3">
        {opportunity.history.map((state, index) => (
          <li key={`${index}:${state.occurred_at}`}>
            <Decision
              state={state}
              // **The entry before it, because a hand-over is only visible as
              // a difference.** One row says *engaged, owned by Ravi*; whether
              // that was Ravi taking it on or Ana giving it to him is the pair.
              previous={index === 0 ? null : (opportunity.history[index - 1] ?? null)}
              viewerId={viewerId}
              people={people}
            />
          </li>
        ))}
      </ol>
    </section>
  );
}

/**
 * One entry: what changed, who changed it, why, and when.
 *
 * **The reason leads.** *"Wrong segment — they're SMB"* is the whole value of
 * the record; the stage is how the product filed it. A trail that put the
 * vocabulary first would read as a status log rather than as a colleague's
 * note.
 */
function Decision({
  state,
  previous,
  viewerId,
  people,
}: {
  state: WorkflowState;
  previous: WorkflowState | null;
  viewerId: string | null;
  people: ReadonlyMap<string, string>;
}) {
  return (
    <div className="flex flex-col gap-0.5 border-l-2 border-border pl-3">
      <p className="text-[0.9375rem] leading-6 text-content">{state.reason}</p>
      <p className="text-xs text-content-subtle">
        {actor(state, viewerId, people)} · {movement(state, previous, viewerId, people)} ·{' '}
        {formatDay(state.occurred_at)}
      </p>
    </div>
  );
}

/**
 * What this entry actually was.
 *
 * **The stage alone cannot say.** An entry recorded at `engaged` is *"took it
 * on"* when the owner arrived with it and *"handed it to Ravi"* when the stage
 * never moved — the same row, two different acts, and reading only the stage
 * would have told a seller that Ana took on an account she had just given
 * away.
 *
 * ### Why ownership speaks only where it is the news
 *
 * A close that also moved the owner reads as the close, because that is what
 * happened: *"closed it won"* is the fact, and the assignment beside it is
 * bookkeeping. **Ownership leads only when it is the change** — no stage
 * movement at all, or the move into being worked, which is the one transition
 * that exists to put an account into somebody's hands.
 */
function movement(
  state: WorkflowState,
  previous: WorkflowState | null,
  viewerId: string | null,
  people: ReadonlyMap<string, string>,
): string {
  if (previous === null || state.owner_id === previous.owner_id) return STAGE_PAST[state.stage];
  if (state.stage !== previous.stage && state.stage !== 'engaged') return STAGE_PAST[state.stage];

  // The actor gave it to themselves — taking it on, or taking it back off
  // whoever had it.
  if (state.owner_id !== null && state.owner_id === state.decided_by) {
    return previous.owner_id === null
      ? STAGE_PAST[state.stage]
      : `took it over from ${nameOf(previous.owner_id, people, viewerId)}`;
  }
  return `handed it to ${nameOf(state.owner_id, people, viewerId)}`;
}

/**
 * Who decided, in the only terms the product can honestly use.
 *
 * `decided_by` is null on exactly one entry — the opening one, which is *"the
 * one state Signora may author"*. Saying **Signora** there rather than
 * *"somebody"* is the distinction the whole product rests on: intelligence
 * suggests, humans commit, and the record already knows which this was.
 *
 * **It names people now**, which the doc comment above expected to arrive with
 * C-024 and which TM-01 delivered instead. *Somebody here* survives as the
 * fallback for a membership that never had an address, and for somebody who
 * has since left — a name the roster no longer holds is a fact about today,
 * and the record is about then.
 */
function actor(
  state: WorkflowState,
  viewerId: string | null,
  people: ReadonlyMap<string, string>,
): string {
  if (state.decided_by === null) return 'Signora';
  if (state.decided_by === viewerId) return 'You';
  return people.get(state.decided_by) ?? 'Somebody here';
}

/**
 * The stage, in the past tense.
 *
 * **A translation, never a paraphrase** — each maps to exactly one recorded
 * stage, so what a reader is told can be checked against what was stored.
 */
const STAGE_PAST: Record<WorkflowState['stage'], string> = {
  tracking: 'put it back on the list',
  engaged: 'took it on',
  closed_won: 'closed it won',
  closed_lost: 'closed it lost',
  dismissed: 'dismissed it',
};
