"""workspace_tenancy: the URL a workspace lives at.

📁 **The finalized design, `Fortune Signora Onboarding.dc.html` screen `03`** —
*"Workspace URL · `eu.signora.app/northwind` · Available · **Checked as you
type, 300ms after you stop. Permanent once created.**"* ⛔ **`createWorkspace`
took a name and nothing else**, so the only required step in the whole flow
could not be built.

## ⚡ One column, one unique index, no new concept

**`workspace.slug`, `varchar(63)`, `NOT NULL`, `UNIQUE`.** ⛔ **No new table and
no new module** — a workspace's address is a property of the workspace, and
anything else would be a second place to look for one string.

## 🔴 Why the backfill is `id`-derived and not name-derived

**Existing rows need a value before the column can be `NOT NULL`.** ⚠️ **The
obvious backfill — slugify the name — is wrong here for two reasons**:

⛔ **It is not unique.** Two workspaces called *Playground* are ordinary in a
development database and a collision would abort the migration halfway.

⛔ **It would publish a name that was never chosen as an address.** 📁 The
design's slug is *"permanent once created"*, and inventing a permanent public
identifier out of a display name is a product decision this migration is not
entitled to make.

✅ **So an existing row gets `w-<first 8 of its id>`** — **unique by
construction, obviously machine-made, and clearly not something a customer
picked.** ⚡ **Every workspace created after this migration gets the slug its
owner actually typed.**

## ✅ Reversible, and the down is honest about what it costs

**`downgrade()` drops the column.** ⚠️ **LIMITATION: the slugs are not
recoverable** — 📁 the same shape the Slice Handoff for `0021` recorded. **The
workspaces survive; the addresses do not.**

## ⛔ No tenancy-policy change

📁 `workspace` is the tenancy ROOT and is already registered — it composes no
`WorkspaceScopedMixin` because a workspace cannot be scoped to itself
(`11-tenancy.md`). **Adding a column to a classified table changes nothing
about its classification**, and `tenancy_policy.py` is deliberately untouched.

⚠️ **Numbered `0062` rather than `0061`.** 📁 Lane C holds `0061_webhook_delivery`
on `lane-c-sync`, **checked before writing this rather than after**
([C-201](../../../docs/LANE_COORDINATION.md) is what the collision costs, and
they renumbered around Lane A's `0060` earlier the same day).

🔴 **`down_revision` is `0060`, which is this branch's real head, and it
RE-PARENTS to `0061` on the rebase that brings Lane C's work in.** ⛔ **Pointing
at `0061` today would break `alembic upgrade head` on every clone that does not
have it** — a chain is only linear against the tree it is standing in. ⚡ **The
number is already conflict-free; only the parent moves**, which is the smaller
half and the one a rebase is for.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0062"
down_revision: str | None = "0060"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # ⚡ **Nullable first, backfilled, then tightened.** ⛔ A `NOT NULL` column
    # added in one step against a non-empty table fails, and the failure is
    # only visible on a database that has rows — which a fresh clone does not.
    op.add_column("workspace", sa.Column("slug", sa.String(length=63), nullable=True))

    op.execute(
        sa.text(
            "UPDATE workspace SET slug = 'w-' || substr(replace(id::text, '-', ''), 1, 8) "
            "WHERE slug IS NULL"
        )
    )

    op.alter_column("workspace", "slug", nullable=False)
    # 🔴 **The unique index is the guarantee.** 📁 Screen `03`'s availability
    # check is a courtesy that saves somebody from discovering the collision
    # after they press Create — **it is not what makes the slug unique**, and a
    # check without this constraint would lose the race it exists to describe.
    op.create_unique_constraint("uq_workspace_slug", "workspace", ["slug"])


def downgrade() -> None:
    op.drop_constraint("uq_workspace_slug", "workspace", type_="unique")
    op.drop_column("workspace", "slug")
