"""ai_research_engine: research_task, research_finding, research_synthesis

Revision ID: 0018
Revises: 0017
Create Date: 2026-07-31

**Three tables, because there are three data categories** — not because there
are three domain types. The Knowledge Ontology's classification shows up in the
schema, and each table inherits the storage rules of the category it belongs to:

| Table | Category | Precedent it follows |
|---|---|---|
| `research_task` | **operational history** — Signora's account of its own behaviour | `ai_inference` (0015) |
| `research_finding` | **derived intelligence** — rebuildable from the rows it cites | `signal` (0012), `business_event` (0011) |
| `research_synthesis` | **materialized AI artifact** — what a model actually produced | `ai_narration` (0016), `ai_reasoning` (0017) |

A single table with a `kind` discriminator would be one representation serving
three truths with three different rebuild semantics: a pipeline rebuild
*regenerates* findings, *must never fabricate* a synthesis, and *records* tasks.

**Immutable, like every table since 0008.** `signora_app` holds `SELECT`,
`INSERT` and `DELETE` but **no `UPDATE` grant** on any of the three. A research
run is a record of what happened; a finding is a computation that either
recomputes identically or is a different finding; a synthesis is what a model
said at one moment.

*`research_task` is immutable deliberately, before it has a lifecycle.* Budget,
timeout and resumability arrive with the orchestrator, and this grant decides
now that progress will be recorded as **append-only state rows**, the way
`opportunity_state` records workflow, rather than as columns mutated in place.

**No foreign key points anywhere, and there are two separate reasons.**

*Outward* — `subject_id` and `opportunity_id` are plain UUIDs, matching
`ai_inference` and `ai_reasoning`: a reference into the pipeline would tie these
rows' lifetime to data with a different retention story, and would make them
undeletable when a workspace is erased.

*Inward* — `task_id` is a plain UUID too, and this one was **not obvious**. A
finding's identity is derived from its content and deliberately excludes the
task, so a later run that recomputes the same comparison over the same rows
produces the *same* finding and inserts nothing. `task_id` therefore records the
run that **first derived** it, not the only run that ever did. `ON DELETE
CASCADE` would then erase facts a later run also produced, and `RESTRICT` would
make operational history undeletable for as long as any derivation survives.
Neither is correct, so neither is used.

**`research_finding.task_id` is a departure from the derived-intelligence
precedent, and it is deliberate.** `signal` records no detection run — a derived
fact does not normally say which pass produced it. Research is different because
it is *selective and expensive*: attributing a finding to a run is what makes an
agentic loop auditable, and *"every agentic step logged; artifact provenance
fully reconstructable"* is one of Level 9's graduation criteria.

**What the database cannot check, stated rather than faked.** The domain refuses
a synthesis naming the same finding twice — one source appearing to agree with
itself. A `CHECK` cannot express array-element uniqueness without a subquery, so
that guarantee lives in the domain alone. A join table *would* make it
impossible via a composite primary key, and was rejected: three modules already
store evidence lists as arrays (`evidence_observation_ids`,
`contributing_event_ids`, `supporting_evidence`), and a duplicate here is
cosmetic — `finding_ids` is a reference list, never a count that feeds Support.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0018"
down_revision: str | None = "0017"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None

APP_ROLE = "signora_app"
TABLES = ("research_task", "research_finding", "research_synthesis")


def _audit_columns() -> list[sa.Column]:
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
    # ---- operational history: one act of researching an account.
    op.create_table(
        "research_task",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("correlation_id", postgresql.UUID(as_uuid=True), nullable=False),
        # The account under research, in the AI Platform's addressing
        # vocabulary, so a finding's subject and its citations read alike.
        sa.Column("subject_kind", sa.String(64), nullable=False),
        sa.Column("subject_id", postgresql.UUID(as_uuid=True), nullable=False),
        # What made this account worth the cost. Research is invoked
        # selectively, and the opportunity is the selection.
        sa.Column("opportunity_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("requested_at", sa.DateTime(timezone=True), nullable=False),
        *_audit_columns(),
        sa.CheckConstraint(
            "length(trim(subject_kind)) > 0", name="ck_research_task_subject_is_addressed"
        ),
    )
    op.create_index("ix_research_task_workspace_id", "research_task", ["workspace_id"])
    op.create_index(
        "ix_research_task_opportunity", "research_task", ["workspace_id", "opportunity_id"]
    )
    op.create_index(
        "ix_research_task_correlation", "research_task", ["workspace_id", "correlation_id"]
    )

    # ---- derived intelligence: one thing research worked out, and the rows
    # it worked it out from. Checkable by recomputation, which is the only
    # class the Knowledge Contract calls fully verifiable.
    op.create_table(
        "research_finding",
        # Derived from workspace, subject, derivation@version and the sorted
        # citation tokens (`research_finding_id`). Re-deriving produces this
        # same key, so replay conflicts rather than duplicating.
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        # The run that **first** derived it. Deliberately not part of identity
        # — see the module docstring.
        sa.Column("task_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("subject_kind", sa.String(64), nullable=False),
        sa.Column("subject_id", postgresql.UUID(as_uuid=True), nullable=False),
        # Names the deterministic computation that produced this — which code
        # derived it, so a reader can find that code and run it again.
        sa.Column("derivation", sa.String(128), nullable=False),
        sa.Column("derivation_version", sa.Integer(), nullable=False),
        # What the computation produced: typed attributes in canonical order.
        # A value's type is part of its meaning, so the stored form carries it
        # rather than flattening everything to text.
        sa.Column("attributes", postgresql.JSONB(), nullable=False),
        # The rows this rests on, as citation tokens — the same form
        # `ai_reasoning.supporting_evidence` uses, so one reader resolves both.
        sa.Column("cited", postgresql.ARRAY(sa.String(128)), nullable=False),
        sa.Column("payload_version", sa.Integer(), nullable=False),
        *_audit_columns(),
        sa.CheckConstraint(
            "length(trim(derivation)) > 0", name="ck_research_finding_names_its_derivation"
        ),
        sa.CheckConstraint(
            "derivation_version > 0", name="ck_research_finding_derivation_version_positive"
        ),
        sa.CheckConstraint(
            "payload_version > 0", name="ck_research_finding_payload_version_positive"
        ),
        # **A finding that cites nothing is not derived from anything.** The
        # domain refuses it in flight; this is the same guarantee at rest, so a
        # row arriving by any other path cannot claim to be a derivation.
        # **`cardinality`, not `array_length`.** `array_length('{}', 1)` returns
        # NULL rather than 0, and a CHECK only fails on FALSE — so the obvious
        # spelling accepts the empty array it was written to reject. Found here
        # by the test that was meant to prove it fires; **nine shipped
        # constraints across five tables still carry the broken form**, recorded
        # in 36-empty-array-checks.md.
        sa.CheckConstraint(
            "cardinality(cited) >= 1", name="ck_research_finding_cites_evidence"
        ),
        # A finding with no attributes records that a comparison ran, which is
        # the task's job, not a finding's.
        sa.CheckConstraint(
            "jsonb_typeof(attributes) = 'array' AND jsonb_array_length(attributes) >= 1",
            name="ck_research_finding_states_something",
        ),
    )
    op.create_index("ix_research_finding_workspace_id", "research_finding", ["workspace_id"])
    op.create_index(
        "ix_research_finding_subject",
        "research_finding",
        ["workspace_id", "subject_kind", "subject_id"],
    )
    op.create_index("ix_research_finding_task", "research_finding", ["workspace_id", "task_id"])

    # ---- materialized AI artifact: what the model made of the findings.
    op.create_table(
        "research_synthesis",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("task_id", postgresql.UUID(as_uuid=True), nullable=False),
        # Grounded statements: text plus the citations each rests on.
        sa.Column("statements", postgresql.JSONB(), nullable=False),
        # Referenced by identity, never absorbed. A finding is immutable, so a
        # reference cannot drift — and holding ids is what keeps each finding
        # separately addressable, and therefore separately checkable, beneath
        # an INFERRED whole.
        sa.Column("finding_ids", postgresql.ARRAY(postgresql.UUID(as_uuid=True)), nullable=False),
        # ---- provenance, complete and denormalized. The AI Platform publishes
        # an `InferenceRecorder` and no reader, so `inference_id` alone would
        # leave this row unable to explain itself.
        sa.Column("prompt_name", sa.String(128), nullable=False),
        sa.Column("prompt_version", sa.Integer(), nullable=False),
        sa.Column("prompt_fingerprint", sa.String(64), nullable=False),
        sa.Column("model", sa.String(128), nullable=False),
        sa.Column("vendor", sa.String(32), nullable=False),
        sa.Column("evidence_digest", sa.String(64), nullable=False),
        sa.Column("inference_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("payload_version", sa.Integer(), nullable=False),
        *_audit_columns(),
        sa.CheckConstraint(
            "prompt_version > 0", name="ck_research_synthesis_prompt_version_positive"
        ),
        sa.CheckConstraint(
            "payload_version > 0", name="ck_research_synthesis_payload_version_positive"
        ),
        # An empty synthesis is a failed inference recorded as a successful
        # one, and the operational history would then disagree with itself.
        sa.CheckConstraint(
            "jsonb_typeof(statements) = 'array' AND jsonb_array_length(statements) >= 1",
            name="ck_research_synthesis_says_something",
        ),
        # A narration over nothing is a model writing unprompted, which is the
        # one thing this module must never publish.
        sa.CheckConstraint(
            "cardinality(finding_ids) >= 1", name="ck_research_synthesis_rests_on_findings"
        ),
    )
    op.create_index("ix_research_synthesis_workspace_id", "research_synthesis", ["workspace_id"])
    op.create_index(
        "ix_research_synthesis_task", "research_synthesis", ["workspace_id", "task_id"]
    )
    op.create_index("ix_research_synthesis_inference", "research_synthesis", ["inference_id"])

    for table in TABLES:
        op.execute(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY")
        op.execute(f"ALTER TABLE {table} FORCE ROW LEVEL SECURITY")
        op.execute(
            f"""
            CREATE POLICY {table}_select ON {table} FOR SELECT
              USING (workspace_id = NULLIF(current_setting('app.workspace_id', true), '')::uuid)
            """
        )
        op.execute(
            f"""
            CREATE POLICY {table}_insert ON {table} FOR INSERT
              WITH CHECK (
                workspace_id = NULLIF(current_setting('app.workspace_id', true), '')::uuid
              )
            """
        )
        op.execute(
            f"""
            CREATE POLICY {table}_delete ON {table} FOR DELETE
              USING (workspace_id = NULLIF(current_setting('app.workspace_id', true), '')::uuid)
            """
        )
        op.execute(f"GRANT SELECT, INSERT, DELETE ON {table} TO {APP_ROLE}")


def downgrade() -> None:
    for table in TABLES:
        op.execute(f"REVOKE ALL ON {table} FROM {APP_ROLE}")
    op.drop_table("research_synthesis")
    op.drop_table("research_finding")
    op.drop_table("research_task")
