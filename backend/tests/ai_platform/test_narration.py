"""M8's capability: deterministic intelligence becomes language, and stays
attributable.

Two halves, deliberately separated. The use-case tests run against fakes and
never call a model — sequencing, provenance and the stop condition are
deterministic engineering behaviour. The persistence tests run against a real
database, because immutability, forced RLS and every constraint on the row
are guarantees only PostgreSQL can demonstrate.

**Nothing here calls a model.** Whether a model narrates *well* is the
harness's question (`make eval`), and conflating the two is what the two-tier
split exists to prevent.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from uuid import UUID, uuid4

import pytest
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError, IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from modules.ai_platform.application.infer import Infer, InferencePolicy
from modules.ai_platform.application.narrate import (
    SUBJECT_KIND,
    Narrate,
    NarrateInput,
    NothingToNarrateError,
)
from modules.ai_platform.domain.evidence import EvidenceSet, EvidenceSetBuilder
from modules.ai_platform.domain.grounding import GroundedStatement, UngroundedOutputError
from modules.ai_platform.domain.narration import (
    MaterializedNarration,
    NarrationError,
    NarrationSubject,
)
from modules.ai_platform.domain.prompt import PromptNotReleasableError, PromptRegistry
from modules.ai_platform.domain.provider import AIProviderRegistry, AIVendor
from modules.ai_platform.infrastructure.repository import SqlNarrationRepository
from signora_platform.db import tenant_scoped_session
from tests.ai_platform.fakes import FakeAdapter
from tests.ai_platform.test_infer import FakeRecorder, a_prompt
from tests.opportunity_engine.test_opportunity_pipeline import _tracked

MODEL = "fake-model"
WORKSPACE = UUID(int=42)
ENTITY = UUID(int=7)
NOW = datetime(2026, 7, 30, 12, 0, tzinfo=UTC)
FUNDING = "business_event:00000000-0000-0000-0000-000000000001"

GOOD = json.dumps({"points": [{"text": "They raised 24M USD.", "evidence": [FUNDING]}]})
INVENTED = json.dumps({"points": [{"text": "They grew 40%.", "evidence": [FUNDING]}]})


# --------------------------------------------------------------------------
# The use case


class FakeSource:
    def __init__(self, evidence: EvidenceSet | None) -> None:
        self._evidence = evidence
        self.asked: list[tuple[UUID, UUID]] = []

    async def evidence_for(self, workspace_id: UUID, entity_id: UUID) -> EvidenceSet | None:
        self.asked.append((workspace_id, entity_id))
        return self._evidence


class FakeNarrations:
    def __init__(self) -> None:
        self.saved: list[MaterializedNarration] = []

    async def save(self, narration: MaterializedNarration) -> None:
        self.saved.append(narration)

    async def latest_for(
        self, workspace_id: UUID, subject_id: UUID
    ) -> MaterializedNarration | None:
        for candidate in reversed(self.saved):
            if (candidate.workspace_id, candidate.subject.id) == (workspace_id, subject_id):
                return candidate
        return None


class FakePublisher:
    def __init__(self) -> None:
        self.published: list[object] = []

    async def publish(
        self, events: object, *, session: object, producer_module: str, correlation_id: UUID
    ) -> None:
        assert isinstance(events, list)
        self.published.extend(events)


class TestNarrationComposesAndDoesNotReason:
    async def test_a_grounded_narration_is_produced_stored_and_announced(self) -> None:
        narrate, narrations, publisher, _ = _narrate()
        result = await narrate.execute(_request())

        assert result.statements[0].text == "They raised 24M USD."
        assert narrations.saved == [result]
        assert len(publisher.published) == 1

    async def test_the_stored_artifact_answers_every_provenance_question(self) -> None:
        """*Which evidence · which prompt · which model · which inference ·
        when* — without reconstruction, and without a join."""
        narrate, _, _, _ = _narrate()
        narration = await narrate.execute(_request())

        assert narration.evidence_digest == _evidence().digest
        assert narration.evidence_refs == (FUNDING,)
        assert (narration.prompt_name, narration.prompt_version) == ("narration", 1)
        assert narration.prompt_fingerprint == a_prompt().fingerprint
        assert narration.model
        assert narration.vendor is AIVendor.OLLAMA
        assert narration.inference_id
        assert narration.created_at

    async def test_the_event_carries_identity_and_counts_never_the_prose(self) -> None:
        """Events carry identity; ports carry payload. A paragraph in an
        envelope makes every wording change a contract change."""
        narrate, _, publisher, _ = _narrate()
        narration = await narrate.execute(_request())

        payload = publisher.published[0].to_payload()  # type: ignore[attr-defined]
        assert payload["narration_id"] == str(narration.id)
        assert payload["statement_count"] == 1
        assert payload["subject_kind"] == SUBJECT_KIND
        assert not any("raised 24M" in str(value) for value in payload.values()), (
            "the narration's text reached the event envelope"
        )

    async def test_an_invented_proposition_never_becomes_a_narration(self) -> None:
        """**The stop condition, mechanically enforced.** A statement the
        pipeline did not compute cannot cite anything for it, so grounding
        rejects the call — nothing is stored and nothing is announced."""
        narrate, narrations, publisher, _ = _narrate(content=INVENTED)

        with pytest.raises(UngroundedOutputError):
            await narrate.execute(_request())

        assert narrations.saved == []
        assert publisher.published == []

    async def test_an_account_with_no_evidence_never_reaches_a_model(self) -> None:
        """An empty evidence set would come back as a fluent paragraph about
        nothing, perfectly grounded in no facts at all."""
        narrate, _, _, adapter = _narrate(evidence=None)

        with pytest.raises(NothingToNarrateError):
            await narrate.execute(_request())

        assert adapter.seen == []

    async def test_the_release_rule_binds_on_the_request_path(self) -> None:
        """`Narrate` takes `execute`, never `measure`. A prompt that has not
        passed evaluation for this model does not reach it."""
        narrate, _, _, adapter = _narrate(prompt=a_prompt(released_for=None))

        with pytest.raises(PromptNotReleasableError):
            await narrate.execute(_request())

        assert adapter.seen == []

    async def test_the_subject_is_named_in_the_platforms_own_vocabulary(self) -> None:
        """`subject_kind`/`subject_id`, not `entity_id`. The substrate does not
        learn the pipeline's concepts."""
        narrate, _, _, _ = _narrate()
        narration = await narrate.execute(_request())

        assert narration.subject == NarrationSubject(kind=SUBJECT_KIND, id=ENTITY)


class TestANarrationMustBeAbleToExplainItself:
    def test_one_with_no_statements_is_refused(self) -> None:
        with pytest.raises(NarrationError, match="no statements"):
            _materialized(statements=())

    def test_one_that_cites_nothing_is_refused(self) -> None:
        with pytest.raises(NarrationError, match="cites nothing"):
            _materialized(evidence_refs=())

    def test_one_that_says_nothing_about_anything_is_refused(self) -> None:
        with pytest.raises(NarrationError, match="what it is about"):
            NarrationSubject(kind="  ", id=ENTITY)


# --------------------------------------------------------------------------
# Persistence


@pytest.mark.integration
class TestTheArtifactIsStoredAsAHistoricalFact:
    async def test_it_round_trips_with_its_provenance_intact(
        self, session_factory: async_sessionmaker[AsyncSession]
    ) -> None:
        workspace_id = uuid4()
        narration = _materialized(workspace_id=workspace_id)
        await _save(session_factory, workspace_id, narration)

        async with tenant_scoped_session(
            session_factory, workspace_id=workspace_id, user_id=uuid4()
        ) as session:
            found = await SqlNarrationRepository(session).latest_for(workspace_id, ENTITY)

        assert found is not None
        assert found.statements == narration.statements
        assert found.evidence_refs == narration.evidence_refs
        assert found.vendor is AIVendor.OLLAMA
        assert found.inference_id == narration.inference_id

    async def test_a_newer_narration_supersedes_by_recency_not_by_edit(
        self, session_factory: async_sessionmaker[AsyncSession]
    ) -> None:
        """Prompt evolution produces a **new** narration. "Current" is a query
        over timestamps, never a mutable column that could disagree."""
        workspace_id = uuid4()
        older = _materialized(workspace_id=workspace_id, created_at=NOW)
        newer = _materialized(
            workspace_id=workspace_id,
            created_at=NOW.replace(hour=13),
            statements=(GroundedStatement(text="A later reading.", evidence=(FUNDING,)),),
        )
        await _save(session_factory, workspace_id, older)
        await _save(session_factory, workspace_id, newer)

        async with tenant_scoped_session(
            session_factory, workspace_id=workspace_id, user_id=uuid4()
        ) as session:
            found = await SqlNarrationRepository(session).latest_for(workspace_id, ENTITY)
            both = (
                await session.execute(text("SELECT count(*) FROM ai_narration"))
            ).scalar_one()

        assert found is not None
        assert found.statements[0].text == "A later reading."
        assert both == 2, "the older narration must survive — it is what a customer was shown"

    async def test_the_application_role_cannot_edit_one(
        self, session_factory: async_sessionmaker[AsyncSession]
    ) -> None:
        workspace_id = uuid4()
        await _save(session_factory, workspace_id, _materialized(workspace_id=workspace_id))

        async with tenant_scoped_session(
            session_factory, workspace_id=workspace_id, user_id=uuid4()
        ) as session:
            with pytest.raises(DBAPIError, match="permission denied"):
                await session.execute(text("UPDATE ai_narration SET model = 'other'"))

    async def test_one_workspace_never_sees_anothers_narration(
        self, session_factory: async_sessionmaker[AsyncSession]
    ) -> None:
        mine, theirs = uuid4(), uuid4()
        await _save(session_factory, mine, _materialized(workspace_id=mine))
        await _save(session_factory, theirs, _materialized(workspace_id=theirs))

        async with tenant_scoped_session(
            session_factory, workspace_id=mine, user_id=uuid4()
        ) as session:
            count = (
                await session.execute(text("SELECT count(*) FROM ai_narration"))
            ).scalar_one()

        assert count == 1

    async def test_a_narration_that_says_nothing_is_refused_by_the_database(
        self, session_factory: async_sessionmaker[AsyncSession]
    ) -> None:
        """The domain refuses it too. Both, because the writer is exactly what
        a future change replaces."""
        workspace_id = uuid4()
        async with tenant_scoped_session(
            session_factory, workspace_id=workspace_id, user_id=uuid4()
        ) as session:
            with pytest.raises(IntegrityError, match="ck_ai_narration_says_something"):
                await session.execute(
                    text(
                        """
                        INSERT INTO ai_narration (
                          id, workspace_id, correlation_id, subject_kind, subject_id,
                          prompt_name, prompt_version, prompt_fingerprint, model, vendor,
                          evidence_digest, evidence_refs, inference_id, statements,
                          payload_version, created_by, updated_by
                        ) VALUES (
                          gen_random_uuid(), :ws, gen_random_uuid(), 'account', :subject,
                          'p', 1, 'f', 'm', 'ollama', 'd', ARRAY['a:1'], gen_random_uuid(),
                          '[]'::jsonb, 1, :ws, :ws
                        )
                        """
                    ),
                    {"ws": workspace_id, "subject": ENTITY},
                )


# --------------------------------------------------------------------------
# helpers


class _Unset:
    """Distinguishes "no evidence argument given" from "evidence is None".

    `None` is a meaningful value here — it is the case where an account has
    nothing to narrate — so it cannot double as the default.
    """


_UNSET = _Unset()


def _evidence() -> EvidenceSet:
    builder = EvidenceSetBuilder(WORKSPACE)
    builder.add(
        kind="business_event",
        id=UUID(int=1),
        summary="Raised 24M USD in a Series B round",
        attributes={"amount": "24000000"},
    )
    return builder.build(assembled_at=NOW)


def _request() -> NarrateInput:
    return NarrateInput(
        workspace_id=WORKSPACE, entity_id=ENTITY, model=MODEL, correlation_id=uuid4()
    )


def _narrate(
    *,
    content: str = GOOD,
    evidence: EvidenceSet | None | _Unset = _UNSET,
    prompt: object | None = None,
) -> tuple[Narrate, FakeNarrations, FakePublisher, FakeAdapter]:
    adapter = FakeAdapter(models=frozenset({MODEL}), content=content)
    providers = AIProviderRegistry()
    providers.register(adapter)
    narrations, publisher = FakeNarrations(), FakePublisher()
    assembled = _evidence() if isinstance(evidence, _Unset) else evidence
    narrate = Narrate(
        infer=Infer(
            providers=providers,
            prompts=PromptRegistry(versions=(prompt or a_prompt(),)),  # type: ignore[arg-type]
            recorder=FakeRecorder(),
            policy=InferencePolicy(max_attempts=1),
        ),
        source=FakeSource(assembled),
        repository=narrations,
        publisher=publisher,
        session=None,  # type: ignore[arg-type]
        prompt_name="narration",
        prompt_version=1,
        clock=lambda: NOW,
    )
    return narrate, narrations, publisher, adapter


def _materialized(**overrides: object) -> MaterializedNarration:
    defaults: dict[str, object] = {
        "id": uuid4(),
        "workspace_id": WORKSPACE,
        "correlation_id": uuid4(),
        "subject": NarrationSubject(kind=SUBJECT_KIND, id=ENTITY),
        "prompt_name": "explanation_narration",
        "prompt_version": 1,
        "prompt_fingerprint": "a" * 64,
        "model": "llama3.1:8b",
        "vendor": AIVendor.OLLAMA,
        "evidence_digest": "b" * 64,
        "evidence_refs": (FUNDING,),
        "inference_id": uuid4(),
        "statements": (GroundedStatement(text="They raised 24M USD.", evidence=(FUNDING,)),),
        "created_at": NOW,
    }
    return MaterializedNarration(**{**defaults, **overrides})  # type: ignore[arg-type]


async def _save(
    factory: async_sessionmaker[AsyncSession], workspace_id: UUID, narration: MaterializedNarration
) -> None:
    async with tenant_scoped_session(
        factory, workspace_id=workspace_id, user_id=uuid4()
    ) as session:
        await SqlNarrationRepository(session).save(narration)


@pytest.mark.integration
class TestTheWholeChainAgainstTheRealPipeline:
    """M8's demonstration: a provider payload becomes a grounded paragraph.

    Runs the real pipeline, the real composition root, the real repositories
    and the real outbox publisher. **The adapter is scripted**, and that is
    deliberate rather than a shortcut: `make eval` is the only command in this
    repository that calls a model, Ollama is never a production dependency
    (ADR-0028), and a deployment gate that needed a GPU would be a gate people
    learn to skip. What is proven here is the half that is deterministic —
    composition, provenance, persistence, publication, and refusal.
    """

    async def test_a_grounded_narration_is_produced_stored_and_published(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        admin_session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        workspace_id, user_id, entity_id, _ = await _tracked(
            session_factory, admin_session_factory, "northwind"
        )
        evidence = await _assembled(session_factory, workspace_id, user_id, entity_id)
        assert evidence is not None
        cited = [fact.ref.token for fact in evidence]

        narration = await _narrate_live(
            session_factory, workspace_id, user_id, entity_id, _restating(cited)
        )

        assert narration.evidence_digest == evidence.digest
        assert narration.subject.id == entity_id
        assert narration.prompt_name == "explanation_narration"
        assert narration.inference_id

        async with tenant_scoped_session(
            session_factory, workspace_id=workspace_id, user_id=user_id
        ) as session:
            stored = await SqlNarrationRepository(session).latest_for(workspace_id, entity_id)
            inferences = (
                await session.execute(text("SELECT count(*) FROM ai_inference"))
            ).scalar_one()
        assert stored is not None
        assert stored.id == narration.id
        assert inferences == 1, "the operational record was written alongside the artifact"

        async with admin_session_factory() as session, session.begin():
            published = (
                await session.execute(
                    text(
                        "SELECT count(*) FROM outbox_event WHERE event_type = "
                        "'ai.narration_completed' AND workspace_id = :ws"
                    ),
                    {"ws": workspace_id},
                )
            ).scalar_one()
        assert published == 1, "the event is published in the transaction that stored the row"

    async def test_an_invented_proposition_is_refused_and_nothing_is_stored(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        admin_session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        """**The milestone's real demonstration.** The guard is deterministic
        even though the thing it guards is not: a figure appearing in no cited
        fact fails the call and the artifact is never written.

        **Finding, recorded here rather than worked around.** The
        `ai_inference` row that `Infer` writes for the failure does *not*
        survive: `tenant_scoped_session` wraps `session.begin()`, so the
        raised error rolls the unit of work back and takes the operational
        record with it. AC-69 therefore holds in the domain — `Infer` records
        every outcome — and **does not hold in production**, which is the
        half that matters for measuring the ungrounded rate (R-10).

        Fixing it means deciding how operational history escapes a business
        transaction, which is an architectural question and not one a coding
        session settles. The test asserts what is true today so the gap is
        visible rather than assumed closed.
        """
        workspace_id, user_id, entity_id, _ = await _tracked(
            session_factory, admin_session_factory, "northwind"
        )
        evidence = await _assembled(session_factory, workspace_id, user_id, entity_id)
        assert evidence is not None
        cited = [fact.ref.token for fact in evidence]

        with pytest.raises(UngroundedOutputError):
            await _narrate_live(
                session_factory,
                workspace_id,
                user_id,
                entity_id,
                json.dumps({"points": [{"text": "They grew 4173%.", "evidence": [cited[0]]}]}),
            )

        async with tenant_scoped_session(
            session_factory, workspace_id=workspace_id, user_id=user_id
        ) as session:
            narrations = (
                await session.execute(text("SELECT count(*) FROM ai_narration"))
            ).scalar_one()
            inferences = (
                await session.execute(text("SELECT count(*) FROM ai_inference"))
            ).scalar_one()

        assert narrations == 0, "an ungrounded output must never reach a customer-visible table"
        assert inferences == 0, (
            "KNOWN GAP, not the desired behaviour: the failure record was rolled back with the "
            "unit of work. When operational history is made to survive a rollback, this "
            "assertion becomes `== 1` with outcome 'ungrounded' — and this test is where that "
            "change will be noticed."
        )


def _restating(cited: list[str]) -> str:
    """A narration that cites every fact and invents nothing.

    Built from the pipeline's own refs rather than from a fixture, so the test
    cannot pass against evidence the pipeline no longer produces.
    """
    return json.dumps({"points": [{"text": "This account is being tracked.", "evidence": cited}]})


async def _assembled(
    factory: async_sessionmaker[AsyncSession], workspace_id: UUID, user_id: UUID, entity_id: UUID
) -> EvidenceSet | None:
    from modules.ai_platform.infrastructure.explanation import OpportunityExplanationSource
    from tests.pipeline import opportunities

    async with tenant_scoped_session(
        factory, workspace_id=workspace_id, user_id=user_id
    ) as session:
        source = OpportunityExplanationSource(opportunities(session, workspace_id))
        return await source.evidence_for(workspace_id, entity_id)


async def _narrate_live(
    factory: async_sessionmaker[AsyncSession],
    workspace_id: UUID,
    user_id: UUID,
    entity_id: UUID,
    content: str,
) -> MaterializedNarration:
    from modules.ai_platform.infrastructure.composition import build_narrate
    from modules.ai_platform.infrastructure.explanation import OpportunityExplanationSource
    from signora_platform.event_bus import PostgresOutboxEventPublisher
    from tests.pipeline import opportunities

    # Registered under the model the shipped prompt has actually been released
    # for, so the release rule is exercised rather than bypassed. The adapter
    # is scripted; the *rule* is real.
    adapter = FakeAdapter(models=frozenset({"llama3.1:8b"}), content=content)
    providers = AIProviderRegistry()
    providers.register(adapter)

    async with tenant_scoped_session(
        factory, workspace_id=workspace_id, user_id=user_id
    ) as session:
        narrate = build_narrate(
            session,
            providers=providers,
            source=OpportunityExplanationSource(opportunities(session, workspace_id)),
            publisher=PostgresOutboxEventPublisher(),
            policy=InferencePolicy(max_attempts=1),
        )
        return await narrate.execute(
            NarrateInput(
                workspace_id=workspace_id,
                entity_id=entity_id,
                model="llama3.1:8b",
                correlation_id=uuid4(),
            )
        )
