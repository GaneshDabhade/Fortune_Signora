"""people: person and affiliation

Revision ID: 0040
Revises: 0039
Create Date: 2026-08-06

**The first table in a new bounded context**, ratified by
[ADR-0400](../../../docs/architecture/adr/0400-person-as-an-entity.md) and
approved at this scope by [D-074](../../../docs/DECISION_REGISTER.md) — *"I
approve moving the People domain implementation earlier in the roadmap. I am
not approving the full People Intelligence feature set."*

**`person` holds an identity and nothing else, and the emptiness is the
design.** No name, no email, no phone, no provider identifier
([C-221](../../../docs/LANE_COORDINATION.md)). Two customers tracking the same
real human hold two unrelated rows — one workspace's evidence must never
become another's, and a shared person row would be the tenancy defect the whole
platform exists to refuse.

**`affiliation` is where the intelligence lives**, and it is an interval rather
than a field. The ADR's load-bearing sentence:

> ***"Priya left Acme"* is not a mutation of Priya — it is an interval
> closing.** Storing a current employer as a field would destroy the history
> the entire product is built on, and would be **the one place in this
> repository where a state change overwrites its own evidence.**

So there is deliberately **no `current_employer` column anywhere here**, and
`ended_on` is nullable because most affiliations will never see a departure.

### Why `UPDATE` is granted here, when most tables refuse it

**Closing an interval is the one legitimate in-place change in this module**,
and it is not an edit of a fact: `started_on`, `title`, `company_id` and
`person_id` are never touched, and `ended_on` moves exactly once — from `NULL`
to a date. **The check constraint makes the only harmful direction impossible**
(`ended_on >= started_on`), and the domain refuses a second close so a
re-closing surfaces as a matching defect rather than overwriting the first.

**Recorded rather than assumed**, because every neighbouring immutable table
withholds `UPDATE` and a reader will ask why this one does not. The alternative
— an append-only interval log superseded on close — was rejected as premature:
nothing yet reads an affiliation's history *of revisions*, only its interval,
and a superseding chain nobody queries is structure without a consumer (§6).
**If a consumer for that history appears, this is the table that changes.**

### No person is joinable to a `Member`

`workspace_tenancy` holds Signora's own users; this holds people at target
accounts who have never heard of Signora. **Different lawful basis, different
lifecycle**, and no foreign key between them in either direction — pinned by
an import contract and a test rather than by this comment.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0040"
down_revision: str | None = "0039"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None

APP_ROLE = "signora_app"
PERSON = "person"
AFFILIATION = "affiliation"


def _tenancy(table: str, *, updatable: bool) -> None:
    grants = "SELECT, INSERT, DELETE" + (", UPDATE" if updatable else "")
    op.execute(f"GRANT {grants} ON {table} TO {APP_ROLE}")
    op.execute(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY")
    op.execute(f"ALTER TABLE {table} FORCE ROW LEVEL SECURITY")
    tenant = "workspace_id = NULLIF(current_setting('app.workspace_id', true), '')::uuid"
    op.execute(f"CREATE POLICY {table}_select ON {table} FOR SELECT USING ({tenant})")
    op.execute(f"CREATE POLICY {table}_insert ON {table} FOR INSERT WITH CHECK ({tenant})")
    op.execute(f"CREATE POLICY {table}_delete ON {table} FOR DELETE USING ({tenant})")
    if updatable:
        # Both halves. `USING` decides which rows are visible to update and
        # `WITH CHECK` decides what they may become — without the second, a
        # row could be updated *out* of its own workspace.
        op.execute(
            f"CREATE POLICY {table}_update ON {table} FOR UPDATE "
            f"USING ({tenant}) WITH CHECK ({tenant})"
        )


def _audit_columns() -> list[sa.Column]:  # type: ignore[type-arg]
    return [
        sa.Column("workspace_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("updated_by", postgresql.UUID(as_uuid=True), nullable=False),
    ]


def upgrade() -> None:
    op.create_table(
        PERSON,
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        *_audit_columns(),
    )
    op.create_index(f"ix_{PERSON}_workspace_id", PERSON, ["workspace_id"])
    _tenancy(PERSON, updatable=False)

    op.create_table(
        AFFILIATION,
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "person_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey(f"{PERSON}.id", ondelete="CASCADE"),
            nullable=False,
        ),
        # **No foreign key to `entity`.** The company is the Knowledge Graph's
        # and this module may not import it; a constraint across a boundary
        # neither module owns would make one context's migration depend on the
        # other's table shape. The id is carried and joined at read time, the
        # same way every other module cites an entity.
        sa.Column("company_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("seniority", sa.String(length=64), nullable=False),
        sa.Column("started_on", sa.Date(), nullable=False),
        # Nullable, and `NULL` means *no departure has been observed* — which
        # is a different claim from *"they still work there"*, and only the
        # first is one this module can make.
        sa.Column("ended_on", sa.Date(), nullable=True),
        *_audit_columns(),
        sa.CheckConstraint(
            "ended_on IS NULL OR ended_on >= started_on",
            name=f"ck_{AFFILIATION}_ends_after_it_starts",
        ),
        sa.CheckConstraint(
            "length(trim(title)) > 0", name=f"ck_{AFFILIATION}_title_is_not_blank"
        ),
    )
    op.create_index(f"ix_{AFFILIATION}_workspace_id", AFFILIATION, ["workspace_id"])
    # The one query the matching rule makes: *"which open affiliations does
    # this company have?"* Partial on `ended_on IS NULL` because a closed
    # affiliation is never a candidate and the open set stays small.
    op.create_index(
        f"ix_{AFFILIATION}_open_at_company",
        AFFILIATION,
        ["workspace_id", "company_id"],
        postgresql_where=sa.text("ended_on IS NULL"),
    )
    op.create_index(f"ix_{AFFILIATION}_person", AFFILIATION, ["workspace_id", "person_id"])
    _tenancy(AFFILIATION, updatable=True)


def downgrade() -> None:
    op.execute(f"REVOKE ALL ON {AFFILIATION} FROM {APP_ROLE}")
    op.drop_table(AFFILIATION)
    op.execute(f"REVOKE ALL ON {PERSON} FROM {APP_ROLE}")
    op.drop_table(PERSON)
