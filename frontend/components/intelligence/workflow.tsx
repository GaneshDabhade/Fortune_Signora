'use client';

import { useState } from 'react';

import { Button, Dialog, Input, Select } from '@/components/ui';
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

/**
 * What the confirm button will actually do.
 *
 * **`Take it on` is wrong the moment somebody is handing the account over**,
 * and the control that says it is the last thing they read before committing.
 * A button that describes a different act than the one it performs is the
 * defect a confirmation exists to prevent.
 */
function confirmWording(
  stage: Stage | null,
  handTo: string | null,
  colleagues: readonly { id: string; name: string }[],
): string {
  if (stage === null) return '';
  if (stage === 'engaged' && handTo !== null) {
    const name = colleagues.find((one) => one.id === handTo)?.name;
    // **Named or not claimed.** If the name has not resolved, say the honest
    // general thing rather than "Hand it to " with nothing after it.
    return name ? `Hand it to ${name}` : 'Hand it over';
  }
  return CONFIRM_WORDING[stage];
}

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
  colleagues = [],
  next,
}: {
  opportunity: AccountOpportunity;
  workspaceId: string | null;
  /** The signed-in user, so taking an account on can assign it to them. */
  viewerId: string | null;
  /** Everybody else in the organization, so an account can be handed to one.
   *
   * **Passed in rather than fetched here.** The same rule `next` follows: a
   * presentational control that reached for a query would make every test of a
   * decision mount a client. **Empty means nobody else is here yet** — a
   * one-person organization — and the control is then absent rather than empty.
   */
  colleagues?: readonly { id: string; name: string }[];
  /** Where the morning continues, if anywhere — a name to offer and a way to
   * go there. **Omitted rather than defaulted**: an offer that goes nowhere is
   * the failure this surface refuses everywhere else.
   *
   * **The navigation is the page's, not this component's.** Reaching for a
   * router here would make a presentational control require one, and every
   * test of a decision would have to mount an app router to assert wording. */
  next?: { name: string; go: () => void } | undefined;
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
        colleagues={colleagues}
        opportunity={opportunity}
        workspaceId={workspaceId}
        viewerId={viewerId}
        stage={choice}
        next={next}
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
  colleagues,
  opportunity,
  workspaceId,
  viewerId,
  stage,
  next,
  onClose,
}: {
  opportunity: AccountOpportunity;
  workspaceId: string | null;
  viewerId: string | null;
  stage: Stage | null;
  colleagues: readonly { id: string; name: string }[];
  next?: { name: string; go: () => void } | undefined;
  onClose: () => void;
}) {
  const [reason, setReason] = useState('');
  // **`null` means *me*.** The commonest case by far — somebody deciding about
  // an account is usually taking it on — so it is the default rather than a
  // choice they have to make first.
  const [handTo, setHandTo] = useState<string | null>(null);
  const [recorded, setRecorded] = useState<Stage | null>(null);
  const decide = useRecordDecision(workspaceId, opportunity.account_id, opportunity.id);

  const close = () => {
    setReason('');
    setHandTo(null);
    setRecorded(null);
    decide.reset();
    onClose();
  };

  // Taking an account on means taking it on. Stated in the dialog rather than
  // applied quietly, because ownership is a fact about a person and one they
  // should see being recorded.
  const engaging = stage === 'engaged';
  const claiming = engaging && viewerId !== null && opportunity.owner_id !== viewerId;
  // **The line that was the whole milestone.** This sent `viewerId` and
  // nothing else, so a seller could take an account on and **could not hand
  // one to a colleague** — while the endpoint had accepted an arbitrary
  // `owner_id` since M6, validated the assignee's membership, and returned
  // `owner_not_a_member` when it failed. The capability was built; the UI had
  // no way to name a person until TM-01
  // ([49-lead-ownership.md](../../../docs/architecture/49-lead-ownership.md) §1).
  const newOwner = engaging ? (handTo ?? (claiming ? viewerId : null)) : null;

  const submit = () => {
    if (stage === null || reason.trim() === '') return;
    decide.mutate(
      { stage, reason, ...(newOwner !== null ? { owner_id: newOwner } : {}) },
      // **R10-02.** The decision is the end of the visit — the one moment the
      // product can be certain the reader is done — and it used to close the
      // dialog and do nothing else. With somewhere to go, it offers; with
      // nowhere, it closes exactly as before.
      { onSuccess: () => (next === undefined ? close() : setRecorded(stage)) },
    );
  };

  return (
    <Dialog
      open={stage !== null}
      onClose={close}
      title={
        recorded
          ? RECORDED_WORDING[recorded]
          : stage
            ? actionWording(opportunity.stage, stage)
            : ''
      }
      description={
        recorded === null && claiming && handTo === null
          ? 'This account will be assigned to you.'
          : undefined
      }
      footer={
        recorded !== null && next !== undefined ? (
          <>
            {/* **An offer, never a redirect.** A page that navigates itself
                after you click something takes the reader's place away from
                them — and a decision is exactly when somebody wants to check
                what they just wrote. So *stay* is a real choice, listed
                first, and nothing moves until they say so. */}
            <Button variant="ghost" onClick={close}>
              Stay here
            </Button>
            {/* **A button rather than a styled link**, because `Button` has
                no `as` and `components/ui` is frozen (§20c) — restyling a
                shared component for one caller is exactly what that rule
                forbids. The same destination is a real link at the foot of the
                page, where the sequence already offers it. */}
            <Button
              onClick={() => {
                close();
                next.go();
              }}
            >
              Next: {next.name}
            </Button>
          </>
        ) : (
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
            {confirmWording(stage, handTo, colleagues)}
          </Button>
        </>
        )
      }
    >
      {recorded !== null ? (
        <p className="text-sm leading-6 text-content-muted">
          Recorded against this account, with your name and the date. Your list has
          moved on — the next most pressing account is below.
        </p>
      ) : (
      <form
        className="flex flex-col gap-3"
        onSubmit={(event) => {
          event.preventDefault();
          submit();
        }}
      >
        {/* **Only when taking an account on**, and only when there is
            somebody to hand it to. Every other decision — closing, dismissing
            — leaves ownership exactly where it was, and offering a control
            there would invite a change nobody asked for. */}
        {engaging && colleagues.length > 0 ? (
          <Select
            label="Who is working this"
            value={handTo ?? ''}
            onChange={(event) => setHandTo(event.target.value || null)}
            options={[
              { value: '', label: 'You' },
              ...colleagues.map((one) => ({ value: one.id, label: one.name })),
            ]}
          />
        ) : null}

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
      )}
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

/**
 * What was just recorded, said back in the past tense.
 *
 * **The title changes rather than a banner appearing.** A dialog that keeps
 * its question after the question is answered invites a reader to answer it
 * twice, and the second attempt would be refused by a domain that is right to
 * refuse it.
 */
const RECORDED_WORDING: Record<Stage, string> = {
  tracking: 'Back to tracking',
  engaged: "You're working this",
  closed_won: 'Recorded as won',
  closed_lost: 'Recorded as lost',
  dismissed: 'Dismissed',
};
