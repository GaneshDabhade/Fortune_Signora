"""Orchestration, and the ten questions the result must answer.

Nothing here calls a model. Sequencing, composition and the customer-facing
acceptance criterion are deterministic engineering behaviour; whether a model
reasons *well* is the harness's question.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from pathlib import Path
from uuid import UUID, uuid4

import pytest

from modules.ai_platform.public import (
    AIProviderRegistry,
    EvidenceSet,
    EvidenceSetBuilder,
    Infer,
    InferencePolicy,
    PromptNotReleasableError,
    PromptRegistry,
    UngroundedOutputError,
)
from modules.ai_reasoning_engine.application.reason import (
    SUBJECT_KIND,
    NothingToReasonAboutError,
    Reason,
    ReasonInput,
)
from modules.ai_reasoning_engine.domain.context import ReasoningContext
from modules.ai_reasoning_engine.domain.package import (
    AlternativeReading,
    DecisionPackage,
    DecisionPackageError,
)
from modules.ai_reasoning_engine.domain.support import SupportBasis
from modules.ai_reasoning_engine.domain.temporal import TemporalExplanation
from modules.buying_score_engine.public import ScoreTrigger, Trend
from modules.opportunity_engine.public import EvidenceState
from tests.ai_platform.fakes import FakeAdapter
from tests.ai_platform.test_infer import FakeRecorder, a_prompt


class _Missing:
    """Distinguishes "no context argument" from "the context is None" — the
    latter is the meaningful case where an account has nothing to reason
    about, so it cannot double as the default."""


_MISSING = _Missing()

MODEL = "fake-model"
WORKSPACE = UUID(int=42)
ENTITY = UUID(int=7)
SCORE = UUID(int=99)
NOW = datetime(2026, 7, 30, 12, 0, tzinfo=UTC)
RETIREMENT = "business_event:00000000-0000-0000-0000-000000000003"
HIRING = "business_event:00000000-0000-0000-0000-000000000002"

REASON_SOURCE = (
    Path(__file__).resolve().parents[2]
    / "modules"
    / "ai_reasoning_engine"
    / "application"
    / "reason.py"
)

GOOD = json.dumps(
    {
        "proposition": {
            "text": "An ERP replacement programme is underway.",
            "evidence": [RETIREMENT, HIRING],
        },
        "summary": {"text": "They are replacing their ERP.", "evidence": [RETIREMENT]},
        "stated_reasoning": [
            {"text": "A system was retired.", "evidence": [RETIREMENT]},
            {"text": "Implementation staff were hired.", "evidence": [HIRING]},
        ],
    }
)
INVENTED = json.dumps(
    {
        "proposition": {"text": "Revenue grew 41%.", "evidence": [RETIREMENT, HIRING]},
        "summary": {"text": "Growth of 41%.", "evidence": [RETIREMENT]},
        "stated_reasoning": [{"text": "A system was retired.", "evidence": [HIRING]}],
    }
)


class TestOrchestrationAndNothingElse:
    async def test_a_package_is_composed_stored_and_announced(self) -> None:
        reason, packages, publisher, _ = _reason()
        package = await reason.execute(_request())

        assert packages.saved == [package]
        assert len(publisher.published) == 1

    async def test_exactly_one_inference_is_made(self) -> None:
        """The structured single-call half of the M8/M9 split. A second call
        here would quietly make this module M10."""
        reason, _, _, adapter = _reason()
        await reason.execute(_request())

        assert len(adapter.seen) == 1

    async def test_an_account_with_no_context_never_reaches_a_model(self) -> None:
        reason, _, _, adapter = _reason(context=None)

        with pytest.raises(NothingToReasonAboutError):
            await reason.execute(_request())

        assert adapter.seen == []

    async def test_the_release_rule_binds_on_the_request_path(self) -> None:
        """`Reason` takes `execute`, never `measure`."""
        reason, _, _, adapter = _reason(prompt=a_prompt(released_for=None))

        with pytest.raises(PromptNotReleasableError):
            await reason.execute(_request())

        assert adapter.seen == []

    async def test_an_invented_figure_never_becomes_a_package(self) -> None:
        """Grounding is the AI Platform's, and this layer does not duplicate
        it — it simply does not catch the exception."""
        reason, packages, publisher, _ = _reason(content=INVENTED)

        with pytest.raises(UngroundedOutputError):
            await reason.execute(_request())

        assert packages.saved == []
        assert publisher.published == []

    def test_the_use_case_stays_a_thin_composition_layer(self) -> None:
        """Every decision was made elsewhere, so this file should read as a
        list of steps. Asserted structurally rather than by review: the
        module that concludes is the one most likely to accumulate rules that
        belong to a stronger owner."""
        source = REASON_SOURCE.read_text()

        for smell in ("if support", "if contested", "if trend", "len(events)", "> 0.5"):
            assert smell not in source, (
                f"{smell!r} in reason.py suggests a rule that belongs to SupportBasis, "
                "TemporalExplanation, or the signal catalog rather than to orchestration"
            )


class TestTheTenQuestionsAreAnswered:
    """**M9's acceptance criterion for customer-facing value** (ADR-0030).

    A package that cannot populate a row has a defect — and eight of the ten
    are answerable without a model having said anything.
    """

    EXPECTED = (
        "What is the conclusion?",
        "Why did Signora reach it?",
        "Which evidence supports it?",
        "Which evidence challenges it?",
        "How recent is the evidence?",
        "Why did this appear now?",
        "Why not earlier?",
        "What changed?",
        "What does it assume?",
        "What are its limitations?",
        "How do I validate it independently?",
    )

    async def test_every_question_has_a_non_empty_answer(self) -> None:
        reason, _, _, _ = _reason()
        answers = (await reason.execute(_request())).answers()

        assert tuple(answers) == self.EXPECTED
        for question, answer in answers.items():
            assert answer, f"unanswered: {question}"
            assert all(line.strip() for line in answer), f"blank answer: {question}"

    async def test_a_quiet_account_still_answers_what_challenges_it(self) -> None:
        """*"Nothing contradicts this"* is stated explicitly. An absent answer
        reads as an unanswered question."""
        reason, _, _, _ = _reason()
        answers = (await reason.execute(_request())).answers()

        assert answers["Which evidence challenges it?"] == (
            "Nothing in the evidence contradicts this conclusion.",
        )

    async def test_a_contested_account_names_the_dissent(self) -> None:
        reason, _, _, _ = _reason(
            support=_support(contested=True, dissenting_signals=2)
        )
        answers = (await reason.execute(_request())).answers()

        challenges = answers["Which evidence challenges it?"]
        assert any("read the same evidence differently" in line for line in challenges)

    async def test_alternative_readings_appear_among_the_challenges(self) -> None:
        reason, _, _, _ = _reason(
            alternatives=(
                AlternativeReading(
                    signal_type="budget_unlocked", reason="nothing of the kind has happened"
                ),
            )
        )
        answers = (await reason.execute(_request())).answers()

        assert any("budget_unlocked" in a for a in answers["Which evidence challenges it?"])


class TestThePackageRefusesToBeUnusable:
    def test_one_that_cites_nothing_is_refused(self) -> None:
        with pytest.raises(DecisionPackageError, match="cites nothing"):
            _package(supporting_evidence=())

    def test_one_with_no_limitations_is_refused(self) -> None:
        """Both come from the catalog, where they are required — an empty one
        here means the catalog was not consulted."""
        with pytest.raises(DecisionPackageError, match="no limitations"):
            _package(limitations=())

    def test_a_contested_basis_already_guarantees_its_dissent_is_named(self) -> None:
        """Which is why the package carries **no** second check for it.

        A package-level repeat could never fire — reaching it required
        defeating the type system from a test, which is what a guard that
        cannot fail looks like from the inside. Removed at T127; the property
        actually worth protecting (does the *conclusion* acknowledge the
        contradiction?) is the rubric's, at evaluation time.
        """
        with pytest.raises(ValueError, match="names no dissenting signal"):
            _support(contested=True, dissenting_signals=0)

    def test_an_empty_evidence_set_is_refused_by_the_platform_not_by_m9(self) -> None:
        """Which is why `ReasoningContext` carries **no** check for it.

        `EvidenceSet` refuses to be built with no facts, so a repeat in this
        module could never fire — the second unreachable guard found at T127,
        and removed for the same reason as the first."""
        from modules.ai_platform.public import EvidenceError

        with pytest.raises(EvidenceError, match="contains no facts"):
            EvidenceSetBuilder(WORKSPACE).build(assembled_at=NOW)


# --------------------------------------------------------------------------
# helpers


class FakeContext:
    def __init__(self, context: ReasoningContext | None) -> None:
        self._context = context

    async def context_for(
        self, workspace_id: UUID, entity_id: UUID
    ) -> ReasoningContext | None:
        return self._context


class FakePackages:
    def __init__(self) -> None:
        self.saved: list[DecisionPackage] = []

    async def save(self, package: DecisionPackage) -> None:
        self.saved.append(package)

    async def latest_for(
        self, workspace_id: UUID, subject_id: UUID
    ) -> DecisionPackage | None:
        return self.saved[-1] if self.saved else None


class FakePublisher:
    def __init__(self) -> None:
        self.published: list[object] = []

    async def publish(
        self, events: object, *, session: object, producer_module: str, correlation_id: UUID
    ) -> None:
        assert isinstance(events, list)
        self.published.extend(events)


def _evidence() -> EvidenceSet:
    builder = EvidenceSetBuilder(WORKSPACE)
    builder.add(kind="business_event", id=UUID(int=3), summary="A system was retired")
    builder.add(kind="business_event", id=UUID(int=2), summary="Implementation staff hired")
    return builder.build(assembled_at=NOW)


def _support(**overrides: object) -> SupportBasis:
    defaults: dict[str, object] = {
        "corroborating_providers": frozenset({"apollo", "coresignal"}),
        "contributing_events": 3,
        "evidence_state": EvidenceState.CURRENT,
        "contested": False,
        "dissenting_signals": 0,
    }
    return SupportBasis(**{**defaults, **overrides})  # type: ignore[arg-type]


def _temporal() -> TemporalExplanation:
    return TemporalExplanation(
        trigger=ScoreTrigger.SIGNAL_GENERATED,
        basis_at=NOW - timedelta(days=9),
        computed_at=NOW,
        delta=12,
        trend=Trend.RISING,
        evidence_state=EvidenceState.CURRENT,
        valid_until=NOW + timedelta(days=14),
        supersedes=UUID(int=8),
    )


def _context(**overrides: object) -> ReasoningContext:
    defaults: dict[str, object] = {
        "evidence": _evidence(),
        "subject_id": ENTITY,
        "originating_buying_score_id": SCORE,
        "support": _support(),
        "temporal": _temporal(),
        "alternative_readings": (),
        "limitations": ("A retired system may already have been replaced.",),
        "suggested_validation": ("Check the careers page for the replacement stack.",),
        "catalog_version": 1,
    }
    return ReasoningContext(**{**defaults, **overrides})  # type: ignore[arg-type]


def _reason(
    *,
    content: str = GOOD,
    context: object = _MISSING,
    prompt: object | None = None,
    support: SupportBasis | None = None,
    alternatives: tuple[AlternativeReading, ...] = (),
) -> tuple[Reason, FakePackages, FakePublisher, FakeAdapter]:
    adapter = FakeAdapter(models=frozenset({MODEL}), content=content)
    providers = AIProviderRegistry()
    providers.register(adapter)
    packages, publisher = FakePackages(), FakePublisher()

    overrides: dict[str, object] = {}
    if support is not None:
        overrides["support"] = support
    if alternatives:
        overrides["alternative_readings"] = alternatives
    assembled = _context(**overrides) if isinstance(context, _Missing) else None

    return (
        Reason(
            infer=Infer(
                providers=providers,
                prompts=PromptRegistry(versions=(prompt or a_prompt(),)),  # type: ignore[arg-type]
                recorder=FakeRecorder(),
                policy=InferencePolicy(max_attempts=1),
            ),
            context=FakeContext(assembled),
            repository=packages,
            publisher=publisher,
            session=None,  # type: ignore[arg-type]
            prompt_name="narration",
            prompt_version=1,
            clock=lambda: NOW,
        ),
        packages,
        publisher,
        adapter,
    )


def _request() -> ReasonInput:
    return ReasonInput(
        workspace_id=WORKSPACE, entity_id=ENTITY, model=MODEL, correlation_id=uuid4()
    )


def _package(**overrides: object) -> DecisionPackage:
    from modules.ai_platform.public import AIVendor, GroundedStatement

    defaults: dict[str, object] = {
        "id": uuid4(),
        "workspace_id": WORKSPACE,
        "correlation_id": uuid4(),
        "subject_kind": SUBJECT_KIND,
        "subject_id": ENTITY,
        "summary": GroundedStatement(text="They are replacing.", evidence=(RETIREMENT,)),
        "proposition": GroundedStatement(text="A replacement is underway.", evidence=(HIRING,)),
        "stated_reasoning": (),
        "supporting_evidence": (RETIREMENT, HIRING),
        "support": _support(),
        "temporal": _temporal(),
        "alternative_readings": (),
        "limitations": ("It may already have been replaced.",),
        "suggested_validation": ("Check the careers page.",),
        "catalog_version": 1,
        "prompt_name": "reasoning",
        "prompt_version": 1,
        "prompt_fingerprint": "a" * 64,
        "model": "llama3.1:8b",
        "vendor": AIVendor.OLLAMA,
        "evidence_digest": "b" * 64,
        "inference_id": uuid4(),
        "originating_buying_score_id": SCORE,
        "created_at": NOW,
    }
    return DecisionPackage(**{**defaults, **overrides})  # type: ignore[arg-type]
