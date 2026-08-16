"""workspace_tenancy: the rest of what a person chose about their own profile.

📁 **The finalized design, `Fortune Signora User Profile.dc.html`** — two of its
nine sections were unbuildable because the columns behind them did not exist:
**Language & region**'s last three fields, and **Accessibility** entire.

## ⛔ Profile's three remaining fields are NOT here, and that is a decision rather than an omission

⚠️ **The first version of this migration added `job_title`, `department` and
`mobile`, and it was wrong.** 📁 **The design marks Job title and Department
`tagLocked` — *"From directory"* — and no directory exists**
([C-248](../../../docs/LANE_COORDINATION.md),
[D-156](../../../docs/DECISION_REGISTER.md) ④): **a locked field with no sync
behind it is a rule the product does not have, painted as one it does.** ⛔
**Mobile is noted *"Verified 14 Mar 2026"*, and nothing verifies a number.**

✅ **`profile.test.tsx` already asserted their absence with those reasons**, and
the columns were removed rather than left unused — **three columns nothing can
write are the speculative shape [§6](../../../CLAUDE.md) forbids.**

## ⚡ Nine columns, one shape, no new concept

📁 **`0045_ai_preferences` is the pattern and it is followed exactly**: columns
on `person_preferences`, `server_default` for every one, and a `CHECK` wherever
the design enumerates the values.

⛔ **No new table, no new module, no enum type in the database.** ⚠️ The
`person_preferences` tenancy policy from `0044` covers these automatically —
**they are columns on a table that is already person-scoped**, which is the
whole reason this is one migration rather than a design discussion.

## 🔴 Where the design enumerates, this constrains. Where it does not, it stores text.

✅ **`text_size` and `screen_reader_verbosity` carry `CHECK` constraints**,
because the design's segmented controls name their options — *100% · 112% ·
125%* and *Concise · Detailed*.

⛔ **`date_format`, `number_format` and `week_starts_on` are nullable text and
carry no constraint.** ⚡ **The design shows ONE value for each** — *"31 Dec
2026"*, *"1.234,56"*, *"Monday"* — **and never lists the options.** ⚠️
**Inventing a `DateFormat` enum from a single sample would decide which formats
Signora supports**, which is a product question this migration is not entitled
to answer. 📁 **`language` and `timezone` are already stored this way**, on the
same table, for the same reason.

## ⚠️ `reduce_motion` defaults to FALSE, and the design's *"from system"* is not lost

📁 The design shows *"On — from system"*. ⛔ **Defaulting the COLUMN to true
would force reduced motion on every person who has never opened the screen.**

✅ **The system half already works and needs no column**: `app/globals.css`
carries `@media (prefers-reduced-motion: reduce)` and the shell uses
`motion-reduce:` variants throughout. ⚡ **So this column is the OVERRIDE — *on
regardless of what the device says* — and the absence of one leaves the existing
media query in charge.** **Nothing is stored to say what the browser already
knows** ([§2](../../../CLAUDE.md), *hidden inputs are architecture defects*: the
device's setting is the device's to report).
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0060"
down_revision: str | None = "0059"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

TABLE = "person_preferences"

#: 📁 The design's segmented control: *100% · 112% · 125%*.
TEXT_SIZES = ("100", "112", "125")
#: 📁 The design's segmented control: *Concise · Detailed*.
VERBOSITIES = ("concise", "detailed")

#: ⚡ **Free text, deliberately** — the design shows one value each and
#: enumerates none. Same treatment as `language` and `timezone`.
_TEXT_COLUMNS = ("date_format", "number_format", "week_starts_on")

#: ⚡ **Toggles.** ⛔ `underline_links` is the one that defaults ON: the design
#: shows it on, and links that stop being underlined for somebody who never
#: opened this screen would be a regression delivered by a migration.
_FLAGS = (
    ("reduce_motion", sa.false()),
    ("increase_contrast", sa.false()),
    ("always_show_focus_ring", sa.false()),
    ("underline_links", sa.true()),
)


def upgrade() -> None:
    for name in _TEXT_COLUMNS:
        # ⚠️ **Nullable, and null means *not chosen*** — not a default dressed
        # as an answer. The surface renders what the person picked or nothing.
        op.add_column(TABLE, sa.Column(name, sa.String(length=120), nullable=True))

    for name, default in _FLAGS:
        op.add_column(
            TABLE, sa.Column(name, sa.Boolean(), nullable=False, server_default=default)
        )

    op.add_column(
        TABLE,
        sa.Column("text_size", sa.String(length=8), nullable=False, server_default="100"),
    )
    op.add_column(
        TABLE,
        sa.Column(
            "screen_reader_verbosity",
            sa.String(length=16),
            nullable=False,
            server_default="detailed",
        ),
    )

    # 🔴 **The database refuses a value the design does not name.** ⛔ A column
    # that accepted `"200"` would let a surface render a size no stylesheet
    # implements, and the defect would reach a customer rather than a test.
    op.create_check_constraint(
        f"ck_{TABLE}_text_size",
        TABLE,
        sa.column("text_size").in_(TEXT_SIZES),
    )
    op.create_check_constraint(
        f"ck_{TABLE}_screen_reader_verbosity",
        TABLE,
        sa.column("screen_reader_verbosity").in_(VERBOSITIES),
    )


def downgrade() -> None:
    op.drop_constraint(f"ck_{TABLE}_screen_reader_verbosity", TABLE, type_="check")
    op.drop_constraint(f"ck_{TABLE}_text_size", TABLE, type_="check")
    for name in ("screen_reader_verbosity", "text_size"):
        op.drop_column(TABLE, name)
    for name, _ in _FLAGS:
        op.drop_column(TABLE, name)
    for name in _TEXT_COLUMNS:
        op.drop_column(TABLE, name)
