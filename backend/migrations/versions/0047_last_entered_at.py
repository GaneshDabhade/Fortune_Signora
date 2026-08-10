"""workspace_tenancy: when a person last entered a workspace

Revision ID: 0047
Revises: 0046
Create Date: 2026-08-10

**[TASK-1422] · Workflow 29 · rule 12 `LAST_USED`.** One nullable column on the
table `0044` created — ⛔ **not a new table, and not a pointer.**

### 🔴 A timestamp per workspace, never `last_used_workspace_id`

📁 **[§2]: *truth has exactly one authoritative representation; everything else
derives from it.*** ⛔ **A stored pointer would be a second representation of a
fact these rows already carry**, and the two would disagree the first time a
membership ended without something remembering to rewrite it.

⚡ **That disagreement is the hazard [D-196] named** — *"a stored preference
that OUTLIVES membership… an authorization failure wearing a convenience
feature's clothes."* ✅ **Deriving the answer over the person's LIVE
memberships makes a departed member's row unreachable rather than merely
stale**: the workspace they left is not in the set the derivation reads, **so
there is nothing to forget to clear.**

### ✅ The tenancy class is unchanged, and that is the point of reusing the table

📁 **[492 §0]: the person-scoped class is *"a narrowing of tenant-owned, never a
parallel to it. `workspace_id` stays non-nullable and every existing guarantee
still applies."*** ⛔ **This column adds no new classification, no new policy
and no new grant** — it lands inside guarantees `0044` already proved, which is
the whole reason it is here rather than in a table of its own.

⚡ **And the workspace foreign key already cascades.** Deleting a workspace
takes these rows with it, so **the third path the row names is structural
rather than something a use case has to remember.**

### The four verifications

| | |
|---|---|
| **Data preservation** | One nullable column with no default. **No existing
  row's values change**, and `NULL` reads as *never entered* — which is what
  every existing row honestly is |
| **Behaviour preservation** | Nothing read it before this row. The engine
  reads `lastUsedWorkspaceId` and nothing wrote it |
| **Capability expansion** | Somebody with several workspaces lands where they
  were working, and stops landing there the moment they lose access |
| **Rollback safety** | Dropping it returns everybody to the chooser, which is
  the behaviour before this row. **Verified down and up** |

[TASK-1422]: ../../../docs/BACKLOG.md
[D-196]: ../../../docs/DECISION_REGISTER.md
[§2]: ../../../CLAUDE.md
[492 §0]: ../../architecture/492-person-scoped-tenancy.md
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0047"
down_revision: str | None = "0046"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None

TABLE = "person_preferences"
COLUMN = "last_entered_at"


def upgrade() -> None:
    # ⛔ **No server default.** *Never entered* is a real answer and must not be
    # backfilled with *entered when the migration ran* — rule 12 would then fire
    # for everybody who has never been anywhere.
    op.add_column(TABLE, sa.Column(COLUMN, sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    op.drop_column(TABLE, COLUMN)
