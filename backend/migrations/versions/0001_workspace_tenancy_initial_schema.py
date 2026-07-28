"""workspace_tenancy: initial schema (workspace, membership) with RLS

Revision ID: 0001
Revises: 0000
Create Date: 2026-07-28

Enum values are declared as literal strings rather than imported from
``modules.workspace_tenancy.domain.entities.WorkspaceRole`` deliberately —
migrations are immutable historical records and must not be coupled to
application code that can change after this migration has already shipped.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0001"
down_revision: str | None = "0000"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None

# create_type=False: the type is created explicitly in upgrade() below, so
# create_table() must not also emit its own CREATE TYPE for the column.
workspace_role = postgresql.ENUM("owner", "member", name="workspace_role", create_type=False)


def upgrade() -> None:
    bind = op.get_bind()
    postgresql.ENUM("owner", "member", name="workspace_role").create(bind, checkfirst=True)

    op.create_table(
        "workspace",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("updated_by", postgresql.UUID(as_uuid=True), nullable=False),
    )

    op.create_table(
        "membership",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "workspace_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("workspace.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("role", workspace_role, nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("updated_by", postgresql.UUID(as_uuid=True), nullable=False),
        sa.UniqueConstraint("workspace_id", "user_id", name="uq_membership_workspace_user"),
    )
    op.create_index("ix_membership_workspace_id", "membership", ["workspace_id"])
    op.create_index("ix_membership_user_id", "membership", ["user_id"])

    # --- Row-Level Security ---
    #
    # workspace is the tenancy root and cannot use the standard
    # workspace-scoped policy (it would be circular: there is no
    # app.workspace_id to check against a workspace's own row until the
    # workspace already exists). INSERT is therefore open to any
    # authenticated principal; SELECT/UPDATE require the caller to already
    # be a member. See docs/architecture/11-tenancy.md's workspace-creation
    # bootstrap pattern.
    op.execute("ALTER TABLE workspace ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE workspace FORCE ROW LEVEL SECURITY")
    op.execute(
        """
        CREATE POLICY workspace_insert ON workspace
          FOR INSERT
          WITH CHECK (true)
        """
    )
    # NULLIF(..., '') is load-bearing, not defensive noise. After a
    # transaction that used SET LOCAL commits, the GUC reverts to '' (empty
    # string) rather than NULL on that pooled connection. A bare
    # ''::uuid cast raises "invalid input syntax for type uuid", turning a
    # missing-context bug into a confusing runtime error. Coercing '' to
    # NULL makes the comparison NULL -> false, so the query returns zero
    # rows: the policy fails closed, quietly and correctly.
    op.execute(
        """
        CREATE POLICY workspace_select ON workspace
          FOR SELECT
          USING (
            id IN (
              SELECT workspace_id FROM membership
              WHERE user_id = NULLIF(current_setting('app.user_id', true), '')::uuid
            )
          )
        """
    )
    op.execute(
        """
        CREATE POLICY workspace_update ON workspace
          FOR UPDATE
          USING (
            id IN (
              SELECT workspace_id FROM membership
              WHERE user_id = NULLIF(current_setting('app.user_id', true), '')::uuid
                AND role = 'owner'
            )
          )
        """
    )

    # membership uses the standard workspace-scoped isolation policy.
    op.execute("ALTER TABLE membership ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE membership FORCE ROW LEVEL SECURITY")
    op.execute(
        """
        CREATE POLICY membership_isolation ON membership
          USING (
            workspace_id = NULLIF(current_setting('app.workspace_id', true), '')::uuid
          )
          WITH CHECK (
            workspace_id = NULLIF(current_setting('app.workspace_id', true), '')::uuid
          )
        """
    )


def downgrade() -> None:
    op.execute("DROP POLICY IF EXISTS membership_isolation ON membership")
    op.execute("DROP POLICY IF EXISTS workspace_update ON workspace")
    op.execute("DROP POLICY IF EXISTS workspace_select ON workspace")
    op.execute("DROP POLICY IF EXISTS workspace_insert ON workspace")
    op.drop_index("ix_membership_user_id", table_name="membership")
    op.drop_index("ix_membership_workspace_id", table_name="membership")
    op.drop_table("membership")
    op.drop_table("workspace")
    workspace_role.drop(op.get_bind(), checkfirst=True)
