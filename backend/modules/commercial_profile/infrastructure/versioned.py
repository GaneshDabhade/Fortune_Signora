"""Reading the declaration in force.

**One line of SQL, expressed once for the whole module**, because it is the
one line here a careful engineer has already got wrong somewhere else.

`signal_profile` reads `WHERE supersedes IS NULL` for *"current"*. On an
immutable table the **new** row is the one that names its predecessor, so a
null `supersedes` marks the **first** version — permanently. The defect is
latent there only because nothing has ever written a second profile.

Three tables in this module would have carried three hand-written copies of
the correct version of that read, which is three chances for the fourth to be
written the wrong way. Now there is one, and a new declaration inherits it
rather than reimplementing it.
"""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import Select, select

from modules.commercial_profile.infrastructure.models import DeclarationModel


def latest[Declaration: DeclarationModel](
    model: type[Declaration], workspace_id: UUID
) -> Select[tuple[Declaration]]:
    """The row in force for a workspace: **the highest version.**

    Ordering by version is also the rule `uq_(workspace_id, version)` already
    enforces, so the reader and the database agree by construction rather than
    by coincidence.

    The explicit `workspace_id` filter is defence in depth, not the control —
    RLS is authoritative on every table this reaches (`CLAUDE.md` §8).
    """
    return (
        select(model)
        .where(model.workspace_id == workspace_id)
        .order_by(model.version.desc())
        .limit(1)
    )
