'use client';

import {
  ArrowDownRight,
  ArrowRight,
  ArrowUpRight,
  Scale,
  TrendingDown,
} from 'lucide-react';

import { howLongAgo } from '@/components/intelligence/dates';
import { Badge } from '@/components/ui';
import type { EvidenceState, Posture, ScoreTrigger, Stage, Trend } from '@/lib/api/types';
import { cn } from '@/lib/design/cn';

/**
 * Display components for Signora's commercial vocabulary.
 *
 * **Deliberately not in `components/ui`.** The design system is generic —
 * buttons, tables, badges — and a system that knew what a buying score was
 * would have started learning the pipeline's language. These compose *from*
 * `components/ui` and its tokens, and add the one thing it must not have: an
 * opinion about what a score, a trigger and an evidence state mean.
 *
 * They live here because they emerged, not in anticipation: each is used on
 * the attention list today, and each is the same idea the account brief will
 * need to render. A fourth is not invented until a screen needs it.
 */

/** Human wording for the Buying Score Engine's trigger vocabulary.
 *
 * **A translation, never a paraphrase.** Each phrase maps one-to-one onto a
 * recorded enum value, so a seller reading *"new evidence arrived"* can find
 * the `signal_generated` that produced it. Inventing a friendlier sentence
 * that blurs two triggers together would make the reason uncheckable, which
 * is the one thing this product cannot afford to be. */
const TRIGGER_WORDING: Record<ScoreTrigger, string> = {
  signal_generated: 'New evidence arrived',
  signal_superseded: 'Earlier evidence was replaced',
  model_changed: 'Your scoring model changed',
  profile_changed: 'Your ideal-customer profile changed',
  evidence_aged: 'Evidence aged out',
};

const EVIDENCE_WORDING: Record<
  EvidenceState,
  { label: string; tone: 'neutral' | 'warning' }
> = {
  current: { label: 'Evidence current', tone: 'neutral' },
  cooling: { label: 'Cooling', tone: 'warning' },
  stale: { label: 'Evidence expired', tone: 'warning' },
};

/**
 * The magnitude behind a row's position.
 *
 * Typographic rather than a gauge or a ring: a dial invites comparison to a
 * maximum that means nothing here. **The score is an ordering of attention,
 * not a probability**, and drawing it as a filled percentage would state a
 * confidence the pipeline never computed.
 *
 * **Deliberately subordinate to the account name.** The list is already sorted,
 * so position carries the ranking and the number only answers *how strongly* —
 * a sanity check rather than the thing being scanned. Rendered muted and
 * tabular so the column reads down the page without competing with the name
 * for the eye. A score set at display weight makes every row equally loud,
 * which is the same as having no hierarchy at all.
 */
export function AttentionScore({ score }: { score: number | null }) {
  if (score === null) {
    return (
      <span
        className="text-lg font-medium tabular-nums text-content-subtle"
        aria-label="No current score"
      >
        —
      </span>
    );
  }
  return (
    <span className="text-lg font-medium tabular-nums text-content-muted">
      <span className="sr-only">Attention score </span>
      {score}
    </span>
  );
}

/**
 * What changed, and which way.
 *
 * Answers the first question of the morning — *what moved overnight* —
 * without a chart. A number and a direction is the whole of it; a sparkline
 * would add pixels and no decision.
 */
export function ScoreMovement({
  trend,
  change,
}: {
  trend: Trend | null;
  change: number | null;
}) {
  if (trend === null || change === null || change === 0) {
    return <span className="text-sm text-content-subtle">No change</span>;
  }
  const Icon = change > 0 ? ArrowUpRight : change < 0 ? ArrowDownRight : ArrowRight;
  return (
    <span
      className={cn(
        'inline-flex items-center gap-1 text-sm tabular-nums',
        change > 0 ? 'text-content' : 'text-content-muted',
      )}
    >
      <Icon aria-hidden className="h-3.5 w-3.5" />
      {change > 0 ? `+${change}` : change}
    </span>
  );
}

/**
 * Why this account is on the list right now.
 *
 * **The single most important line on the row**, and for two milestones it was
 * very nearly a constant. It carried `ScoreTrigger` — *why the score was last
 * recomputed* — which across twelve real accounts produced **two** distinct
 * values: *new evidence arrived* seven times and *evidence aged out* five. A
 * seller reads this line asking **why does this company matter today**, a
 * commercial question the enum structurally cannot answer, and a column that
 * never differs is worse than an absent one because it costs width and
 * attention and returns nothing (R1-01).
 *
 * It now names the hypothesis that most explains the score, which produces six
 * across the same twelve — *active evaluation*, *expansion opportunity*,
 * *displacement opportunity*, *contraction risk*, *new decision maker*,
 * *decision maker departed*. That is a seller's sentence rather than a
 * pipeline's.
 *
 * **The title comes from the catalog, never from this file.** A `Record<
 * SignalType, string>` here would be a second vocabulary, wrong the moment the
 * catalog changed and invisible when it did — and the module that produced
 * this row is forbidden from naming a hypothesis for exactly that reason.
 *
 * While the catalog is in flight the row shows nothing rather than a key.
 * `expansion_opportunity` is not a sentence, and a reader who saw one would
 * learn that this line is machine output.
 */
/**
 * What last moved this number. **On the brief, and no longer on the list.**
 *
 * `ScoreTrigger` describes the last *recomputation*; the evidence badge
 * describes *now*. Side by side on a list row with no visual separation, a
 * reader assumes they describe one moment and concludes the product is
 * confused — *"stale · new evidence arrived"* is literally correct and reads
 * as a defect (R1-02).
 *
 * It is not deleted, because on the brief the question *"why did this number
 * move?"* is one somebody is actually asking, and there it sits beside the
 * arithmetic rather than beside a freshness badge.
 */
export function WhyNow({ trigger }: { trigger: ScoreTrigger | null }) {
  return (
    <span className="text-sm text-content-muted">
      {trigger ? TRIGGER_WORDING[trigger] : 'No current reading'}
    </span>
  );
}

export function Hypothesis({
  signalType,
  title,
}: {
  signalType: string | null;
  /** From `useSignalCatalog`. `undefined` while it loads or if the key is one
   * this catalog version does not declare — which is a real possibility, since
   * a score records the catalog version it was formed under. */
  title: string | undefined;
}) {
  if (signalType === null) {
    // Not "unknown" and not blank: the opportunity is open and its
    // justification has expired, which is the thing the badge beside this
    // already says. Saying it twice in different words invites the reader to
    // reconcile two statements that are one fact.
    return <span className="text-sm text-content-subtle">No current reading</span>;
  }
  if (title === undefined) return null;
  return <span className="text-sm text-content">{title}</span>;
}

/**
 * Which way this row cuts.
 *
 * **A contraction risk and a low-scoring opportunity are opposite facts that
 * rank next to each other**, because the score orders *attention* and refuses
 * to sign it — two accounts can score identically and mean opposite things.
 * Measured on the real twelve, both risk rows sat at positions eleven and
 * twelve, beside the weakest opportunities on the list. A CRO scanning
 * downward reads the bottom of a list as *least important*, and for one of
 * those two rows that is exactly backwards.
 *
 * ### Only contraction is marked
 *
 * A product judgement rather than a derivation, and the same one this file
 * makes about evidence: the list is mostly expansion, so marking every posture
 * would mark almost every row, and a badge on every row saying *everything is
 * fine* trains people to stop reading badges. **The marked minority is the
 * signal.**
 *
 * ### It reads posture and cannot read anything else
 *
 * **This is why it is a component of its own rather than a branch inside
 * `Hypothesis`, and the reason is stronger than tidiness.** The mapping from a
 * catalog key to a commercial meaning belongs to the Buying Score Engine; a
 * copy in the browser would be a second vocabulary, wrong the moment the
 * catalog gained a type and invisible when it did (R9-03). Taking `posture`
 * and nothing else makes that copy **unconstructable** rather than merely
 * tested — the component has no key to pattern-match (§2).
 *
 * **And it no longer waits for the catalog.** The mark used to be attached to
 * the title, so a row whose title had not arrived — every first paint, and
 * *permanently* for a score formed under a catalog version that no longer
 * declares its key — rendered as an unmarked row. That is precisely the
 * confusion the mark exists to prevent, reappearing exactly where nobody was
 * looking. Posture travels on the wire so that a client never needs the
 * catalog to know which way a row cuts; it should never have been spent on
 * making the mark conditional on one.
 *
 * ### Where it sits, and why that is the point
 *
 * **Immediately left of the score**, in the row's status lane beside
 * *Contested* and the evidence badge. The confusion is with a number, so the
 * correction belongs next to the number: *At risk · 31* cannot be read as a
 * weak opportunity. The hypothesis line still says what happened, in the
 * catalog's words — **`decision_maker_departed` renders as a neutral sentence
 * that never says *risk* at all**, so on that row this badge is the only thing
 * carrying it.
 */
export function PostureMark({ posture }: { posture: Posture | null }) {
  if (posture !== 'contractionary') return null;
  return (
    <Badge tone="warning">
      {/* An icon as well as a tone, and words as well as both. Colour alone
          fails a colour-blind reader, and accessibility is a defect class
          rather than an enhancement (§20c). `warning`, not `danger`: a
          contraction risk is a different *kind* of attention, not something
          that has gone wrong. */}
      <TrendingDown aria-hidden className="mr-1 h-3 w-3" />
      At risk
      {/* Two words fit the badge lane a phone already reflows; the sentence
          they abbreviate is the one a screen reader hears. */}
      <span className="sr-only"> to existing revenue</span>
    </Badge>
  );
}

/**
 * How far the evidence can be trusted today.
 *
 * Shown only when it is *not* current. A badge on every row saying
 * "everything is fine" is noise that trains people to stop reading badges.
 */
export function EvidenceHealth({ evidence }: { evidence: EvidenceState }) {
  if (evidence === 'current') return null;
  const { label, tone } = EVIDENCE_WORDING[evidence];
  return <Badge tone={tone}>{label}</Badge>;
}

/**
 * Both readings are live and neither won.
 *
 * **Not a warning.** The Buying Score Engine refuses to average opposing
 * readings away because a fought-over account warrants *more* attention, and
 * the badge says exactly that rather than implying doubt.
 */
export function ContestedMark({ contested }: { contested: boolean }) {
  if (!contested) return null;
  return (
    <Badge tone="accent">
      <Scale aria-hidden className="mr-1 h-3 w-3" />
      Contested
    </Badge>
  );
}

/**
 * Whether anybody is working this account, and whether it is you.
 *
 * **The missing half of the action the product already offers.** J4 shipped
 * *"I'm working this"* and the list rendered nothing with it — take an account
 * on, return here, and the row was identical. `owner_id` and `stage` have been
 * on the wire since M12.1 and neither had ever been used (**D40**).
 *
 * ### It marks and does not reorder
 *
 * Sorting owned rows to the top would make the list's order depend on who is
 * looking, and the ranking is the ranking. A *mine / everyone* filter is right
 * at three hundred accounts and premature at twelve, where a control that
 * always shows the same thing teaches people to ignore controls.
 *
 * ### Silent on the ordinary case
 *
 * An unclaimed account that Signora is merely tracking says nothing — that is
 * most rows most of the time, and a badge on every one of them would be noise
 * that trains a reader past the badges that matter.
 *
 * ### It can say *you* and it cannot say anybody else's name
 *
 * **D23 said *taken*, and that was right until TM-01.** The Python tier
 * verifies tokens without learning who anybody is, so *taken* was the honest
 * form of an identifier nobody could read. **A membership now records the
 * address it was created with**, so a colleague can be named — and the badge
 * says which colleague rather than merely that somebody got there first.
 *
 * **`Taken` survives as the fallback**, for a membership added by identifier
 * before invitations existed. Still honest, and now rare.
 */
export function Ownership({
  ownerId,
  ownerName,
  stage,
  viewerId,
}: {
  ownerId: string | null;
  /** What to call them, when the product can. Absent for a membership with no
   * recorded address — the badge then says *Taken*, as it always did. */
  ownerName?: string | undefined;
  stage: Stage;
  /** The signed-in reader. Null while the session is still resolving, which
   * renders as *taken* rather than as a wrong *yours*. */
  viewerId: string | null;
}) {
  if (ownerId === null) {
    // Closed without an owner — somebody decided about it and never held it.
    // Worth saying, because the row is otherwise indistinguishable from work
    // nobody has looked at.
    if (stage === 'tracking') return null;
    return <Badge tone="neutral">{STAGE_MARK[stage]}</Badge>;
  }

  // **Two different questions, and the row answers whichever the reader has.**
  // A seller asks *which are mine* — binary, and `Yours` is the whole answer.
  // A manager asks *who holds this*, which needs the name.
  return ownerId === viewerId ? (
    <Badge tone="accent">Yours</Badge>
  ) : (
    <Badge tone="neutral">{ownerName ?? 'Taken'}</Badge>
  );
}

/**
 * How long an account has been sitting where it sits.
 *
 * **The Friday-afternoon question**, and the list could not answer it: an
 * account taken on this morning and one taken on in March rendered as the same
 * row, so *"what have I been sitting on?"* meant opening briefs one at a time
 * (LO-06).
 *
 * ### A fact, never a judgement
 *
 * **Signora records workflow decisions and cannot see a call, an email or a
 * meeting.** So it must never say an account is neglected, stalled or at risk —
 * a seller who spoke to this customer yesterday would be told they had not, by
 * a product with no way to know. It states how long it has been since something
 * it *can* see happened, and the reader decides what that means.
 *
 * **No threshold, and that is a decision rather than an omission.** A number at
 * which an account becomes *too* old is a per-customer judgement, and the
 * module's own policy artifact refuses it: every opportunity records the policy
 * version that qualified it, so adding an unrelated setting there would churn
 * the recorded explanation of every historical opportunity — the same argument
 * that kept qualification out of the scoring model. **The threshold arrives
 * with the thing that needs one**, which is a notification, and that needs
 * M14a.
 *
 * ### Only where somebody has committed
 *
 * A tracked account's age is *Signora's* suggestion ageing, which the brief
 * already states and the evidence badge already grades. This is the clock that
 * starts when a person takes responsibility.
 */
export function HeldSince({ stage, since }: { stage: Stage; since: string }) {
  if (stage !== 'engaged') return null;
  return <span className="text-xs text-content-subtle">Taken on {howLongAgo(since)}</span>;
}

/** What a stage is called where there is room for one word. The brief spells
 * each of them out; a list row has to be scannable. */
const STAGE_MARK: Record<Stage, string> = {
  tracking: 'Tracking',
  engaged: 'Being worked',
  closed_won: 'Won',
  closed_lost: 'Lost',
  dismissed: 'Dismissed',
};
