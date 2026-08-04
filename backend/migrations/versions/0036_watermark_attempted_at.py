"""provider_platform: when a provider last *looked*, not only what it found

Revision ID: 0036
Revises: 0035
Create Date: 2026-08-03

**One nullable column, and it answers a question the table could not.**

`provider_watermark.position` records **how far a subject has been read**, and
it advances only when records arrive (`run_sync.py`). So a successful read that
returned nothing left no trace at all — which means **an account nobody has
found anything about is indistinguishable from one nobody has checked.** Those
diverge exactly where a seller needs them to: *"Latest evidence · 5 weeks ago"*
cannot say whether the account went quiet or the pipeline did.

`attempted_at` is written on **every completed run**, regardless of
`high_water`, keeping *how far we read* and *when we last tried* in the one row
that already knows the subject.

**Nullable, and deliberately not backfilled.** Every existing row was read at
some point and nothing recorded when. A default of `now()` would assert that
every subject was checked at migration time, which is false for all of them;
`created_at` would assert it was checked once and never since, which is false
for most. **The honest value is null**, and the product says it does not know
rather than showing a date the migration invented.

**Not `UPDATE`-free, and that is correct** — the same reasoning migration 0030
records for this table. This is *current position*, not a historical record:
what happened is in `provider_sync` and the outbox, and this row only ever
answers *where are we now*. Immutability (`CLAUDE.md` §2) binds records of
facts, and a watermark is a bookmark.

**No RLS statement here.** `provider_watermark` is workspace-owned and its
policy was established with the table; adding a column does not change it, and
the tenancy suite continues to assert it.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0036"
down_revision: str | None = "0035"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "provider_watermark",
        sa.Column("attempted_at", sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("provider_watermark", "attempted_at")
