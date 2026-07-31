'use client';

import { ArrowDownRight, ArrowRight, ArrowUpRight, Scale } from 'lucide-react';

import { Badge } from '@/components/ui';
import type { EvidenceState, ScoreTrigger, Trend } from '@/lib/api/types';
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

const EVIDENCE_WORDING: Record<EvidenceState, { label: string; tone: 'neutral' | 'warning' }> =
  {
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
 * **The single most important line on the row.** A list that ranks without
 * saying why is a leaderboard, and a seller cannot act on a leaderboard.
 */
export function WhyNow({ trigger }: { trigger: ScoreTrigger | null }) {
  return (
    <span className="text-sm text-content-muted">
      {trigger ? TRIGGER_WORDING[trigger] : 'No current reading'}
    </span>
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
