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
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from modules.signal_engine.application.triage import QueueState, TriagedSignal
from modules.signal_engine.domain.resolution import (
    Actioned,
    Assigned,
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
