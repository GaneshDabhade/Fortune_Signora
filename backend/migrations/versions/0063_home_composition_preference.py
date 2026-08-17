"""workspace_tenancy: a person's chosen Home composition.

📁 **The finalized design, `Fortune Signora Home.dc.html` §04** — resolution rule
2: *"Person has set a start-page preference of a specific composition… Honoured
over role."* ⛔ **No column carried it**, so rule 2 was unreachable and Home
resolved from role alone.

## ⚡ One nullable column, and the nullability is the feature

**`person_preferences.home_composition`, `varchar(32)`, `NULL`.** ⛔ **`NULL`
means *not set* and is NOT the same as `'seller'`**: the resolver falls through
to rules 3–5 when it is absent, so a default here would pin every person to one
composition and make rule 3 permanently unreachable.

## ⛔ No CHECK constraint, deliberately

📁 **The four names are the DESIGN's closed set** and the domain validates
against `HOME_COMPOSITIONS`. ⚠️ **A database CHECK would make adding a fifth
composition a migration rather than a design decision** — and 📁 `0045` and
`0060` set the precedent for this table: the columns the design enumerates carry
a CHECK, and the ones whose vocabulary is the design's own do not
(`language`, `timezone`, `date_format`).

## ✅ Additive and reversible

**Nothing to backfill** — every existing row means *not set*, which is the
correct answer for somebody who has never chosen. **`downgrade()` drops the
column; the only loss is the preference itself.**

⛔ **No tenancy-policy change.** 📁 `person_preferences` is already registered and
person-scoped from `0044`; a column on a classified table changes nothing about
its classification.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0063"
down_revision: str | None = "0062"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "person_preferences",
        sa.Column("home_composition", sa.String(length=32), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("person_preferences", "home_composition")
