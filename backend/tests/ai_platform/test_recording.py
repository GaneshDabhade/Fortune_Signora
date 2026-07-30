"""What the platform durably remembers about its own model calls.

Against a real database as ``signora_app``, because every guarantee here is
one PostgreSQL enforces and none of them can be demonstrated against a fake:
the row is workspace-scoped by RLS, cannot be edited, and refuses to record
a success it cannot attribute.

**Nothing here calls a model.** The recorder writes records; whether a model
reasoned well is the harness's question (T120). The two-tier split holds even
in the tests that touch infrastructure.
"""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID, uuid4

import pytest
from sqlalchemy import select, text
from sqlalchemy.exc import DBAPIError, IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from modules.ai_platform.domain.provider import AIVendor
from modules.ai_platform.domain.record import InferenceOutcome, InferenceRecord
from modules.ai_platform.domain.usage import InferenceUsage
from modules.ai_platform.infrastructure.models import AIInferenceModel
from modules.ai_platform.infrastructure.repository import DETAIL_LIMIT, SqlInferenceRecorder
from signora_platform.db import tenant_scoped_session

pytestmark = pytest.mark.integration

NOW = datetime(2026, 7, 30, 12, 0, tzinfo=UTC)
FUNDING = "business_event:00000000-0000-0000-0000-000000000001"


def a_record(
    workspace_id: UUID,
    *,
    outcome: InferenceOutcome = InferenceOutcome.OK,
    vendor: AIVendor | None = AIVendor.OLLAMA,
    served_model: str | None = "llama3.1:8b-instruct-q8_0",
    detail: str | None = None,
    usage: InferenceUsage | None = None,
) -> InferenceRecord:
    return InferenceRecord(
        id=uuid4(),
        workspace_id=workspace_id,
        correlation_id=uuid4(),
        prompt_name="explanation_narration",
        prompt_version=1,
        prompt_fingerprint="a" * 64,
        requested_model="llama3.1:8b",
        served_model=served_model,
        vendor=vendor,
        evidence_digest="b" * 64,
        evidence_refs=(FUNDING,),
        outcome=outcome,
        usage=usage or InferenceUsage(input_tokens=412, output_tokens=88, latency_ms=1_240),
        detail=detail,
        created_at=NOW,
    )


async def _write(
    factory: async_sessionmaker[AsyncSession], workspace_id: UUID, record: InferenceRecord
) -> None:
    """The recorder opens its own session (ADR-0029), so there is no caller
    transaction here to join — which is the behaviour, not a shortcut."""
    del workspace_id
    await SqlInferenceRecorder(factory).record(record)


async def _rows(
    factory: async_sessionmaker[AsyncSession], workspace_id: UUID
) -> list[AIInferenceModel]:
    async with tenant_scoped_session(
        factory, workspace_id=workspace_id, user_id=uuid4()
    ) as session:
        result = await session.execute(select(AIInferenceModel))
        return list(result.scalars())


async def _raw_insert(
    factory: async_sessionmaker[AsyncSession],
    *,
    outcome: str = "ok",
    vendor: str = "'ollama'",
    served_model: str = "'llama3.1:8b'",
    detail: str = "NULL",
) -> None:
    """Insert straight into the table, bypassing the recorder.

    The constraints below are database guarantees, so they are asserted at the
    database. Routing them through `SqlInferenceRecorder` would prove nothing:
    it deliberately swallows its own write failures (ADR-0029), so such a test
    would pass whether the constraint existed or not.
    """
    workspace_id = uuid4()
    async with tenant_scoped_session(
        factory, workspace_id=workspace_id, user_id=uuid4()
    ) as session:
        await session.execute(
            text(
                f"""
                INSERT INTO ai_inference (
                  id, workspace_id, correlation_id, prompt_name, prompt_version,
                  prompt_fingerprint, requested_model, served_model, vendor,
                  evidence_digest, evidence_refs, outcome, input_tokens, output_tokens,
                  latency_ms, retries, detail, created_by, updated_by
                ) VALUES (
                  gen_random_uuid(), :ws, gen_random_uuid(), 'p', 1,
                  'f', 'm', {served_model}, {vendor},
                  'd', ARRAY['a:1'], '{outcome}', 0, 0,
                  0, 0, {detail}, :ws, :ws
                )
                """
            ),
            {"ws": workspace_id},
        )


class TestEveryOutcomeSurvives:
    """A table recording only successes cannot report a failure rate, and the
    ungrounded rate is what turns risk R-10 into a number."""

    @pytest.mark.parametrize("outcome", list(InferenceOutcome))
    async def test_each_outcome_round_trips(
        self, session_factory: async_sessionmaker[AsyncSession], outcome: InferenceOutcome
    ) -> None:
        workspace_id = uuid4()
        succeeded = outcome is InferenceOutcome.OK
        await _write(
            session_factory,
            workspace_id,
            a_record(
                workspace_id,
                outcome=outcome,
                detail=None if succeeded else "the model cited nothing",
                vendor=AIVendor.OLLAMA if succeeded else None,
                served_model="llama3.1:8b-instruct-q8_0" if succeeded else None,
            ),
        )

        (row,) = await _rows(session_factory, workspace_id)
        assert row.outcome == outcome.value

    async def test_a_successful_row_carries_its_full_provenance(
        self, session_factory: async_sessionmaker[AsyncSession]
    ) -> None:
        """AC-69. Prompt identity, model, vendor, evidence and usage — enough
        to reconstruct what the model saw without storing what it was sent."""
        workspace_id = uuid4()
        await _write(session_factory, workspace_id, a_record(workspace_id))

        (row,) = await _rows(session_factory, workspace_id)
        assert row.prompt_name == "explanation_narration"
        assert row.prompt_version == 1
        assert row.prompt_fingerprint == "a" * 64
        assert row.requested_model == "llama3.1:8b"
        assert row.served_model == "llama3.1:8b-instruct-q8_0"
        assert row.vendor == AIVendor.OLLAMA.value
        assert row.evidence_digest == "b" * 64
        assert row.evidence_refs == [FUNDING]
        assert (row.input_tokens, row.output_tokens, row.latency_ms) == (412, 88, 1_240)

    async def test_a_failure_that_reached_a_vendor_still_names_it(
        self, session_factory: async_sessionmaker[AsyncSession]
    ) -> None:
        """Nothing served the call, and the vendor is known anyway. A
        rate-limit incident attributable to nobody is the same defect as a
        false attribution, in the other direction."""
        workspace_id = uuid4()
        await _write(
            session_factory,
            workspace_id,
            a_record(
                workspace_id,
                outcome=InferenceOutcome.TRANSIENT,
                served_model=None,
                detail="[ollama] rate limited",
                usage=InferenceUsage(input_tokens=0, output_tokens=0, latency_ms=0, retries=2),
            ),
        )

        (row,) = await _rows(session_factory, workspace_id)
        assert row.vendor == AIVendor.OLLAMA.value
        assert row.served_model is None
        assert row.retries == 2, "a retry storm must be legible in the rows that prove one"


class TestTheRowRefusesToMisreportItself:
    """Constraints that state what a row is allowed to claim.

    Each is enforced by PostgreSQL rather than by the writer, because the
    writer is exactly what a future change replaces.
    """

    async def test_a_success_cannot_come_from_nobody(
        self, session_factory: async_sessionmaker[AsyncSession]
    ) -> None:
        """Asserted against the database directly rather than through the
        recorder, because the recorder now swallows its own write failures by
        design (ADR-0029) — so a test routed through it would pass whether the
        constraint existed or not."""
        with pytest.raises(IntegrityError, match="ck_ai_inference_success_names_its_source"):
            await _raw_insert(session_factory, vendor="NULL", served_model="NULL")

    async def test_a_failure_must_state_a_reason(
        self, session_factory: async_sessionmaker[AsyncSession]
    ) -> None:
        """An incident with no first line. The converse matters too: a
        successful row carrying a reason means something was hidden."""
        with pytest.raises(IntegrityError, match="ck_ai_inference_failure_states_a_reason"):
            await _raw_insert(
                session_factory,
                outcome="ungrounded",
                vendor="NULL",
                served_model="NULL",
                detail="NULL",
            )

    async def test_the_constraint_still_matches_the_outcome_it_names(self) -> None:
        """Both constraints above are written in SQL against the literal
        ``'ok'``. If ``InferenceOutcome.OK`` were renamed, they would not
        fail — they would quietly stop applying, and every test above would
        still pass."""
        assert InferenceOutcome.OK.value == "ok"

    async def test_a_long_failure_message_is_truncated_rather_than_dropped(
        self, session_factory: async_sessionmaker[AsyncSession]
    ) -> None:
        """The most thoroughly ungrounded output produces the longest report.
        Losing that row to a length error would discard exactly the evidence
        the table exists to keep."""
        workspace_id = uuid4()
        await _write(
            session_factory,
            workspace_id,
            a_record(
                workspace_id,
                outcome=InferenceOutcome.UNGROUNDED,
                served_model=None,
                vendor=None,
                detail="uncited_statement: " * 500,
            ),
        )

        (row,) = await _rows(session_factory, workspace_id)
        assert row.detail is not None
        assert len(row.detail) == DETAIL_LIMIT
        assert row.detail.startswith("uncited_statement:")


class TestTheRecordIsWorkspaceOwned:
    async def test_one_workspace_never_sees_another_workspaces_inferences(
        self, session_factory: async_sessionmaker[AsyncSession]
    ) -> None:
        """RLS, not application filtering. The digest and refs on a row
        address one workspace's facts, and the ungrounded rate is a fact
        about that workspace's data."""
        mine, theirs = uuid4(), uuid4()
        await _write(session_factory, mine, a_record(mine))
        await _write(session_factory, theirs, a_record(theirs))

        assert len(await _rows(session_factory, mine)) == 1
        assert len(await _rows(session_factory, theirs)) == 1

    async def test_the_recorder_scopes_to_the_records_own_workspace(
        self, session_factory: async_sessionmaker[AsyncSession]
    ) -> None:
        """Stronger than the check it replaced (ADR-0029).

        The recorder opens its own session and scopes it from
        ``record.workspace_id`` — taken from the verified evidence set, never
        from anything a client supplied. So a row landing in the wrong
        workspace is not *refused*, it is **unrepresentable**: there is no
        ambient caller context for it to disagree with.
        """
        mine, theirs = uuid4(), uuid4()
        await _write(session_factory, mine, a_record(theirs))

        assert await _rows(session_factory, mine) == []
        assert len(await _rows(session_factory, theirs)) == 1

    async def test_rls_still_refuses_a_foreign_write_at_the_database(
        self, session_factory: async_sessionmaker[AsyncSession]
    ) -> None:
        """The guarantee underneath, asserted where it lives. The recorder can
        no longer attempt a foreign write, so this proves the table would
        refuse one arriving by any other path."""
        mine, theirs = uuid4(), uuid4()
        async with tenant_scoped_session(
            session_factory, workspace_id=mine, user_id=uuid4()
        ) as session:
            with pytest.raises(DBAPIError, match="row-level security"):
                await session.execute(
                    text(
                        "INSERT INTO ai_inference (id, workspace_id, correlation_id, "
                        "prompt_name, prompt_version, prompt_fingerprint, requested_model, "
                        "served_model, vendor, evidence_digest, evidence_refs, outcome, "
                        "input_tokens, output_tokens, latency_ms, retries, detail, "
                        "created_by, updated_by) VALUES (gen_random_uuid(), :theirs, "
                        "gen_random_uuid(), 'p', 1, 'f', 'm', 'm', 'ollama', 'd', "
                        "ARRAY['a:1'], 'ok', 0, 0, 0, 0, NULL, :theirs, :theirs)"
                    ),
                    {"theirs": theirs},
                )


class TestTheRecordIsImmutable:
    async def test_the_application_role_cannot_edit_an_inference(
        self, session_factory: async_sessionmaker[AsyncSession]
    ) -> None:
        """The ungrounded rate read from an editable table would be a number
        nobody could defend — and the rows worth editing are exactly the
        embarrassing ones."""
        workspace_id = uuid4()
        await _write(session_factory, workspace_id, a_record(workspace_id))

        async with tenant_scoped_session(
            session_factory, workspace_id=workspace_id, user_id=uuid4()
        ) as session:
            with pytest.raises(DBAPIError, match="permission denied"):
                await session.execute(text("UPDATE ai_inference SET outcome = 'ok'"))


class TestOperationalPersistenceFailureIsNeverInvisible:
    """The alarm on the alarm (ADR-0029).

    Business success and operational persistence are intentionally decoupled:
    a narration produced correctly must not be discarded because a log row
    could not be written. But a swallowed write is a row that silently never
    existed, and enough of them make the ungrounded rate optimistic for a
    *second* time by a *second* mechanism — which is the exact failure this
    whole ADR exists to remove.

    So the swallow is loud: an ERROR line naming what was lost, and a counter
    an alert can bind to.
    """

    async def test_a_write_failure_does_not_fail_the_caller(
        self, session_factory: async_sessionmaker[AsyncSession]
    ) -> None:
        recorder = SqlInferenceRecorder(_broken(), metrics=_CountingMetrics())
        await recorder.record(a_record(uuid4()))

    async def test_a_write_failure_is_counted(
        self, session_factory: async_sessionmaker[AsyncSession]
    ) -> None:
        metrics = _CountingMetrics()
        await SqlInferenceRecorder(_broken(), metrics=metrics).record(a_record(uuid4()))

        assert metrics.failures == 1, (
            "a lost inference record must reach operational monitoring — otherwise the "
            "platform's self-measurement degrades silently"
        )

    async def test_a_write_failure_says_what_was_lost(
        self, session_factory: async_sessionmaker[AsyncSession], caplog: pytest.LogCaptureFixture
    ) -> None:
        """An engineer reading the alert must be able to identify the call
        without the row that would have identified it."""
        record = a_record(uuid4(), outcome=InferenceOutcome.UNGROUNDED, detail="made it up")
        with caplog.at_level("ERROR"):
            await SqlInferenceRecorder(_broken(), metrics=_CountingMetrics()).record(record)

        (logged,) = [r for r in caplog.records if "operational history lost" in r.message]
        assert logged.correlation_id == str(record.correlation_id)  # type: ignore[attr-defined]
        assert logged.outcome == "ungrounded"  # type: ignore[attr-defined]

    async def test_a_healthy_write_counts_no_failure(
        self, session_factory: async_sessionmaker[AsyncSession]
    ) -> None:
        """The positive control. A counter incremented unconditionally would
        satisfy every test above and alert on nothing."""
        metrics = _CountingMetrics()
        await SqlInferenceRecorder(session_factory, metrics=metrics).record(a_record(uuid4()))

        assert metrics.failures == 0


class _CountingMetrics:
    def __init__(self) -> None:
        self.failures = 0

    def recording_failed(self) -> None:
        self.failures += 1


def _broken() -> async_sessionmaker[AsyncSession]:
    """A session factory pointed at nothing. Fails on connect, which is the
    realistic shape of the outage this guards — the database being unreachable
    is exactly when the recorder is busiest and least able to write."""
    from sqlalchemy.ext.asyncio import create_async_engine

    return async_sessionmaker(
        create_async_engine("postgresql+asyncpg://nobody:nobody@127.0.0.1:1/nothing")
    )
