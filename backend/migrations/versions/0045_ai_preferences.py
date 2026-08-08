"""workspace_tenancy: what a person chose about how Signora reasons for them

Revision ID: 0045
Revises: 0044
Create Date: 2026-08-08

**[TASK-470] · Workflow 9 · screen `04 AI preferences`.** Five columns on the
table `0044` created — **not a second table**, because they are the same
person's choices in the same workspace and splitting them would give one
aggregate two rows to keep in step.

### ⚡ Every default is the conservative end, and that is the design's rule

> ***"Consent is never inferred."***

**So a preference nobody has expressed must not read as one they granted.**
`always_show_citations` is `false` and the floor is `3` — both as drawn.

⚠️ **`ai_insights` and `ai_drafts` default `true`, and that is not a
contradiction.** Neither is a permission over the customer's data: insights
rank what Signora already read, and *"drafts open in your composer — **nothing
is ever sent on your behalf**"*. **The sentence that makes drafting safe is a
property of the product, not of this flag.**

### ⛔ What is deliberately NOT a column

**A workspace AI policy.** The design draws two rows this table cannot hold:
*"Write risk flags to the CRM — switched off for everyone in this workspace"*
is a **workspace** setting and none exists, and *"use my calls to improve the
model — off across all customers, and this cannot be switched on"* is a
**product** fact rather than a stored choice. ⛔ **A column for either would
make a policy look like a preference somebody could change** — recorded at
[C-249].

### The four verifications

| | |
|---|---|
| **Data preservation** | Five nullable-with-default columns on an existing
  table. **No existing row's values change**; every one gains the defaults it
  already behaved as |
| **Behaviour preservation** | Nothing reads them before this row's own panel |
| **Capability expansion** | A person decides how much Signora volunteers, and
  how it answers |
| **Rollback safety** | Dropping them returns everybody to those same
  defaults. **Verified down and up** |

[TASK-470]: ../../../docs/BACKLOG.md
[C-249]: ../../../docs/LANE_COORDINATION.md
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0045"
down_revision: str | None = "0044"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None

TABLE = "person_preferences"


def upgrade() -> None:
    op.add_column(
        TABLE, sa.Column("ai_insights", sa.Boolean(), nullable=False, server_default=sa.true())
    )
    op.add_column(
        TABLE, sa.Column("ai_drafts", sa.Boolean(), nullable=False, server_default=sa.true())
    )
    op.add_column(
        TABLE,
        sa.Column("always_show_citations", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.add_column(
        TABLE,
        sa.Column("answer_style", sa.String(length=16), nullable=False, server_default="direct"),
    )
    op.add_column(
        TABLE, sa.Column("confidence_floor", sa.Integer(), nullable=False, server_default="3")
    )
    # ⛔ **Bounded here as well as in the enum and the schema.** The design's
    # control offers three values; anything else is a floor nothing can act on.
    op.create_check_constraint(
        f"ck_{TABLE}_confidence_floor", TABLE, "confidence_floor BETWEEN 3 AND 5"
    )
    op.create_check_constraint(
        f"ck_{TABLE}_answer_style", TABLE, "answer_style IN ('direct', 'detailed')"
    )


def downgrade() -> None:
    op.drop_constraint(f"ck_{TABLE}_answer_style", TABLE, type_="check")
    op.drop_constraint(f"ck_{TABLE}_confidence_floor", TABLE, type_="check")
    for column in (
        "confidence_floor",
        "answer_style",
        "always_show_citations",
        "ai_drafts",
        "ai_insights",
    ):
        op.drop_column(TABLE, column)
