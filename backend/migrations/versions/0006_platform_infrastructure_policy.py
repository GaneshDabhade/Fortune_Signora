"""platform: infrastructure tables are owned by platform services only

Revision ID: 0006
Revises: 0005
Create Date: 2026-07-28

Implements the ratified Platform Infrastructure Policy
(docs/architecture/11-tenancy.md, "Platform Infrastructure Tables").

Infrastructure-owned tables — ``outbox_event``, ``processed_event``,
``dead_letter_event``, ``alembic_version`` — belong to platform services.
Business modules must never read them. Until now ``signora_app`` held full
DML on all of them, which meant an unfiltered ``SELECT * FROM
outbox_event`` in any module returned **every workspace's event payloads**:
these tables carry ``workspace_id`` but deliberately have no RLS, because
the relay must sweep all workspaces in a single pass.

The fix is to split read from write along the line the architecture already
draws:

* the **application** publishes — ``INSERT`` on ``outbox_event``, and
  ``INSERT`` on ``dead_letter_event`` so a worker can record a permanently
  failed event;
* the **relay** consumes — ``SELECT``/``UPDATE`` on ``outbox_event`` and
  full access to ``dead_letter_event`` for replay, under its own identity;
* neither can bypass RLS.

``processed_event`` keeps ``SELECT`` for ``signora_app``: the idempotency
claim is ``INSERT ... ON CONFLICT DO NOTHING``, and PostgreSQL requires
``SELECT`` on the table to evaluate the conflict target. Verified
empirically — revoking it fails the claim with "permission denied". The
ledger holds no payload, only ``(consumer_name, event_id)``, so this is not
a cross-tenant read path.
"""

from collections.abc import Sequence

from alembic import op

revision: str = "0006"
down_revision: str | None = "0005"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None

APP_ROLE = "signora_app"
RELAY_ROLE = "signora_relay"


def upgrade() -> None:
    op.execute(
        f"""
        DO $$
        BEGIN
          IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = '{RELAY_ROLE}') THEN
            CREATE ROLE {RELAY_ROLE} NOLOGIN;
          END IF;
        END
        $$
        """
    )
    # The relay is privileged with respect to *platform* tables, never with
    # respect to tenant data. It reads events across all workspaces because
    # that is its job; it must still be unable to read a workspace's rows.
    op.execute(f"ALTER ROLE {RELAY_ROLE} NOBYPASSRLS")
    op.execute(f"GRANT USAGE ON SCHEMA public TO {RELAY_ROLE}")

    op.execute(f"GRANT SELECT, UPDATE ON outbox_event TO {RELAY_ROLE}")
    op.execute(f"GRANT SELECT, INSERT, UPDATE, DELETE ON dead_letter_event TO {RELAY_ROLE}")
    op.execute(f"GRANT SELECT, INSERT ON processed_event TO {RELAY_ROLE}")
    op.execute(f"GRANT SELECT ON alembic_version TO {RELAY_ROLE}")

    # The application publishes and nothing more. Revoking everything first
    # makes the resulting grant exact rather than additive — a later reading
    # of this migration should not have to reconstruct the prior state to
    # know what the role ends up holding.
    op.execute(f"REVOKE ALL ON outbox_event FROM {APP_ROLE}")
    op.execute(f"GRANT INSERT ON outbox_event TO {APP_ROLE}")

    op.execute(f"REVOKE ALL ON dead_letter_event FROM {APP_ROLE}")
    op.execute(f"GRANT INSERT ON dead_letter_event TO {APP_ROLE}")

    op.execute(f"REVOKE ALL ON processed_event FROM {APP_ROLE}")
    op.execute(f"GRANT SELECT, INSERT ON processed_event TO {APP_ROLE}")


def downgrade() -> None:
    op.execute(f"REVOKE ALL ON outbox_event FROM {RELAY_ROLE}")
    op.execute(f"REVOKE ALL ON dead_letter_event FROM {RELAY_ROLE}")
    op.execute(f"REVOKE ALL ON processed_event FROM {RELAY_ROLE}")
    op.execute(f"REVOKE SELECT ON alembic_version FROM {RELAY_ROLE}")
    op.execute(f"REVOKE USAGE ON SCHEMA public FROM {RELAY_ROLE}")

    for table in ("outbox_event", "processed_event", "dead_letter_event"):
        op.execute(f"GRANT SELECT, INSERT, UPDATE, DELETE ON {table} TO {APP_ROLE}")

    # The role is not dropped: it may hold grants in other databases, and
    # dropping a role that still owns anything fails confusingly.
