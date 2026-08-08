"""workspace_tenancy: what a person chose about how Signora looks to them

Revision ID: 0044
Revises: 0043
Create Date: 2026-08-08

**[TASK-470] · Workflow 9 · User Profile.** The row names a user-preference
store as the one capability absent behind this workflow, and it asks the
implementing lane to answer a question rather than assume it:

> *"A preference row keyed by user and not workspace has no `workspace_id`, so
> §8's classification is not automatic. It is registered in
> `tenancy_policy.py` in the same change — and the row must say which and
> why."*

### 🔴 The answer: person *within* a workspace, and it is a narrowing

**[418] already ruled the aggregate** — *"a profile preference, a notification
matrix and a session belong to a person within a workspace"* — and [492 §0]
gives the shape:

> ***"A narrowing of tenant-owned, never a parallel to it. `workspace_id`
> stays non-nullable and every existing guarantee still applies. One predicate
> is added: `user_id = current_setting('app.user_id')::uuid`."***

**So this table is tenant-owned in the full sense** — non-nullable
`workspace_id`, RLS enabled *and* forced, separate policies for read and
write, registered in `TENANT_OWNED_TABLES` — **and then narrower still.**

⚠️ **The row itself says *account*-scoped, and this disagrees with it.** The
disagreement is recorded rather than resolved silently, in
`domain/preferences.py` and at [C-247]. ⛔ **Account-global has no lawful home
today**: a table with no `workspace_id` can only be platform infrastructure,
which *"a business module must never query"* — and a profile panel queries
this on every render.

### ⚡ Why the user predicate is in the policy and not only in the query

**Defence in depth is the rule, and here the depths are different guarantees.**
The `WHERE user_id = …` in the repository stops the module reading a
colleague's row **by mistake**; the policy stops it **at all**, including from
a query nobody has written yet. **A preference row must never become a route
to another account's data** — the row names that as its Security Invariant.

### The four verifications

| | |
|---|---|
| **Data preservation** | A new table. Nothing existing is read, written or
  dropped |
| **Behaviour preservation** | Nothing reads it before this row's own panels.
  Every existing path is untouched |
| **Capability expansion** | A person's theme, density, language and timezone
  survive signing out — *"every device you sign in from"* |
| **Rollback safety** | Dropping it returns everybody to the defaults, which
  is exactly the state a person who never opened the screen is already in.
  **Verified down and up** |

[TASK-470]: ../../../docs/BACKLOG.md
[418]: ../../../docs/architecture/418-platform-foundation-assessment.md
[492 §0]: ../../../docs/architecture/492-person-scoped-tenancy.md
[C-247]: ../../../docs/LANE_COORDINATION.md
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0044"
down_revision: str | None = "0043"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None

APP_ROLE = "signora_app"
TABLE = "person_preferences"

#: The tenant predicate every table here carries.
_WORKSPACE = "workspace_id = NULLIF(current_setting('app.workspace_id', true), '')::uuid"
#: ⚡ **The narrowing** — 492 §0. `app.user_id` has been set on every
#: transaction since migration 0001; this is the first table whose *rows* are
#: filtered by it.
_PERSON = "user_id = NULLIF(current_setting('app.user_id', true), '')::uuid"
_SCOPE = f"{_WORKSPACE} AND {_PERSON}"


def upgrade() -> None:
    op.create_table(
        TABLE,
        sa.Column(
            "workspace_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("workspace.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        # **Every column is nullable or defaulted**, because a person who has
        # never opened the screen still has preferences: the absence of a row
        # means *the defaults*, and so does a row with nothing chosen.
        sa.Column("theme", sa.String(length=16), nullable=False, server_default="system"),
        sa.Column(
            "density", sa.String(length=16), nullable=False, server_default="comfortable"
        ),
        # ⛔ **Nullable, and NOT defaulted to UTC.** *Not chosen* and *chose
        # UTC* are different facts, and the design's timezone prompt can only
        # be offered while the first one is still true.
        sa.Column("timezone", sa.String(length=64), nullable=True),
        sa.Column("language", sa.String(length=16), nullable=True),
        sa.Column("time_format", sa.String(length=8), nullable=False, server_default="24h"),
        sa.Column("pronouns", sa.String(length=32), nullable=True),
        sa.Column("display_name", sa.String(length=32), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("updated_by", postgresql.UUID(as_uuid=True), nullable=False),
        # **(workspace, person) is the identity** — one row per person per
        # organization, which is what 418's *person within a workspace* means
        # expressed as a key.
        sa.PrimaryKeyConstraint("workspace_id", "user_id"),
    )
    # ⛔ **Bounded in the database as well as the enum.** The enums refuse an
    # unknown value at the edge; this holds for anything that never passes
    # through it.
    op.create_check_constraint(
        f"ck_{TABLE}_theme", TABLE, "theme IN ('light', 'dark', 'system')"
    )
    op.create_check_constraint(
        f"ck_{TABLE}_density", TABLE, "density IN ('comfortable', 'compact')"
    )
    op.create_check_constraint(
        f"ck_{TABLE}_time_format", TABLE, "time_format IN ('24h', '12h')"
    )

    op.execute(f"GRANT SELECT, INSERT, UPDATE, DELETE ON {TABLE} TO {APP_ROLE}")
    op.execute(f"ALTER TABLE {TABLE} ENABLE ROW LEVEL SECURITY")
    # **`FORCE` matters separately**: without it the table's owner is exempt
    # from its own policies (docs/architecture/11-tenancy.md).
    op.execute(f"ALTER TABLE {TABLE} FORCE ROW LEVEL SECURITY")

    # 🔴 **Every policy carries BOTH predicates.** The workspace half is the
    # tenancy guarantee every table here has; the person half is 492's
    # narrowing, and it is what stops a preference row becoming a route to a
    # colleague's account — the Security Invariant this row names.
    op.execute(f"CREATE POLICY {TABLE}_select ON {TABLE} FOR SELECT USING ({_SCOPE})")
    op.execute(f"CREATE POLICY {TABLE}_insert ON {TABLE} FOR INSERT WITH CHECK ({_SCOPE})")
    # **Both halves.** `USING` decides which rows may be updated; `WITH CHECK`
    # decides what they may become — omitting the second would let a write
    # move a row onto another person.
    op.execute(
        f"CREATE POLICY {TABLE}_update ON {TABLE} FOR UPDATE "
        f"USING ({_SCOPE}) WITH CHECK ({_SCOPE})"
    )
    op.execute(f"CREATE POLICY {TABLE}_delete ON {TABLE} FOR DELETE USING ({_SCOPE})")


def downgrade() -> None:
    op.execute(f"REVOKE ALL ON {TABLE} FROM {APP_ROLE}")
    for suffix in ("time_format", "density", "theme"):
        op.drop_constraint(f"ck_{TABLE}_{suffix}", TABLE, type_="check")
    op.drop_table(TABLE)
