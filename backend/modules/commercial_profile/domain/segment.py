"""An ICP as a thing a customer can name, open, copy and retire.

**The aggregate [ADR-0041](../../../../docs/architecture/adr/0041-icp-aggregate.md)
ratified, and it reuses rather than replaces.** `EmployeeRange`, the criteria
validation and `IcpError` all come from `icp.py` unchanged — they were right,
and nothing about giving an ICP an identity makes them less right.

### What changed, and only this

An ICP used to be a `ProductIcp` inside one workspace-wide `IcpDeclaration`:
addressed by `product_id`, one per product, with no id, no name and no state.
**It is now addressed by its own id**, which is what every verb a customer
asked for needs — duplicate, archive, restore, compare, per-ICP history.

### Three rules the shape enforces

**A draft is not a version.** A version is something the customer intentionally
published; a draft is what they typed. Discarding a draft leaves no trace,
because nothing was ever said. This is what lets AI proposals, collaborative
editing and approval workflows be operations on drafts without polluting an
immutable chain.

**Execution invariants bind at publication, not at creation.** A draft may name
no product; a published ICP may not. The gate asks *"can the platform act on
this?"* and never *"is this a good segment?"* — the same rule the Prompt
Registry applies when it refuses to release an unevaluated prompt.

**Products are a relationship, not identity.** *"Mid-market fintech in the US,
100–1000 employees"* is a complete description of a segment without naming
anything sold, which is why one ICP may name several products and why the
requirement is about actionability rather than meaning.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from uuid import UUID

from modules.commercial_profile.domain.icp import (
    MAX_NOTES,
    EmployeeRange,
    IcpError,
    validate_criterion_list,
)

#: What a customer calls a segment. Long enough for "Mid-market financial
#: services", short enough that a paragraph is obviously the wrong field.
MAX_NAME = 80
#: A typo guard rather than a business rule. The real bound is the catalog:
#: every product named must be one the workspace currently sells.
MAX_PRODUCTS = 64


class SegmentState(StrEnum):
    """Where an ICP is in its life.

    **Derived from the latest transition, never stored.** A mutable column
    would answer *"is it archived?"* and lose *"who archived it, and when?"* —
    which is the question asked during exactly the conversation where it
    matters.
    """

    #: Created, never published. May be incomplete.
    DRAFT = "draft"
    #: In force. Signora may act on it.
    PUBLISHED = "published"
    #: Retired by the customer. Reversible, and its content is untouched.
    ARCHIVED = "archived"


class SegmentTransitionError(IcpError):
    """A lifecycle move the aggregate does not permit."""


#: The transitions an ICP may make. A table rather than branches: adding a
#: state is a row, and an illegal move is refused by construction rather than
#: by whichever `if` happened to be written.
_ALLOWED: dict[SegmentState, frozenset[SegmentState]] = {
    SegmentState.DRAFT: frozenset({SegmentState.PUBLISHED}),
    # Publishing again is a new version, not a transition — the state does not
    # move. Archiving is the only thing that leaves `PUBLISHED`.
    SegmentState.PUBLISHED: frozenset({SegmentState.ARCHIVED}),
    SegmentState.ARCHIVED: frozenset({SegmentState.PUBLISHED}),
}


@dataclass(frozen=True, slots=True)
class SegmentCriteria:
    """What the customer said about who buys.

    **Identical in substance to `ProductIcp` minus the product**, which is now
    a relationship on the version rather than a field here. The validation is
    the same function, so a rule fixed in one place stays fixed in both.
    """

    industries: tuple[str, ...] = ()
    countries: tuple[str, ...] = ()
    employees: EmployeeRange | None = None
    notes: str = ""

    def __post_init__(self) -> None:
        validate_criterion_list(self.industries, what="industry")
        validate_criterion_list(self.countries, what="country")
        if len(self.notes) > MAX_NOTES:
            raise IcpError(f"a note about an ideal customer is limited to {MAX_NOTES} characters.")

    @property
    def describes_nobody_in_particular(self) -> bool:
        """Whether this would fit every company on earth.

        **A question, not a refusal.** A draft is allowed to be empty; only
        publication requires it to say something, and even then the rule is
        that it must say *something*, never that the something must be narrow.
        Refusing a broad segment would be this module judging the customer's
        business.
        """
        return not self.industries and not self.countries and self.employees is None


@dataclass(frozen=True, slots=True)
class SegmentVersion:
    """One published statement about a segment. Immutable, always.

    **Never a draft.** Every row here is something a customer decided to
    publish, which is what makes the chain worth citing — and what lets a
    discarded draft cost nothing.
    """

    id: UUID
    segment_id: UUID
    workspace_id: UUID
    version: int
    name: str
    criteria: SegmentCriteria
    #: Products this segment buys, from the workspace's catalog. **Versioned
    #: with the content**, so *"we added CPQ to this segment in March"* is
    #: recoverable rather than inferred.
    product_ids: tuple[UUID, ...]
    created_at: datetime
    created_by: UUID
    supersedes: UUID | None = None

    def __post_init__(self) -> None:
        if self.version < 1:
            raise IcpError("a published version is at version 1 or above.")
        _validate_name(self.name)
        if not self.product_ids:
            # The publication gate, expressed where it cannot be skipped.
            raise IcpError(
                "say which product or products this segment buys. Signora looks for "
                "companies that will buy something you sell, so a published segment "
                "that names nothing cannot be acted on."
            )
        if len(self.product_ids) > MAX_PRODUCTS:
            raise IcpError(f"a segment is limited to {MAX_PRODUCTS} products.")
        if len(set(self.product_ids)) != len(self.product_ids):
            raise IcpError("the same product is listed twice.")
        if self.criteria.describes_nobody_in_particular:
            raise IcpError(
                "say at least one thing about who buys this. A description with no "
                "criteria would fit every company on earth."
            )


@dataclass(frozen=True, slots=True)
class Segment:
    """A named customer segment — the thing a customer opens and manages.

    **Identity only.** Content lives in versions and lifecycle lives in
    transitions, so this row never changes after it is written. That is what
    makes a citation from an opportunity or a signal resolvable forever, no
    matter how many times the description is revised.
    """

    id: UUID
    workspace_id: UUID
    created_at: datetime
    created_by: UUID


@dataclass(frozen=True, slots=True)
class SegmentTransition:
    """One lifecycle move, and who made it.

    Append-only, each row a **complete** statement of state rather than a
    delta — the shape `opportunity_state` already uses, so the status *is* the
    audit log rather than something kept beside it.
    """

    id: UUID
    segment_id: UUID
    workspace_id: UUID
    sequence: int
    state: SegmentState
    occurred_at: datetime
    actor_id: UUID

    def __post_init__(self) -> None:
        if self.sequence < 0:
            raise IcpError("a transition sequence starts at 0.")


def _validate_name(name: str) -> None:
    if not name.strip():
        raise IcpError("give this segment a name you would recognise in a list.")
    if len(name) > MAX_NAME:
        raise IcpError(f"a segment name is limited to {MAX_NAME} characters.")


def next_state(
    current: SegmentState,
    to: SegmentState,
    *,
    at: datetime,
    by: UUID,
    segment_id: UUID,
    workspace_id: UUID,
    sequence: int,
    id: UUID,
) -> SegmentTransition:
    """The next lifecycle row, refusing a move the table does not allow.

    **`by` has no default**, on the rule the Opportunity Engine already
    follows: a state change nobody is attributable for is one nobody can
    explain, and a default would quietly attribute every one to the platform.
    """
    if to not in _ALLOWED[current]:
        raise SegmentTransitionError(f"a segment cannot move from {current.value} to {to.value}.")
    return SegmentTransition(
        id=id,
        segment_id=segment_id,
        workspace_id=workspace_id,
        sequence=sequence,
        state=to,
        occurred_at=at,
        actor_id=by,
    )
