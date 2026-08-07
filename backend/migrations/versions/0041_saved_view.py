"""workspace_tenancy: a named, shared declaration of a query

Revision ID: 0041
Revises: 0040
Create Date: 2026-08-07

**TASK-450, [455 §4] slice 2.** [TASK-449] published `public/saved_views.py`
and deliberately no table. This creates it.

**Four screens wrote this definition independently** — Companies, the App
Shell, Global Search and Reports — and [452] measured it as the
highest-leverage capability in the product.

### The declaration is opaque, and the schema says so

`JSONB`, `NOT NULL`, and **no index on its contents**. [D-091]: *"The storage
layer never interprets the saved declaration itself. Its responsibility is
persistence and retrieval, not execution."* ⚡ **A GIN index would exist to
answer questions about what is inside a declaration**, and this module is not
allowed to ask one — the index is absent for the same reason the parser is.

### One row per version, and no `is_live` column

A declaration is never edited; a change is a new row whose `supersedes` names
the one it replaces. **Live is derived from that chain rather than stored** —
a boolean beside it would be a second representation of one fact, and the two
would disagree the first time a version landed (`CLAUDE.md` §2).

`supersedes` is `ON DELETE SET NULL` rather than `CASCADE`: **if an earlier
version were ever removed, the later ones must survive**, because losing a
current reading because its history went is precisely what versioning exists
to prevent.

### Not append-only, and this one differs from 0035 on purpose

`UPDATE` **is** granted, and only retirement uses it. `membership_role_change`
records what *was* true and is therefore append-only; a saved view is a thing
that is still in use, and retiring it is a change to its present state rather
than a correction of its past. **Nothing else updates a row here** — a
revision is an `INSERT`.

### The four verifications

| | |
|---|---|
| **Data preservation** | A new table. Nothing existing is read, written or dropped |
| **Behaviour preservation** | Nothing reads it yet — the reader, writer and
  endpoints are [TASK-451], slice 3. Every existing path is untouched |
| **Capability expansion** | A workspace can name a question and share it,
  and an earlier reading stays explainable |
| **Rollback safety** | Dropping it loses only rows written after the
  upgrade. **Verified down and up.** Nothing that existed before this
  migration depends on it |

[455 §4]: ../../../docs/architecture/455-context-definitions-r02-r03.md
[TASK-449]: ../../../docs/BACKLOG.md
[TASK-451]: ../../../docs/BACKLOG.md
[452]: ../../../docs/architecture/452-app-shell-traceability-audit.md
[D-091]: ../../../docs/DECISION_REGISTER.md
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0041"
down_revision: str | None = "0040"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None

APP_ROLE = "signora_app"
TABLE = "saved_view"


def upgrade() -> None:
    op.create_table(
        TABLE,
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "workspace_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("workspace.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("declaration", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column(
            "supersedes",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey(f"{TABLE}.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("retired_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("updated_by", postgresql.UUID(as_uuid=True), nullable=False),
    )
    op.create_index(f"ix_{TABLE}_workspace_id", TABLE, ["workspace_id"])
    # **The listing index.** `live()` reads a workspace's views newest-first
    # and excludes retired ones; without this it is a scan of every version
    # ever written, which is the shape that degrades exactly as a workspace
    # gets value from the feature.
    op.create_index(
        f"ix_{TABLE}_live",
        TABLE,
        ["workspace_id", "created_at"],
        postgresql_where=sa.text("retired_at IS NULL"),
    )

    # `UPDATE` is granted and only retirement uses it — see the note above on
    # why this differs from `membership_role_change`.
    op.execute(f"GRANT SELECT, INSERT, UPDATE, DELETE ON {TABLE} TO {APP_ROLE}")
    op.execute(f"ALTER TABLE {TABLE} ENABLE ROW LEVEL SECURITY")
    # **`FORCE` matters separately**: without it the table's owner is exempt
    # from its own policies (docs/architecture/11-tenancy.md).
    op.execute(f"ALTER TABLE {TABLE} FORCE ROW LEVEL SECURITY")
    op.execute(
        f"""
        CREATE POLICY {TABLE}_select ON {TABLE} FOR SELECT
          USING (workspace_id = NULLIF(current_setting('app.workspace_id', true), '')::uuid)
        """
    )
    op.execute(
        f"""
        CREATE POLICY {TABLE}_insert ON {TABLE} FOR INSERT
          WITH CHECK (workspace_id = NULLIF(current_setting('app.workspace_id', true), '')::uuid)
        """
    )
    # **Both halves.** `USING` decides which rows are visible to update;
    # `WITH CHECK` decides what they may become. Omitting the second would let
    # a retirement move a row into another workspace.
    op.execute(
        f"""
        CREATE POLICY {TABLE}_update ON {TABLE} FOR UPDATE
          USING (workspace_id = NULLIF(current_setting('app.workspace_id', true), '')::uuid)
          WITH CHECK (workspace_id = NULLIF(current_setting('app.workspace_id', true), '')::uuid)
        """
    )
    op.execute(
        f"""
        CREATE POLICY {TABLE}_delete ON {TABLE} FOR DELETE
          USING (workspace_id = NULLIF(current_setting('app.workspace_id', true), '')::uuid)
        """
    )


def downgrade() -> None:
    op.execute(f"REVOKE ALL ON {TABLE} FROM {APP_ROLE}")
    op.drop_index(f"ix_{TABLE}_live", table_name=TABLE)
    op.drop_index(f"ix_{TABLE}_workspace_id", table_name=TABLE)
    op.drop_table(TABLE)
