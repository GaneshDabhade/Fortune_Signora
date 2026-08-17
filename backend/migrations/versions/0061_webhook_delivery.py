"""A customer's endpoint is owed a delivery — [TASK-1481](../../../docs/BACKLOG.md).

📁 **The design's whole specification, one sentence** — `Fortune Signora
Settings.dc.html`, *API keys & webhooks*:

    "Failed webhook deliveries retry with backoff for 24 hours, then park with
     the payload retained."

## ⚠️ Renumbered `0060` → `0061`, and the reason is worth two lines

**Lane A's `0060_profile_locale_accessibility` claimed `0060` from `0059` and
promoted first.** 📁 [§20e](../../../CLAUDE.md) exempts migrations from the
identifier-block scheme precisely so this stays dense: *"Alembic's
`down_revision` is a linear chain, so a gap is not a cosmetic oddity but a
broken migration graph … the chain is the identity; the filename follows it."*
✅ **QE flagged the collision before it was hit**, which is why it cost a
rename rather than a debugging session.

## 🔴 Tenant-owned, and its former neighbours are not

⚠️ **`outbox_event`, `processed_event` and `dead_letter_event` are
`PLATFORM_INFRASTRUCTURE_TABLES`** — 📁 [§8](../../../CLAUDE.md): *"the
application role publishes (`INSERT`) and cannot read"*. ⛔ **This table was
first written beside them, in `signora_platform/event_bus/`, and classified the
opposite way** — which is what made [C-108](../../../docs/LANE_COORDINATION.md)
a question. ✅ **It now lives in its own bounded context**,
`modules/webhook_delivery/`, on the product owner's 2026-08-17 ruling and the
[D-237](../../../docs/DECISION_REGISTER.md) precedent.

⚡ **The design decides it, not the neighbourhood.** 📁 The *API keys &
webhooks* table has a **`State`** column and a **`Last used`** column, on a
screen a customer opens. ⛔ **A row `signora_app` cannot read is a column that
renders nothing** — so this is `TENANT_OWNED`, with `workspace_id`, RLS, forced
RLS, and a policy per command.

> ✅ **The distinction that makes both correct: a dead letter is the
> *platform's* account of its own behaviour; a webhook delivery is the
> *customer's* record of something they configured and are owed.**

## ⚡ `UPDATE` is granted here, and that is not a lapse of the immutability rule

📁 [§2](../../../CLAUDE.md) makes immutability the default *"for anything that
records a fact"* — and names **workflow state** as a distinct data category
from operational history. ⛔ **A delivery in flight is not a fact that
happened; it is a commitment being worked.** ⚡ Its state genuinely changes:
`pending` → `pending` (one backoff later) → `delivered` or `parked`.

⛔ **What is immutable is the `payload`**, and the design says so in the same
sentence that sets the window — *"park with the payload retained"*. **A parked
delivery whose payload a customer cannot inspect is indistinguishable from one
that was dropped.**

## ✅ `DELETE` — the same answer this repository gave one table ago

📁 `test_tenancy_policy.py`: *"erasability is a property of the TENANCY model,
not of what a row means: a workspace that cannot be deleted is a retention
problem on every table it owns."* ⚡ **`0059` learned this by being refused.
This one is granted from the start.**
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "0061"
down_revision: str | None = "0060"
branch_labels: str | None = None
depends_on: str | None = None

APP_ROLE = "signora_app"
TABLE = "webhook_delivery"

_WORKSPACE = "workspace_id = NULLIF(current_setting('app.workspace_id', true), '')::uuid"


def upgrade() -> None:
    op.create_table(
        TABLE,
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("workspace_id", postgresql.UUID(as_uuid=True), nullable=False),
        # ⚡ **Which endpoint this was owed to.** ⛔ Identity only — the URL and
        # its scope belong to the endpoint's own row, and a copy here would be
        # the one somebody edits and the other one does not.
        sa.Column("endpoint_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("event_type", sa.String(length=255), nullable=False),
        # 🔴 **Retained through parking — the design says so.**
        sa.Column("payload", postgresql.JSONB(), nullable=False),
        # 📁 `webhook_delivery.DeliveryState` — pending · delivered · parked.
        # ⛔ Stored as text rather than a PostgreSQL enum: adding a state to an
        # enum needs a migration on a table that may be large, and the values
        # are the module's to define.
        sa.Column("state", sa.String(length=16), nullable=False),
        # ⚡ **The window runs from HERE, never from the last attempt** — a
        # per-attempt window lets a delivery extend its own deadline by failing.
        sa.Column("first_attempted_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("attempts", sa.Integer(), nullable=False),
        # ⛔ **Non-null exactly while `pending`** — a pending row with no
        # scheduled attempt is one nothing will ever pick up, which is the shape
        # that loses deliveries silently. Asserted by the check below rather
        # than remembered.
        sa.Column("next_attempt_at", sa.DateTime(timezone=True), nullable=True),
        # 📁 The design's `Last used` column.
        sa.Column("last_attempted_at", sa.DateTime(timezone=True), nullable=True),
        # ⚡ **Why it is where it is**, in words an operator can act on ([§17](../../../CLAUDE.md)).
        sa.Column("last_failure_reason", sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.CheckConstraint(
            "(state = 'pending') = (next_attempt_at IS NOT NULL)",
            name=f"ck_{TABLE}_pending_has_next_attempt",
        ),
        sa.CheckConstraint(
            "state IN ('pending', 'delivered', 'parked')",
            name=f"ck_{TABLE}_state",
        ),
    )

    # ⚡ **The worker's only query**: *what is due, oldest first.* ⛔ Partial, on
    # `pending` alone — a delivered or parked row is never claimed again, and an
    # index carrying them grows without ever being read.
    op.create_index(
        f"ix_{TABLE}_due",
        TABLE,
        ["next_attempt_at"],
        postgresql_where=sa.text("state = 'pending'"),
    )
    # 📁 The Settings screen's query: this workspace's endpoints, newest first.
    op.create_index(
        f"ix_{TABLE}_endpoint",
        TABLE,
        ["workspace_id", "endpoint_id", sa.text("first_attempted_at DESC")],
    )

    op.execute(f"ALTER TABLE {TABLE} ENABLE ROW LEVEL SECURITY")
    op.execute(f"ALTER TABLE {TABLE} FORCE ROW LEVEL SECURITY")
    op.execute(f"GRANT SELECT, INSERT, UPDATE, DELETE ON {TABLE} TO {APP_ROLE}")

    op.execute(f"CREATE POLICY {TABLE}_select ON {TABLE} FOR SELECT USING ({_WORKSPACE})")
    op.execute(f"CREATE POLICY {TABLE}_insert ON {TABLE} FOR INSERT WITH CHECK ({_WORKSPACE})")
    # ⚡ **Both halves.** ⛔ `USING` alone would let a row be updated INTO another
    # workspace — the check that a policy with one clause silently omits.
    op.execute(
        f"CREATE POLICY {TABLE}_update ON {TABLE} FOR UPDATE "
        f"USING ({_WORKSPACE}) WITH CHECK ({_WORKSPACE})"
    )
    op.execute(f"CREATE POLICY {TABLE}_delete ON {TABLE} FOR DELETE USING ({_WORKSPACE})")


def downgrade() -> None:
    op.execute(f"DROP POLICY IF EXISTS {TABLE}_delete ON {TABLE}")
    op.execute(f"DROP POLICY IF EXISTS {TABLE}_update ON {TABLE}")
    op.execute(f"DROP POLICY IF EXISTS {TABLE}_insert ON {TABLE}")
    op.execute(f"DROP POLICY IF EXISTS {TABLE}_select ON {TABLE}")
    op.execute(f"REVOKE ALL ON {TABLE} FROM {APP_ROLE}")
    op.drop_index(f"ix_{TABLE}_endpoint", table_name=TABLE)
    op.drop_index(f"ix_{TABLE}_due", table_name=TABLE)
    op.drop_table(TABLE)
