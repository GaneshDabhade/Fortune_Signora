"""Permanent guarantees the Buying Score Engine rests on.

**This is the pipeline's first intentional reduction.** Every stage above it
adds information and destroys none; this one turns many live hypotheses into
a single integer. That makes it the first place the architecture could lose
something it cannot recover — so the guarantees here are about the reduction
being *safe*, not about the number being *right*.

*Permanent architectural principle, ratified 2026-07-29:*

> Buying scores **prioritize commercial attention**. They do not predict
> purchasing behaviour. They do not estimate probability. They do not
> resolve contradiction. They summarize *explainable* commercial attention.

Four guarantees carry it:

* **A score reproduces from its own ledger** — no clock, no configuration,
  integer arithmetic end to end. An explanation that only approximately
  reproduces its number is not an explanation.
* **Contradiction is prioritized, never netted.** Opposing readings both add
  attention; a fought-over account must never score like an inert one.
* **A business event is counted once**, so the same grounds read two ways
  cannot inflate a score.
* **A score is never the canonical representation of an account.** No
  account attributes on the table, no account surface on the read port.

The rest protect immutability, tenancy, and the customer-authored weighting.
"""

from __future__ import annotations

import ast
import inspect
from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from modules.buying_score_engine.application.queries import BuyingScoreQueries
from modules.buying_score_engine.domain import ledger as ledger_module
from modules.buying_score_engine.domain import scoring as scoring_module
from modules.buying_score_engine.domain.ledger import (
    Contribution,
    ContributionLedger,
    LedgerError,
)
from modules.buying_score_engine.domain.score import (
    BuyingScore,
    BuyingScoreError,
    ScoreTrigger,
    Trend,
)
from modules.buying_score_engine.domain.scoring_model import PERCENT, Posture
from modules.buying_score_engine.domain.workspace_model import (
    ScoringOverrides,
    WorkspaceScoringModel,
    resolve_model,
)
from modules.buying_score_engine.infrastructure.model_loader import load_scoring_model
from modules.signal_engine.infrastructure.catalog_loader import load_catalog
from modules.signal_engine.public import Relevance, SignalType

NOW = datetime(2026, 3, 1, tzinfo=UTC)

#: Column names that would make a score an account record rather than a
#: projection over signals.
ACCOUNT_LIKE = (
    "name",
    "domain",
    "website",
    "industry",
    "employee",
    "revenue",
    "country",
    "region",
    "address",
    "description",
)

#: Words that would make a score a forecast. It is not one, and a field
#: implying otherwise would be believed.
PREDICTION_LIKE = ("probability", "likelihood", "forecast", "prediction", "chance", "odds")

#: The only numbers scoring code may compare against. Zero and one are
#: structural — *nothing* and *something*; anything else is a commercial
#: judgement that belongs in the scoring model artifact.
STRUCTURAL_NUMBERS = (0, 1)


def _is_business_number(value: object) -> bool:
    return isinstance(value, int | float) and not isinstance(value, bool) and (
        value not in STRUCTURAL_NUMBERS
    )


def _entry(
    *,
    points: int,
    posture: Posture = Posture.EXPANSIONARY,
    counted: bool = True,
    event_id: UUID | None = None,
) -> Contribution:
    return Contribution(
        business_event_id=event_id or uuid4(),
        signal_id=uuid4(),
        signal_type=SignalType.EXPANSION_OPPORTUNITY,
        posture=posture,
        relevance=Relevance.PRIMARY,
        base_weight=points,
        relevance_multiplier=PERCENT,
        age_band="fresh",
        age_multiplier=PERCENT,
        contribution=points if counted else 0,
        counted=counted,
        reason="stated so a customer can challenge it",
        band_started_at=NOW,
        band_ends_at=NOW + timedelta(days=30),
    )


class TestTheScoreIsAProjectionNotAReplacement:
    """A buying score may summarize intelligence. It must never replace it."""

    async def test_the_table_holds_no_account_attributes(
        self, admin_session_factory: async_sessionmaker[AsyncSession]
    ) -> None:
        """A row that grew a name or an industry would become a de facto
        account record within a year, and consumers would read it instead of
        the intelligence it summarizes."""
        async with admin_session_factory() as session, session.begin():
            columns = set(
                (
                    await session.execute(
                        text(
                            "SELECT column_name FROM information_schema.columns "
                            "WHERE table_name = 'buying_score'"
                        )
                    )
                )
                .scalars()
                .all()
            )

        offenders = sorted(
            column for column in columns if any(word in column.lower() for word in ACCOUNT_LIKE)
        )
        assert offenders == [], (
            f"buying_score carries {offenders}. An account's truth lives in claims, the "
            "Knowledge Graph, observations and business events — never in a summary of them."
        )

    async def test_the_table_promises_no_prediction(
        self, admin_session_factory: async_sessionmaker[AsyncSession]
    ) -> None:
        async with admin_session_factory() as session, session.begin():
            columns = set(
                (
                    await session.execute(
                        text(
                            "SELECT column_name FROM information_schema.columns "
                            "WHERE table_name = 'buying_score'"
                        )
                    )
                )
                .scalars()
                .all()
            )

        offenders = sorted(
            column for column in columns if any(word in column.lower() for word in PREDICTION_LIKE)
        )
        assert offenders == [], (
            f"buying_score carries {offenders}. A score prioritizes commercial attention; it "
            "does not estimate the probability of a purchase."
        )

    def test_the_read_port_offers_no_account_representation(self) -> None:
        """A port that also served account state would become the place
        consumers get accounts from — at which point the score has quietly
        replaced the pipeline."""
        surface = {name for name in dir(BuyingScoreQueries) if not name.startswith("_")}

        offenders = sorted(
            name
            for name in surface
            if any(word in name.lower() for word in ("entity", "account", "company", "top", "rank"))
        )
        assert offenders == [], f"the read port exposes {offenders}"

    def test_a_score_cannot_be_built_without_its_ledger(self) -> None:
        """`projected_from` is the only constructor, and it takes the ledger
        first. Read the dependency as ledger → score."""
        signature = inspect.signature(BuyingScore.projected_from)

        assert list(signature.parameters)[0] == "ledger"


class TestTheScoreReproducesFromItsLedger:
    def test_a_score_disagreeing_with_its_ledger_is_refused(self) -> None:
        """**A corrupt explanation, not a discrepancy to reconcile later.**"""
        ledger = ContributionLedger(entries=(_entry(points=30),), ceiling=120)

        with pytest.raises(BuyingScoreError, match="corrupt explanation"):
            BuyingScore(
                id=uuid4(),
                workspace_id=uuid4(),
                entity_id=uuid4(),
                value=ledger.value() + 1,
                trend=Trend.STEADY,
                delta=0,
                ledger=ledger,
                contested=False,
                dissenting_signal_ids=(),
                computed_at=NOW,
                valid_until=None,
                basis_at=NOW,
                trigger=ScoreTrigger.SIGNAL_GENERATED,
                scoring_model_version=0,
                model_artifact_version=1,
                profile_version=0,
            )

    def test_reproduction_needs_no_clock_and_no_configuration(self) -> None:
        ledger = ContributionLedger(
            entries=(_entry(points=30), _entry(points=25)), ceiling=120
        )
        signature = inspect.signature(ContributionLedger.value)

        assert list(signature.parameters) == ["self"]
        assert ledger.value() == ledger.value()

    def test_the_arithmetic_is_integral_end_to_end(self) -> None:
        """Float accumulation would make the one artifact whose job is to be
        checkable only approximately checkable."""
        source = ast.parse(inspect.getsource(ledger_module))
        divisions = [
            ast.unparse(node)
            for node in ast.walk(source)
            if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Div)
        ]

        assert divisions == [], (
            f"true division in ledger arithmetic: {divisions}. A stored score must reproduce "
            "exactly, and floating point cannot promise that."
        )

    def test_the_ledger_carries_the_ceiling_it_normalized_against(self) -> None:
        """A historical score explained through today's ceiling would be a
        different number wearing the same label."""
        annotations = inspect.get_annotations(ContributionLedger, eval_str=True)

        assert "ceiling" in annotations


class TestContradictionIsPrioritizedNotResolved:
    """The decision the whole module turns on."""

    def test_a_contested_account_outscores_an_inert_one(self) -> None:
        """Netting would make the two most different accounts in the book
        score identically."""
        contested = ContributionLedger(
            entries=(
                _entry(points=30, posture=Posture.EXPANSIONARY),
                _entry(points=25, posture=Posture.CONTRACTIONARY),
            ),
            ceiling=120,
        )
        inert = ContributionLedger(entries=(), ceiling=120)

        assert contested.value() > inert.value()
        assert contested.total() == 55, "opposing readings must not cancel"

    def test_attention_can_never_be_negative(self) -> None:
        """A minus sign is the netting this module refuses, made
        unrepresentable rather than merely discouraged."""
        with pytest.raises(LedgerError, match="Attention is unsigned"):
            _entry(points=-25)

    def test_contradiction_is_named_rather_than_counted(self) -> None:
        ledger = ContributionLedger(
            entries=(
                _entry(points=40, posture=Posture.EXPANSIONARY),
                _entry(points=15, posture=Posture.CONTRACTIONARY),
            ),
            ceiling=120,
        )

        assert ledger.is_contested
        assert len(ledger.dissent()) == 1

    async def test_the_database_refuses_a_contested_score_with_no_dissent(
        self, admin_session_factory: async_sessionmaker[AsyncSession]
    ) -> None:
        """A consumer told *"contested"* without being told *by what* learns
        that something disagrees while being denied the means to look."""
        async with admin_session_factory() as session, session.begin():
            definition = (
                await session.execute(
                    text(
                        "SELECT pg_get_constraintdef(oid) FROM pg_constraint "
                        "WHERE conname = 'ck_buying_score_dissent_is_named'"
                    )
                )
            ).scalar_one_or_none()

        assert definition is not None

    def test_posture_never_becomes_a_sign_in_scoring_code(self) -> None:
        """Read as a syntax tree: posture may be carried and compared, but
        never negated into the arithmetic."""
        source = ast.parse(inspect.getsource(scoring_module))
        negations = [
            ast.unparse(node)
            for node in ast.walk(source)
            if isinstance(node, ast.UnaryOp)
            and isinstance(node.op, ast.USub)
            and "posture" in ast.unparse(node).lower()
        ]

        assert negations == [], f"posture is being negated into the score: {negations}"


class TestEvidenceIsCountedOnce:
    def test_one_business_event_cannot_be_counted_twice(self) -> None:
        """Structural, not a deduplication pass: the same grounds read two
        ways are one set of grounds."""
        shared = uuid4()

        with pytest.raises(LedgerError, match="counted twice"):
            ContributionLedger(
                entries=(
                    _entry(points=30, event_id=shared),
                    _entry(points=25, event_id=shared),
                ),
                ceiling=120,
            )

    def test_an_uncounted_entry_carrying_points_is_refused(self) -> None:
        with pytest.raises(LedgerError, match="not counted but carries"):
            Contribution(
                business_event_id=uuid4(),
                signal_id=uuid4(),
                signal_type=SignalType.EXPANSION_OPPORTUNITY,
                posture=Posture.EXPANSIONARY,
                relevance=Relevance.PRIMARY,
                base_weight=30,
                relevance_multiplier=PERCENT,
                age_band="fresh",
                age_multiplier=PERCENT,
                contribution=30,
                counted=False,
                reason="an explanation that disagrees with its own arithmetic",
                band_started_at=NOW,
                band_ends_at=NOW,
            )

    def test_every_contribution_states_a_reason(self) -> None:
        """A number a customer cannot challenge is exactly the opaque score
        this module exists to avoid."""
        with pytest.raises(LedgerError, match="no reason"):
            Contribution(
                business_event_id=uuid4(),
                signal_id=uuid4(),
                signal_type=SignalType.EXPANSION_OPPORTUNITY,
                posture=Posture.EXPANSIONARY,
                relevance=Relevance.PRIMARY,
                base_weight=30,
                relevance_multiplier=PERCENT,
                age_band="fresh",
                age_multiplier=PERCENT,
                contribution=30,
                counted=True,
                reason="   ",
                band_started_at=NOW,
                band_ends_at=NOW,
            )


class TestNoUndeclaredConstant:
    def test_no_scoring_rule_compares_against_a_business_constant(self) -> None:
        """Weights, multipliers, band boundaries and the ceiling are declared
        in the scoring model artifact, where they are versioned and
        reviewable. Read as a syntax tree so the prose saying so cannot be
        mistaken for one."""
        source = ast.parse(inspect.getsource(scoring_module))

        offenders = [
            ast.unparse(node)
            for node in ast.walk(source)
            if isinstance(node, ast.Compare)
            for comparator in node.comparators
            if isinstance(comparator, ast.Constant) and _is_business_number(comparator.value)
        ]
        assert offenders == [], (
            f"scoring compares against a constant: {offenders}. Every commercial number lives "
            "in the model artifact."
        )

    def test_decay_reuses_the_catalogs_own_relevance_window(self) -> None:
        """Band boundaries are fractions of each type's declared window, so a
        second judgement about how long a hypothesis stays current never
        grows up beside the first."""
        model = load_scoring_model()

        assert all(0 < band.through_percent <= PERCENT for band in model.age_bands)
        assert model.age_bands[-1].through_percent == PERCENT

    def test_the_shipped_model_weighs_exactly_the_catalogs_vocabulary(self) -> None:
        """A signal type nobody weighted contributes nothing, and reads as an
        account where nothing has happened."""
        catalog = load_catalog()

        load_scoring_model().validate_covers(frozenset(d.key for d in catalog.types))


class TestPostureBelongsToSignora:
    def test_a_workspace_cannot_invert_what_a_signal_type_means(self) -> None:
        """Weights are a commercial judgement and the customer's. Whether
        `CONTRACTION_RISK` reads as contractionary is a fact about the
        language — a workspace flipping it would make `contested`
        incomparable across every customer."""
        artifact = load_scoring_model()
        stored = WorkspaceScoringModel(
            id=uuid4(),
            workspace_id=uuid4(),
            version=1,
            overrides=ScoringOverrides(base_weights={SignalType.CONTRACTION_RISK: 99}),
            created_at=NOW,
            created_by=uuid4(),
        )

        resolved = resolve_model(artifact, stored)

        assert resolved.weight_for(SignalType.CONTRACTION_RISK).posture is Posture.CONTRACTIONARY

    def test_overrides_have_no_posture_field_at_all(self) -> None:
        """Unrepresentable rather than validated away."""
        annotations = inspect.get_annotations(ScoringOverrides, eval_str=True)

        assert "posture" not in annotations

    async def test_the_customer_table_has_no_posture_column(
        self, admin_session_factory: async_sessionmaker[AsyncSession]
    ) -> None:
        async with admin_session_factory() as session, session.begin():
            columns = set(
                (
                    await session.execute(
                        text(
                            "SELECT column_name FROM information_schema.columns "
                            "WHERE table_name = 'workspace_scoring_model'"
                        )
                    )
                )
                .scalars()
                .all()
            )

        assert "posture" not in columns


class TestImmutabilityAndValidity:
    @pytest.mark.parametrize("table", ["buying_score", "workspace_scoring_model"])
    async def test_the_application_role_cannot_update(
        self, table: str, admin_session_factory: async_sessionmaker[AsyncSession]
    ) -> None:
        """Immutability is enforced by the absent grant, not by convention.
        A recomputation is a new row naming the one it replaces — which is
        what makes `trend` a fact about history rather than a guess."""
        async with admin_session_factory() as session, session.begin():
            granted = (
                await session.execute(
                    text(
                        "SELECT privilege_type FROM information_schema.role_table_grants "
                        "WHERE grantee = 'signora_app' AND table_name = :t"
                    ),
                    {"t": table},
                )
            ).scalars()
            privileges = set(granted)

        assert "UPDATE" not in privileges
        assert {"SELECT", "INSERT"} <= privileges

    def test_the_repository_offers_no_update_method(self) -> None:
        from modules.buying_score_engine.application.ports import BuyingScoreRepository

        assert not [
            name for name in dir(BuyingScoreRepository) if "update" in name or "edit" in name
        ]

    async def test_a_score_cannot_expire_before_it_was_computed(
        self, admin_session_factory: async_sessionmaker[AsyncSession]
    ) -> None:
        """A stated validity period that never held is worse than none."""
        async with admin_session_factory() as session, session.begin():
            definition = (
                await session.execute(
                    text(
                        "SELECT pg_get_constraintdef(oid) FROM pg_constraint "
                        "WHERE conname = 'ck_buying_score_validity_ordered'"
                    )
                )
            ).scalar_one_or_none()

        assert definition is not None

    async def test_a_score_stays_inside_its_declared_scale(
        self, admin_session_factory: async_sessionmaker[AsyncSession]
    ) -> None:
        async with admin_session_factory() as session, session.begin():
            definition = (
                await session.execute(
                    text(
                        "SELECT pg_get_constraintdef(oid) FROM pg_constraint "
                        "WHERE conname = 'ck_buying_score_range'"
                    )
                )
            ).scalar_one_or_none()

        assert definition is not None

    def test_supersession_points_backwards(self) -> None:
        """Forced by immutability: a forward pointer would have to be written
        onto the older row, which needs the UPDATE grant the table
        deliberately withholds."""
        annotations = inspect.get_annotations(BuyingScore, eval_str=True)

        assert "supersedes" in annotations
        assert "superseded_by" not in annotations


class TestTenancy:
    @pytest.mark.parametrize("table", ["buying_score", "workspace_scoring_model"])
    async def test_row_level_security_is_enabled_and_forced(
        self, table: str, admin_session_factory: async_sessionmaker[AsyncSession]
    ) -> None:
        async with admin_session_factory() as session, session.begin():
            row = (
                await session.execute(
                    text(
                        "SELECT relrowsecurity, relforcerowsecurity FROM pg_class "
                        "WHERE relname = :t"
                    ),
                    {"t": table},
                )
            ).one()

        assert row.relrowsecurity, f"{table} does not have RLS enabled"
        assert row.relforcerowsecurity, f"{table} does not force RLS on its owner"

    def test_the_sweep_is_workspace_scoped(self) -> None:
        """A cross-tenant sweep cannot be served under forced RLS without a
        role that bypasses it, and no such role may exist. Choosing which
        workspaces to sweep is the scheduler's job."""
        from modules.buying_score_engine.application.sweep import SweepStaleScores

        assert "workspace_id" in inspect.signature(SweepStaleScores.execute).parameters
