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
    async with tenant_scoped_session(
        factory, workspace_id=workspace_id, user_id=uuid4()
    ) as session:
        await SqlInferenceRecorder(session).record(record)


async def _rows(
    factory: async_sessionmaker[AsyncSession], workspace_id: UUID
) -> list[AIInferenceModel]:
    async with tenant_scoped_session(
        factory, workspace_id=workspace_id, user_id=uuid4()
    ) as session:
        result = await session.execute(select(AIInferenceModel))
        return list(result.scalars())


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
        workspace_id = uuid4()
        with pytest.raises(IntegrityError, match="ck_ai_inference_success_names_its_source"):
            await _write(
                session_factory,
                workspace_id,
                a_record(workspace_id, vendor=None, served_model=None),
            )

    async def test_a_failure_must_state_a_reason(
        self, session_factory: async_sessionmaker[AsyncSession]
    ) -> None:
        """An incident with no first line. The converse matters too: a
        successful row carrying a reason means something was swallowed."""
        workspace_id = uuid4()
        with pytest.raises(IntegrityError, match="ck_ai_inference_failure_states_a_reason"):
            await _write(
                session_factory,
                workspace_id,
                a_record(
                    workspace_id,
                    outcome=InferenceOutcome.UNGROUNDED,
                    served_model=None,
                    vendor=None,
                    detail=None,
                ),
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

    async def test_a_row_cannot_be_written_into_another_workspace(
        self, session_factory: async_sessionmaker[AsyncSession]
    ) -> None:
        mine, theirs = uuid4(), uuid4()
        with pytest.raises(DBAPIError, match="row-level security"):
            await _write(session_factory, mine, a_record(theirs))


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
