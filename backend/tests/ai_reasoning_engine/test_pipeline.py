"""M9's demonstration: a provider payload becomes a Decision Package.

Runs the **real** pipeline, the real context adapter, the real composition
root, the real repository and the real outbox publisher. The model adapter is
scripted, deliberately and for the same reason M8's is: `make eval` is the only
command in this repository that calls a model, a local runtime is never a
production dependency (ADR-0028), and a deployment gate needing a GPU is a gate
people learn to skip.

What is proven here is the half that is deterministic — and for M9 that half is
**twelve of the fifteen parts**. Support, temporal, alternative readings,
limitations and validation are assembled from real pipeline rows without a model
having said anything, which is the whole claim of Deterministic Explainability.

**`reasoning@1` earned its release on 2026-07-31 against `granite3.3:2b`** —
2 cases, 0 grounding failures, 0 schema failures, coverage 0.833. It is
released for **that model and no other**, which these tests assert in both
directions: the certified model resolves, and `llama3.1:8b` is still refused
because nothing ever measured it.

That is why the chain below is still exercised against an *in-memory registry*
rather than the shipped one. The double is bound to `llama3.1:8b`, so it
proves the release **mechanism** without depending on which model happens to
be certified this month — and `TestTheReleaseRuleBindsTheRequestPath` asserts
the shipped manifest holds exactly the one measurement that earned it, with
`passed` derived from the failure counts rather than stored.
"""

from __future__ import annotations

import json
from datetime import date
from uuid import UUID, uuid4

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from modules.ai_platform.public import (
    AIProviderRegistry,
    Evaluation,
    Infer,
    InferencePolicy,
    PromptNotReleasableError,
    PromptRegistry,
    PromptVersion,
)
from modules.ai_reasoning_engine.application.reason import ReasonInput
from modules.ai_reasoning_engine.domain.context import ReasoningContext
from modules.ai_reasoning_engine.domain.package import DecisionPackage
from modules.ai_reasoning_engine.domain.support import SupportLevel
from modules.ai_reasoning_engine.infrastructure.composition import (
    PROMPT_DIR,
    REASONING_PROMPT,
    REASONING_PROMPT_VERSION,
    build_reason,
)
from modules.ai_reasoning_engine.infrastructure.context import PipelineReasoningContext
from modules.ai_reasoning_engine.infrastructure.repository import SqlDecisionPackageRepository
from modules.buying_score_engine.public import ScoreTrigger
from signora_platform.db.session import tenant_scoped_session
from tests.ai_platform.fakes import FakeAdapter
from tests.opportunity_engine.test_opportunity_pipeline import _tracked
from tests.pipeline import _published

MODEL = "llama3.1:8b"

pytestmark = pytest.mark.integration


def _released_registry() -> PromptRegistry:
    """A registry holding M9's prompt **with a passing evaluation**.

    A test double for the registry, not for the release *rule*: the rule is
    the real one, and it is satisfied here by a measurement of the shape it
    demands. The shipped manifest is untouched — `test_the_shipped_prompt_has
    _earned_no_release` is what stops this becoming a way to grant one.
    """
    text_ = (PROMPT_DIR / f"{REASONING_PROMPT}@{REASONING_PROMPT_VERSION}.md").read_text()
    return PromptRegistry(
        versions=(
            PromptVersion(
                name=REASONING_PROMPT,
                version=REASONING_PROMPT_VERSION,
                owner="ai-platform@signora",
                text=text_,
                evaluations=(
                    Evaluation(
                        model=MODEL,
                        dataset="explanation_narration",
                        dataset_version=1,
                        rubric_version=1,
                        evaluated_on=date(2026, 7, 30),
                        sample_size=2,
                        grounding_failures=0,
                        schema_failures=0,
                        coverage=1.0,
                    ),
                ),
            ),
        )
    )


def _reasoned(cited: list[str]) -> str:
    """A conclusion that cites the pipeline's own refs and invents nothing.

    Built from the refs the pipeline actually produced rather than a fixture,
    so this cannot pass against evidence the pipeline no longer emits. Two
    distinct premises, because `ReasonedOutput` refuses fewer.
    """
    return json.dumps(
        {
            "proposition": {"text": "This account warrants attention now.", "evidence": cited},
            "summary": {"text": "This account is being tracked.", "evidence": cited[:1]},
            "stated_reasoning": [
                {"text": "An opportunity is open for this account.", "evidence": cited[:1]},
                {"text": "A buying score supports it.", "evidence": cited[1:2] or cited[:1]},
            ],
        }
    )


async def _context(
    factory: async_sessionmaker[AsyncSession],
    workspace_id: UUID,
    user_id: UUID,
    entity_id: UUID,
) -> ReasoningContext | None:
    from modules.ai_platform.infrastructure.explanation import OpportunityExplanationSource
    from tests.pipeline import opportunities, signals

    async with tenant_scoped_session(
        factory, workspace_id=workspace_id, user_id=user_id
    ) as session:
        source = PipelineReasoningContext(
            opportunities=opportunities(session, workspace_id),
            signals=signals(session, workspace_id),
            evidence=OpportunityExplanationSource(opportunities(session, workspace_id)),
        )
        return await source.context_for(workspace_id, entity_id)


async def _reason_live(
    factory: async_sessionmaker[AsyncSession],
    workspace_id: UUID,
    user_id: UUID,
    entity_id: UUID,
    content: str,
    *,
    prompts: PromptRegistry | None = None,
) -> DecisionPackage:
    from modules.ai_platform.infrastructure.explanation import OpportunityExplanationSource
    from modules.ai_platform.infrastructure.prompt_loader import load_prompt_registry
    from modules.ai_platform.infrastructure.repository import SqlInferenceRecorder
    from signora_platform.event_bus import PostgresOutboxEventPublisher
    from tests.pipeline import opportunities, signals

    providers = AIProviderRegistry()
    providers.register(FakeAdapter(models=frozenset({MODEL}), content=content))

    async with tenant_scoped_session(
        factory, workspace_id=workspace_id, user_id=user_id
    ) as session:
        reason = build_reason(
            session,
            # Bound to M9's own prompt directory. Which prompts an `Infer`
            # serves is the application composition root's decision — the one
            # place that may import both modules' infrastructure — because
            # `public/` sits below `infrastructure/` and cannot publish a
            # loader that reads the filesystem.
            infer=Infer(
                providers=providers,
                prompts=prompts or load_prompt_registry(PROMPT_DIR),
                # The same factory, so operational history commits on its own
                # transaction and survives this block rolling back (ADR-0029).
                recorder=SqlInferenceRecorder(factory),
                policy=InferencePolicy(max_attempts=1),
            ),
            opportunities=opportunities(session, workspace_id),
            signals=signals(session, workspace_id),
            evidence=OpportunityExplanationSource(opportunities(session, workspace_id)),
            publisher=PostgresOutboxEventPublisher(),
        )
        return await reason.execute(
            ReasonInput(
                workspace_id=workspace_id,
                entity_id=entity_id,
                model=MODEL,
                correlation_id=uuid4(),
            )
        )


class TestTheDeterministicTwelveNeedNoModel:
    """**The claim M9 exists to make.** Twelve of fifteen parts are assembled
    from pipeline rows, so a package is valuable before a model speaks — and a
    failure to reach one degrades the package rather than emptying it."""

    async def test_context_assembles_from_the_real_pipeline(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        admin_session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        workspace_id, user_id, entity_id, _ = await _tracked(
            session_factory, admin_session_factory, "northwind"
        )

        context = await _context(session_factory, workspace_id, user_id, entity_id)

        assert context is not None
        assert context.subject_id == entity_id
        assert context.originating_buying_score_id
        assert context.evidence.digest

        # **Support is composed from real events, not defaulted.** Asserted
        # positively because an empty basis still produces a *valid* level
        # (LIMITED) — a mutation returning no providers and no events would
        # otherwise pass while telling every customer their evidence is
        # single-sourced.
        assert context.support.contributing_events > 0
        assert context.support.corroborating_providers
        assert context.support.level in tuple(SupportLevel)

        # Temporal is copied from the originating score, field for field.
        assert context.temporal.trigger in tuple(ScoreTrigger)
        assert context.temporal.basis_at <= context.temporal.computed_at
        assert context.temporal.why_now().startswith("This reading exists because")

        # Catalog text, composed only for the types that actually contributed,
        # deduplicated, and non-empty because both are required in the catalog.
        assert context.limitations and context.suggested_validation
        assert len(set(context.limitations)) == len(context.limitations), "not deduplicated"
        assert len(set(context.suggested_validation)) == len(context.suggested_validation)
        assert context.catalog_version > 0

    async def test_context_assembly_is_reproducible(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        admin_session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        """**Nothing here reads a clock or depends on iteration order.**

        Two assemblies over unchanged rows must be identical, because a hidden
        input would make a package's digest — the thing a customer cites —
        depend on when it happened to be built.
        """
        workspace_id, user_id, entity_id, _ = await _tracked(
            session_factory, admin_session_factory, "northwind"
        )

        first = await _context(session_factory, workspace_id, user_id, entity_id)
        second = await _context(session_factory, workspace_id, user_id, entity_id)

        assert first is not None and second is not None
        assert first.evidence.digest == second.evidence.digest
        assert first.support == second.support
        assert first.temporal == second.temporal
        assert first.limitations == second.limitations
        assert first.alternative_readings == second.alternative_readings

    async def test_an_untracked_account_yields_no_context(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        admin_session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        """`None`, never an empty context. A conclusion about an account the
        pipeline has said nothing about is not degraded — it is invented."""
        workspace_id, user_id, _, _ = await _tracked(
            session_factory, admin_session_factory, "northwind"
        )

        assert await _context(session_factory, workspace_id, user_id, uuid4()) is None


#: The model `reasoning@1` earned its release against, 2026-07-31. **Not a
#: permanent pin.** It was selected because it is the only candidate tested
#: that stays entirely resident in 4 GiB of VRAM, and the renderer/parser
#: protocol inconsistency in ADR-0031 is why several stronger models were
#: refused. Revisit once that is corrected.
CERTIFIED_MODEL = "granite3.3:2b"


class TestTheReleaseRuleBindsTheRequestPath:
    """A prompt is usable **exactly where a measurement says it is.**

    Rewritten 2026-07-31, when `reasoning@1` earned its release. The previous
    version asserted the manifest was *empty* and instructed whoever broke it
    to replace it with the run that earned the release — which is what
    happened. What it protected has not changed: a release that no measurement
    produced must fail the suite, and it would otherwise be invisible.
    """

    def test_the_shipped_release_names_the_run_that_earned_it(self) -> None:
        """Every field is asserted against the recorded measurement.

        A hand-written entry would have to fabricate all of them consistently,
        and `passed` is **derived** from the failure counts rather than stored
        — so a fabricated "release" that did not also fabricate zero grounding
        failures would not read as released at all.
        """
        from modules.ai_platform.infrastructure.prompt_loader import load_prompt_registry

        version = load_prompt_registry(PROMPT_DIR).get(REASONING_PROMPT, REASONING_PROMPT_VERSION)

        assert len(version.evaluations) == 1, (
            "reasoning@1 should record exactly the one run that earned its release. "
            "Evaluations accumulate; an unexpected count means one was added by hand."
        )
        earned = version.evaluations[0]
        assert earned.model == CERTIFIED_MODEL
        assert earned.dataset == "explanation_narration"
        assert earned.dataset_version == 1
        assert earned.grounding_failures == 0
        assert earned.schema_failures == 0
        assert earned.passed, "a recorded evaluation that does not pass is not a release"

    def test_the_release_does_not_extend_to_other_models(self) -> None:
        """**Release is earned per (model, dataset), never in general.**

        Developing against one model demonstrates nothing about another —
        which this milestone proved the hard way: five models were run against
        this benchmark and four did not pass it.
        """
        from modules.ai_platform.infrastructure.prompt_loader import load_prompt_registry

        version = load_prompt_registry(PROMPT_DIR).get(REASONING_PROMPT, REASONING_PROMPT_VERSION)

        assert version.is_released_for(CERTIFIED_MODEL), "the certified model must be released"
        assert not version.is_released_for(MODEL), (
            f"reasoning@1 must not be usable with {MODEL}; it was never measured against it."
        )

    async def test_execute_refuses_an_unreleased_prompt_and_stores_nothing(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        admin_session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        """A refusal, not a degraded package. The rule is what stops a prompt
        reaching a customer on a model nothing measured it against."""
        workspace_id, user_id, entity_id, _ = await _tracked(
            session_factory, admin_session_factory, "northwind"
        )
        context = await _context(session_factory, workspace_id, user_id, entity_id)
        assert context is not None
        cited = [fact.ref.token for fact in context.evidence]

        with pytest.raises(PromptNotReleasableError):
            await _reason_live(session_factory, workspace_id, user_id, entity_id, _reasoned(cited))

        async with tenant_scoped_session(
            session_factory, workspace_id=workspace_id, user_id=user_id
        ) as session:
            stored = (await session.execute(text("SELECT count(*) FROM ai_reasoning"))).scalar_one()
        assert stored == 0, "a refused inference must leave no customer-visible row"


class TestTheWholeChainAgainstTheRealPipeline:
    async def test_a_package_is_produced_stored_and_published(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        admin_session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        workspace_id, user_id, entity_id, _ = await _tracked(
            session_factory, admin_session_factory, "northwind"
        )
        context = await _context(session_factory, workspace_id, user_id, entity_id)
        assert context is not None
        cited = [fact.ref.token for fact in context.evidence]

        package = await _reason_live(
            session_factory,
            workspace_id,
            user_id,
            entity_id,
            _reasoned(cited),
            prompts=_released_registry(),
        )

        assert package.evidence_digest == context.evidence.digest
        assert package.subject_id == entity_id
        assert package.prompt_name == REASONING_PROMPT
        assert package.inference_id
        # Every one of the eleven customer questions is answered.
        assert all(package.answers().values())

        async with tenant_scoped_session(
            session_factory, workspace_id=workspace_id, user_id=user_id
        ) as session:
            stored = await SqlDecisionPackageRepository(session).latest_for(workspace_id, entity_id)
            inferences = (
                await session.execute(text("SELECT count(*) FROM ai_inference"))
            ).scalar_one()

        assert stored is not None
        assert stored.id == package.id
        assert stored.support.level is package.support.level
        assert stored.temporal.trigger is package.temporal.trigger
        assert stored.limitations == package.limitations
        # Read under the **relay's** identity, never the application's:
        # `signora_app` holds no SELECT grant on `outbox_event`, and that is
        # the Platform Infrastructure Policy working rather than an
        # inconvenience to route around (migration 0006, CLAUDE.md §8).
        published = await _published(admin_session_factory, "ai_reasoning.completed")
        assert len(published) == 1, "the event announcing the conclusion reached the outbox"
        announced = published[0]
        assert announced.workspace_id == workspace_id
        assert announced.producer_module == "ai_reasoning_engine"
        assert announced.payload["reasoning_id"] == str(package.id)
        assert announced.payload["support"] == package.support.level.value
        # Identity and counts, never the prose: a paragraph in an envelope
        # makes every wording change a contract change.
        assert "proposition" not in announced.payload
        assert announced.payload["conclusion_count"] == len(package.statements)
        assert inferences == 1, "the operational record was written alongside the artifact"

    async def test_the_stored_support_level_is_derived_not_read_back(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        admin_session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        """`support_level` and `contested` are **write-only query surface**.

        They duplicate facts the `support` JSONB already carries, and
        duplicated truth eventually becomes contradictory truth. The
        duplication earns its place as an operator query surface and is
        neutralised by never letting the copies influence behaviour.

        Asserted two ways, because one alone would be weak: the scalar agrees
        with the derived level at the moment of writing, **and** the read path
        contains no reference to it at all. The second is what would fail if
        someone later 'optimised' the read by trusting the column.
        """
        workspace_id, user_id, entity_id, _ = await _tracked(
            session_factory, admin_session_factory, "northwind"
        )
        context = await _context(session_factory, workspace_id, user_id, entity_id)
        assert context is not None
        package = await _reason_live(
            session_factory,
            workspace_id,
            user_id,
            entity_id,
            _reasoned([fact.ref.token for fact in context.evidence]),
            prompts=_released_registry(),
        )

        async with tenant_scoped_session(
            session_factory, workspace_id=workspace_id, user_id=user_id
        ) as session:
            stored = await SqlDecisionPackageRepository(session).latest_for(workspace_id, entity_id)
            raw = (
                await session.execute(
                    text("SELECT support_level, contested FROM ai_reasoning WHERE id = :i"),
                    {"i": package.id},
                )
            ).one()

        assert stored is not None
        assert stored.support.level.value == raw[0]
        assert stored.support.contested == raw[1]

    def test_the_read_path_never_consults_the_duplicated_columns(self) -> None:
        """The structural half, and the one that survives a refactor.

        A drift between the JSONB and the scalars cannot reach a customer while
        `_to_package` cannot see them. If this fails, the two representations
        have become one truth with two authorities.
        """
        import ast
        import inspect

        from modules.ai_reasoning_engine.infrastructure import repository

        read_path = ast.parse(inspect.getsource(repository._to_package))
        consulted = {node.attr for node in ast.walk(read_path) if isinstance(node, ast.Attribute)}
        assert "support_level" not in consulted
        assert "contested" not in consulted, (
            "`contested` must come from the support basis, not from its duplicate column."
        )


class TestTheRepositoryStoresHistoryRatherThanState:
    """Packages accumulate. **"Latest" is a query, never a mutable column.**

    A `current` flag would be a second representation of a fact the timestamps
    already carry — and maintaining one needs the `UPDATE` grant this table
    deliberately withholds.
    """

    async def test_the_most_recent_package_is_returned(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        admin_session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        """Two packages, and the later one wins.

        Written with **two** rows on purpose: with one stored package, a read
        ordered oldest-first is indistinguishable from one ordered newest-first,
        and the ordering is the only thing `latest_for` actually decides.
        """
        from datetime import UTC, datetime, timedelta

        from tests.ai_reasoning_engine.test_reason import _package

        workspace_id, user_id, entity_id, _ = await _tracked(
            session_factory, admin_session_factory, "northwind"
        )
        earlier = datetime.now(UTC) - timedelta(hours=2)
        older = _package(workspace_id=workspace_id, subject_id=entity_id, created_at=earlier)
        newer = _package(
            workspace_id=workspace_id,
            subject_id=entity_id,
            created_at=earlier + timedelta(hours=1),
        )

        async with tenant_scoped_session(
            session_factory, workspace_id=workspace_id, user_id=user_id
        ) as session:
            repository = SqlDecisionPackageRepository(session)
            await repository.save(older)
            await repository.save(newer)

        async with tenant_scoped_session(
            session_factory, workspace_id=workspace_id, user_id=user_id
        ) as session:
            latest = await SqlDecisionPackageRepository(session).latest_for(workspace_id, entity_id)

        assert latest is not None
        assert latest.id == newer.id, "the older package was returned as the current one"
        # The superseded package is still readable — a package records what a
        # customer was shown, and history is not overwritten by a better answer.
        assert latest.created_at > older.created_at

    async def test_a_package_survives_the_round_trip_unchanged(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        admin_session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        """Every one of the fifteen parts, not merely the identity.

        A serialiser that dropped `dissenting_signals`, `supersedes` or a
        catalog line would leave a package that still loads and still looks
        complete — which is exactly the failure a customer would meet while
        trying to disagree with it.
        """
        from tests.ai_reasoning_engine.test_reason import _package

        workspace_id, user_id, entity_id, _ = await _tracked(
            session_factory, admin_session_factory, "northwind"
        )
        original = _package(workspace_id=workspace_id, subject_id=entity_id)

        async with tenant_scoped_session(
            session_factory, workspace_id=workspace_id, user_id=user_id
        ) as session:
            await SqlDecisionPackageRepository(session).save(original)

        async with tenant_scoped_session(
            session_factory, workspace_id=workspace_id, user_id=user_id
        ) as session:
            restored = await SqlDecisionPackageRepository(session).latest_for(
                workspace_id, entity_id
            )

        assert restored is not None
        assert restored.summary == original.summary
        assert restored.proposition == original.proposition
        assert restored.stated_reasoning == original.stated_reasoning
        assert restored.supporting_evidence == original.supporting_evidence
        assert restored.support == original.support
        assert restored.temporal == original.temporal
        assert restored.alternative_readings == original.alternative_readings
        assert restored.limitations == original.limitations
        assert restored.suggested_validation == original.suggested_validation
        assert restored.catalog_version == original.catalog_version
        assert restored.vendor is original.vendor
        assert restored.evidence_digest == original.evidence_digest
        assert restored.inference_id == original.inference_id
        assert restored.originating_buying_score_id == original.originating_buying_score_id
        # The eleven customer questions still answer after a round trip.
        assert restored.answers() == original.answers()

    async def test_a_contested_package_keeps_its_dissent_through_storage(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        admin_session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        """**Contradiction must survive the last stage too.**

        Six upstream stages preserve dissent rather than netting it away; a
        serialiser that dropped `dissenting_signals` would undo all of it at
        the final write, and the default fixture — uncontested, zero dissent —
        cannot tell. Found by a surviving mutation.

        It also exercises `ck_ai_reasoning_contested_names_its_dissent`: a
        contested row that named no dissent would be refused by PostgreSQL,
        which is where the invariant belongs. The writer is replaceable; the
        invariant is not.
        """
        from tests.ai_reasoning_engine.test_reason import _package, _support

        workspace_id, user_id, entity_id, _ = await _tracked(
            session_factory, admin_session_factory, "northwind"
        )
        original = _package(
            workspace_id=workspace_id,
            subject_id=entity_id,
            support=_support(contested=True, dissenting_signals=2),
        )

        async with tenant_scoped_session(
            session_factory, workspace_id=workspace_id, user_id=user_id
        ) as session:
            await SqlDecisionPackageRepository(session).save(original)

        async with tenant_scoped_session(
            session_factory, workspace_id=workspace_id, user_id=user_id
        ) as session:
            restored = await SqlDecisionPackageRepository(session).latest_for(
                workspace_id, entity_id
            )

        assert restored is not None
        assert restored.support.contested is True
        assert restored.support.dissenting_signals == 2
        # And a customer is told what disagrees, not merely that something does.
        assert any("read the same evidence differently" in c for c in restored._challenges())

    async def test_the_stored_basis_is_byte_stable(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        admin_session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        """Providers are stored **sorted**, so insertion order cannot leak in.

        A `frozenset`'s iteration order is not a declared input, and a stored
        artifact whose bytes depend on one is a package two identical runs
        would disagree about. Invisible with a single provider — which is what
        let the mutation survive.
        """
        from tests.ai_reasoning_engine.test_reason import _package, _support

        workspace_id, user_id, entity_id, _ = await _tracked(
            session_factory, admin_session_factory, "northwind"
        )
        original = _package(
            workspace_id=workspace_id,
            subject_id=entity_id,
            support=_support(
                corroborating_providers=frozenset({"zoominfo", "apollo", "coresignal"})
            ),
        )

        async with tenant_scoped_session(
            session_factory, workspace_id=workspace_id, user_id=user_id
        ) as session:
            await SqlDecisionPackageRepository(session).save(original)

        async with tenant_scoped_session(
            session_factory, workspace_id=workspace_id, user_id=user_id
        ) as session:
            stored = (
                await session.execute(
                    text("SELECT support -> 'corroborating_providers' FROM ai_reasoning"),
                )
            ).scalar_one()

        assert stored == ["apollo", "coresignal", "zoominfo"], (
            "providers were written in set-iteration order rather than sorted"
        )
