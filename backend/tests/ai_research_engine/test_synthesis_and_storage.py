"""What a brief must be, and what storage must preserve.

Both halves were found by surviving mutations: the synthesis validators had no
test at all, the attribute codec's `datetime` branch was unreachable from any
finding a derivation currently produces, and nothing exercised re-saving a
finding a second run had already established.
"""

from __future__ import annotations

from datetime import UTC, date, datetime
from decimal import Decimal
from uuid import uuid4

import pytest
from pydantic import ValidationError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from modules.ai_platform.public import AIVendor, EvidenceRef, EvidenceValue, GroundedStatement
from modules.ai_research_engine.domain.research import (
    ResearchFinding,
    ResearchSynthesis,
    ResearchTask,
    research_finding_id,
)
from modules.ai_research_engine.domain.synthesis import SynthesisedResearch
from modules.ai_research_engine.infrastructure.models import ResearchFindingModel
from modules.ai_research_engine.infrastructure.repository import (
    SqlResearchRepository,
    attributes_of,
    decode,
    encode,
)
from signora_platform.db import tenant_scoped_session

WORKSPACE = uuid4()
SUBJECT = EvidenceRef(kind="entity", id=uuid4())
CITED = (EvidenceRef(kind="business_event", id=uuid4()),)
NOW = datetime(2026, 7, 31, 12, 0, tzinfo=UTC)


def _statement(text: str, *tokens: str) -> GroundedStatement:
    return GroundedStatement(text=text, evidence=tokens)


class TestABriefMustRelateFindings:
    def test_a_single_statement_is_refused(self) -> None:
        """A brief of one statement restates a finding, and the findings are
        already readable on their own."""
        with pytest.raises(ValidationError, match="restatement, not a"):
            SynthesisedResearch(brief=(_statement("One thing.", "research_finding:a"),))

    def test_a_brief_citing_one_finding_throughout_is_refused(self) -> None:
        """**The other half.** Two statements about the same finding relate
        nothing — the model has reworded a result and charged a model call."""
        token = f"research_finding:{uuid4()}"
        with pytest.raises(ValidationError, match="relates nothing"):
            SynthesisedResearch(
                brief=(_statement("First.", token), _statement("Second.", token))
            )

    def test_two_statements_over_two_findings_are_accepted(self) -> None:
        synthesis = SynthesisedResearch(
            brief=(
                _statement("Thin evidence.", f"research_finding:{uuid4()}"),
                _statement("Recent evidence.", f"research_finding:{uuid4()}"),
            )
        )
        assert len(synthesis.statements()) == 2

    def test_there_is_nowhere_to_put_a_recommendation(self) -> None:
        with pytest.raises(ValidationError):
            SynthesisedResearch(
                brief=(_statement("a", "x:1"), _statement("b", "y:2")),
                next_action="call them",  # type: ignore[call-arg]
            )

    def test_a_synthesis_output_has_no_address(self) -> None:
        """Rule 12, at the schema. Nothing can cite what the model returned."""
        synthesis = SynthesisedResearch(
            brief=(_statement("a", "x:1"), _statement("b", "y:2"))
        )
        assert not hasattr(synthesis, "ref")


class TestEveryStoredValueComesBackAsItself:
    @pytest.mark.parametrize(
        "value",
        [
            True,
            False,
            0,
            42,
            Decimal("0.4"),
            datetime(2026, 6, 1, 9, 30, tzinfo=UTC),
            date(2026, 6, 1),
            "builtwith,apollo",
        ],
    )
    def test_it_round_trips(self, value: EvidenceValue) -> None:
        """**A stored finding nobody can reconstruct is one nobody can
        recompute.** `bool` is tested before `int` and `datetime` before
        `date`, so a value must come back as its own type and not its
        parent's."""
        restored = decode(encode(value))

        assert restored == value
        assert type(restored) is type(value)

    def test_an_unknown_tag_is_refused_rather_than_guessed(self) -> None:
        from modules.ai_research_engine.domain.research import ResearchError

        with pytest.raises(ResearchError, match="unknown type tag"):
            decode({"type": "invented", "value": 1})


def _finding(task_id: object, **overrides: object) -> ResearchFinding:
    attributes: tuple[tuple[str, EvidenceValue], ...] = (
        ("conclusions", 2),
        ("measured_at", datetime(2026, 6, 1, 9, 30, tzinfo=UTC)),
        ("spread", Decimal("0.4")),
        ("corroborated", True),
    )
    return ResearchFinding(
        id=research_finding_id(
            workspace_id=WORKSPACE,
            subject=SUBJECT,
            derivation="corroboration",
            derivation_version=1,
            cited=CITED,
        ),
        workspace_id=WORKSPACE,
        task_id=task_id,  # type: ignore[arg-type]
        subject=SUBJECT,
        derivation="corroboration",
        derivation_version=1,
        attributes=attributes,
        cited=CITED,
        created_at=NOW,
        **overrides,  # type: ignore[arg-type]
    )


def _task() -> ResearchTask:
    return ResearchTask(
        id=uuid4(),
        workspace_id=WORKSPACE,
        correlation_id=uuid4(),
        subject=SUBJECT,
        opportunity_id=uuid4(),
        requested_at=NOW,
    )


def _synthesis(task: ResearchTask, finding: ResearchFinding) -> ResearchSynthesis:
    return ResearchSynthesis(
        id=uuid4(),
        workspace_id=WORKSPACE,
        task_id=task.id,
        statements=(
            _statement("Thin.", finding.ref.token),
            _statement("Recent.", finding.ref.token),
        ),
        finding_ids=(finding.id,),
        prompt_name="research_synthesis",
        prompt_version=1,
        prompt_fingerprint="f" * 64,
        model="llama3.1:8b",
        vendor=AIVendor.OLLAMA,
        evidence_digest="d" * 64,
        inference_id=uuid4(),
        created_at=NOW,
    )


@pytest.mark.integration
class TestReRunningAgreesRatherThanCollides:
    async def test_a_second_run_re_deriving_one_finding_inserts_it_once(
        self, session_factory: async_sessionmaker[AsyncSession]
    ) -> None:
        """**The whole of resumability.** A finding's key *is* its content, so
        a conflict means this exact finding already exists — a re-run inserts
        what is new and silently agrees about what is not. Without that, a
        partially completed run could never be resumed by running it again.
        """
        first, second = _task(), _task()

        for task in (first, second):
            finding = _finding(task.id)
            async with tenant_scoped_session(
                session_factory, workspace_id=WORKSPACE, user_id=uuid4()
            ) as session:
                await SqlResearchRepository(session).save(
                    task, (finding,), _synthesis(task, finding)
                )

        async with tenant_scoped_session(
            session_factory, workspace_id=WORKSPACE, user_id=uuid4()
        ) as session:
            rows = (await session.execute(select(ResearchFindingModel))).scalars().all()

        assert len(rows) == 1
        # The row records the run that *first* derived it, which is why
        # `task_id` is deliberately absent from the identity.
        assert rows[0].task_id == first.id

    async def test_a_stored_finding_reconstructs_with_every_type_intact(
        self, session_factory: async_sessionmaker[AsyncSession]
    ) -> None:
        task = _task()
        finding = _finding(task.id)

        async with tenant_scoped_session(
            session_factory, workspace_id=WORKSPACE, user_id=uuid4()
        ) as session:
            await SqlResearchRepository(session).save(task, (finding,), _synthesis(task, finding))

        async with tenant_scoped_session(
            session_factory, workspace_id=WORKSPACE, user_id=uuid4()
        ) as session:
            (row,) = (await session.execute(select(ResearchFindingModel))).scalars().all()

        assert attributes_of(row.attributes) == finding.attributes
