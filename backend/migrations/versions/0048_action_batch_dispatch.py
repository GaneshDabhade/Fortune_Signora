"""The Action Batch records dispatch and failure — TASK-465, slice 5.

**Two transitions join the alphabet**, because applying became asynchronous and
the gap between *approved* and *applied* is now a thing a customer watches:

* ``dispatched`` — the application was **durably accepted** and handed to a
  worker. §14: *a handler responds once the request has been durably accepted,
  never after the work.*
* ``application_failed`` — the work did not run, with the reason recorded.
  P-A, which 455 applies to this slice by name: **still running and failed to
  start must never render alike.**

**The column is widened from 16 to 32 characters, and that is the deliberate
half.** ``application_failed`` is 18, so the existing width would have decided
the domain's vocabulary for it — and a transition named ``failed`` to fit a
column is exactly the kind of quiet compromise §4 forbids, because the word
that reaches the log is the word a customer reads in a history. Widening a
``varchar`` is additive and reversible; renaming a domain verb is neither.

**Both new transitions are unattributed**, which is why the second constraint
changes too. Application already had no actor, on the authority of the approval
already recorded; dispatch and failure are performed by the same authority. **A
worker is not an actor**, and naming the approver as the author of a background
failure would put a false name in a history somebody may have to defend.

**A nullable ``reason`` column joins the log**, holding the sentence a failed
application records. It is the one thing about a failure the aggregate cannot
recompute — every other transition derives entirely from the batch — and P-A
needs it so the screen can say more than *something went wrong*.

**No data migration.** Every existing row carries one of the five original
transitions and stays valid under the widened constraint — the change only
admits more, never re-interprets what is there.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0048"
down_revision: str | None = "0047"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

TRANSITION = "action_batch_transition"

#: The alphabet after this migration. **Kept in the order the domain declares
#: them**, so a reader comparing the two files is comparing like with like.
TRANSITIONS = (
    "approved",
    "rejected",
    "withdrawn",
    "dispatched",
    "applied",
    "application_failed",
    "reversed",
)
BEFORE = ("approved", "rejected", "withdrawn", "applied", "reversed")

#: **The transitions performed on the authority of an approval already
#: recorded**, rather than by a person deciding again.
UNATTRIBUTED = ("dispatched", "applied", "application_failed")

_KNOWN = "ck_action_batch_transition_is_a_known_transition"
_ATTRIBUTION = "ck_action_batch_transition_only_application_is_unattributed"


def _known(values: Sequence[str]) -> str:
    return " OR ".join(f"transition = '{value}'" for value in values)


def _unattributed(values: Sequence[str]) -> str:
    listed = ", ".join(f"'{value}'" for value in values)
    return f"actor_id IS NOT NULL OR transition IN ({listed})"


def upgrade() -> None:
    # **Nullable, so every existing row is already valid.** Only an
    # `application_failed` transition ever carries one.
    op.add_column(TRANSITION, sa.Column("reason", sa.Text(), nullable=True))

    # **Widen before the constraint admits the longer value.** The reverse
    # order would create a moment where a permitted value could not be stored.
    op.alter_column(
        TRANSITION,
        "transition",
        existing_type=sa.String(length=16),
        type_=sa.String(length=32),
        existing_nullable=False,
    )

    op.drop_constraint(_KNOWN, TRANSITION, type_="check")
    op.create_check_constraint(_KNOWN, TRANSITION, _known(TRANSITIONS))

    op.drop_constraint(_ATTRIBUTION, TRANSITION, type_="check")
    op.create_check_constraint(_ATTRIBUTION, TRANSITION, _unattributed(UNATTRIBUTED))


def downgrade() -> None:
    """**Reversible, and it says what reversing would cost.**

    ⚠️ Downgrading with any ``dispatched`` or ``application_failed`` row stored
    will fail on the narrowed constraint — **loudly, which is correct**. Those
    rows are history: an application that was accepted or that failed really
    happened, and silently deleting them to make a schema fit would be the
    falsified history §2 forbids.
    """
    op.drop_constraint(_ATTRIBUTION, TRANSITION, type_="check")
    op.create_check_constraint(_ATTRIBUTION, TRANSITION, _unattributed(("applied",)))

    op.drop_constraint(_KNOWN, TRANSITION, type_="check")
    op.create_check_constraint(_KNOWN, TRANSITION, _known(BEFORE))

    op.alter_column(
        TRANSITION,
        "transition",
        existing_type=sa.String(length=32),
        type_=sa.String(length=16),
        existing_nullable=False,
    )

    op.drop_column(TRANSITION, "reason")
