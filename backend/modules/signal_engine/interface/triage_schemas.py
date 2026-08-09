"""HTTP schemas for the Signal Center — the queue, and leaving it.

**A separate file from `schemas.py`, deliberately.** That one is the validation
surface: *what should I check before acting on this?* This one is triage: *have
I dealt with it?* Two screens, and a shared module would make the first
router import the request body of a write it never performs.

**Read schemas only, and that is a boundary rather than a stopping point.**
Recording a decision needs an authorization tuple this platform does not have —
every write surface in the repository carries its own `Resource`, and there is
no `signal` one. Adding it touches `signora_platform/`, which the Change Budget
puts at 🔴. **[C-224](../../../../docs/LANE_COORDINATION.md) carries the
request and the proposed request bodies**; they are deliberately not defined
here, because a schema no route can reach is a contract nobody agreed to.
"""

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from modules.signal_engine.application.triage import QueueState, TriagedSignal
from modules.signal_engine.domain.resolution import (
    MAX_REASON,
    Actioned,
    Assigned,
    DismissalReason,
    Dismissed,
    Outcome,
    Resolution,
    Snoozed,
)


class ResolutionResponse(BaseModel):
    """A decision, as recorded."""

    model_config = ConfigDict(frozen=True)

    id: UUID = Field(description="This decision. Cite it to correct it.")
    signal_id: UUID = Field(description="The hypothesis it is about.")
    outcome: str = Field(description="One of: actioned, assigned, snoozed, dismissed.")
    assigned_to: UUID | None = Field(
        default=None, description="Who it went to. Present only on an assignment."
    )
    snoozed_until: datetime | None = Field(
        default=None, description="When it comes back. Present only on a snooze."
    )
    reason: str | None = Field(
        default=None,
        description="Why it should not have been raised. Present only on a dismissal.",
    )
    actor_id: UUID = Field(
        description=(
            "Who decided. **Never Signora** — every outcome here is a human judgement, and "
            "a machine-authored one would be the platform marking its own work."
        )
    )
    recorded_at: datetime = Field(description="When they decided.")
    supersedes: UUID | None = Field(
        default=None,
        description=(
            "The decision this replaces, if it is a correction. **Nothing is deleted**: the "
            "earlier record stays readable, so a dismissal somebody regretted cannot quietly "
            "cease to exist."
        ),
    )

    @classmethod
    def from_domain(cls, resolution: Resolution) -> "ResolutionResponse":
        outcome = resolution.outcome
        return cls(
            id=resolution.id,
            signal_id=resolution.signal_id,
            outcome=_name_of(outcome),
            assigned_to=outcome.to if isinstance(outcome, Assigned) else None,
            snoozed_until=outcome.until if isinstance(outcome, Snoozed) else None,
            reason=outcome.reason.text if isinstance(outcome, Dismissed) else None,
            actor_id=resolution.actor_id,
            recorded_at=resolution.recorded_at,
            supersedes=resolution.supersedes,
        )


class QueueEntryResponse(BaseModel):
    """One hypothesis and where it stands."""

    model_config = ConfigDict(frozen=True)

    signal_id: UUID = Field(
        description=(
            "The hypothesis. The same identifier the validation surface and the score's "
            "ledger cite, so the three join without a second lookup."
        )
    )
    signal_type: str = Field(
        description=(
            "Which kind of hypothesis. **A key, not a name** — the name is resolved by the "
            "signal catalog, which is the one place a type is named."
        )
    )
    entity_id: UUID = Field(
        description=(
            "Which account this is about. Redundant on the per-account read and "
            "load-bearing on the workspace queue, where an entry that cannot say which "
            "company it concerns is one nobody can act on. The name is resolved through "
            "the identity batch, as everywhere else."
        )
    )
    rationale: str = Field(
        description=(
            "Why this matters *here*, and what it rests on — the two halves the domain "
            "keeps together so the interpretation a customer reads and the evidence an "
            "auditor checks cannot diverge. **Per signal, not per type**: the catalog's "
            "`why_it_matters` is a fact about the TYPE, true before any account exhibits "
            "it, so rendering that as the summary would put the same sentence under every "
            "row and be wrong on all of them."
        )
    )
    state: QueueState = Field(
        description=(
            "open, snoozed, or closed. **Derived from the decision and the current time, "
            "never stored** — which is exactly why a snoozed signal comes back on its own: "
            "the clock moved, and nothing had to run."
        )
    )
    resolution: ResolutionResponse | None = Field(
        default=None,
        description=(
            "The decision in force, or absent when nobody has made one. **Absent means "
            "still open and is not a decision to do nothing** — that is what `actioned` is "
            "for, and conflating them would lose the difference between work somebody "
            "finished and work nobody has looked at."
        ),
    )

    @classmethod
    def from_domain(cls, entry: TriagedSignal) -> "QueueEntryResponse":
        return cls(
            signal_id=entry.signal.id,
            signal_type=entry.signal.signal_type.value,
            entity_id=entry.signal.entity_id,
            rationale=entry.signal.rationale,
            state=entry.state,
            resolution=(
                ResolutionResponse.from_domain(entry.resolution)
                if entry.resolution is not None
                else None
            ),
        )


class QueueResponse(BaseModel):
    """The triage queue for one account."""

    model_config = ConfigDict(frozen=True)

    account_id: UUID
    entries: tuple[QueueEntryResponse, ...] = Field(
        description=(
            "Live hypotheses about this account with their decisions. Empty is an answer — "
            "an account nothing is currently believed about has nothing to triage, which is "
            "not an error."
        )
    )


class ResolutionHistoryResponse(BaseModel):
    """Everything ever decided about one hypothesis."""

    model_config = ConfigDict(frozen=True)

    signal_id: UUID
    decisions: tuple[ResolutionResponse, ...] = Field(
        description=(
            "Oldest first. **Nothing is deleted: every resolution is auditable** — a "
            "dismissal that was later actioned is still here, and so is the reason given "
            "for it at the time."
        )
    )


def _name_of(outcome: Outcome) -> str:
    """**Exhaustive by construction.** `Outcome` is a closed union, so `mypy`
    refuses this function if a fifth member is added without a branch here."""
    match outcome:
        case Actioned():
            return "actioned"
        case Assigned():
            return "assigned"
        case Snoozed():
            return "snoozed"
        case Dismissed():
            return "dismissed"


__all__ = [
    "QueueEntryResponse",
    "QueueResponse",
    "ResolutionHistoryResponse",
    "ResolutionResponse",
]


class ActionedRequest(BaseModel):
    """*"I dealt with it."* **Carries nothing**, because what was done happens
    in a CRM, a call or an inbox — none of which Signora can see."""

    model_config = ConfigDict(frozen=True)
    kind: Literal["actioned"]

    def to_domain(self) -> Outcome:
        return Actioned()


class AssignedRequest(BaseModel):
    """*"Somebody else owns this now."* **Routing, not resolving** — the signal
    stays open, because a queue that treated handing over as an ending would
    lose every signal passed to a colleague."""

    model_config = ConfigDict(frozen=True)
    kind: Literal["assigned"]
    to: UUID = Field(description="The member the decision now belongs to.")

    def to_domain(self) -> Outcome:
        return Assigned(to=self.to)


class SnoozedRequest(BaseModel):
    """*"Not now, but not wrong."* The signal returns at the stated time with
    its original evidence intact — because nothing about it is touched."""

    model_config = ConfigDict(frozen=True)
    kind: Literal["snoozed"]
    until: datetime = Field(
        description=(
            "When it should come back. Must be in the future and carry a timezone — "
            "a snooze that has already elapsed would return the signal immediately."
        )
    )

    def to_domain(self) -> Outcome:
        return Snoozed(until=self.until)


class DismissedRequest(BaseModel):
    """*"We should not have been shown this."* **The only outcome that says
    Signora was wrong**, and the reason is what a rule can later learn from."""

    model_config = ConfigDict(frozen=True)
    kind: Literal["dismissed"]
    reason: str = Field(
        min_length=1,
        max_length=MAX_REASON,
        description=(
            "Why this signal should not have been raised, in your own words. "
            "Required: a dismissal with no reason is indistinguishable from one "
            "nobody explained."
        ),
    )

    def to_domain(self) -> Outcome:
        return Dismissed(reason=DismissalReason(self.reason))


class ResolveSignalRequest(BaseModel):
    """What a person decided about a signal.

    **The outcome is a discriminated union, not a string plus optional
    fields.** `outcome: "dismissed"` with `reason: null` would be a request the
    schema accepts and the domain refuses — and *"a dismissal cannot be
    recorded without a reason"* is the acceptance criterion. Four shapes, each
    carrying exactly what its outcome needs, make the omission a `422` at the
    edge instead of an exception behind it (§2, *types should make incorrect
    architecture impossible*).

    ⛔ **No `actor_id`.** The person is the verified principal on the request;
    a body able to name its own actor could sign somebody else's name to a
    decision that outlives them.
    """

    model_config = ConfigDict(frozen=True)

    outcome: ActionedRequest | AssignedRequest | SnoozedRequest | DismissedRequest = Field(
        discriminator="kind"
    )

    def to_domain(self) -> Outcome:
        return self.outcome.to_domain()
