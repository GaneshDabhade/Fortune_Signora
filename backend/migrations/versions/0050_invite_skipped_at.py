"""workspace_tenancy: when a person skipped the invite-the-team activation card

Revision ID: 0050
Revises: 0049
Create Date: 2026-08-13

**[TASK-1424] · `Fortune Signora Home.dc.html` §*Activation*.** One nullable
column on the table `0044` created, `0047` and `0049` extended.

### 📁 The rule this column exists for

> ***"Blocking cards — CRM and calls — cannot be dismissed. Non-blocking cards
> can be skipped, which hides them for 30 DAYS per person and is REVERSIBLE
> from the progress line."***
>
> ***"Skip state is per person, on the server, for 30 days. Nothing about
> activation lives in localStorage."***

### 🔴 A timestamp, and here the design forces it rather than merely favouring it

⚡ **`0049` chose a timestamp over a boolean on judgement.** ⛔ **This one has no
choice**: *hidden for thirty days* is a question about **when**, and a boolean
cannot answer it. **The window is derived from the moment** — ✅ so nothing
stores an expiry that a clock change or a retimed job could disagree with, and
📁 [§2] gets one authoritative representation rather than two.

### ✅ Reversible costs nothing extra

**Setting it to `NULL` un-skips**, which is the whole of *"reversible from the
progress line"*. ⛔ **No second column, no `is_skipped` beside a date to
contradict it.**

### The four verifications

| | |
|---|---|
| **Data preservation** | One nullable column, no default. **No existing row
  changes**, and `NULL` reads as *not skipped* — which every existing row is |
| **Behaviour preservation** | Nothing reads it before this row. **The invite
  card does not render today** |
| **Capability expansion** | Somebody who is not ready to invite colleagues can
  put the card away without being nagged, **and get it back** |
| **Rollback safety** | Dropping it returns everybody to *not skipped*, which is
  the behaviour before this row. ⚠️ **A re-showing rather than a loss** |

[TASK-1424]: ../../../docs/BACKLOG.md
[§2]: ../../../CLAUDE.md
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0050"
down_revision: str | None = "0049"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None

TABLE = "person_preferences"
COLUMN = "invite_skipped_at"


def upgrade() -> None:
    # ⛔ **No server default.** Backfilling *skipped when the migration ran*
    # would hide the card from everybody for thirty days, including people who
    # have never seen it.
    op.add_column(TABLE, sa.Column(COLUMN, sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    op.drop_column(TABLE, COLUMN)
