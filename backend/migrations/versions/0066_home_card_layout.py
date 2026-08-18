"""workspace_tenancy: how a person arranged Home's cards

Revision ID: 0066
Revises: 0065
Create Date: 2026-08-18

**`Fortune Signora Home.dc.html` §10 — the *Customise* control.**

### 📁 The rules this column exists for

> **§10, keyboard**: *"**Customise** — opens the card-order panel as a drawer.
> Escape closes and returns focus to the trigger."* `⌘⇧H`
>
> **`3.2.3`**: *"**Card order within a composition is stable across visits.**
> Completed activation cards hold position rather than reordering."*
>
> **`U-05`, interim ruling**: *"**reorder and remove only.** Adding
> cross-composition cards is out of scope for the first implementation."*

### 🔴 Why `JSONB` rather than a table

⚡ **The value is one person's arrangement of one screen**, read whole and written
whole. ⛔ **A `home_card_position` table would be rows nothing ever queries across**
— no report asks *"which cards do people remove?"* — and it would put Home's card
catalogue into the database schema, where the next card Signora ships would need a
migration to be arrangeable.

### ⛔ The card ids are Home's, and this module does not know them

📁 **Home is the composition authority** and its registry lives in the frontend.
**This column stores what the person arranged and validates shape and bounds
only** — a catalogue here would be the duplication [§2] forbids, and it would
reject every card shipped after the migration ran.

### ⚡ Two lists per composition, and one would not do

**`{"seller": {"order": [...], "hidden": [...]}}`.** ⛔ **A single list of kept
cards cannot tell *removed* from *added since*** — so a person who customised in
August would silently never see a card shipped in September. ✅ **A card in
neither list is new**, and Home draws it at its registry position.

### The four verifications

| | |
|---|---|
| **Data preservation** | One column with a `{}` default and a server default to
  match. **No existing row loses anything**, and `{}` reads as *never
  customised* — which every existing row is |
| **Behaviour preservation** | Nothing reads it before this row. **Home renders
  the registry's own order today**, and an empty map means exactly that |
| **Capability expansion** | A person can put the card they never use out of the
  way, and it stays that way — 📁 `3.2.3`'s *"stable across visits"* |
| **Rollback safety** | Dropping it returns everybody to the registry order.
  ⚠️ **An arrangement is lost, and that is stated rather than glossed**: it is a
  preference, not a record of anything that happened |

[§2]: ../../../CLAUDE.md
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0066"
down_revision: str | None = "0065"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None

TABLE = "person_preferences"
COLUMN = "home_layout"


def upgrade() -> None:
    # ⚡ **`NOT NULL` with a server default of `{}`**, rather than nullable.
    # ⛔ `NULL` and `{}` would both mean *never customised*, and two spellings of
    # one absence is the ambiguity every reader then has to handle twice.
    op.add_column(
        TABLE,
        sa.Column(
            COLUMN,
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
    )


def downgrade() -> None:
    op.drop_column(TABLE, COLUMN)
