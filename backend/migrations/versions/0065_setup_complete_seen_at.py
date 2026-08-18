"""workspace_tenancy: when a person was told setup had finished

Revision ID: 0065
Revises: 0064
Create Date: 2026-08-18

**`Fortune Signora Home.dc.html` state 04.** One nullable column on the table
`0044` created and `0047`, `0049`, `0050` and `0063` extended.

### 📁 The rule this column exists for

> **State 04 · `state.activated`** — entry: *"All blocking cards complete."*
> Renders: *"Composition switches to SELLER, OPERATIONS or EXECUTIVE on the next
> render. **A one-time strip states that setup is finished and what changed.**"*
>
> **`AC-H03`**: *"Complete the last blocking card: the next render is the role
> composition, with the setup-complete strip shown **exactly once**."*

### 🔴 Why a column at all, when completion is already derived

⚡ **Completion is derived and must stay derived** — 📁 *"completion is derived
from the source of truth, never stored on Home."* ⛔ **This column stores
something else entirely**: not whether setup finished, but whether **this person
has been told**. ✅ **The first is a fact about the workspace; the second is a
fact about a reader**, and no amount of deriving the first answers the second.

### 🔴 A timestamp, not a boolean, and the neighbours settle it

**`first_run_dismissed_at` and `invite_skipped_at` are both timestamps on this
table**, and `0049` records the reasoning: `NULL` is the absence, and the moment
answers *when* without a second migration. ⚡ **The question this column will
actually be asked is *"why did the strip appear twice?"***, and a boolean cannot
answer it.

### ⚠️ Per person, not per workspace

📁 The design says *"one-time"* of **a strip somebody reads**. ⛔ A colleague who
joins an already-activated workspace has still never been told, so **their first
entry is their once** — which is why this lives on `person_preferences` rather
than on `workspace`.

### The four verifications

| | |
|---|---|
| **Data preservation** | One nullable column, no default. **No existing row
  changes**, and `NULL` reads as *not yet told* — which every existing row is |
| **Behaviour preservation** | Nothing reads it before this row. **State 04 does
  not render today**, so no strip appears or disappears |
| **Capability expansion** | The one moment a workspace stops being a setup task
  and starts being a product is stated once, to each person, rather than never |
| **Rollback safety** | Dropping it returns everybody to *not yet told*. ⚠️ **A
  re-showing rather than a loss** — the same shape as `0050`'s rollback, and the
  strip is informational rather than destructive |
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0065"
down_revision: str | None = "0064"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None

TABLE = "person_preferences"
COLUMN = "setup_complete_seen_at"


def upgrade() -> None:
    # ⛔ **No server default.** Backfilling *told when the migration ran* would
    # suppress the strip for every person who has never seen it, including the
    # one who is about to finish connecting their CRM.
    op.add_column(TABLE, sa.Column(COLUMN, sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    op.drop_column(TABLE, COLUMN)
