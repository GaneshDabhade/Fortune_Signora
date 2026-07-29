"""Permanent guarantees the Knowledge Graph rests on.

These state architectural properties, not feature behaviour. Each one, if
it stopped holding, would break something no test of a feature would
notice — and would do so silently, which is the whole reason they live
here.

Two of them are about what the graph must *never* become:

* **The graph resolves identity, not truth.** The moment an entity carries
  an attribute value, disagreement between providers dies at the earliest
  possible moment and every downstream module inherits a single number
  nobody can justify.
* **`MatchStrength` is a semantic category, never a score.** A number
  invites weighting; weighting invites thresholds; thresholds are the
  hidden heuristic that deterministic identity resolution exists to avoid.
"""

from __future__ import annotations

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from modules.knowledge_graph.domain.identity import (
    RULE_PRECEDENCE,
    RULE_STRENGTH,
    MatchStrength,
    ResolutionRule,
)

GRAPH_TABLES = ("entity", "identity_binding", "resolution_decision", "relationship")

#: Column names that would mean a score had entered the graph. Checked by
#: substring, because the drift arrives as `match_score` or `confidence_pct`
#: rather than as anything named exactly `score`.
SCORE_LIKE = ("score", "weight", "confidence", "probability", "rank")


class TestTheGraphStoresNoTruth:
    """AC-28, asserted structurally rather than trusted."""

    async def test_the_entity_table_holds_identity_only(
        self, admin_session_factory: async_sessionmaker[AsyncSession]
    ) -> None:
        """An entity is an identity, not a record.

        A `name` or `employee_count` column here would be the collapse the
        architecture rejects: it would immediately disagree with the claims
        underneath it, and within a year every consumer would read the
        column instead of the evidence.
        """
        async with admin_session_factory() as session, session.begin():
            columns = set(
                (
                    await session.execute(
                        text(
                            "SELECT column_name FROM information_schema.columns "
                            "WHERE table_name = 'entity'"
                        )
                    )
                )
                .scalars()
                .all()
            )

        assert columns == {
            "id",
            "kind",
            "workspace_id",
            "created_at",
            "updated_at",
            "created_by",
            "updated_by",
        }, (
            "the entity table has acquired a column beyond identity. The Knowledge Graph "
            "resolves identity, not truth (ratified 2026-07-28) — attribute values live in "
            "claims, and a column here starts resolving them."
        )

    @pytest.mark.parametrize("table", GRAPH_TABLES)
    async def test_no_graph_table_holds_a_score(
        self, admin_session_factory: async_sessionmaker[AsyncSession], table: str
    ) -> None:
        """`MatchStrength` must never become a number, and a numeric column
        is how it would.

        Storing a strength as a score would make it comparable, summable,
        and thresholdable — and the first weighted comparison is the end of
        deterministic resolution.
        """
        async with admin_session_factory() as session, session.begin():
            columns = (
                (
                    await session.execute(
                        text(
                            "SELECT column_name, data_type FROM information_schema.columns "
                            "WHERE table_name = :table"
                        ),
                        {"table": table},
                    )
                )
                .mappings()
                .all()
            )

        offenders = [
            column["column_name"]
            for column in columns
            if any(word in column["column_name"].lower() for word in SCORE_LIKE)
        ]
        assert offenders == [], (
            f"{table} carries {offenders}. Identity resolution is deterministic: strength is a "
            "declared property of a rule, never a computed number."
        )


class TestMatchStrengthIsNotANumber:
    """**Permanent invariant, ratified 2026-07-29.**

    `MatchStrength` exists only to describe the quality of the matching
    rule. It must never become a numeric score, participate in a weighted
    calculation, or underpin heuristic resolution. A future engineer must
    not be able to convert it into probabilistic scoring by accident.
    """

    def test_it_refuses_numeric_conversion(self) -> None:
        for strength in MatchStrength:
            with pytest.raises(TypeError):
                int(strength)
            with pytest.raises(TypeError):
                float(strength)

    def test_it_refuses_to_be_ordered(self) -> None:
        """Ordering is the door weighting comes through: once strengths
        sort, someone sums them."""
        with pytest.raises(TypeError):
            _ = MatchStrength.CERTAIN < MatchStrength.STRONG
        with pytest.raises(TypeError):
            _ = sorted(MatchStrength)

    def test_every_declared_strength_is_a_word(self) -> None:
        for strength in MatchStrength:
            assert not strength.value.replace(".", "").isdigit()

    def test_strength_is_declared_per_rule_not_computed(self) -> None:
        """A strength that were a function of anything but the rule would
        be a computed belief, and a computed belief invites tuning."""
        for rule in ResolutionRule:
            assert isinstance(RULE_STRENGTH[rule], MatchStrength)

    def test_every_rule_has_exactly_one_place_in_precedence(self) -> None:
        """Precedence, not weight, is how rules are compared. A rule
        missing from the order would be silently unreachable; a duplicate
        would make resolution depend on iteration order."""
        assert sorted(RULE_PRECEDENCE, key=lambda r: r.value) == sorted(
            ResolutionRule, key=lambda r: r.value
        )
        assert len(RULE_PRECEDENCE) == len(set(RULE_PRECEDENCE))


class TestAmbiguityMergesNothing:
    """AC-29, enforced by the database rather than by the use case that
    happens to write the row.

    An under-merge is a visible duplicate somebody reports. An over-merge
    silently mixes two customers' intelligence and looks perfectly clean
    while doing it, so the guarantee belongs where no code path can miss
    it.
    """

    async def test_an_ambiguous_binding_cannot_name_an_entity(
        self, admin_session_factory: async_sessionmaker[AsyncSession]
    ) -> None:
        async with admin_session_factory() as session, session.begin():
            definition = (
                await session.execute(
                    text(
                        "SELECT pg_get_constraintdef(oid) FROM pg_constraint "
                        "WHERE conname = 'ck_identity_binding_ambiguous_binds_nothing'"
                    )
                )
            ).scalar_one_or_none()

        assert definition is not None, (
            "the constraint forbidding an ambiguous binding from naming an entity is gone. "
            "Ambiguity must merge nothing — a wrong merge is invisible and corrupts every "
            "downstream signal."
        )
        assert "ambiguous" in definition


class TestTheEvidenceChainIsUnbroken:
    """raw record → claim → decision → entity. No link may be weakened.

    Traversal must work in both directions: *"why do we believe this?"* is
    the export an enterprise customer asks for, and *"what depended on
    this?"* is what makes a corrected mapper's blast radius knowable.
    """

    async def test_every_binding_references_a_decision(
        self, admin_session_factory: async_sessionmaker[AsyncSession]
    ) -> None:
        """A binding with no decision behind it is a merge nobody can
        explain, review, or revise."""
        async with admin_session_factory() as session, session.begin():
            nullable = (
                await session.execute(
                    text(
                        "SELECT is_nullable FROM information_schema.columns "
                        "WHERE table_name = 'identity_binding' AND column_name = 'decision_id'"
                    )
                )
            ).scalar_one()

        assert nullable == "NO"

    async def test_a_decision_supersedes_backwards(
        self, admin_session_factory: async_sessionmaker[AsyncSession]
    ) -> None:
        """Immutability and supersession are only compatible one way.

        A forward `superseded_by` would have to be written onto the older
        row, which needs an UPDATE grant `resolution_decision` deliberately
        does not have. A backward pointer keeps both properties true at
        once — and if this column ever flips direction, immutability has
        quietly been given up.
        """
        async with admin_session_factory() as session, session.begin():
            columns = set(
                (
                    await session.execute(
                        text(
                            "SELECT column_name FROM information_schema.columns "
                            "WHERE table_name = 'resolution_decision'"
                        )
                    )
                )
                .scalars()
                .all()
            )

        assert "supersedes" in columns
        assert "superseded_by" not in columns, (
            "resolution_decision has gained a forward supersession pointer, which cannot be "
            "written without an UPDATE grant. Either the column is unused or immutability "
            "has been given up."
        )
