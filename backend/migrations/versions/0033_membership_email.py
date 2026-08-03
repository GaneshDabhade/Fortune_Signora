"""workspace_tenancy: a membership remembers the address it was created with

Revision ID: 0033
Revises: 0032
Create Date: 2026-08-03

**The roster could not name anybody.** `GET /members` returned `user_id` and
`role`, and rendering identifiers would be a table of UUIDs pretending to be a
team ([C-203](../../docs/LANE_COORDINATION.md)).

**The address is a fact about how the membership came to exist**, not a mirror
of somebody's profile — which is the distinction that keeps it inside §13. A
display name is Better Auth's and would go stale; *the address this membership
was created with* is a historical fact about an act, and stays true forever.

Two sources, both already present and neither a new capability:

| | |
|---|---|
| **The founder** | `create_workspace` runs under a verified token, and `AuthenticatedPrincipal.email` has carried the address since M1.2 |
| **Everybody after them** | The invitation they accepted, which records the address an administrator typed (migration `0031`) |

**Nullable, and no backfill.** Memberships created by `POST /members` were
given a `user_id` and no address; **inventing one would be exactly what
`0029`'s watermark refused** — *"existing rows keep an empty subject rather
than a guessed one"*. A row without an address renders as *"Somebody here"*,
which is the wording the product has used since D23.

### The four verifications

| | |
|---|---|
| **Data preservation** | One nullable column. No row is written, moved or dropped |
| **Behaviour preservation** | Every existing membership reads `NULL` and renders exactly as it did — which was *nothing*, because there was no roster |
| **Capability expansion** | An owner can see who is in their organization, by address |
| **Rollback safety** | Dropping the column loses only addresses that can be recovered — the founder's from the token on next sign-in, everybody else's from the invitation they accepted. **Nothing unrecoverable is lost** |
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0033"
down_revision: str | None = "0032"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None

TABLE = "membership"


def upgrade() -> None:
    op.add_column(TABLE, sa.Column("member_email", sa.String(320), nullable=True))


def downgrade() -> None:
    op.drop_column(TABLE, "member_email")
