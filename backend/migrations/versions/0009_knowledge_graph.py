"""knowledge_graph: entity, identity_binding, resolution_decision, relationship

Revision ID: 0009
Revises: 0008
Create Date: 2026-07-29

Four workspace-owned tables with forced RLS and their full policy sets in
this same revision.

**`resolution_decision` is immutable, and the database enforces it.**
`signora_app` holds `SELECT`, `INSERT`, and `DELETE` on it but **not
`UPDATE`** — a wrong resolution is corrected by a new decision naming the
one it supersedes, never by editing the old one. That is why the
supersession pointer on this table points *backwards*: a forward
`superseded_by` would have to be written onto the older row, which the
missing grant makes impossible.

`DELETE` is granted for the same reason it is on `claim`: the graph is
*derived* data. Dropping and rebuilding it from claims is the rollback path
for a bad resolution rule, and a regenerated decision is a new decision
rather than an edited one.

**`entity` deliberately has no attribute columns.** An entity is an
identity, not a record; a `name` column here would be truth-resolution in
miniature and would immediately disagree with the claims underneath it
(docs/architecture/22-knowledge-graph.md, AC-28).
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0009"
down_revision: str | None = "0008"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None

APP_ROLE = "signora_app"
TABLES = ("entity", "identity_binding", "resolution_decision", "relationship")
IMMUTABLE_TABLES = ("resolution_decision",)


def _audit_columns() -> list[sa.Column]:
    return [
        sa.Column("workspace_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("updated_by", postgresql.UUID(as_uuid=True), nullable=False),
    ]


def upgrade() -> None:
    op.create_table(
        "entity",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("kind", sa.String(32), nullable=False),
        *_audit_columns(),
    )
    op.create_index("ix_entity_workspace_id", "entity", ["workspace_id"])
    op.create_index("ix_entity_kind", "entity", ["workspace_id", "kind"])

    op.create_table(
        "resolution_decision",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("provider", sa.String(64), nullable=False),
        sa.Column("provider_external_id", sa.String(512), nullable=False),
        sa.Column("outcome", sa.String(32), nullable=False),
        # Each reason records the rule, the field, the matched value, and
        # the strength declared for that rule at decision time. Denormalized
        # so the audit record stays self-describing: revising a rule's
        # strength later must not silently rewrite what past decisions said.
        sa.Column("reasons", postgresql.JSONB(), nullable=False, server_default="[]"),
        sa.Column("entity_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column(
            "candidate_entity_ids",
            postgresql.ARRAY(postgresql.UUID(as_uuid=True)),
            nullable=False,
            server_default="{}",
        ),
        sa.Column(
            "evidence_claim_ids",
            postgresql.ARRAY(postgresql.UUID(as_uuid=True)),
            nullable=False,
            server_default="{}",
        ),
        sa.Column("decided_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("supersedes", postgresql.UUID(as_uuid=True), nullable=True),
        *_audit_columns(),
        sa.ForeignKeyConstraint(["entity_id"], ["entity.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["supersedes"], ["resolution_decision.id"], ondelete="SET NULL"),
    )
    op.create_index("ix_resolution_decision_workspace_id", "resolution_decision", ["workspace_id"])
    op.create_index("ix_resolution_decision_entity_id", "resolution_decision", ["entity_id"])
    op.create_index(
        "ix_resolution_decision_identity",
        "resolution_decision",
        ["workspace_id", "provider", "provider_external_id"],
    )

    op.create_table(
        "identity_binding",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("provider", sa.String(64), nullable=False),
        sa.Column("provider_external_id", sa.String(512), nullable=False),
        sa.Column("state", sa.String(32), nullable=False),
        # Nullable: an AMBIGUOUS binding resolves to no single entity, and
        # recording that is the point — it must not be represented as a
        # binding that happens to be missing.
        sa.Column("entity_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("decision_id", postgresql.UUID(as_uuid=True), nullable=False),
        # Identity hints carried forward from the claims that produced this
        # binding, so resolving a later provider identity compares against
        # stored values rather than re-reading another module's claims.
        sa.Column("domain", sa.String(255), nullable=True),
        sa.Column("legal_name", sa.String(512), nullable=True),
        sa.Column("country", sa.String(64), nullable=True),
        sa.Column("superseded_by", postgresql.UUID(as_uuid=True), nullable=True),
        *_audit_columns(),
        sa.ForeignKeyConstraint(["entity_id"], ["entity.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["decision_id"], ["resolution_decision.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["superseded_by"], ["identity_binding.id"], ondelete="SET NULL"),
        # **Ambiguity merges nothing** (AC-29), enforced by the database
        # rather than by the use case that happens to write the row. An
        # over-merge is invisible in the data and corrupts every downstream
        # signal, so the guarantee belongs where no code path can miss it.
        sa.CheckConstraint(
            "state <> 'ambiguous' OR entity_id IS NULL",
            name="ck_identity_binding_ambiguous_binds_nothing",
        ),
    )
    op.create_index("ix_identity_binding_workspace_id", "identity_binding", ["workspace_id"])
    op.create_index("ix_identity_binding_entity_id", "identity_binding", ["entity_id"])
    # One *current* binding per provider identity per workspace. The
    # constraint is the concurrency guard: two workers resolving the same
    # hint simultaneously would otherwise create two entities, and the
    # database is the only place that race can be settled.
    op.create_index(
        "uq_identity_binding_current",
        "identity_binding",
        ["workspace_id", "provider", "provider_external_id"],
        unique=True,
        postgresql_where=sa.text("superseded_by IS NULL"),
    )

    op.create_table(
        "relationship",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("kind", sa.String(64), nullable=False),
        sa.Column("source_entity_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("target_entity_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("valid_from", sa.DateTime(timezone=True), nullable=False),
        # NULL means "still true". A removal sets it rather than deleting
        # the row: what a company used and stopped using is exactly what a
        # competitive-displacement signal reads.
        sa.Column("valid_to", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "evidence_claim_ids",
            postgresql.ARRAY(postgresql.UUID(as_uuid=True)),
            nullable=False,
            server_default="{}",
        ),
        sa.Column("superseded_by", postgresql.UUID(as_uuid=True), nullable=True),
        *_audit_columns(),
        sa.ForeignKeyConstraint(["source_entity_id"], ["entity.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["target_entity_id"], ["entity.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["superseded_by"], ["relationship.id"], ondelete="SET NULL"),
    )
    op.create_index("ix_relationship_workspace_id", "relationship", ["workspace_id"])
    op.create_index("ix_relationship_source", "relationship", ["source_entity_id", "kind"])
    op.create_index("ix_relationship_target", "relationship", ["target_entity_id", "kind"])
    op.create_index(
        "uq_relationship_current",
        "relationship",
        ["workspace_id", "kind", "source_entity_id", "target_entity_id"],
        unique=True,
        postgresql_where=sa.text("valid_to IS NULL AND superseded_by IS NULL"),
    )

    for table in TABLES:
        op.execute(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY")
        op.execute(f"ALTER TABLE {table} FORCE ROW LEVEL SECURITY")
        op.execute(
            f"""
            CREATE POLICY {table}_select ON {table} FOR SELECT
              USING (workspace_id = NULLIF(current_setting('app.workspace_id', true), '')::uuid)
            """
        )
        op.execute(
            f"""
            CREATE POLICY {table}_insert ON {table} FOR INSERT
              WITH CHECK (
                workspace_id = NULLIF(current_setting('app.workspace_id', true), '')::uuid
              )
            """
        )
        op.execute(
            f"""
            CREATE POLICY {table}_delete ON {table} FOR DELETE
              USING (workspace_id = NULLIF(current_setting('app.workspace_id', true), '')::uuid)
            """
        )

        if table in IMMUTABLE_TABLES:
            # No UPDATE policy and no UPDATE grant. An attempted overwrite
            # fails with a permission error rather than succeeding quietly,
            # which is what makes the invariant real rather than a comment.
            op.execute(f"GRANT SELECT, INSERT, DELETE ON {table} TO {APP_ROLE}")
            continue

        op.execute(
            f"""
            CREATE POLICY {table}_update ON {table} FOR UPDATE
              USING (workspace_id = NULLIF(current_setting('app.workspace_id', true), '')::uuid)
              WITH CHECK (
                workspace_id = NULLIF(current_setting('app.workspace_id', true), '')::uuid
              )
            """
        )
        op.execute(f"GRANT SELECT, INSERT, UPDATE, DELETE ON {table} TO {APP_ROLE}")


def downgrade() -> None:
    for table in reversed(TABLES):
        op.execute(f"REVOKE ALL ON {table} FROM {APP_ROLE}")
    op.drop_table("relationship")
    op.drop_table("identity_binding")
    op.drop_table("resolution_decision")
    op.drop_table("entity")
