"""Permanent guarantees the Observation Engine rests on.

Two are about what the module must never become:

* **It detects change; it does not determine significance.** A threshold
  here would be a constant nobody can justify that four modules trust
  within a year. Materiality belongs to the Business Event Engine's
  curated, versioned taxonomy, where a rule can be argued about.
* **Change is never computed across providers.** Apollo reporting 120 on
  Monday and CoreSignal 145 on Tuesday is disagreement. Merging the series
  would manufacture growth that never happened, and correcting for it would
  mean deciding which provider is authoritative — truth resolution.

The rest protect the evidence chain, which every later module's
explainability depends on.
"""

from __future__ import annotations

import ast
import inspect
from types import ModuleType

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from modules.observation_engine.application import record
from modules.observation_engine.domain import derivation
from modules.observation_engine.domain.semantics import ATTRIBUTE_KINDS
from modules.provider_normalization.public import ClaimAttribute

#: Column names that would mean significance had entered the module.
#: Checked by substring, because the drift arrives as `importance_score` or
#: `is_material` rather than as anything named exactly `score`.
SIGNIFICANCE_LIKE = ("score", "weight", "confidence", "importance", "severity", "material")


class TestTheEngineDetectsChangeNotSignificance:
    """**Permanent invariant, ratified 2026-07-29.**

    Claims preserve evidence · the Knowledge Graph resolves identity · the
    Observation Engine detects change · the Business Event Engine determines
    business meaning · the Signal Engine determines commercial meaning.
    """

    async def test_the_observation_table_holds_no_significance(
        self, admin_session_factory: async_sessionmaker[AsyncSession]
    ) -> None:
        async with admin_session_factory() as session, session.begin():
            columns = set(
                (
                    await session.execute(
                        text(
                            "SELECT column_name FROM information_schema.columns "
                            "WHERE table_name = 'observation'"
                        )
                    )
                )
                .scalars()
                .all()
            )

        offenders = sorted(
            column
            for column in columns
            if any(word in column.lower() for word in SIGNIFICANCE_LIKE)
        )
        assert offenders == [], (
            f"observation carries {offenders}. The Observation Engine detects change; whether a "
            "change matters is the Business Event Engine's question, answered against a curated "
            "taxonomy rather than a column."
        )

    @pytest.mark.parametrize("module", [derivation, record], ids=["derivation", "use_case"])
    def test_no_magnitude_is_compared_against_a_constant(self, module: ModuleType) -> None:
        """The failure mode this guards is specific and plausible: someone
        adds `if magnitude < 5: return` to reduce noise, and a constant
        nobody can justify starts filtering the pipeline invisibly.

        Read as a syntax tree rather than as text, so the prose *explaining*
        that there is no threshold cannot be mistaken for one.
        """
        tree = ast.parse(inspect.getsource(module))

        offenders = [
            ast.unparse(node)
            for node in ast.walk(tree)
            if isinstance(node, ast.Compare)
            and _mentions_magnitude(node.left)
            and any(isinstance(c, ast.Constant) and _is_number(c.value) for c in node.comparators)
        ]
        assert offenders == [], (
            f"magnitude is compared against a constant in {module.__name__}: {offenders}. "
            "That is a materiality rule, and it belongs in the Business Event Engine's "
            "versioned taxonomy where it can be reviewed."
        )


def _mentions_magnitude(node: ast.expr) -> bool:
    return any(
        isinstance(inner, ast.Name)
        and "magnitude" in inner.id
        or isinstance(inner, ast.Attribute)
        and "magnitude" in inner.attr
        for inner in ast.walk(node)
    )


def _is_number(value: object) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


class TestChangeIsNeverCrossProvider:
    async def test_every_observation_names_the_provider_that_asserted_it(
        self, admin_session_factory: async_sessionmaker[AsyncSession]
    ) -> None:
        """Dropping the provider is how disagreement becomes phantom change,
        and it is also what would stop AI Reasoning from ever saying
        "sources disagree"."""
        async with admin_session_factory() as session, session.begin():
            nullable = (
                await session.execute(
                    text(
                        "SELECT is_nullable FROM information_schema.columns "
                        "WHERE table_name = 'observation' AND column_name = 'provider'"
                    )
                )
            ).scalar_one()

        assert nullable == "NO"

    def test_derivation_takes_exactly_one_provider(self) -> None:
        """Structural: the signature cannot express a cross-provider series,
        so no caller can construct one by accident."""
        signature = inspect.signature(derivation.derive)

        assert "provider" in signature.parameters
        assert signature.parameters["provider"].annotation == "str", (
            "a collection of providers here would make the phantom-change bug expressible"
        )


class TestTheEvidenceChainIsUnbroken:
    async def test_an_observation_cannot_exist_without_citing_a_claim(
        self, admin_session_factory: async_sessionmaker[AsyncSession]
    ) -> None:
        """AC-32, enforced by the database rather than by the code path that
        happens to write the row."""
        async with admin_session_factory() as session, session.begin():
            definition = (
                await session.execute(
                    text(
                        "SELECT pg_get_constraintdef(oid) FROM pg_constraint "
                        "WHERE conname = 'ck_observation_cites_evidence'"
                    )
                )
            ).scalar_one_or_none()

        assert definition is not None, (
            "the constraint requiring an observation to cite evidence is gone. An observation "
            "nobody can trace looks like knowledge without being it."
        )

    async def test_the_shape_of_an_observation_matches_its_kind(
        self, admin_session_factory: async_sessionmaker[AsyncSession]
    ) -> None:
        """A change must bound the window it occurred within; an occurrence
        has nothing to have moved from. A half-formed observation would let
        a consumer compute a delta against a value nobody observed."""
        async with admin_session_factory() as session, session.begin():
            definition = (
                await session.execute(
                    text(
                        "SELECT pg_get_constraintdef(oid) FROM pg_constraint "
                        "WHERE conname = 'ck_observation_shape_matches_kind'"
                    )
                )
            ).scalar_one_or_none()

        assert definition is not None
        assert "previous_observed_at" in definition

    async def test_an_observation_supersedes_backwards(
        self, admin_session_factory: async_sessionmaker[AsyncSession]
    ) -> None:
        """Immutability and supersession are only compatible one way. If this
        column ever flips direction, immutability has quietly been given up."""
        async with admin_session_factory() as session, session.begin():
            columns = set(
                (
                    await session.execute(
                        text(
                            "SELECT column_name FROM information_schema.columns "
                            "WHERE table_name = 'observation'"
                        )
                    )
                )
                .scalars()
                .all()
            )

        assert "supersedes" in columns
        assert "superseded_by" not in columns


class TestEveryAttributeIsClassified:
    @pytest.mark.parametrize("attribute", list(ClaimAttribute))
    def test_the_vocabulary_is_fully_classified(self, attribute: ClaimAttribute) -> None:
        """A silent default is how a new canonical attribute acquires
        observation behaviour nobody chose. Adding one already requires an
        RFC; classifying it is part of that RFC."""
        assert attribute in ATTRIBUTE_KINDS, (
            f"'{attribute}' has no declared observation semantics. Classify it as STATE or "
            "OCCURRENCE — the choice decides whether it produces transitions or first sightings."
        )
