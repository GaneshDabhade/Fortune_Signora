"""workspace_tenancy: a membership ends rather than disappearing

Revision ID: 0033
Revises: 0032
Create Date: 2026-08-02

**Somebody leaving an organization is a business event, not a deletion.**
`policy.csv` has granted owners `member:remove` since M1 and nothing could
perform it — a reviewed authorization decision for an operation the system did
not have.

### The row survives, and that is what keeps the product readable

Decision history, the account timeline, narration attribution and every audit
question cite a membership. **Deleting one would silently rewrite the past**:
*"Ana dismissed this account"* would become *"somebody dismissed this
account"*, and the invitation Ana sent would lose its inviter.

So a departure writes three columns onto a row that otherwise never changes —
the same shape as `WorkflowState`, where a decision records **who · when ·
why** and nothing is removed (46-team-management.md, D3).

### The unique constraint becomes partial, and it has to

`uq_membership_workspace_user` forbade a second membership for one person in
one workspace. **With ended rows that would make re-joining impossible** — a
contractor who returns, or a colleague removed by mistake, could never come
back. The constraint therefore applies **only to live memberships**, which is
the same shape migration `0031` gave invitations one revision earlier.

### The four verifications

| | |
|---|---|
| **Data preservation** | **Additive only.** Three nullable columns; no row is written, moved or dropped. The dropped constraint is replaced by a partial index that is strictly weaker, so nothing that was valid becomes invalid |
| **Behaviour preservation** | Existing memberships have `ended_at IS NULL` and are therefore live under every new predicate. **Membership verification, the members list and RLS all behave exactly as before** |
| **Capability expansion** | An owner can end a membership, and the record says who did it, when, and why |
| **Rollback safety** | `downgrade()` restores the original unique constraint and drops the columns. **Reversal is safe while no membership has ended**; once one has, the constraint could refuse a legitimate re-join — which is why the downgrade fails loudly rather than dropping rows to make room |
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0033"
down_revision: str | None = "0032"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None

TABLE = "membership"
OLD_CONSTRAINT = "uq_membership_workspace_user"
LIVE_INDEX = "uq_membership_live_user"


def upgrade() -> None:
    op.add_column(TABLE, sa.Column("ended_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column(
        TABLE, sa.Column("ended_by", postgresql.UUID(as_uuid=True), nullable=True)
    )
    # Free text, like `WorkflowState.reason`. **Not an enum**: the reasons a
    # person leaves an organization are a customer's vocabulary, not Signora's,
    # and a fixed list would push every real answer into "other".
    op.add_column(TABLE, sa.Column("ended_reason", sa.String(500), nullable=True))

    op.drop_constraint(OLD_CONSTRAINT, TABLE, type_="unique")
    op.create_index(
        LIVE_INDEX,
        TABLE,
        ["workspace_id", "user_id"],
        unique=True,
        postgresql_where=sa.text("ended_at IS NULL"),
    )


def downgrade() -> None:
    # **Fails loudly rather than deleting.** Restoring the total constraint over
    # rows that include ended memberships would refuse a legitimate re-join, and
    # the only way to force it through is to destroy history. A migration that
    # silently dropped audit rows to satisfy a constraint would be worse than
    # one that refuses.
    op.execute(
        """
        DO $$
        BEGIN
          IF EXISTS (SELECT 1 FROM membership WHERE ended_at IS NOT NULL) THEN
            RAISE EXCEPTION
              'Cannot downgrade: ended memberships exist and the original '
              'constraint would refuse a re-join. Reversing this migration '
              'would require deleting audit history.';
          END IF;
        END $$;
        """
    )
    op.drop_index(LIVE_INDEX, table_name=TABLE)
    op.create_unique_constraint(OLD_CONSTRAINT, TABLE, ["workspace_id", "user_id"])
    op.drop_column(TABLE, "ended_reason")
    op.drop_column(TABLE, "ended_by")
    op.drop_column(TABLE, "ended_at")
