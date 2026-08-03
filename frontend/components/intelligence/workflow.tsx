'use client';

import { useState } from 'react';

import { Button, Dialog, Input, Select } from '@/components/ui';
import { ApiError } from '@/lib/api/client';
import type { AccountOpportunity, Stage } from '@/lib/api/types';
import { useOpenOpportunity, useRecordDecision } from '@/lib/query/hooks';

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
 * One thing a seller is about to do.
 *
 * **A hand-over is not a stage**, and this type is where that is enforced: it
 * carries the stage the account will be in *and* whether ownership is what is
 * moving, because those are two independent facts and a single enum could only
 * hold one of them. Inventing `transferred` as a fifth stage would have made a
 * *state* out of an *event*, and every win-rate figure computed later would
 * have had to learn to ignore it.
 */
interface Choice {
  stage: Stage;
  /** Ownership is the change; the stage is going nowhere. */
  handover: boolean;
}

/**
 * What the confirm button will actually do.
 *
 * **`Take it on` is wrong the moment somebody is handing the account over**,
 * and the control that says it is the last thing they read before committing.
 * A button that describes a different act than the one it performs is the
 * defect a confirmation exists to prevent.
 */
function confirmWording(
  choice: Choice | null,
  handTo: string | null,
  colleagues: readonly { id: string; name: string }[],
  holding: boolean,
): string {
  if (choice === null) return '';
  if (choice.handover && !holding) return 'Take it over';
  if ((choice.handover || choice.stage === 'engaged') && handTo !== null) {
    const name = colleagues.find((one) => one.id === handTo)?.name;
    // **Named or not claimed.** If the name has not resolved, say the honest
    // general thing rather than "Hand it to " with nothing after it.
    return name ? `Hand it to ${name}` : 'Hand it over';
  }
  if (choice.handover) return 'Hand it over';
  return CONFIRM_WORDING[choice.stage];
}

/**
 * What the reason field asks when ownership is the thing moving.
 *
 * Keyed by whether the reader currently holds it, because the two are
 * different questions: giving an account away and taking one on are not the
 * same act described from opposite ends, and a single label would collect the
 * same shapeless sentence for both.
 */
const HANDOVER_QUESTION = {
  giving: 'Why is somebody else taking this on?',
  taking: 'Why are you taking this over?',
} as const;

/**
 * What happens to the account afterwards.
 *
 * **The product built recoverability and never mentioned it at the moment
 * somebody was deciding whether to risk it** (LO-05, the screen audit). A
 * dismissal *is* recoverable — the decided section exists precisely so a
 * seller can find one again — and a rep who does not know that will not
 * dismiss anything, which is exactly what a Sales Manager said out loud during
 * R4-04: *"I'd tell my reps not to dismiss anything."*
 *
 * **A rep who will not dismiss produces no qualification-quality signal at
 * all**, which is the one thing `dismissed` exists to capture. So the sentence
 * that makes the decision safe belongs on the dialog, not on the screen a
 * reader reaches afterwards.
 *
 * **A statement of consequence, never reassurance.** A won deal is told
 * plainly that it does not come back, because that one is *not* recoverable
 * and pretending otherwise would be the more expensive kindness.
 */
const CONSEQUENCE: Record<Stage, string> = {
  tracking: 'This comes back onto your list.',
  engaged: 'This stays on your list, marked as yours.',
  closed_won:
    'This closes the deal and leaves your list. Won deals stay won — if the company comes back, that is a new opportunity.',
  closed_lost:
    'This leaves your list. You can find it again under the accounts you have already decided, and pick it up if it comes back.',
  dismissed:
    'This leaves your list. You can find it again under the accounts you have already decided, and track it again if you change your mind.',
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
  const [choice, setChoice] = useState<Choice | null>(null);

  // **Whether ownership can move, which `allowed_next` structurally cannot
  // say.** That list is the domain's *stage* table, and a hand-over changes no
  // stage — so an account being worked offered `Won`, `Lost` and `Not a real
  // opportunity` and **no way to give it to anybody**. The endpoint has
  // accepted a same-stage owner change since M6; the only thing missing was a
  // control, and a seller going on leave had to close their accounts to get
  // them off their name
  // ([49-lead-ownership.md](../../../docs/architecture/49-lead-ownership.md) §13).
  //
  // Offered while the work is live and nowhere else: a closed account has no
  // work to hand over, and a `tracking` one is offered `I'm working this`,
  // which already asks who is taking it.
  const holding = opportunity.owner_id !== null && opportunity.owner_id === viewerId;
  const live = opportunity.stage === 'engaged' && opportunity.owner_id !== null;
  // Giving needs somebody to give it to; taking needs somebody to be. **A
  // control that cannot complete is not offered** rather than offered and
  // refused.
  const canHandOver = live && (holding ? colleagues.length > 0 : viewerId !== null);

  // A won deal is terminal and the server says so by sending nothing. **No
  // empty toolbar and no disabled buttons** — a control that cannot be used
  // teaches a reader to distrust the ones that can.
  //
  // **But silence is not an explanation** (LO-05). A seller arriving at a won
  // account found every other brief offering something and this one offering
  // nothing, with no sentence saying why — which reads as the product having
  // failed rather than as a deliberate rule. It is the one place in the
  // lifecycle where a reader can do nothing, so it is the one place that has
  // to say what happens instead.
  if (opportunity.allowed_next.length === 0 && !canHandOver) {
    return <WonAndFinished opportunity={opportunity} workspaceId={workspaceId} />;
  }

  return (
    <div className="flex flex-wrap items-center gap-2">
      {opportunity.allowed_next.map((stage, index) => (
        <Button
          key={stage}
          size="sm"
          variant={index === 0 ? 'secondary' : 'ghost'}
          onClick={() => setChoice({ stage, handover: false })}
        >
          {actionWording(opportunity.stage, stage)}
        </Button>
      ))}

      {canHandOver ? (
        <Button
          size="sm"
          variant="ghost"
          onClick={() => setChoice({ stage: opportunity.stage, handover: true })}
        >
          {holding ? 'Hand it over' : 'Take it over'}
        </Button>
      ) : null}

      <DecisionDialog
        colleagues={colleagues}
        opportunity={opportunity}
        workspaceId={workspaceId}
        viewerId={viewerId}
        choice={choice}
        next={next}
        onClose={() => setChoice(null)}
      />
    </div>
  );
}

/**
 * A won deal — the one place in the lifecycle where a reader can do nothing.
 *
 * ### Why it says something at all
 *
 * Every other brief offers a move; this one offered an empty space, which
 * reads as the product having failed rather than as a deliberate rule
 * (LO-05, F-7). **Silence is not an explanation.**
 *
 * ### And why it offers a way out that is not a reopening
 *
 * *"I clicked the wrong row"* had **no answer at all** — a won deal is
 * terminal, correctly, and the recourse the domain names (*the next deal at
 * that account is genuinely a new opportunity*) had no route into the product
 * until LO-07 built one.
 *
 * **The mistake is preserved rather than erased.** The closed deal keeps its
 * history, its reason and its outcome; the new opportunity carries the
 * sentence explaining why it exists. A one-click undo would edit the past,
 * which is the one thing this module refuses — and it would quietly remove a
 * false win from a figure somebody may already have reported.
 */
function WonAndFinished({
  opportunity,
  workspaceId,
}: {
  opportunity: AccountOpportunity;
  workspaceId: string | null;
}) {
  const [asking, setAsking] = useState(false);
  const [reason, setReason] = useState('');
  const open = useOpenOpportunity(workspaceId, opportunity.account_id);

  const close = () => {
    setReason('');
    open.reset();
    setAsking(false);
  };

  return (
    <div className="flex flex-col items-start gap-2">
      <p className="text-sm leading-6 text-content-muted">
        Won deals stay won. If this company comes back, that is a new opportunity — this
        one keeps its history.
      </p>
      <Button size="sm" variant="ghost" onClick={() => setAsking(true)}>
        Work this account again
      </Button>

      <Dialog
        open={asking}
        onClose={close}
        title="Work this account again"
        description="The deal you closed stays exactly as it is. This opens a new opportunity beside it."
        footer={
          <>
            <Button variant="ghost" onClick={close} disabled={open.isPending}>
              Cancel
            </Button>
            <Button
              onClick={() => reason.trim() !== '' && open.mutate({ reason })}
              disabled={reason.trim() === '' || open.isPending}
            >
              Open it
            </Button>
          </>
        }
      >
        <form
          className="flex flex-col gap-3"
          onSubmit={(event) => {
            event.preventDefault();
            if (reason.trim() !== '') open.mutate({ reason });
          }}
        >
          <Input
            // **The whole value of a manual opening.** The automatic path
            // records the score and the policy that qualified it; a human
            // opening has neither, so this sentence is the only explanation
            // the new opportunity will ever carry.
            label="Why is this worth working again?"
            value={reason}
            onChange={(event) => setReason(event.target.value)}
            maxLength={512}
            autoFocus
            hint="Recorded against the new opportunity permanently, with your name and the date."
            {...(open.error ? { error: refusal(open.error) } : {})}
          />
        </form>
      </Dialog>
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
  choice,
  next,
  onClose,
}: {
  opportunity: AccountOpportunity;
  workspaceId: string | null;
  viewerId: string | null;
  choice: Choice | null;
  colleagues: readonly { id: string; name: string }[];
  next?: { name: string; go: () => void } | undefined;
  onClose: () => void;
}) {
  const [reason, setReason] = useState('');
  // **`null` means *me*.** The commonest case by far — somebody deciding about
  // an account is usually taking it on — so it is the default rather than a
  // choice they have to make first.
  const [handTo, setHandTo] = useState<string | null>(null);
  // **What was decided, and who held it when.** The second half is not
  // redundant: recording the decision invalidates the brief, so by the time
  // this panel renders the account already belongs to somebody else and asking
  // *"do I hold this?"* then would answer about the world after the act. The
  // success wording is about the act.
  const [recorded, setRecorded] = useState<{ choice: Choice; holding: boolean } | null>(null);
  const decide = useRecordDecision(workspaceId, opportunity.account_id, opportunity.id);

  const close = () => {
    setReason('');
    setHandTo(null);
    setRecorded(null);
    decide.reset();
    onClose();
  };

  const handover = choice?.handover ?? false;
  // Who holds it *now* — which decides whether this dialog is giving the
  // account away or taking it on.
  const holding = opportunity.owner_id !== null && opportunity.owner_id === viewerId;
  // Taking an account on means taking it on. Stated in the dialog rather than
  // applied quietly, because ownership is a fact about a person and one they
  // should see being recorded.
  const engaging = choice?.stage === 'engaged' && !handover;
  const claiming = engaging && viewerId !== null && opportunity.owner_id !== viewerId;
  // **The line that was the whole milestone.** This sent `viewerId` and
  // nothing else, so a seller could take an account on and **could not hand
  // one to a colleague** — while the endpoint had accepted an arbitrary
  // `owner_id` since M6, validated the assignee's membership, and returned
  // `owner_not_a_member` when it failed. The capability was built; the UI had
  // no way to name a person until TM-01
  // ([49-lead-ownership.md](../../../docs/architecture/49-lead-ownership.md) §1).
  //
  // **A hand-over names the person in both directions.** Giving it away sends
  // whoever was chosen; taking it over sends the reader — and that second case
  // is what *"two people both think they own an account"* looks like when the
  // product lets them settle it in the open, with a reason recorded, instead of
  // one of them quietly closing it.
  const newOwner = handover
    ? holding
      ? handTo
      : viewerId
    : engaging
      ? (handTo ?? (claiming ? viewerId : null))
      : null;
  // **The one control here that can be incomplete.** Everywhere else ownership
  // has a sensible default; giving an account away does not — *"to whom"* has
  // no answer the product may guess.
  const unaddressed = handover && holding && handTo === null;

  const submit = () => {
    if (choice === null || reason.trim() === '' || unaddressed) return;
    decide.mutate(
      { stage: choice.stage, reason, ...(newOwner !== null ? { owner_id: newOwner } : {}) },
      // **R10-02.** The decision is the end of the visit — the one moment the
      // product can be certain the reader is done — and it used to close the
      // dialog and do nothing else. With somewhere to go, it offers; with
      // nowhere, it closes exactly as before.
      { onSuccess: () => (next === undefined ? close() : setRecorded({ choice, holding })) },
    );
  };

  return (
    <Dialog
      open={choice !== null}
      onClose={close}
      title={
        recorded
          ? recordedWording(recorded.choice, recorded.holding)
          : choice
            ? choice.handover
              ? holding
                ? 'Hand it over'
                : 'Take it over'
              : actionWording(opportunity.stage, choice.stage)
            : ''
      }
      description={
        recorded !== null
          ? undefined
          : handover
            ? holding
              ? undefined
              : // **Said before it happens, not discovered afterwards.** Taking
                // an account somebody else is working is a legitimate act — a
                // territory change, a colleague on leave — and the product's
                // job is to make it visible rather than to prevent it.
                'This account is being worked by somebody else. It will move to you, and the change will be on its record.'
            : claiming && handTo === null
              ? 'This account will be assigned to you.'
              : choice
                ? CONSEQUENCE[choice.stage]
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
            disabled={reason.trim() === '' || unaddressed || decide.isPending}
          >
            {confirmWording(choice, handTo, colleagues, holding)}
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

        {/* **No default, deliberately.** Handing an account over has no
            commonest case the product may assume — the first colleague in a
            list is not a guess, it is a person — so the placeholder is
            unselectable and the confirm stays disabled until somebody is
            named. */}
        {handover && holding ? (
          <Select
            label="Who is taking it on"
            value={handTo ?? ''}
            onChange={(event) => setHandTo(event.target.value || null)}
            options={[
              { value: '', label: 'Choose a colleague' },
              ...colleagues.map((one) => ({ value: one.id, label: one.name })),
            ]}
          />
        ) : null}

        <Input
          label={
            handover
              ? HANDOVER_QUESTION[holding ? 'giving' : 'taking']
              : choice
                ? REASON_QUESTION[choice.stage]
                : ''
          }
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
/**
 * What just happened, said back to the person who did it.
 *
 * **`You're working this` is wrong when you have just given the account
 * away** — the same defect as the confirm button LO-01 corrected, one screen
 * later, and found the same way: by writing the test rather than by reading
 * the diff.
 */
function recordedWording(choice: Choice, holding: boolean): string {
  if (choice.handover) return holding ? 'Handed over' : "You're working this";
  return RECORDED_WORDING[choice.stage];
}

const RECORDED_WORDING: Record<Stage, string> = {
  tracking: 'Back to tracking',
  engaged: "You're working this",
  closed_won: 'Recorded as won',
  closed_lost: 'Recorded as lost',
  dismissed: 'Dismissed',
};
