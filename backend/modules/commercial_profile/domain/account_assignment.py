"""Who owns an account, and who looks after it.

**[ADR-0411](../../../../docs/architecture/adr/0411-customer-organized-account-metadata.md).**

**Customer-organized account metadata, and the first of the three this module
did not already hold.** Tags shipped with [TASK-466](../../../../docs/BACKLOG.md);
this is Account Owner and CSM.

### ⛔ A reference to a member, never a name

📁 **The ruling's own words**: *"A reference to a workspace **member**, not free
text. A person who leaves must not leave a dangling string — the reference is
what makes removal answerable."*

⚡ **So the value stored is a `user_id`**, and *"who owns this account?"* is a
question that stays answerable when somebody leaves, because the membership is
still the thing being pointed at. **A typed name would have been a string that
outlived the person and told nobody.**

### ⚠️ Why a row per role rather than two columns on the account

**Both refuse a second owner.** The row shape is chosen for what it does to the
**inverse**.

📁 **ADR-0405**:
*an action is approved before it is effective*, and **the consuming domain owns
performing the operation and implementing the inverse.** Assigning an owner
across a selection is exactly that kind of operation, and **the inverse of
*"set the owner on these forty accounts"* is *"restore what each one had"***
— which needs the previous value per account, not a nullable column.

✅ **`Reassignment` carries it**, the same shape `TagApplication.changed`
carries one aggregate over: **the inverse operates on what actually moved**,
never on what was requested.

### ⛔ What this deliberately is not

**Not a permission.** 📁 ADR-0411 §4 leaves field-level permissions explicitly
unresolved and [ADR-0410](../../../../docs/architecture/adr/0410-authorization-capability-layer.md)
owns them. **Owning an account grants nothing** — it records who is
responsible, and Casbin decides who may act.

**Not a `ClaimAttribute`.** 📁 ADR-0411 §1: *"nobody asserted a customer's own
tag"*, and nobody asserted its owner either. **A claim records what a provider
said; this records what the customer decided**, and merging them would make
the provenance of every claim ambiguous.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from uuid import UUID


class AssignmentError(ValueError):
    """An assignment could not be described the way this module requires."""


class AccountRole(StrEnum):
    """The two roles ADR-0411 names.

    ⛔ **Closed, and not because a third is unimaginable.** The ruling's scope
    line is *"Those three. Nothing else"*, and a role nobody has approved
    arriving through a string would be scope entering by the back door.
    """

    OWNER = "owner"
    """**Commercially responsible for the account.** What Companies draws."""

    CSM = "csm"
    """**Responsible for the customer after they buy.** Account 360 draws both,
    and they are frequently different people — which is the whole reason the
    ruling names two."""


@dataclass(frozen=True, slots=True)
class AccountAssignment:
    """One member, holding one role, on one account.

    **`(workspace_id, account_id, role)` is the identity**, so a second owner
    is unrepresentable rather than merely discouraged — 📁 [§2](../../../../CLAUDE.md),
    *prefer a violation that cannot be constructed.*
    """

    workspace_id: UUID
    #: The account as the Knowledge Graph knows it. ⛔ **Carried, never
    #: constrained** — a foreign key here would make this module's migration
    #: depend on another bounded context's table shape, the same reasoning
    #: `people`'s `company_id` records.
    account_id: UUID
    role: AccountRole
    #: The member. ⚡ **A `user_id`, verified against
    #: `WorkspaceQueryPort.get_membership` before it is stored** — the
    #: application layer does that, because a domain object that reached for a
    #: port would be an infrastructure dependency pointing outward.
    member_user_id: UUID


@dataclass(frozen=True, slots=True)
class Reassignment:
    """What a bulk assignment actually changed, and what undoes it.

    ⚠️ **`previous` is the whole point.** Unassigning is not the inverse of
    assigning: an account that already had an owner must get **that owner**
    back, not nothing. 📁 The same distinction `TagApplication` draws between
    `requested` and `changed`, and it is the half that is normally missing.
    """

    role: AccountRole
    #: **Who this reassignment put there.** ⚡ **Required for the reversal to be
    #: conditional rather than destructive**: an undo must only undo *its own*
    #: change, so it compares before it writes.
    #:
    #: 🔴 **Added after three failing tests, from QE's hypotheses.** Without it
    #: `restore` overwrote whatever it found — **a lost update wearing an
    #: undo's clothes**: the batch set an owner, a colleague chose a different
    #: one, and *take it back* silently discarded their decision.
    assigned_to: UUID | None = None
    #: Accounts whose holder actually moved, with who held it before —
    #: `None` where nobody did.
    previous: tuple[tuple[UUID, UUID | None], ...] = ()
    #: Accounts already held by the requested member. ⛔ **Not reversed**, because
    #: nothing about them changed.
    unchanged: tuple[UUID, ...] = ()

    def __post_init__(self) -> None:
        moved = {account for account, _ in self.previous}
        overlap = moved & set(self.unchanged)
        if overlap:
            raise AssignmentError(
                f"{sorted(str(account) for account in overlap)} are recorded as both "
                "changed and unchanged. An account is one or the other, and a reversal "
                "built from both would restore an owner that never moved."
            )

    def inverse(self) -> tuple[tuple[UUID, UUID | None], ...]:
        """**What to write to undo this**, per account.

        ⛔ **`previous`, never `unchanged`** — reversing an account that did not
        move would take an owner away from somebody who always had one, which
        is a change the customer never asked for and would not be able to
        explain.

        ⚠️ **This says what to restore, never that it is still safe to.** The
        condition is `assigned_to`, and it is the repository's to apply —
        **an undo that does not check has undone somebody else's work.**
        """
        return self.previous


@dataclass(frozen=True, slots=True)
class AssignmentBatch:
    """A bulk owner change, and what it did — if it has run.

    **Three states of `moved`, and a consumer can tell them apart:**

    | | |
    |---|---|
    | `None` | **Not applied.** Nothing to reverse |
    | empty `previous` | **Applied**, and every account already had that member |
    | populated | **Applied**, and the reversal restores exactly these |

    ⛔ **`None` and *"applied and moved nobody"* are different answers**, and
    only the first is still waiting for somebody to approve it.
    """

    batch_id: UUID
    role: AccountRole
    member_user_id: UUID
    requested: tuple[UUID, ...]
    moved: Reassignment | None = None

    def to_reverse(self) -> tuple[tuple[UUID, UUID | None], ...]:
        """**What the reversal writes** — nothing at all if it never applied."""
        return () if self.moved is None else self.moved.inverse()


__all__ = [
    "AccountAssignment",
    "AssignmentBatch",
    "AccountRole",
    "AssignmentError",
    "Reassignment",
]
