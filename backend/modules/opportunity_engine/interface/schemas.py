"""HTTP response schemas for the Opportunity Engine.

Deliberately separate from the domain entities, even where field-identical:
coupling the wire contract to the domain model makes a domain refactor a
client-breaking change (19-api-conventions.md).

**Every field here answers a question a salesperson would ask.** The test for
inclusion was *"would someone selling understand why this is present?"* — and
several domain fields did not survive it:

- `generation` — how many opportunities this account has had. A uniqueness
  device that stops two concurrent qualifications both succeeding. Nobody
  selling has ever wanted to know it.
- `policy_version` — which qualification policy admitted this account. Real,
  auditable, and a support question rather than a sales one.
- `originating_buying_score_id` — the provenance link. It belongs on the
  account brief, where a citation can be *followed*; on a list row it is an
  opaque identifier nobody can act on.
- `contested_at_creation` — superseded by the live `contested`, which is what
  a seller is actually deciding on today.

None of them are secret and none are hidden — they are simply not part of
*this* answer, and a row that carries them teaches a reader that the fields on
it are not worth reading.

**Descriptions are `Field(description=…)`, not `#:` comments.** The first draft
used comments, which document the class for a Python reader and reach the
generated OpenAPI as nothing at all — so every field arrived on the wire
undocumented while the source looked thorough. A test now asserts the schema
itself, because that is what a client actually receives.
"""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from modules.buying_score_engine.public import Posture
from modules.opportunity_engine.application.queries import (
    DecidedAccount,
    OpportunityBrief,
    TrackedOpportunity,
)
from modules.opportunity_engine.domain.opportunity import (
    EvidenceState,
    OpportunityState,
    Qualification,
    Stage,
    allowed_from,
)

#: Where each stage sits in the order work moves. Read from the enum rather
#: than written out, so a stage added to the domain cannot be forgotten here
#: and silently sort last.
_STAGE_ORDER: dict[Stage, int] = {stage: index for index, stage in enumerate(Stage)}


class OpenOpportunityRequest(BaseModel):
    """A human deciding an account is worth working, whatever the score says.

    **The route into `Qualification.MANUAL`**, which the domain has modelled
    since M12.1, the brief has rendered as *"somebody here added it"* since
    M12.3, and **nothing could produce** — `QualifyOpportunity` had exactly one
    caller, the buying-score handler, which never names a person
    (49-lead-ownership.md §14, F-3).

    Note what is **not** here, on the same reasoning as a decision: no
    `opened_by`. Who opened it is the verified principal, because an opening
    entry that could name somebody else would let one member sign another's
    name to a commitment.

    And no `account_id` in the body — it is the path, because the account is
    what a seller arrives with.
    """

    model_config = ConfigDict(frozen=True)

    reason: str = Field(
        max_length=512,
        description=(
            "Why this is worth working when Signora did not say so. **Required, and it "
            "is the whole value of a manual opening**: the automatic path records the "
            "score and the policy that qualified it, and a human opening has neither — "
            "the sentence is the only explanation the account will ever carry."
        ),
    )


class OpenedOpportunityResponse(BaseModel):
    """What was opened, enough for a client to navigate to it."""

    model_config = ConfigDict(frozen=True)

    id: UUID = Field(description="The new opportunity.")
    account_id: UUID = Field(description="The company it is about.")
    stage: Stage = Field(
        description=(
            "Always `tracking`. **A human opening an opportunity is still only a "
            "suggestion becoming a record** — taking it on is a separate, deliberate "
            "act, and opening one that arrived already owned would collapse the "
            "distinction the whole module rests on."
        )
    )
    generation: int = Field(
        description=(
            "How many times this account has been opened before. **A reopening is a new "
            "opportunity rather than an edited one**: the deal that closed keeps its "
            "history, its reasons and its outcome, and nothing rewrites them."
        )
    )
    opened_at: datetime = Field(description="When it was opened.")


class RecordDecisionRequest(BaseModel):
    """A human deciding something about an account.

    **The only write in the product surface, and the shape encodes why.**
    Every other endpoint reports what the pipeline computed; this one records
    what a person chose, and *intelligence suggests, humans commit* is what
    makes the two different kinds of fact.

    Note what is **not** here: `actor_id`. Who decided is taken from the
    verified principal on the request, never from the body — a caller able to
    name the actor could sign another member's name to a decision, and the
    workflow history is the one record in Signora that nothing can reproduce
    from evidence if it is wrong.
    """

    model_config = ConfigDict(frozen=True)

    stage: Stage = Field(
        description=(
            "Where this should stand now. Only some changes are legal from where it "
            "stands today — a won deal never reopens, and a stage that changes nothing "
            "is refused rather than recorded as noise in the audit trail."
        )
    )
    reason: str = Field(
        # 512 is the column's own bound, echoed so an over-long reason is a
        # documented 422 naming the field rather than a database error. The
        # *rule* that a reason cannot be blank stays in the domain, which is
        # the one place it is enforced.
        max_length=512,
        description=(
            "Why you decided this, in your words. Required on every change, because "
            "workflow has to explain itself as thoroughly as the intelligence does — "
            "*'someone changed it'* is not an explanation. On a dismissal this is the "
            "only feedback Signora ever gets about its own qualification quality."
        ),
    )
    owner_id: UUID | None = Field(
        default=None,
        description=(
            "Who should hold this account from now on. Null leaves ownership exactly as "
            "it is. Membership is verified server-side on every assignment, so an account "
            "cannot be handed to somebody outside the workspace."
        ),
    )


class AccountAttentionResponse(BaseModel):
    """One account on the attention list — a row a seller decides from."""

    model_config = ConfigDict(frozen=True)

    id: UUID = Field(description="The opportunity. Use this to open the account's full brief.")
    account_id: UUID = Field(
        description=(
            "The company this opportunity is about. Resolve its name from the "
            "accounts endpoint of the Knowledge Graph: no single module may reach both "
            "workflow and entity names, so the two are composed by the caller."
        )
    )

    score: int | None = Field(
        description=(
            "Commercial attention, 0–100. An ordering, not a probability and not a "
            "prediction. Null when the evidence behind it has expired — the opportunity "
            "is still open and the number that justified it is no longer current."
        )
    )
    trend: str | None = Field(
        description="Which way the score last moved: rising, falling, or steady."
    )
    score_change: int | None = Field(
        description=(
            "Signed movement against the previous reading. Distinguishes an account that "
            "has sat at 70 for a month from one that reached 70 last night."
        )
    )
    signal_type: str | None = Field(
        description=(
            "The hypothesis that most explains this score — *active evaluation*, "
            "*expansion opportunity*, *contraction risk*. **Resolve its title from the "
            "signal catalog**: this row carries the key and never the name, because the "
            "module that ranks accounts is forbidden from reaching the one that forms "
            "hypotheses, and a client holding its own translation table would be a second "
            "vocabulary that drifts from the catalog within a release. Null when no score "
            "is live, or when nothing counted toward one."
        )
    )
    contested: bool = Field(
        description=(
            "Whether opposing readings are both live. A contested account is not a less "
            "certain one; it ranks above a quiet account at the same score, because a "
            "fought-over account warrants more attention rather than average attention."
        )
    )

    posture: Posture | None = Field(
        description=(
            "What the leading hypothesis implies commercially — expansionary, contractionary "
            "or neutral. **Null exactly when `signal_type` is null**, since both come from the "
            "live score. Sent so a client never has to map catalog keys to a commercial "
            "meaning: that mapping is the Buying Score Engine's, and a copy here would be a "
            "second vocabulary, wrong the moment the catalog gained a type. **Never a sign in "
            "any arithmetic** — two accounts can score identically and mean opposite things, "
            "which is the whole reason this is carried separately."
        )
    )

    evidence: EvidenceState = Field(
        description=(
            "How the intelligence behind this opportunity is holding up: current, cooling, "
            "or stale. Computed when you ask and never stored, so you can see that an "
            "account went cold without Signora closing it for you."
        )
    )
    stage: Stage = Field(description="Where this sits in your workflow.")
    owner_id: UUID | None = Field(
        description="Who holds this account, or null if nobody has taken it."
    )

    opened_at: datetime = Field(
        description=(
            "When the opportunity was opened. Also half of the pagination keyset, which "
            "is why it appears on the row rather than only inside the cursor."
        )
    )

    since: datetime = Field(
        description=(
            "When this stage and owner were last recorded — how long the account has stood "
            "where it stands. **A fact, never a judgement**: Signora records workflow "
            "decisions and cannot see a call, an email or a meeting, so it must not claim "
            "an account is neglected. It states how long it has been since anything it "
            "*can* see happened, and the reader decides what that means."
        )
    )

    @classmethod
    def from_domain(cls, tracked: TrackedOpportunity) -> "AccountAttentionResponse":
        score = tracked.current_score
        # **The ledger decides which hypothesis leads, not this module.** Asking
        # it is the difference between passing a key through and forming a
        # judgement about intelligence in the module least equipped to review
        # one — which is what its import contract forbids.
        leading = score.ledger.leading() if score else None
        return cls(
            id=tracked.opportunity.id,
            account_id=tracked.opportunity.entity_id,
            score=score.value if score else None,
            trend=score.trend.value if score else None,
            score_change=score.delta if score else None,
            signal_type=leading.signal_type.value if leading else None,
            # Computed on the line above and dropped until now — the same
            # shape as `owner_id` in M12.2 and `signal_type` in M12.3.
            posture=leading.posture if leading else None,
            contested=score.contested if score else False,
            evidence=tracked.evidence_state,
            stage=tracked.state.stage,
            owner_id=tracked.state.owner_id,
            opened_at=tracked.opportunity.created_at,
            # **Already loaded.** `_page` returns the opportunity beside its
            # current state, so this costs no query — the row has been carrying
            # `stage` and `owner_id` off that same state since M12.2 and left
            # *when* behind (LO-06).
            since=tracked.state.occurred_at,
        )


class WorkflowStateResponse(BaseModel):
    """One complete statement of workflow state, as it was recorded."""

    model_config = ConfigDict(frozen=True)

    stage: Stage = Field(description="Where this stood after the change.")
    owner_id: UUID | None = Field(
        description="Who held it at that point, or null if nobody had taken it."
    )
    decided_by: UUID | None = Field(
        description=(
            "The person who made this change. Null only on the opening entry — Signora may "
            "suggest tracking an account and may do nothing else, so that is the one state "
            "with no human behind it."
        )
    )
    reason: str = Field(
        description=(
            "Why it changed. Recorded on every entry, because workflow has to explain itself "
            "as thoroughly as the intelligence does — *'someone changed it'* is not an "
            "explanation."
        )
    )
    occurred_at: datetime = Field(description="When it changed.")

    @classmethod
    def from_domain(cls, state: OpportunityState) -> "WorkflowStateResponse":
        return cls(
            stage=state.stage,
            owner_id=state.owner_id,
            decided_by=state.actor_id,
            reason=state.reason,
            occurred_at=state.occurred_at,
        )


class DecidedAccountResponse(BaseModel):
    """One account somebody finished with, and what they said about it.

    **Four fields, and none of them is a score.** The attention row carries
    seven because a seller is deciding what to work; nobody triages a list of
    decisions. Putting a live score here would invite a reader to re-litigate a
    judgement using a number that moved after they made it — and the account's
    own brief is one click away for anybody who wants exactly that.

    **`reason` is the customer's own words**, and this is the only place in the
    product that shows them back. Every transition has required one since
    M12.3; nothing has ever rendered one.
    """

    model_config = ConfigDict(frozen=True)

    account_id: UUID = Field(description="The account, so the row can open its brief.")
    opportunity_id: UUID = Field(description="The workflow record the decision belongs to.")
    stage: Stage = Field(
        description=(
            "What was decided. **`dismissed` and `closed_lost` are different answers** — one "
            "says Signora should not have surfaced this account, the other says it was worth "
            "pursuing and did not close. A client must not merge them."
        )
    )
    reason: str = Field(description="Why, in the words the person typed.")
    owner_id: UUID | None = Field(
        description=(
            "Who held it when the decision was made, or null if nobody had taken it. Compared "
            "against the reader to say *yours* — the tier verifies tokens without learning "
            "who anybody is, so it can never say a name (**D23**)."
        )
    )
    decided_by: UUID | None = Field(
        description=(
            "**Who decided, which is not the same person as who held it.** An account "
            "nobody ever took on can still be dismissed, and until this field existed that "
            "judgement was unattributable: the row could say *yours* only when the reader "
            "had *held* it. Null only on an opening state, which never reaches this list."
        )
    )
    decided_at: datetime = Field(description="When.")

    @classmethod
    def from_domain(cls, decided: DecidedAccount) -> "DecidedAccountResponse":
        return cls(
            account_id=decided.opportunity.entity_id,
            opportunity_id=decided.opportunity.id,
            stage=decided.state.stage,
            reason=decided.state.reason,
            owner_id=decided.state.owner_id,
            # Already loaded, like `since` on the attention row: the state is
            # read beside the opportunity, and this field was simply left off.
            decided_by=decided.state.actor_id,
            decided_at=decided.state.occurred_at,
        )


class AccountOpportunityResponse(BaseModel):
    """What Signora committed to about this account, and what has happened since.

    **The brief's *then and now*.** Every field is either a fact recorded when
    somebody committed, or the same fact today. A score of 50 means something
    different on an account opened at 20 than on one opened at 60, and the
    attention list cannot show that because it only knows about now.
    """

    model_config = ConfigDict(frozen=True)

    id: UUID = Field(description="The opportunity — Signora's record of a commitment.")
    account_id: UUID = Field(description="The company it is about.")

    stage: Stage = Field(
        description=(
            "Where this sits in your workflow. Only `tracking` can be reached without a "
            "person: Signora suggests, and every stage beyond that names who decided it."
        )
    )
    owner_id: UUID | None = Field(
        description="Who holds this account, or null if nobody has taken it."
    )
    opened_at: datetime = Field(description="When Signora started tracking this account.")
    opened_by: Qualification = Field(
        description=(
            "How it got here — `automatic` if Signora suggested it from the evidence, "
            "`manual` if a person opened it regardless of the score."
        )
    )

    score_at_open: int = Field(
        description=(
            "Commercial attention at the moment of commitment. A **fact about then**, never "
            "a cached copy of the current number — it is what justified opening this, and it "
            "does not change when the score does."
        )
    )
    contested_at_open: bool = Field(
        description=(
            "Whether opposing readings were already live when it opened. Read beside "
            "`contested` on the score: an account that has *become* contested is a different "
            "situation from one that always was."
        )
    )

    score: int | None = Field(
        description=(
            "Commercial attention now. Null when no score is live — the opportunity outlives "
            "the score that created it, so a commitment stays open after its justification "
            "expires."
        )
    )
    score_change_since_open: int | None = Field(
        description=(
            "Signed movement since the commitment was made. **The one number the attention "
            "list cannot show you**, because it only knows about today. Null rather than "
            "zero when no score is live: zero is a reading that has not moved."
        )
    )
    evidence: EvidenceState = Field(
        description=(
            "How the intelligence behind this commitment is holding up: current, cooling, or "
            "stale. Computed when you ask and never stored, so an account can go cold without "
            "Signora closing it for you."
        )
    )

    history: tuple[WorkflowStateResponse, ...] = Field(
        description=(
            "Every workflow state in order, oldest first. Append-only and never rewritten — "
            "the status *is* the audit trail rather than something kept beside it, so the two "
            "cannot disagree."
        )
    )

    allowed_next: tuple[Stage, ...] = Field(
        description=(
            "Which stages this may legally become from where it stands. **Sent rather than "
            "inferred**: the rules are the domain's, and a client that reimplemented them "
            "would be a second copy of them, wrong the moment either changed. Empty on a won "
            "deal, which does not reopen — the next deal at that account is genuinely a new "
            "opportunity. A client offers exactly these and the server still refuses anything "
            "else, because a list a caller can ignore is not enforcement."
        )
    )

    @classmethod
    def from_domain(cls, brief: OpportunityBrief) -> "AccountOpportunityResponse":
        return cls(
            id=brief.opportunity.id,
            account_id=brief.opportunity.entity_id,
            stage=brief.state.stage,
            owner_id=brief.state.owner_id,
            opened_at=brief.opportunity.created_at,
            opened_by=brief.opportunity.qualification,
            score_at_open=brief.opportunity.score_at_creation,
            contested_at_open=brief.opportunity.contested_at_creation,
            score=brief.current_score.value if brief.current_score else None,
            score_change_since_open=brief.score_change_since_open,
            evidence=brief.evidence_state,
            history=tuple(WorkflowStateResponse.from_domain(s) for s in brief.history),
            # **Ordered by the `Stage` enum's own declaration**, which runs
            # tracking → engaged → won → lost → dismissed: the order work
            # actually moves in. Two things at once — the same position always
            # produces the same wire bytes (`allowed_from` returns a frozenset,
            # whose iteration order would otherwise be a hidden input), and a
            # client rendering them in order leads with the move a seller
            # usually wants. Sorting alphabetically did the first and put
            # *"Lost"* ahead of *"I'm working this"*.
            allowed_next=tuple(
                sorted(allowed_from(brief.state.stage), key=lambda s: _STAGE_ORDER[s])
            ),
        )


__all__ = [
    "AccountAttentionResponse",
    "AccountOpportunityResponse",
    "DecidedAccountResponse",
    "OpenOpportunityRequest",
    "OpenedOpportunityResponse",
    "RecordDecisionRequest",
    "WorkflowStateResponse",
]
