"""A named, shared declaration of a query — **R-02, and the contract only**.

**Four screens wrote this definition independently** — Companies, the App
Shell, Global Search and Reports — and [452] measured it as **the
highest-leverage capability in the product**: sixteen screens inherit the
shell that needs it.

[452]: ../../../../docs/architecture/452-app-shell-traceability-audit.md

**This module publishes the contract and nothing else** (TASK-449). No table,
no endpoint, no implementation. ⚡ **That is the deliverable rather than a
staging post**: a consumer lane can compile, type-check and test against these
types **before a row is ever persisted**, and `lint-imports` proves the
coupling never forms in the wrong direction while they do.

### What this context is responsible for, and the four words it must not know

**A name · an author · a workspace · an opaque declaration · retrieval ·
permission-aware listing · versioning.** That is all.

> ⛔ **It never parses, validates, executes, ranks or optimises a
> declaration, and it never learns what *filter* or *sort* mean.** The
> declaration is opaque on purpose: the moment this store could call one
> *invalid*, `workspace_tenancy` would be responsible for another module's
> semantics — the boundary `commercial_profile` keeps by never reading the
> pipeline.

⛔ **It never materialises results.** A saved view is a question somebody
wrote down; running it belongs to whichever module owns the answer.

### Why a change is a new version and never an edit

**`IcpDeclaration`'s shape, for `IcpDeclaration`'s reason.** A view that could
be edited is a view whose earlier readings cannot be explained: a colleague
who acted on *"my accounts, contested first"* last week needs that to still
mean what it meant. **A change is a new version naming the one it replaces**,
and the old one stays readable.

### No events, and that is a decision rather than an omission

**[P-C](../../../../docs/DOMAIN_DISCOVERY_REGISTER.md): an event exists when a
consumer appears, and none has.** A context definition is exactly where a
speculative event catalog would otherwise be born, so this one says no.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Protocol
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from signora_platform.pagination import CursorPosition


class SavedViewView(BaseModel):
    """One saved view, as another module may see it.

    A frozen view rather than an ORM row: an ORM instance carries a session, a
    write path and lazy loaders, all of which would let a consumer change this
    module's table by accident.
    """

    model_config = ConfigDict(frozen=True)

    id: UUID
    workspace_id: UUID
    name: str = Field(
        description=(
            "What the person called it. The customer's words, never derived from the "
            "declaration — a view named by its filters would rename itself when they changed."
        )
    )
    declaration: dict[str, Any] = Field(
        description=(
            "The query, exactly as the owning screen wrote it. **Opaque to this module**: "
            "it is never parsed, validated, executed or ranked here, and this module does "
            "not know what any key in it means."
        )
    )
    created_by: UUID
    created_at: datetime
    supersedes: UUID | None = Field(
        default=None,
        description=(
            "The version this one replaces. Null on the first. A declaration is never "
            "edited, so a change is a new row naming the old one and the old one stays "
            "readable."
        ),
    )
    retired_at: datetime | None = Field(
        default=None,
        description=(
            "When somebody stopped using it. Retired rather than deleted: a view that "
            "explained a decision must still explain it afterwards."
        ),
    )


class SavedViewListView(BaseModel):
    """One page of saved views.

    `has_more` rather than a total, on the precedent every paged read in this
    repository already follows: counting every view on every request costs a
    scan to answer a question asked only to decide whether to draw one more
    control.
    """

    model_config = ConfigDict(frozen=True)

    items: tuple[SavedViewView, ...]
    has_more: bool
    next_position: CursorPosition | None = None


class SavedViewReader(Protocol):
    """Reading saved views. **The half a consumer needs first.**

    Separate from the writer because the two are granted differently: every
    member reads the views their workspace shares, and creating one is an act
    with an author. A single port would make every reader a writer.
    """

    async def by_id(self, workspace_id: UUID, saved_view_id: UUID) -> SavedViewView | None:
        """The view, or `None` when it is not visible in this workspace.

        **Absence is a legitimate answer, not an error**: a view from another
        workspace is invisible under RLS, and retrying will not make it
        appear."""
        ...

    async def live(
        self, workspace_id: UUID, *, after: CursorPosition | None, limit: int
    ) -> SavedViewListView:
        """The views in force — **superseded and retired ones excluded**.

        **Live is derived, never stored.** A boolean column beside the
        supersession chain would be a second representation of one fact, and
        the two would disagree the first time a version landed."""
        ...


class SavedViewWriter(Protocol):
    """Recording a saved view, and retiring one.

    ⛔ **No `update`, and the absence is the design.** A declaration is never
    edited; `save` with `supersedes` is how a change is made, which keeps the
    earlier reading explainable. A port offering `update` would make the
    immutability a rule somebody has to remember rather than one the contract
    cannot express.
    """

    async def save(self, view: SavedViewView) -> None:
        """Record a view, or a new version naming the one it replaces.

        **The caller supplies the identity**, as `TargetAccount` does, so a
        retry is idempotent and a rename is distinguishable from a
        remove-and-re-add."""
        ...

    async def retire(self, workspace_id: UUID, saved_view_id: UUID, *, at: datetime) -> None:
        """Stop offering it, without removing what it explained."""
        ...


__all__ = [
    "SavedViewListView",
    "SavedViewReader",
    "SavedViewView",
    "SavedViewWriter",
]
