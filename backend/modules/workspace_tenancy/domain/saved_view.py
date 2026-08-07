"""The Saved View aggregate — **a question somebody wrote down**.

**TASK-450, [455 §4](../../../../docs/architecture/455-context-definitions-r02-r03.md)
slice 2.** [TASK-449](../../../../docs/BACKLOG.md) published the contract in
`public/saved_views.py` and deliberately nothing else. This is the aggregate
behind it and the rules that make its versioning true in code rather than in a
docstring.

### The one thing this aggregate must never learn

⛔ **What is inside a declaration.** [D-091](../../../../docs/DECISION_REGISTER.md):
*"The storage layer never interprets the saved declaration itself. Its
responsibility is persistence and retrieval, not execution."*

**So there is no validation of the declaration's contents here, and its
absence is the design.** A `SavedView` that could call a declaration *invalid*
would need to know what a filter is, and `workspace_tenancy` would then own
another module's semantics — the boundary `commercial_profile` keeps by never
reading the pipeline. ⚡ **The only rule this aggregate enforces about the
declaration is that there is one**: an empty mapping is a view that asks
nothing, and a name pointing at no question is the one shape that cannot be
retrieved usefully by anybody.

### Versioning is a chain, and `live` is derived from it

**A declaration is never edited.** A change is `revise()`, which mints a new
identity naming the one it replaces, and the old row stays readable — because
a colleague who acted on *"my accounts, contested first"* last week needs that
to still mean what it meant.

⚠️ **There is no `is_live` flag, and that is load-bearing.** The public
contract states it: *"Live is derived, never stored. A boolean column beside
the supersession chain would be a second representation of one fact, and the
two would disagree the first time a version landed"* — [§2](../../../../CLAUDE.md),
truth has exactly one authoritative representation. **`superseded_by` is not
stored either**, for the same reason: the chain is discoverable from
`supersedes`, and storing both directions is storing one fact twice.

### Retirement is not deletion

A retired view stops being offered and stays readable, because **a view that
explained a decision must still explain it afterwards**. Retiring is
idempotent in the sense that matters — retiring twice is a caller error, not a
silent overwrite of the first timestamp, since the first is the one that
happened.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import UTC, datetime
from typing import Any
from uuid import UUID, uuid4

from modules.workspace_tenancy.domain.exceptions import (
    EmptyDeclarationError,
    InvalidSavedViewNameError,
    SavedViewAlreadyRetiredError,
)

#: Long enough for a sentence a person would actually type, and bounded so a
#: name cannot become the declaration by other means.
MAX_SAVED_VIEW_NAME_LENGTH = 200


@dataclass(frozen=True, slots=True)
class SavedView:
    """One version of one saved view.

    **Frozen**, so a caller cannot edit a declaration by reaching through the
    aggregate — the immutability the public contract promises is the type's
    rather than a convention the repository has to remember.
    """

    id: UUID
    workspace_id: UUID
    name: str
    declaration: dict[str, Any]
    created_by: UUID
    created_at: datetime
    supersedes: UUID | None = None
    retired_at: datetime | None = None

    @classmethod
    def declare(
        cls,
        *,
        workspace_id: UUID,
        name: str,
        declaration: dict[str, Any],
        created_by: UUID,
        now: datetime | None = None,
        saved_view_id: UUID | None = None,
    ) -> SavedView:
        """The first version of a view.

        **The caller may supply the identity**, as `TargetAccount` does, so a
        retry is idempotent and a rename is distinguishable from a
        remove-and-re-add.
        """
        return cls(
            id=saved_view_id or uuid4(),
            workspace_id=workspace_id,
            name=checked_name(name),
            declaration=checked_declaration(declaration),
            created_by=created_by,
            created_at=now or datetime.now(UTC),
            supersedes=None,
        )

    def revise(
        self,
        *,
        name: str | None = None,
        declaration: dict[str, Any] | None = None,
        created_by: UUID,
        now: datetime | None = None,
        saved_view_id: UUID | None = None,
    ) -> SavedView:
        """A new version replacing this one, naming it.

        ⚡ **The author is required rather than carried forward.** A revision
        is an act with its own actor: inheriting `created_by` would attribute
        somebody else's edit to whoever wrote the first version, which is the
        attribution defect [§10](../../../../CLAUDE.md) names — *"an error must
        never name a component that was not involved"*, applied to people.

        ⛔ **A retired view is not revised.** Reviving it would make the
        retirement reversible without saying so, and the honest way back is a
        new declaration.
        """
        if self.retired_at is not None:
            raise SavedViewAlreadyRetiredError(self.id)

        return SavedView(
            id=saved_view_id or uuid4(),
            workspace_id=self.workspace_id,
            name=checked_name(self.name if name is None else name),
            declaration=checked_declaration(
                self.declaration if declaration is None else declaration
            ),
            created_by=created_by,
            created_at=now or datetime.now(UTC),
            supersedes=self.id,
        )

    def retire(self, *, at: datetime | None = None) -> SavedView:
        """Stop offering it, without removing what it explained.

        **Retiring an already-retired view raises rather than re-stamping.**
        The first timestamp is the one that happened, and overwriting it would
        quietly move a fact about the past.
        """
        if self.retired_at is not None:
            raise SavedViewAlreadyRetiredError(self.id)
        return replace(self, retired_at=at or datetime.now(UTC))

    @property
    def is_retired(self) -> bool:
        """⚡ **Derived, and there is no column behind it.** The timestamp is
        the fact; a boolean beside it would be the same fact twice."""
        return self.retired_at is not None


def checked_name(name: str) -> str:
    """A name the customer would recognise, and never one derived from the
    declaration — *"a view named by its filters would rename itself when they
    changed"* (`public/saved_views.py`)."""
    stripped = name.strip()
    if not stripped:
        raise InvalidSavedViewNameError("a saved view needs a name somebody chose")
    if len(stripped) > MAX_SAVED_VIEW_NAME_LENGTH:
        raise InvalidSavedViewNameError(
            f"a saved view name is at most {MAX_SAVED_VIEW_NAME_LENGTH} characters"
        )
    return stripped


def checked_declaration(declaration: dict[str, Any]) -> dict[str, Any]:
    """⛔ **The only check, and deliberately the weakest one possible.**

    That the declaration exists — **not that any key in it means anything**.
    D-091 is explicit that interpreting it here would make this module
    responsible for another's semantics, so nothing below asks what a key is.

    **A copy is taken** so the caller cannot mutate a stored declaration
    through the mapping it passed in; the frozen dataclass would not stop that
    on its own.
    """
    if not declaration:
        raise EmptyDeclarationError("a saved view records a question, and this one asks nothing")
    return dict(declaration)


#: Exported because `public/`'s writer must apply the same two rules to a
#: view a consumer constructed. **The rule stays here and is called from
#: there** — a second copy in the adapter is how two strengths of one check
#: start disagreeing (§2).
__all__ = [
    "MAX_SAVED_VIEW_NAME_LENGTH",
    "SavedView",
    "checked_declaration",
    "checked_name",
]
