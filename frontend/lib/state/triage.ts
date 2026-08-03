/**
 * What the attention list is asking a seller to look at, beyond its order.
 *
 * **The list is ordered by score, and that is correct.** But an account can
 * rank high on evidence that has aged, or on a company two providers describe
 * differently — and a seller scanning top-down reads the score first. The row
 * already carries both facts; nothing says how many rows carry them.
 *
 * > **This partitions; it never re-ranks.** The attention ranking already
 * > decides what matters most, and a second ordering here would be this surface
 * > inventing an urgency of its own — the refusal Sales Engagement makes in the
 * > same words (`50-sales-engagement.md` §22).
 *
 * **Every question below is a filter over a fact the server already computed.**
 * `evidence_state` is derived by the Opportunity Engine, `contested` by the
 * Knowledge Graph's identity resolution, `trend` by the Buying Score Engine.
 * Nothing here decides anything commercial; it counts and groups.
 *
 * ### What was deliberately not built
 *
 * **No *neglected* or *sitting too long* question.** It would need a threshold,
 * and a threshold is a judgement Signora has no basis for: it *cannot see a
 * call, an email or a meeting* (`49-lead-ownership.md`, LO-06), so an account
 * held for three weeks may have been worked every day. `HeldSince` renders the
 * duration and **grades nothing**, and this file keeps that discipline rather
 * than quietly reversing it one layer up.
 *
 * **No urgency, no score, no ordering of the questions by importance.** They are
 * listed in a fixed reading order, and the counts are the only quantity.
 */

import type { AccountAttention, EvidenceState, Trend } from '@/lib/api/types';

/** A question the accounts on this list are raising. */
export type Raised = 'verify' | 'ageing' | 'rising';

const RAISED: readonly Raised[] = ['verify', 'ageing', 'rising'];

/**
 * What a customer calls each one, and what it means underneath.
 *
 * **The customer's vocabulary, at the frontend edge** (ADR-0034). *Contested*
 * is the Knowledge Graph's word for an identity two providers disagree about;
 * a seller would say the record needs checking.
 */
export const RAISED_WORDS: Record<Raised, string> = {
  verify: 'Worth verifying',
  ageing: 'Ranked on ageing evidence',
  rising: 'Rising',
};

/**
 * The one-line explanation under each question.
 *
 * **Stated once, here.** A component repeating it would be a second copy of a
 * sentence that has to stay true to what the filter actually does.
 */
export const RAISED_MEANING: Record<Raised, string> = {
  verify: 'Providers describe this company differently.',
  ageing: 'The evidence behind the score has aged.',
  rising: 'The score last moved up.',
};

/** Whether one account raises one question. **A filter, never a judgement.** */
export function raises(account: AccountAttention, question: Raised): boolean {
  switch (question) {
    case 'verify':
      return account.contested;
    case 'ageing':
      // `cooling` and `stale` are both *not current*. The distinction matters
      // on a row, where the reader is deciding about one account; it does not
      // matter to the question *how many of these are built on old news*.
      return AGEING.includes(account.evidence);
    case 'rising':
      return RISING.includes(account.trend as Trend);
  }
}

const AGEING: readonly EvidenceState[] = ['cooling', 'stale'];
const RISING: readonly Trend[] = ['rising'];

/** One question, and the accounts raising it. */
export interface TriageGroup {
  question: Raised;
  /** **In the order they arrived.** See the module note: this never re-ranks. */
  accounts: AccountAttention[];
}

/**
 * Which questions this list actually raises.
 *
 * **A question nobody raises is absent, never present at zero.** A strip that
 * always shows the same three labels looks identical for every workspace, which
 * is the defect R1-06 named on the workflow line and D6 named on a filter: *a
 * control that always shows the same thing teaches people to ignore controls.*
 * A seller who sees *Worth verifying* therefore knows, before reading it, that
 * something is worth verifying.
 *
 * **An account may raise more than one**, and appears under each. Two questions
 * about one account are two things to do, and collapsing them to the "worst"
 * would be this surface ranking again.
 */
export function triage(accounts: readonly AccountAttention[]): TriageGroup[] {
  return RAISED.map((question) => ({
    question,
    accounts: accounts.filter((account) => raises(account, question)),
  })).filter((group) => group.accounts.length > 0);
}

/**
 * The question a URL is asking for, or `null` for the whole list.
 *
 * **An unknown value reads as no filter rather than failing** — the same rule
 * `scopeFrom` follows, for the same reason: a hand-edited or stale link should
 * show a seller their accounts, not an error.
 */
export function raisedFrom(value: string | null | undefined): Raised | null {
  return RAISED.includes(value as Raised) ? (value as Raised) : null;
}

/**
 * A link that keeps the current view.
 *
 * **Composed onto whatever query is already there**, because the owner scope
 * travels in the same URL and a seller filtering by question must not silently
 * lose the fact that they were looking at their own accounts.
 */
export function withRaised(path: string, raised: Raised | null): string {
  if (raised === null) {
    return path;
  }
  return path.includes('?') ? `${path}&raises=${raised}` : `${path}?raises=${raised}`;
}
