"""ai_research_engine: research_request, research_request_state

Revision ID: 0021
Revises: 0020
Create Date: 2026-08-01

**Two tables, because a request has a history and an artifact does not.**
`0018` created three tables for what research *produces* and said, in as many
words, what would happen when a lifecycle arrived:

> *`research_task` is immutable deliberately, before it has a lifecycle.
> Budget, timeout and resumability arrive with the orchestrator, and this grant
> decides now that progress will be recorded as **append-only state rows**, the
> way `opportunity_state` records workflow, rather than as columns mutated in
> place.*

That decision is honoured here rather than revisited. There is no status column
on `research_task`, and no `UPDATE` grant anywhere — a research request's
status **is** its audit trail, exactly as an opportunity's is.

| Table | Category | Precedent it follows |
|---|---|---|
| `research_request` | **workflow state** — a person asked for something | `opportunity` (0014) |
| `research_request_state` | **workflow state** — where the ask has got to | `opportunity_state` (0014) |

**Why a request is not a `research_task` with a status.** They answer different
questions and have different lifetimes. A task is written only when a run
succeeded — `Research.run()` stores nothing until every step has, so that a
partial run can never look like a completed one that found nothing to say. A
request exists from the moment somebody clicked, survives a run that failed,
and is the only record that anybody wanted this at all. Folding them would
either make the task mutable or make a failed run invisible.

**`entity_id` and `opportunity_id` are plain UUIDs, no foreign keys** — the
same reasoning `0018` gives: a reference into the pipeline would tie a workflow
row's lifetime to data with a different retention story and make it undeletable
when a workspace is erased.

**`generation` is the concurrency control**, and it is `opportunity`'s device
(migration `0014`) rather than a new one: *"a uniqueness device that stops two
concurrent qualifications both succeeding."* Two clicks arriving in the same
millisecond both find no request in flight, both compute the same generation,
and one loses on `uq_research_request_generation` — which is what stops a second
minute-long model call. The application check exists so the *ordinary* repeat
answers *"one is already running"* rather than an error.

**A partial index on status was written first and is wrong**, recorded here
because the reason generalises. `WHERE status IN ('requested','running')` looks
like *"one unfinished request per account"* and is not: history is append-only,
so the `requested` row survives its own `running` row and the index refuses the
transition it was meant to permit. On an append-only table a partial index over
status constrains **history**, never the present. Found by the test that was
meant to prove it fires — the same way `cardinality(cited)` was found at `0018`.

**Renumbered from `0020` at merge.** Lane B's `icp_declaration` took that
number first; Alembic's chain is linear and a lane rebasing resolves its own
collision (CLAUDE.md §20e). Nothing else about this migration changed.

**Currency is `MAX(sequence)` per request**, deliberately not `0012`'s
`WHERE supersedes IS NULL`, which reads the *first* version as current on an
immutable table (`B-001`). A maximum cannot invert.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0021"
down_revision: str | None = "0020"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None

APP_ROLE = "signora_app"
TABLES = ("research_request", "research_request_state")


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
    op.create_table(
        "research_request",
        # Minted, never derived. Asking twice about the same account over the
        # same evidence is two asks; a derived id would collide them and lose
        # the second person's request.
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("entity_id", postgresql.UUID(as_uuid=True), nullable=False),
        # What made this account researchable. Research compares the evidence
        # beneath a qualified opportunity, so the opportunity is the selection.
        sa.Column("opportunity_id", postgresql.UUID(as_uuid=True), nullable=False),
        # The verified principal. A model call and a minute of a worker were
        # spent on somebody's behalf, and nothing reconstructs whose.
        sa.Column("requested_by", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("requested_at", sa.DateTime(timezone=True), nullable=False),
        # How many times this account has been researched, counting from 0.
        # Not a fact anybody asked for — a uniqueness device, exactly as
        # `opportunity.generation` is, and the only thing that makes two
        # simultaneous clicks resolve to one run.
        sa.Column("generation", sa.Integer(), nullable=False),
        *_audit_columns(),
        sa.UniqueConstraint(
            "workspace_id", "entity_id", "generation", name="uq_research_request_generation"
        ),
        sa.CheckConstraint("generation >= 0", name="ck_research_request_generation_non_negative"),
    )
    op.create_index("ix_research_request_workspace_id", "research_request", ["workspace_id"])
    op.create_index(
        "ix_research_request_entity", "research_request", ["workspace_id", "entity_id"]
    )

    op.create_table(
        "research_request_state",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("request_id", postgresql.UUID(as_uuid=True), nullable=False),
        # The account, repeated here so the partial in-flight index can be
        # unique per account without a join. A denormalization, and the only
        # one: it is written once from the request and can never drift,
        # because neither row is ever updated.
        sa.Column("entity_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("sequence", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(32), nullable=False),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
        # The artifact, on `completed` and nothing else.
        sa.Column("task_id", postgresql.UUID(as_uuid=True), nullable=True),
        # Why, on `failed` and nothing else.
        sa.Column("detail", sa.Text(), nullable=True),
        *_audit_columns(),
        sa.ForeignKeyConstraint(["request_id"], ["research_request.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("request_id", "sequence", name="uq_research_request_state_sequence"),
        sa.CheckConstraint("sequence >= 0", name="ck_research_request_state_sequence_non_negative"),
        sa.CheckConstraint(
            "status IN ('requested', 'running', 'completed', 'nothing_to_research', 'failed')",
            name="ck_research_request_state_known_status",
        ),
        # The domain enforces both of these in flight. Repeated at rest so a
        # row arriving by any other path cannot claim a completed run with
        # nothing to read, or a failure with no reason.
        sa.CheckConstraint(
            "(status = 'completed') = (task_id IS NOT NULL)",
            name="ck_research_request_state_completed_names_its_artifact",
        ),
        sa.CheckConstraint(
            "(status = 'failed') = (detail IS NOT NULL AND length(trim(detail)) > 0)",
            name="ck_research_request_state_failure_states_why",
        ),
    )
    op.create_index(
        "ix_research_request_state_workspace_id", "research_request_state", ["workspace_id"]
    )
    # The current state: the highest sequence per request.
    op.create_index(
        "ix_research_request_state_current",
        "research_request_state",
        ["request_id", sa.text("sequence DESC")],
    )
    # In-flight lookups: the state table is read first because *unfinished*
    # is where status lives.
    op.create_index(
        "ix_research_request_state_entity_status",
        "research_request_state",
        ["workspace_id", "entity_id", "status"],
    )

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
        # No UPDATE grant and no UPDATE policy. Progress is an append.
        op.execute(f"GRANT SELECT, INSERT, DELETE ON {table} TO {APP_ROLE}")


def downgrade() -> None:
    for table in TABLES:
        op.execute(f"REVOKE ALL ON {table} FROM {APP_ROLE}")
    op.drop_table("research_request_state")
    op.drop_table("research_request")
