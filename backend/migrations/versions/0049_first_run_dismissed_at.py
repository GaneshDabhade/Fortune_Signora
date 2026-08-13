"""workspace_tenancy: when a person dismissed the first-run overlay

Revision ID: 0049
Revises: 0048
Create Date: 2026-08-12

**[TASK-1424] · Workflow 29 · Authenticated Entry rule 20 `FIRST_RUN`.** One
nullable column on the table `0044` created and `0047` last extended — ⛔ **not
a new table, and not a boolean.**

### 🔴 Why a timestamp rather than `first_run_dismissed: bool`

📁 **The design's words are *"dismissible forever"***, and a boolean records
that fact and nothing else. ⚡ **A timestamp answers the same question — `NULL`
is *not dismissed* — and answers two more the product will ask**: *when did
this person finish being new*, and *did they dismiss it before or after the
thing we changed*. ⛔ **A boolean cannot be widened later without a second
migration and a backfill that invents a moment**, which is exactly the shape
[§2] calls duplicated truth arriving late.

⚠️ **And it matches the column beside it.** `last_entered_at` is a nullable
timestamp whose `NULL` means *never*; this reads the same way, so the two are
learned once rather than twice.

### ✅ The trigger is already built, and this column is only the other half

📁 **`last_entered_at` (`0047`) already distinguishes *never entered* from
*entered long ago***, which is rule 20's *"first login"*. ⛔ **What it cannot
say is whether somebody has already been shown the overlay and closed it** —
and without that, *"dismissible forever"* is a promise the product breaks at
the next sign-in.

### ⛔ Not stored on the client, and the design says so twice

📁 ***"Nothing about activation lives in localStorage."*** ⚡ The overlay is a
sibling of those cards and obeys the same sentence. **A dismissal in a browser
is a dismissal a person loses when they change machine** — which turns *forever*
into *until Tuesday*.

### The four verifications

| | |
|---|---|
| **Data preservation** | One nullable column with no default. **No existing
  row's values change**, and `NULL` reads as *not dismissed* — which is what
  every existing row honestly is |
| **Behaviour preservation** | Nothing reads it before this row. **The overlay
  does not render today**, so no journey changes on the way in |
| **Capability expansion** | Somebody signing in for the first time is told what
  this is and what to do, once, and never again after they close it |
| **Rollback safety** | Dropping it returns everybody to *not dismissed*, which
  is the behaviour before this row — ⚠️ **and that is a re-showing rather than a
  loss**: the overlay is two sentences, not a setting somebody configured |

[TASK-1424]: ../../../docs/BACKLOG.md
[§2]: ../../../CLAUDE.md
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0049"
down_revision: str | None = "0048"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None

TABLE = "person_preferences"
COLUMN = "first_run_dismissed_at"


def upgrade() -> None:
    # ⛔ **No server default.** *Not dismissed* is a real answer, and
    # backfilling it with *dismissed when the migration ran* would silently
    # deny the overlay to every existing person — including anybody who has
    # signed up and not yet signed in.
    op.add_column(TABLE, sa.Column(COLUMN, sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    op.drop_column(TABLE, COLUMN)
