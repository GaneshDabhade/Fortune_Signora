"""Permanent guarantees the Business Event Engine rests on.

Two protect the boundary the module was built to hold:

* **It answers "why is this business-relevant?" — nothing more.** How
  important the account is, whether Sales should engage, what priority this
  deserves, and how likely a purchase is belong downstream. A business
  event carries no priority, score, urgency, or rank.
* **Every business threshold lives in the taxonomy.** The split between
  language and derivation is worthless if it is only a convention, so rule
  modules are parsed as syntax trees and a numeric literal in a comparison
  fails the build.

The rest protect the vocabulary itself, which is now a product asset: the
taxonomy is the language the product, analytics, AI reasoning,
recommendations, and customer interfaces all speak.
"""

from __future__ import annotations

import ast
import inspect
from types import ModuleType

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from modules.business_event_engine.domain.rules import RULES, point, window
from modules.business_event_engine.domain.taxonomy import BusinessEventType
from modules.business_event_engine.infrastructure.taxonomy_loader import load_taxonomy

RULE_MODULES: tuple[ModuleType, ...] = (point, window)

#: Column names that would mean commercial judgement had entered the module.
#: Checked by substring, because the drift arrives as `engagement_priority`
#: or `is_hot` rather than as anything named exactly `priority`.
JUDGEMENT_LIKE = (
    "priority",
    "score",
    "urgency",
    "rank",
    "importance",
    "likelihood",
    "propensity",
    "confidence",
)

#: The only numbers a rule may compare against. Zero and one are structural
#: — *nothing* and *something* — while any other number is a claim about the
#: world that somebody must be able to argue with.
STRUCTURAL_NUMBERS = (0, 1)

#: Terms that exist only to describe Signora's data model. A business
#: domain naming one has stopped describing the customer's business.
DATA_MODEL_TERMS = frozenset({"firmographic", "technographic", "behavioural", "behavioral"})

#: Vocabulary a customer should never need to know in order to read what
#: happened to their account.
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
    "workspace",
    "attribute",
    "payload",
)


class TestNoThresholdLivesInCode:
    """**Taxonomy defines language; rules define derivation.**

    A threshold in rule code is unversioned, unreviewable, and invisible in
    the evidence chain. A seller asking *"why was I told this?"* would get
    an answer that bottoms out in a constant.
    """

    @pytest.mark.parametrize("module", RULE_MODULES, ids=lambda m: m.__name__.rsplit(".", 1)[-1])
    def test_no_rule_compares_against_a_business_constant(self, module: ModuleType) -> None:
        """Read as a syntax tree rather than as text, so the prose
        *explaining* that thresholds live in the taxonomy cannot be mistaken
        for one."""
        tree = ast.parse(inspect.getsource(module))

        offenders = [
            ast.unparse(node)
            for node in ast.walk(tree)
            if isinstance(node, ast.Compare)
            for comparator in node.comparators
            if isinstance(comparator, ast.Constant) and _is_business_number(comparator.value)
        ]
        assert offenders == [], (
            f"{module.__name__} compares against a constant: {offenders}. Every business "
            "threshold must be declared in the taxonomy, where it can be reviewed, versioned, "
            "and cited in an explanation."
        )

    def test_every_declared_parameter_is_read_by_its_rule(self) -> None:
        """An orphan parameter is a number in the product's language that
        nothing acts on — a promise the taxonomy silently breaks."""
        taxonomy = load_taxonomy()
        source = "\n".join(inspect.getsource(module) for module in RULE_MODULES)

        orphans = [
            f"{definition.key.value}.{name}"
            for definition in taxonomy.types
            for name in definition.parameters
            if f'"{name}"' not in source
        ]
        assert orphans == [], (
            f"declared but never read: {orphans}. A parameter nothing consumes is a threshold "
            "reviewers believe is in force when it is not."
        )

    def test_every_type_has_exactly_one_rule(self) -> None:
        detected = [rule.detects for rule in RULES]

        assert sorted(set(detected), key=lambda t: t.value) == sorted(
            (definition.key for definition in load_taxonomy().types), key=lambda t: t.value
        )
        assert len(detected) == len(set(detected)), "two rules detecting one type is ambiguous"


class TestNoCommercialJudgement:
    """The module answers exactly one question, and the schema is where that
    boundary is easiest to erode."""

    async def test_the_table_holds_no_priority_or_score(
        self, admin_session_factory: async_sessionmaker[AsyncSession]
    ) -> None:
        async with admin_session_factory() as session, session.begin():
            columns = set(
                (
                    await session.execute(
                        text(
                            "SELECT column_name FROM information_schema.columns "
                            "WHERE table_name = 'business_event'"
                        )
                    )
                )
                .scalars()
                .all()
            )

        offenders = sorted(
            column for column in columns if any(word in column.lower() for word in JUDGEMENT_LIKE)
        )
        assert offenders == [], (
            f"business_event carries {offenders}. Whether Sales should engage, how important the "
            "account is, and how likely a purchase is belong to the Signal Engine and everything "
            "after it."
        )

    async def test_every_event_names_the_providers_behind_it(
        self, admin_session_factory: async_sessionmaker[AsyncSession]
    ) -> None:
        """Agreement is evidence. Dropping the providers is how it would
        quietly become a confidence."""
        async with admin_session_factory() as session, session.begin():
            definition = (
                await session.execute(
                    text(
                        "SELECT pg_get_constraintdef(oid) FROM pg_constraint "
                        "WHERE conname = 'ck_business_event_names_a_provider'"
                    )
                )
            ).scalar_one_or_none()

        assert definition is not None


class TestTheVocabularyIsAProductAsset:
    """*If a CRO opened Signora today, would they immediately understand
    what this event means?*"""

    def test_every_type_is_fully_described(self) -> None:
        """`why_it_matters` exists so the taxonomy cannot grow a type nobody
        can justify — if the sentence is hard to write, the type probably
        should not exist."""
        for definition in load_taxonomy().types:
            assert definition.title.strip()
            assert definition.description.strip()
            assert definition.why_it_matters.strip()

    @pytest.mark.parametrize("field", ["key", "title", "description", "why_it_matters"])
    def test_no_internal_vocabulary_reaches_the_customer(self, field: str) -> None:
        offenders = [
            (definition.key.value, word)
            for definition in load_taxonomy().types
            for word in INTERNAL_VOCABULARY
            if word in str(getattr(definition, field)).lower()
        ]
        assert offenders == [], (
            f"{offenders} leaks vocabulary a customer should never need to know. Business events "
            "describe what happened in the customer's business, not how Signora discovered it."
        )

    def test_no_business_domain_uses_data_model_terminology(self) -> None:
        """The claim vocabulary categorises data by where it came from;
        business domains categorise events by what they mean.

        The rule is *not* that the two sets are disjoint — `capital` and
        `workforce` are ordinary business words that happen to be reasonable
        data categories too. It is that the terms which exist only to
        describe a data model never reach a customer.
        """
        business = {definition.domain.value for definition in load_taxonomy().types}

        assert not (business & DATA_MODEL_TERMS), (
            f"{sorted(business & DATA_MODEL_TERMS)} describes where data came from, not what "
            "happened to the business. No CRO has ever asked about a technographic."
        )

    def test_every_type_declares_the_evidence_it_rests_on(self) -> None:
        """Declared so a vocabulary change that orphans a type is visible
        rather than silent."""
        for definition in load_taxonomy().types:
            assert definition.evidence_attributes


class TestDurableBusinessHistory:
    async def test_an_event_cannot_exist_without_citing_evidence(
        self, admin_session_factory: async_sessionmaker[AsyncSession]
    ) -> None:
        async with admin_session_factory() as session, session.begin():
            definition = (
                await session.execute(
                    text(
                        "SELECT pg_get_constraintdef(oid) FROM pg_constraint "
                        "WHERE conname = 'ck_business_event_cites_evidence'"
                    )
                )
            ).scalar_one_or_none()

        assert definition is not None, (
            "the constraint requiring a business event to cite evidence is gone. An event that "
            "cannot be traced back is an assertion, not intelligence."
        )

    async def test_an_event_supersedes_backwards(
        self, admin_session_factory: async_sessionmaker[AsyncSession]
    ) -> None:
        """Immutability and supersession are only compatible one way. If this
        column ever flips direction, durable history has been given up."""
        async with admin_session_factory() as session, session.begin():
            columns = set(
                (
                    await session.execute(
                        text(
                            "SELECT column_name FROM information_schema.columns "
                            "WHERE table_name = 'business_event'"
                        )
                    )
                )
                .scalars()
                .all()
            )

        assert "supersedes" in columns
        assert "superseded_by" not in columns

    async def test_both_version_numbers_are_recorded(
        self, admin_session_factory: async_sessionmaker[AsyncSession]
    ) -> None:
        """Conflating meaning with wire shape means tuning a threshold breaks
        a consumer contract, so nobody ever tunes a threshold."""
        async with admin_session_factory() as session, session.begin():
            columns = set(
                (
                    await session.execute(
                        text(
                            "SELECT column_name FROM information_schema.columns "
                            "WHERE table_name = 'business_event'"
                        )
                    )
                )
                .scalars()
                .all()
            )

        assert {"taxonomy_version", "payload_version"} <= columns


def _is_business_number(value: object) -> bool:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return False
    return value not in STRUCTURAL_NUMBERS


@pytest.mark.parametrize("type_key", list(BusinessEventType))
def test_every_type_in_the_enum_is_declared_in_the_taxonomy(type_key: BusinessEventType) -> None:
    """The enum is the code's view of the language; the artifact is the
    product's. They must not drift."""
    assert load_taxonomy().definition(type_key)
