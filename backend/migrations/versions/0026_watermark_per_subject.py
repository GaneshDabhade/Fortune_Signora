"""provider_platform: a watermark belongs to one subject

Revision ID: 0026
Revises: 0025
Create Date: 2026-08-02

**B-004.** `provider_watermark` is keyed `(workspace_id, provider, capability)`
and carries no subject, so a workspace watching two accounts shares one
position between them. Sync Acme to Tuesday, then sync Initech: Initech's run
starts from Acme's position and **silently skips every record older than it**.
Nothing fails, nothing is logged, and the missing evidence never becomes a
signal.

**Latent until now, and it stops being latent in the next slice.** Nothing
outside the Provider Simulation Framework has ever supplied a `subject`, so no
workspace has yet had two. PP-02 builds the consumer that gives every declared
account one, which is why [ADR-0036](../../docs/architecture/adr/0036-target-account-contract.md)
names this *"one defect that must be fixed before the consumer is built"*.

**Existing rows keep an empty subject rather than a guessed one.** Which
account an old position belongs to is not recoverable — the column did not
exist — and inventing an attribution would be worse than admitting none. An
empty subject matches no real one, so those rows become inert and the first
sync of each subject correctly requests a full snapshot. **That is the
behaviour an absent watermark already asks for**, so nothing new is introduced
to handle it.

**The downgrade discards watermarks, and says so.** Narrowing the constraint
means collapsing many rows into one per `(workspace, provider, capability)`,
and there is no correct choice of which to keep. It keeps the furthest-advanced
position, which is the safe direction for a *constraint* and the unsafe one for
*coverage* — a subject behind it would be skipped. **Re-running the upgrade
does not repair that**; the honest recovery after a downgrade is to reset the
affected watermarks, which is already the documented recovery for a bad run and
destroys no history: syncs and raw records are separate tables and are
untouched here.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0026"
down_revision: str | None = "0025"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None

TABLE = "provider_watermark"
OLD_CONSTRAINT = "uq_provider_watermark_scope"
NEW_CONSTRAINT = "uq_provider_watermark_subject"


def upgrade() -> None:
    # Nullable first, then backfilled, then NOT NULL: the table is live in
    # every developer database and an unbackfilled NOT NULL would refuse.
    op.add_column(TABLE, sa.Column("subject", sa.String(length=512), nullable=True))
    op.execute(f"UPDATE {TABLE} SET subject = '' WHERE subject IS NULL")
    op.alter_column(TABLE, "subject", nullable=False)

    op.drop_constraint(OLD_CONSTRAINT, TABLE, type_="unique")
    op.create_unique_constraint(
        NEW_CONSTRAINT, TABLE, ["workspace_id", "provider", "capability", "subject"]
    )


def downgrade() -> None:
    op.drop_constraint(NEW_CONSTRAINT, TABLE, type_="unique")

    # Collapse to one row per old key before the narrower constraint can
    # exist. Keeping the furthest-advanced position is stated in the module
    # docstring above as the unsafe-for-coverage direction; it is chosen
    # because a constraint cannot be created over duplicates at all.
    op.execute(
        f"""
        DELETE FROM {TABLE} w
        USING {TABLE} keep
        WHERE w.workspace_id = keep.workspace_id
          AND w.provider = keep.provider
          AND w.capability = keep.capability
          AND (
                w.position IS DISTINCT FROM keep.position
                  AND (keep.position IS NOT NULL AND (w.position IS NULL OR w.position < keep.position))
                OR (w.position IS NOT DISTINCT FROM keep.position AND w.id > keep.id)
              )
        """
    )

    op.create_unique_constraint(
        OLD_CONSTRAINT, TABLE, ["workspace_id", "provider", "capability"]
    )
    op.drop_column(TABLE, "subject")
