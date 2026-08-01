'use client';

import { useState } from 'react';

import { Button, Dialog, Input } from '@/components/ui';
import { ApiError } from '@/lib/api/client';
import type { AccountOpportunity, Stage } from '@/lib/api/types';
import { useRecordDecision } from '@/lib/query/hooks';

/**
 * Where a seller says what they decided.
 *
 * **The first thing in Signora that writes.** Every other surface reports what
 * the pipeline computed; this records what a person chose, and the two are
 * different kinds of fact — delete every derived table and the pipeline
 * rebuilds it byte for byte, while nothing anywhere reproduces a decision
 * somebody made. *Intelligence suggests; humans commit.*
 *
 * ### Why the controls sit with the stage rather than at the end of the page
 *
 * The stage line already states where this stands. Putting the change beside
 * it means workflow lives in exactly one place on the screen — and an AE who
 * arrived already knowing they are working this account does not have to read
 * a brief to say so. A reader who is still deciding scrolls, decides, and
 * comes back to the one control they have already seen.
 *
 * ### Why every decision asks for a sentence
 *
 * The domain refuses a state with no reason, and that is not a validation
 * quirk to route around: **workflow has to explain itself as thoroughly as the
 * intelligence does.** On a dismissal it is the only feedback Signora ever
 * gets about its own qualification quality, which makes it the most valuable
 * sentence a customer ever types here.
 *
 * ### Why the moves are not listed in this file
 *
 * `allowed_next` arrives on the brief, derived from the domain's own
 * transition table. A copy here would be a second representation of the rules,
 * wrong the moment either changed — and the server refuses anything else
 * regardless, because a list a caller can ignore is not enforcement.
 */

/**
 * What each move is called, in a seller's words rather than the schema's.
 *
 * **A translation, never a paraphrase** — each phrase maps to exactly one
 * recorded stage, so what somebody clicked can be checked against the record.
 * `dismissed` is deliberately not softened into "closed": it means *we should
 * not have been shown this*, which is feedback about Signora's judgement
 * rather than a sales outcome, and blurring the two would destroy the only
 * signal the platform gets about its own qualification quality.
 */
const ACTION_WORDING: Record<Stage, string> = {
  tracking: 'Track this again',
  engaged: "I'm working this",
  closed_won: 'Won',
  closed_lost: 'Lost',
  dismissed: 'Not a real opportunity',
};

/**
 * The moves that read differently depending on where they are offered from.
 *
 * **R4-02.** From `tracking`, *"Lost"* sits beside *"nobody has taken it yet"*
 * and reads as a mistake in the product rather than as an outcome distinct
 * from *"Not a real opportunity"*. An AE asked it directly: *"What's the
 * difference between Lost and Not a real opportunity if I never touched it?"*
 * — which is exactly the distinction this module exists to protect, unreadable
 * at the point of use.
 *
 * **The domain is not touched and must not be.** A deal you knew about, did
 * not chase, and that closed elsewhere *is* a loss; the stage set is right.
 * This is a labelling problem, and the fix stays in the label.
 *
 * Keyed by origin, falling through to `ACTION_WORDING` — so a move that reads
 * correctly from everywhere is written once, and only the exception is stated.
 */
const ACTION_FROM: Partial<Record<Stage, Partial<Record<Stage, string>>>> = {
  tracking: { closed_lost: 'Lost without pursuing' },
};

function actionWording(from: Stage, to: Stage): string {
  return ACTION_FROM[from]?.[to] ?? ACTION_WORDING[to];
}

/**
 * What the reason field is actually asking.
 *
 * A single *"Reason"* label would collect a single kind of sentence. The
 * question changes what a seller writes, and on a dismissal it is the
 * difference between "not interested" and something the qualification policy
 * could one day be improved by.
 */
const REASON_QUESTION: Record<Stage, string> = {
  tracking: 'Why are you picking this back up?',
  engaged: 'Why are you taking this on?',
  closed_won: 'What won it?',
  closed_lost: 'Why was it lost?',
  dismissed: "Why shouldn't Signora have shown you this?",
};

const CONFIRM_WORDING: Record<Stage, string> = {
  tracking: 'Track it again',
  engaged: 'Take it on',
  closed_won: 'Record the win',
  closed_lost: 'Record the loss',
  dismissed: 'Dismiss it',
};

export function WorkflowActions({
  opportunity,
  workspaceId,
  viewerId,
}: {
  opportunity: AccountOpportunity;
  workspaceId: string | null;
  /** The signed-in user, so taking an account on can assign it to them. */
  viewerId: string | null;
}) {
  const [choice, setChoice] = useState<Stage | null>(null);

  // A won deal is terminal and the server says so by sending nothing. **No
  // empty toolbar and no disabled buttons** — a control that cannot be used
  // teaches a reader to distrust the ones that can.
  if (opportunity.allowed_next.length === 0) return null;

  return (
    <div className="flex flex-wrap items-center gap-2">
      {opportunity.allowed_next.map((stage, index) => (
        <Button
          key={stage}
          size="sm"
          variant={index === 0 ? 'secondary' : 'ghost'}
          onClick={() => setChoice(stage)}
        >
          {actionWording(opportunity.stage, stage)}
        </Button>
      ))}

      <DecisionDialog
        opportunity={opportunity}
        workspaceId={workspaceId}
        viewerId={viewerId}
        stage={choice}
        onClose={() => setChoice(null)}
      />
    </div>
  );
}

/**
 * One decision, and the sentence that explains it.
 *
 * **Not optimistic, deliberately.** Everywhere else on this page a figure is
 * one the server computed; a stage that flipped locally and was then refused
 * would be the one place the product stated something untrue, however briefly.
 *
 * A refusal is shown **in the domain's own words**. Those sentences were
 * written to be read — *"A won deal does not reopen — the next deal at that
 * account is genuinely a new opportunity"* — and replacing them with
 * *"Something went wrong"* would throw away the best explanation in the
 * system.
 */
function DecisionDialog({
  opportunity,
  workspaceId,
  viewerId,
  stage,
  onClose,
}: {
  opportunity: AccountOpportunity;
  workspaceId: string | null;
  viewerId: string | null;
  stage: Stage | null;
  onClose: () => void;
}) {
  const [reason, setReason] = useState('');
  const decide = useRecordDecision(workspaceId, opportunity.account_id, opportunity.id);

  const close = () => {
    setReason('');
    decide.reset();
    onClose();
  };

  // Taking an account on means taking it on. Stated in the dialog rather than
  // applied quietly, because ownership is a fact about a person and one they
  // should see being recorded.
  const claiming =
    stage === 'engaged' && viewerId !== null && opportunity.owner_id !== viewerId;

  const submit = () => {
    if (stage === null || reason.trim() === '') return;
    decide.mutate(
      { stage, reason, ...(claiming ? { owner_id: viewerId } : {}) },
      { onSuccess: close },
    );
  };

  return (
    <Dialog
      open={stage !== null}
      onClose={close}
      title={stage ? actionWording(opportunity.stage, stage) : ''}
      description={claiming ? 'This account will be assigned to you.' : undefined}
      footer={
        <>
          <Button variant="ghost" onClick={close} disabled={decide.isPending}>
            Cancel
          </Button>
          <Button
            onClick={submit}
            // Disabled on an empty reason so the domain's refusal is not used
            // as a form validator. The server still enforces it.
            disabled={reason.trim() === '' || decide.isPending}
          >
            {stage ? CONFIRM_WORDING[stage] : ''}
          </Button>
        </>
      }
    >
      <form
        className="flex flex-col gap-3"
        onSubmit={(event) => {
          event.preventDefault();
          submit();
        }}
      >
        <Input
          label={stage ? REASON_QUESTION[stage] : ''}
          value={reason}
          onChange={(event) => setReason(event.target.value)}
          maxLength={512}
          autoFocus
          hint="Recorded against this account permanently, with your name and the date."
          {...(decide.error ? { error: refusal(decide.error) } : {})}
        />
      </form>
    </Dialog>
  );
}

/**
 * What the server said, when it can be trusted to be about this decision.
 *
 * The Opportunity Engine's refusals are prose written for a customer. A
 * network failure is not, so anything without the API's error envelope gets a
 * sentence that does not pretend to know what happened.
 *
 * ### One code is answered here rather than passed through
 *
 * **`transition_refused` is only reachable by being out of date.** This dialog
 * offers exactly `allowed_next`, derived server-side from the domain's own
 * table, so an illegal move needs a stale page or a colleague deciding at the
 * same moment. The domain's explanation — *"'tracking' cannot become
 * 'closed_won'. Allowed from here: …"* — answers a question the reader did not
 * ask, in the platform's vocabulary (ADR-0034), and leaves them with nothing to
 * do.
 *
 * **This is not a second copy of the transition rules.** It states no rule,
 * which is exactly what makes it safe to hold client-side where a table would
 * not be. The server's prose is unchanged and still reaches the logs, the API
 * and every other consumer.
 *
 * Every other code passes through, because every other refusal is a statement
 * about the customer's own data that they can act on.
 */
function refusal(error: unknown): string {
  if (error instanceof ApiError) {
    if (error.code === 'transition_refused') {
      return 'This account has moved since you opened this page. Reload to see where it stands.';
    }
    return error.message;
  }
  return 'This could not be recorded. Nothing has changed — try again.';
}
