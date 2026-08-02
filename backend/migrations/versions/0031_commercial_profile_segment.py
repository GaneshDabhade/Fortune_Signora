"""commercial_profile: icp segments — identity, versions, products, lifecycle

Revision ID: 0031
Revises: 0030
Create Date: 2026-08-02

**An ICP becomes a thing a customer can name, open, copy and retire**
([ADR-0041](../../../docs/architecture/adr/0041-icp-aggregate.md)). It was a
value object inside one workspace-wide declaration, addressed by `product_id`,
one per product, with no id, no name and no state.

Four tables, and each answers a question the others must not:

* **`icp_segment`** — identity, and nothing else. **What every future citation
  points at.** If the versioned row were the segment, each revision would mint
  a new id and every citation an opportunity ever made would stop resolving.
* **`icp_segment_version`** — published content, immutable. **Never a draft:**
  a version is something the customer decided to publish, which is what makes
  the chain worth citing.
* **`icp_segment_product`** — which products a segment buys, **versioned with
  the content**, so *"we added CPQ in March"* is recoverable.
* **`icp_segment_state`** — append-only lifecycle, each row a *complete*
  statement rather than a delta, so the status **is** the audit log rather
  than something kept beside it. The shape `opportunity_state` already uses.

**No `UPDATE` grant anywhere.** Content is superseded and lifecycle is
appended; nothing here is edited, which is what the state table exists to make
possible without a mutable flag.

**The old `icp_declaration` is left untouched and still serves the existing
editor.** This migration copies; it deletes nothing. **Old read stays until new
read has proven itself** — a customer-facing migration replaces incrementally
or it replaces at the worst possible moment.

**The copy is 1:1 and deterministic.** Each `ProductIcp` inside the current
declaration becomes one segment, one version naming one product, and one
`published` transition attributed to the declaration's own author. No
heuristics, no interpretation, and every field has a source.

**Reversibility ends at the first write the old model cannot hold** — a
multi-product segment, or a second segment for one product. Both are refused
by `icp_declaration`'s own rules, so a reverse migration would have to discard
or merge. `downgrade()` drops the new tables and leaves `icp_declaration`
exactly as it was, which is lossless **only while nothing new has been
written.**
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0031"
down_revision: str | None = "0030"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None

SEGMENT = "icp_segment"
VERSION = "icp_segment_version"
PRODUCT = "icp_segment_product"
STATE = "icp_segment_state"
APP_ROLE = "signora_app"

_SCOPE = "workspace_id = NULLIF(current_setting('app.workspace_id', true), '')::uuid"


def _tenant_rls(table: str) -> None:
    """The module's standard policy set. **No `UPDATE`, deliberately** — every
    table here is append-only, and granting one would make immutability a
    convention rather than a permission."""
    op.execute(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY")
    op.execute(f"ALTER TABLE {table} FORCE ROW LEVEL SECURITY")
    op.execute(f"CREATE POLICY {table}_select ON {table} FOR SELECT USING ({_SCOPE})")
    op.execute(f"CREATE POLICY {table}_insert ON {table} FOR INSERT WITH CHECK ({_SCOPE})")
    op.execute(f"CREATE POLICY {table}_delete ON {table} FOR DELETE USING ({_SCOPE})")
    op.execute(f"GRANT SELECT, INSERT, DELETE ON {table} TO {APP_ROLE}")


def _audit_columns() -> list[sa.Column]:  # type: ignore[type-arg]
    return [
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("updated_by", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")
        ),
    ]


def upgrade() -> None:
    op.create_table(
        SEGMENT,
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("workspace_id", postgresql.UUID(as_uuid=True), nullable=False),
        *_audit_columns(),
    )
    op.create_index(f"ix_{SEGMENT}_workspace", SEGMENT, ["workspace_id"])
    _tenant_rls(SEGMENT)

    op.create_table(
        VERSION,
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("workspace_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "segment_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey(f"{SEGMENT}.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(80), nullable=False),
        # Criteria travel as one JSONB document because they are read and
        # written whole and never queried field by field. **The product set is
        # not in here** — it is a relationship, and putting it in JSON would
        # make "which segments buy Revenue Cloud?" a scan.
        sa.Column("criteria", postgresql.JSONB(), nullable=False),
        sa.Column(
            "supersedes",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey(f"{VERSION}.id", ondelete="SET NULL"),
            nullable=True,
        ),
        *_audit_columns(),
        # The concurrency control, and the same one the module's other
        # declarations use: two callers who read version 3 both build 4, and
        # the second insert is refused rather than silently winning.
        sa.UniqueConstraint("segment_id", "version", name=f"uq_{VERSION}_number"),
        sa.CheckConstraint("version >= 1", name=f"ck_{VERSION}_starts_at_one"),
        sa.CheckConstraint("length(trim(name)) > 0", name=f"ck_{VERSION}_has_a_name"),
    )
    # The one query the list screen makes: the current version of every
    # segment in a workspace, newest first.
    op.create_index(
        f"ix_{VERSION}_current", VERSION, ["workspace_id", "segment_id", "version"]
    )
    _tenant_rls(VERSION)

    op.create_table(
        PRODUCT,
        sa.Column("workspace_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "version_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey(f"{VERSION}.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        # **No foreign key to a product.** Products live inside the versioned
        # `product_catalog` JSONB document and have no table of their own, so
        # there is nothing to reference. A removed product therefore leaves the
        # reference intact and the screen resolves it against the current
        # catalog — the same handling `keptForCatalog` already implements.
        sa.Column("product_id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")
        ),
    )
    op.create_index(f"ix_{PRODUCT}_product", PRODUCT, ["workspace_id", "product_id"])
    _tenant_rls(PRODUCT)

    op.create_table(
        STATE,
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("workspace_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "segment_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey(f"{SEGMENT}.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("sequence", sa.Integer(), nullable=False),
        sa.Column("state", sa.String(16), nullable=False),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
        # **No default.** A lifecycle change nobody is attributable for is one
        # nobody can explain, and the column refuses to let that happen.
        sa.Column("actor_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")
        ),
        sa.UniqueConstraint("segment_id", "sequence", name=f"uq_{STATE}_sequence"),
        sa.CheckConstraint("sequence >= 0", name=f"ck_{STATE}_sequence_non_negative"),
        sa.CheckConstraint(
            "state IN ('draft', 'published', 'archived')", name=f"ck_{STATE}_known"
        ),
    )
    op.create_index(f"ix_{STATE}_latest", STATE, ["workspace_id", "segment_id", "sequence"])
    _tenant_rls(STATE)

    _copy_existing_declarations()


def _copy_existing_declarations() -> None:
    """Every `ProductIcp` in force becomes one published segment.

    **Runs as the migration identity with RLS not applying**, which is why it
    can read every workspace at once — and it is also why it is written as one
    statement per table rather than a loop: the set is small, the order is
    determined, and a procedural copy would need a cursor over tenants.

    **The current declaration only.** Superseded ones stay where they are:
    they are history of a model that still exists, and copying them would
    invent segment versions the customer never published.
    """
    op.execute(
        f"""
        CREATE TEMPORARY TABLE _icp_copy ON COMMIT DROP AS
        WITH current_declaration AS (
            SELECT DISTINCT ON (workspace_id)
                   id, workspace_id, profiles, created_by, created_at
              FROM icp_declaration
             ORDER BY workspace_id, version DESC
        )
        SELECT gen_random_uuid()               AS segment_id,
               gen_random_uuid()               AS version_id,
               gen_random_uuid()               AS state_id,
               d.workspace_id,
               d.created_by,
               d.created_at,
               (profile ->> 'product_id')::uuid AS product_id,
               profile - 'product_id'           AS criteria
          FROM current_declaration d,
               LATERAL jsonb_array_elements(d.profiles) AS profile
        """
    )

    op.execute(
        f"""
        INSERT INTO {SEGMENT} (id, workspace_id, created_by, updated_by, created_at, updated_at)
        SELECT segment_id, workspace_id, created_by, created_by, created_at, created_at
          FROM _icp_copy
        """
    )
    # **Named from the product, because that is what the ICP was.** A segment
    # called "Revenue Cloud" is exactly as informative as the row it replaces,
    # and inventing a better name would be the migration deciding something
    # the customer did not say.
    op.execute(
        f"""
        INSERT INTO {VERSION}
            (id, workspace_id, segment_id, version, name, criteria, supersedes,
             created_by, updated_by, created_at, updated_at)
        SELECT c.version_id, c.workspace_id, c.segment_id, 1,
               left(coalesce(nullif(trim(p.name), ''), 'Ideal customer'), 80),
               c.criteria, NULL,
               c.created_by, c.created_by, c.created_at, c.created_at
          FROM _icp_copy c
          LEFT JOIN LATERAL (
              SELECT prod ->> 'name' AS name
                FROM (
                    SELECT DISTINCT ON (workspace_id) products
                      FROM product_catalog
                     WHERE workspace_id = c.workspace_id
                     ORDER BY workspace_id, version DESC
                ) cat,
                LATERAL jsonb_array_elements(cat.products) AS prod
               WHERE (prod ->> 'id')::uuid = c.product_id
               LIMIT 1
          ) p ON TRUE
        """
    )
    op.execute(
        f"""
        INSERT INTO {PRODUCT} (workspace_id, version_id, product_id, created_at)
        SELECT workspace_id, version_id, product_id, created_at FROM _icp_copy
        """
    )
    op.execute(
        f"""
        INSERT INTO {STATE}
            (id, workspace_id, segment_id, sequence, state, occurred_at, actor_id, created_at)
        SELECT state_id, workspace_id, segment_id, 0, 'published',
               created_at, created_by, created_at
          FROM _icp_copy
        """
    )


def downgrade() -> None:
    """Drop the new tables. `icp_declaration` is untouched throughout.

    **Lossless only while nothing new has been written.** A multi-product
    segment or a second segment for one product cannot be represented by
    `icp_declaration`, whose own rules refuse both — so once a customer has
    used the capability this migration enables, reversing it discards
    information rather than restoring a previous state. Stated here rather
    than discovered during a rollback.
    """
    for table in (STATE, PRODUCT, VERSION, SEGMENT):
        op.execute(f"REVOKE ALL ON {table} FROM {APP_ROLE}")
        op.drop_table(table)
