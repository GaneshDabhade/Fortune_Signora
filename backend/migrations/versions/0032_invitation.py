"""workspace_tenancy: an organization can grow

Revision ID: 0032
Revises: 0031
Create Date: 2026-08-02

**Until now every workspace was permanently whoever created it.**
`POST /members` takes a `user_id`, nothing resolved an email to a user, and
there was no way to invite anybody at all.

**An invitation is addressed to an email, not to a user**, because a customer
knows a colleague's address and must not need to know anything else. The
person may have no Signora account, may sign in with Google, or may already
belong to three other organizations — none of which the inviter can be asked
about (46-team-management.md, D1).

### Four states, and two columns

`accepted_at` and `revoked_at` are facts with a moment. **`pending` is the
absence of both, and `expired` is `expires_at < now()`** — derived, never
flipped by a job, because a stored `expired` flag needs something to write it
and until that thing runs the row is wrong. Same discipline as `evidence_state`
and as release-derived-from-evaluations.

### The partial unique index is the design, not an optimisation

**One live invitation per `(workspace, email)`.** Two live invitations to one
address are two ways in — so *resend* is necessarily the same row, and
*change the role* is necessarily revoke-and-create. **The constraint and the
principle are one mechanism**, which is what makes the rule unrepresentable to
violate rather than merely discouraged (CLAUDE.md §2).

### `invited_by` never moves

An immutable historical fact, exactly like `decided_by` on a workflow state.
An invitation belongs to the *workspace*; the inviter is provenance, not an
owner. Acceptance still succeeds after they leave, because the organization
invited this person and a departure does not withdraw that — **withdrawal is an
act, and it has a column.**

### No token column, deliberately

Acceptance matches the `invited_email` against the **verified `email` claim the
JWT already carries** and the Python tier already requires. A bearer token in a
link is a credential sitting in an inbox: forwarded, archived, and synced to
devices nobody remembers owning. **Tokenless makes a forwarded invitation fail
closed** (§15, Challenge A).
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0032"
down_revision: str | None = "0031"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None

APP_ROLE = "signora_app"
TABLE = "invitation"
LIVE_INDEX = "uq_invitation_live_email"


def upgrade() -> None:
    op.create_table(
        TABLE,
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "workspace_id",
            postgresql.UUID(as_uuid=True),
            # Cascades with the workspace, like `membership`: an invitation into
            # an organization that no longer exists is not history worth keeping,
            # it is a row nothing can ever resolve.
            sa.ForeignKey("workspace.id", ondelete="CASCADE"),
            nullable=False,
        ),
        # Stored as the customer typed it, lowercased by the domain before it
        # arrives. Matching a verified claim is exact, and two spellings of one
        # address would be two live invitations the index could not see.
        sa.Column("invited_email", sa.String(320), nullable=False),
        # `create_type=False` on the postgresql dialect's ENUM, not
        # `sa.Enum`: the type was created in migration 0001 and only the
        # dialect-specific class honours the flag inside `create_table`.
        sa.Column(
            "role",
            postgresql.ENUM("owner", "member", name="workspace_role", create_type=False),
            nullable=False,
        ),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("accepted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False
        ),
        # `created_by` is the inviter, and the audit trail reads it. Named by the
        # shared convention rather than `invited_by` so every table answers
        # "who did this" through the same column.
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("updated_by", postgresql.UUID(as_uuid=True), nullable=False),
    )
    op.create_index(f"ix_{TABLE}_workspace_id", TABLE, ["workspace_id"])
    # **Partial, and that is the whole point.** A revoked or accepted invitation
    # to an address must not stop a new one being sent; a live one must.
    op.create_index(
        LIVE_INDEX,
        TABLE,
        ["workspace_id", "invited_email"],
        unique=True,
        postgresql_where=sa.text("accepted_at IS NULL AND revoked_at IS NULL"),
    )

    # No UPDATE grant beyond what accepting and revoking need — both write a
    # timestamp onto an otherwise frozen row. Nothing may edit an offer.
    op.execute(f"GRANT SELECT, INSERT, UPDATE ON {TABLE} TO {APP_ROLE}")
    op.execute(f"ALTER TABLE {TABLE} ENABLE ROW LEVEL SECURITY")
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
    op.execute(
        f"""
        CREATE POLICY {TABLE}_update ON {TABLE} FOR UPDATE
          USING (workspace_id = NULLIF(current_setting('app.workspace_id', true), '')::uuid)
          WITH CHECK (workspace_id = NULLIF(current_setting('app.workspace_id', true), '')::uuid)
        """
    )


def downgrade() -> None:
    op.execute(f"REVOKE ALL ON {TABLE} FROM {APP_ROLE}")
    op.drop_index(LIVE_INDEX, table_name=TABLE)
    op.drop_index(f"ix_{TABLE}_workspace_id", table_name=TABLE)
    op.drop_table(TABLE)
