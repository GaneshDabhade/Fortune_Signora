"""Permanent guarantees the Signal Engine rests on.

**Signals are the first subjective layer in the pipeline.** Everything
above is globally true; everything below must remain traceable back to
globally true information. That subjectivity has to stay explicit,
explainable, and constrained — and these are the constraints.

Three protect the boundary:

* **No commercial scoring.** The module answers *"why might this matter to
  this customer?"*, never how likely a purchase is or which account to
  prioritise. There is no score, priority, likelihood, or rank anywhere.
* **The vocabulary stays global.** A workspace configures relevance over
  Signora's catalog and can never invent a type — the constraint that makes
  AI prompting, benchmarking, analytics, and support possible at all.
* **No threshold lives in code.** Windows and contributor counts come from
  the catalog or the profile, asserted by a syntax-tree invariant.

The rest protect the evidence chain and the customer-authored data.
"""

from __future__ import annotations

import ast
import inspect

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from modules.signal_engine.domain import rules
from modules.signal_engine.domain.catalog import Relevance, SignalType
from modules.signal_engine.infrastructure.catalog_loader import load_catalog

#: Column names that would mean propensity had entered the module.
SCORING_LIKE = (
    "score",
    "priority",
    "likelihood",
    "propensity",
    "rank",
    "weight",
    "confidence",
    "importance",
)

#: The only numbers a strategy may compare against. Zero and one are
#: structural — *nothing* and *something*; anything else is a business
#: judgement that belongs in the catalog or the profile.
STRUCTURAL_NUMBERS = (0, 1)

#: Vocabulary a customer should never need to know to read a hypothesis.
INTERNAL_VOCABULARY = (
    "apollo",
    "builtwith",
    "crunchbase",
    "coresignal",
    "bombora",
    "provider",
    "claim",
    "observation",
    "entity",
    "workspace_id",
    "payload",
)


class TestNoCommercialScoring:
    """The module answers exactly one question."""

    async def test_the_signal_table_holds_no_scoring(
        self, admin_session_factory: async_sessionmaker[AsyncSession]
    ) -> None:
        async with admin_session_factory() as session, session.begin():
            columns = set(
                (
                    await session.execute(
                        text(
                            "SELECT column_name FROM information_schema.columns "
                            "WHERE table_name = 'signal'"
                        )
                    )
                )
                .scalars()
                .all()
            )

        offenders = sorted(
            column for column in columns if any(word in column.lower() for word in SCORING_LIKE)
        )
        assert offenders == [], (
            f"signal carries {offenders}. How likely a purchase is, which account to prioritise, "
            "and what to recommend belong to the Buying Score Engine and everything after it."
        )

    def test_relevance_is_a_category_with_no_numeric_meaning(self) -> None:
        """A number invites weighting, weighting invites thresholds, and a
        threshold here would be a propensity judgement in the wrong
        module."""
        for relevance in Relevance:
            assert not relevance.value.replace(".", "").isdigit()

    def test_no_strategy_compares_against_a_business_constant(self) -> None:
        """Read as a syntax tree, so the prose explaining that thresholds
        live in the catalog cannot be mistaken for one."""
        tree = ast.parse(inspect.getsource(rules))

        offenders = [
            ast.unparse(node)
            for node in ast.walk(tree)
            if isinstance(node, ast.Compare)
            for comparator in node.comparators
            if isinstance(comparator, ast.Constant) and _is_business_number(comparator.value)
        ]
        assert offenders == [], (
            f"a detection strategy compares against a constant: {offenders}. Windows and "
            "contributor counts are declared in the catalog or the workspace profile."
        )


class TestTheVocabularyStaysGlobal:
    """A per-workspace type vocabulary would mean AI Reasoning could not be
    prompted about a signal, benchmarks could not compare customers, and
    support could not answer a question without first learning that
    customer's private dialect."""

    def test_the_profile_can_only_reference_catalog_types(self) -> None:
        """Structural: a profile entry is typed as a `SignalType`, so an
        invented type is unrepresentable rather than merely discouraged."""
        from modules.signal_engine.domain.profile import ProfileEntry

        annotations = inspect.get_annotations(ProfileEntry, eval_str=True)

        assert annotations["signal_type"] is SignalType

    @pytest.mark.parametrize("type_key", list(SignalType))
    def test_every_type_in_the_enum_is_declared_in_the_catalog(self, type_key: SignalType) -> None:
        assert load_catalog().definition(type_key)

    def test_every_declared_type_is_fully_described(self) -> None:
        for definition in load_catalog().types:
            assert definition.title.strip()
            assert definition.hypothesis.strip()
            assert definition.why_it_matters.strip()

    @pytest.mark.parametrize("field", ["key", "title", "hypothesis", "why_it_matters"])
    def test_no_internal_vocabulary_reaches_the_customer(self, field: str) -> None:
        offenders = [
            (definition.key.value, word)
            for definition in load_catalog().types
            for word in INTERNAL_VOCABULARY
            if word in str(getattr(definition, field)).lower()
        ]
        assert offenders == [], (
            f"{offenders} leaks vocabulary a customer should never need to know."
        )

    def test_every_hypothesis_is_phrased_as_a_possibility(self) -> None:
        """A signal proposes; it does not assert. A type whose hypothesis
        reads as a fact has drifted into the Business Event Engine's
        territory."""
        hedges = ("may", "might", "suggests", "could", "can")
        certain = [
            definition.key.value
            for definition in load_catalog().types
            if not any(word in definition.hypothesis.lower() for word in hedges)
        ]
        assert certain == [], (
            f"{certain} state their hypothesis as fact. Business events describe reality; "
            "signals describe potential commercial meaning, and the language must show it."
        )


class TestTheEvidenceChainIsUnbroken:
    async def test_a_signal_cannot_exist_without_citing_business_events(
        self, admin_session_factory: async_sessionmaker[AsyncSession]
    ) -> None:
        """Everything below the Signal Engine must remain traceable back to
        globally true information."""
        async with admin_session_factory() as session, session.begin():
            definition = (
                await session.execute(
                    text(
                        "SELECT pg_get_constraintdef(oid) FROM pg_constraint "
                        "WHERE conname = 'ck_signal_cites_business_events'"
                    )
                )
            ).scalar_one_or_none()

        assert definition is not None

    async def test_an_ignored_hypothesis_cannot_be_stored(
        self, admin_session_factory: async_sessionmaker[AsyncSession]
    ) -> None:
        """`IGNORED` means the hypothesis is not held here at all, not that
        it is held weakly."""
        async with admin_session_factory() as session, session.begin():
            definition = (
                await session.execute(
                    text(
                        "SELECT pg_get_constraintdef(oid) FROM pg_constraint "
                        "WHERE conname = 'ck_signal_relevance_is_held'"
                    )
                )
            ).scalar_one_or_none()

        assert definition is not None
        assert "ignored" in definition

    async def test_both_versions_are_recorded(
        self, admin_session_factory: async_sessionmaker[AsyncSession]
    ) -> None:
        """*Why does this exist* has two halves: Signora's catalog and the
        customer's profile. A historical signal missing either is
        unexplainable."""
        async with admin_session_factory() as session, session.begin():
            columns = set(
                (
                    await session.execute(
                        text(
                            "SELECT column_name FROM information_schema.columns "
                            "WHERE table_name = 'signal'"
                        )
                    )
                )
                .scalars()
                .all()
            )

        assert {"catalog_version", "profile_version"} <= columns

    async def test_a_signal_supersedes_backwards(
        self, admin_session_factory: async_sessionmaker[AsyncSession]
    ) -> None:
        async with admin_session_factory() as session, session.begin():
            columns = set(
                (
                    await session.execute(
                        text(
                            "SELECT column_name FROM information_schema.columns "
                            "WHERE table_name = 'signal'"
                        )
                    )
                )
                .scalars()
                .all()
            )

        assert "supersedes" in columns
        assert "superseded_by" not in columns


class TestCustomerAuthoredConfiguration:
    """`signal_profile` is the first thing in the platform that cannot be
    regenerated from anything. It is a statement a customer makes about
    their own business, and it needs the rigour that implies."""

    async def test_a_workspace_has_at_most_one_current_profile(
        self, admin_session_factory: async_sessionmaker[AsyncSession]
    ) -> None:
        """Two live interpretations with no way to say which applied would
        make every signal generated during the overlap unexplainable."""
        async with admin_session_factory() as session, session.begin():
            index = (
                await session.execute(
                    text(
                        "SELECT indexdef FROM pg_indexes "
                        "WHERE indexname = 'uq_signal_profile_current'"
                    )
                )
            ).scalar_one_or_none()

        assert index is not None
        assert "UNIQUE" in index
        assert "supersedes IS NULL" in index

    async def test_every_profile_version_records_who_authored_it(
        self, admin_session_factory: async_sessionmaker[AsyncSession]
    ) -> None:
        """A profile change is a commercial decision, and a customer should
        be able to see who made it and when."""
        async with admin_session_factory() as session, session.begin():
            nullable = (
                await session.execute(
                    text(
                        "SELECT is_nullable FROM information_schema.columns "
                        "WHERE table_name = 'signal_profile' AND column_name = 'created_by'"
                    )
                )
            ).scalar_one()

        assert nullable == "NO"

    async def test_profile_versions_are_unique_per_workspace(
        self, admin_session_factory: async_sessionmaker[AsyncSession]
    ) -> None:
        """A signal names a version; two profiles sharing one would make the
        reference ambiguous."""
        async with admin_session_factory() as session, session.begin():
            found = (
                await session.execute(
                    text(
                        "SELECT count(*) FROM pg_constraint "
                        "WHERE conname = 'uq_signal_profile_version'"
                    )
                )
            ).scalar_one()

        assert found == 1


def _is_business_number(value: object) -> bool:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return False
    return value not in STRUCTURAL_NUMBERS
