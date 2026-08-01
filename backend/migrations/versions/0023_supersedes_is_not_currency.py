"""drop every partial index keyed on `supersedes IS NULL` (B-001)

Revision ID: 0023
Revises: 0022
Create Date: 2026-08-01

**Three indexes were built on an inverted reading of currency**, and dropping
them is half of `B-001`. The other half is the three `current()` readers, fixed
in the same change.

`B-001` was raised against `signal_profile` alone. The repository-wide invariant
written to stop it recurring — *"no index may key currency on `supersedes IS
NULL`"* — **failed immediately against two tables nobody had looked at**:
`workspace_scoring_model` (`0013`) and `workspace_opportunity_policy` (`0014`).
All three are customer-authored configuration, all three are Lane A's, and all
three had the identical defect copied forward. That is the argument for writing
an invariant as a scan rather than as a per-table assertion.

    UNIQUE (workspace_id) WHERE supersedes IS NULL

Migration `0012` described `uq_signal_profile_current` as *"one current profile per workspace… what stops
two concurrent configuration writes leaving a workspace with two live
interpretations."* On an immutable table it is neither of those things.

**It indexes the *first* version, not the current one.** Version 1 has a null
`supersedes`; version 2 is the row that *names* version 1. So the index contains
exactly one row per workspace — the original — forever.

**And after the first write it cannot fail.** Two concurrent version-2 writes
both carry `supersedes = <v1>`, neither is null, and both insert. The condition
the comment claims to prevent is precisely the one it does not prevent: **a guard
that cannot fail is documentation pretending to be code** (CLAUDE.md §2), and the
comment beside it was a false claim sitting in the repository.

**What actually protects the invariant is already there.**
`uq_signal_profile_version (workspace_id, version)` refuses a duplicate version,
so two concurrent revisions computing the same next version collide and one
loses. That is the real concurrency control, it works at every version rather
than only the first, and it is the same device `product_catalog` (`0019`) and
`research_request` (`0021`) use.

**`supersedes` stays.** It is a true statement about lineage and every
historical signal's explanation reads through it; it simply is not a currency
marker, and nothing may treat it as one again.

**Reversible, and the down-migration recreates the index as it was** — including
its defect. A migration that "fixed" history on the way down would make the two
directions describe different schemas, and `0012` is a record of what was true
then.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0023"
down_revision: str | None = "0022"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


#: index name -> table. All three identical, all three wrong the same way.
INDEXES = {
    "uq_signal_profile_current": "signal_profile",
    "uq_scoring_model_current": "workspace_scoring_model",
    "uq_opportunity_policy_current": "workspace_opportunity_policy",
}


def upgrade() -> None:
    for index, table in INDEXES.items():
        op.drop_index(index, table_name=table)


def downgrade() -> None:
    for index, table in INDEXES.items():
        op.create_index(
            index,
            table,
            ["workspace_id"],
            unique=True,
            postgresql_where=sa.text("supersedes IS NULL"),
        )
