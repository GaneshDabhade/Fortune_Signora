"""What the company is pushing right now.

**The fourth declaration.** The catalog says what a customer sells, the ideal
customer says who buys it, the committee says who has to agree — and this says
*which of it matters at the moment*. A seller's answer to *"what are you
working on this quarter?"*, recorded in their own words.

### Why it is not called a priority

The roadmap and [ADR-0035](../../../../docs/architecture/adr/0035-commercial-profile.md)
name this capability **business priorities**, and *"a priority is a ranking of
these"*. The aggregate is deliberately **not** modelled that way, for a reason
the module's own guard states out loud: `tests/commercial_profile/
test_boundary.py` refuses any domain identifier containing `priority` or
`rank`, because an ordinal in the head of the pipeline is one consumer away
from a weight in a score.

**Exempting the one place the temptation is strongest would be a guard that
has stopped guarding.** So there is no rank, no ordinal, and no position: a
product is in focus or it is not. That is also what a seller actually says —
*"we're pushing Revenue Cloud this quarter"*, not *"Revenue Cloud is priority
two"*.

### It states intent; it applies it to nothing

Nothing here decides what a focus *means*. It does not weight a score, rank an
account, filter a list or change which signals matter. A consumer may one day
read it and do those things; this module records that the customer said it,
and the date, and who.

**Signal relevance is a different question and a different module.** *"Funding
rounds matter more to us than hiring"* is the Signal Engine's `signal_profile`
— what Signora should treat as interesting. *"We're pushing Revenue Cloud"* is
this: what the customer is selling right now. The two are easy to confuse and
must not merge; see the module design document.

### Why there is no period

A focus records what is true now, and *when the customer last said so* is
already stored — every declaration carries `created_at` and its author. A
customer-typed *"Q3 2026"* would be a second representation of the same fact,
free to disagree with the first. **Trigger for adding one: a customer who
needs to declare next quarter's focus before the quarter starts**, which is a
different fact and would deserve its own field.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from modules.commercial_profile.domain.declaration import CommercialProfileError

MAX_OBJECTIVE = 1024


class CommercialFocusError(CommercialProfileError):
    """A focus cannot be recorded as stated."""


@dataclass(frozen=True, slots=True)
class CommercialFocus:
    """What the workspace is pushing, as declared at one moment.

    Immutable and versioned as a whole, on the terms every declaration here
    shares: a revision is a new row naming the one it replaces, and the
    database agrees — there is no `UPDATE` grant on the table.

    **Versioned separately from the other three**, and this one changes
    fastest: a catalog moves quarterly, an ideal customer rarely, and a focus
    every planning cycle. Folding it into any of them would fill their audit
    histories with somebody else's changes.
    """

    id: UUID
    workspace_id: UUID
    version: int
    #: The products being pushed. **In the customer's arrangement, carrying no
    #: rank** — the same rule as the ideal customer's criteria and the
    #: committee's roles. A product is in focus or it is not.
    products: tuple[UUID, ...]
    #: What they are trying to do, in their words — *"land three health
    #: systems"*. Read by a colleague, never parsed.
    objective: str
    created_at: datetime
    #: Who said so. A commercial declaration is a decision, and a customer is
    #: entitled to know whose.
    created_by: UUID
    supersedes: UUID | None = None

    def __post_init__(self) -> None:
        if self.version < 1:
            raise CommercialFocusError("a stored declaration is at version 1 or above.")
        if len(set(self.products)) != len(self.products):
            raise CommercialFocusError(
                "the same product is in focus twice. Saying it louder is not a second statement."
            )
        if len(self.objective) > MAX_OBJECTIVE:
            raise CommercialFocusError(f"an objective is limited to {MAX_OBJECTIVE} characters.")

    # **An empty focus is legal, and this is the one place that differs from
    # the ideal customer.** There, an entry with nothing in it was refused,
    # because an entry that says nothing is indistinguishable from leaving the
    # product out — and leaving it out was always available. Here the
    # aggregate *is* the statement, so there is nothing to leave out: an empty
    # focus is how a customer says *"we are not pushing anything in
    # particular"*, and it has an author and a moment, which is exactly what
    # makes it different from never having said anything.

    def revise(
        self,
        products: tuple[UUID, ...],
        objective: str,
        *,
        id: UUID,
        by: UUID,
        now: datetime,
    ) -> CommercialFocus:
        """The next version of this focus.

        Validation happens in the new declaration's own construction, so an
        invalid revision never exists — not even briefly, and not in a
        variable somebody might go on to save.
        """
        return CommercialFocus(
            id=id,
            workspace_id=self.workspace_id,
            version=self.version + 1,
            products=products,
            objective=objective,
            created_at=now,
            created_by=by,
            supersedes=self.id,
        )


def first_focus(
    workspace_id: UUID,
    products: tuple[UUID, ...],
    objective: str,
    *,
    id: UUID,
    by: UUID,
    now: datetime,
) -> CommercialFocus:
    """The first focus a workspace declares.

    Separate from `revise` because there is nothing to supersede, and a
    `supersedes=None` branch inside `revise` would be a second meaning for one
    method — *"replace that"* and *"there was nothing"* are different
    statements about the past.
    """
    return CommercialFocus(
        id=id,
        workspace_id=workspace_id,
        version=1,
        products=products,
        objective=objective,
        created_at=now,
        created_by=by,
        supersedes=None,
    )
