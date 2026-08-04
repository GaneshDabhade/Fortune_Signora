"""The competitor declaration's own rules, with no database and no HTTP.

**The sixth declaration**, and the first whose whole purpose is a *risk*. These
assert what the module records, what it refuses, and — the part that matters
most for this one — **that it grades nobody.**
"""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID, uuid4

import pytest

from modules.commercial_profile.domain.competitors import (
    MAX_COMPETITORS,
    MAX_NAME,
    Competitor,
    CompetitorsError,
    DeclaredCompetitors,
    first_competitors,
)

WORKSPACE = UUID("11111111-1111-4111-8111-111111111111")
ACTOR = UUID("22222222-2222-4222-8222-222222222222")
NOW = datetime(2026, 8, 4, tzinfo=UTC)


def competitor(name: str) -> Competitor:
    return Competitor(id=uuid4(), name=name)


def declared(*names: str) -> DeclaredCompetitors:
    return first_competitors(
        WORKSPACE,
        tuple(competitor(name) for name in names),
        id=uuid4(),
        by=ACTOR,
        now=NOW,
    )


class TestACompetitor:
    def test_carries_a_name_and_a_stable_id(self) -> None:
        entry = competitor("Salesforce")
        assert entry.name == "Salesforce"

    def test_refuses_a_blank_name(self) -> None:
        with pytest.raises(CompetitorsError, match="needs a name"):
            Competitor(id=uuid4(), name="   ")

    def test_refuses_a_name_past_the_limit(self) -> None:
        with pytest.raises(CompetitorsError, match=str(MAX_NAME)):
            Competitor(id=uuid4(), name="x" * (MAX_NAME + 1))

    def test_holds_nothing_that_grades_it(self) -> None:
        """**The boundary, asserted rather than trusted.**

        `commercial_profile` records and evaluates nobody, and a competitor is
        the field most likely to acquire a weight — it is *about* a threat, so
        a number feels natural. `test_boundary.py` refuses `priority` and
        `rank` repository-wide; this refuses the vocabulary a competitor would
        attract specifically, in the file somebody would add it to.
        """
        forbidden = {"threat", "severity", "level", "score", "weight", "tier", "rank"}
        fields = {field.lower() for field in Competitor.__slots__}
        assert not (fields & forbidden), f"a competitor is being graded: {fields & forbidden}"


class TestTheDeclaration:
    def test_the_first_one_supersedes_nothing(self) -> None:
        assert declared("Salesforce").supersedes is None

    def test_starts_at_version_one(self) -> None:
        assert declared("Salesforce").version == 1

    def test_records_who_said_so_and_when(self) -> None:
        entry = declared("Salesforce")
        assert (entry.created_by, entry.created_at) == (ACTOR, NOW)

    def test_an_empty_declaration_is_legal(self) -> None:
        """*"We do not track competitors"* is a statement, not an absence.

        It has an author and a moment, which is exactly what distinguishes it
        from never having said anything — and a consumer that could not tell
        those apart would report an empty result where the truth is an empty
        input.
        """
        assert declared().competitors == ()

    def test_refuses_a_version_below_one(self) -> None:
        with pytest.raises(CompetitorsError, match="version 1 or above"):
            DeclaredCompetitors(
                id=uuid4(),
                workspace_id=WORKSPACE,
                version=0,
                competitors=(),
                created_at=NOW,
                created_by=ACTOR,
            )

    def test_refuses_a_list_past_the_limit(self) -> None:
        with pytest.raises(CompetitorsError, match="market category"):
            first_competitors(
                WORKSPACE,
                tuple(competitor(f"Rival {n}") for n in range(MAX_COMPETITORS + 1)),
                id=uuid4(),
                by=ACTOR,
                now=NOW,
            )

    def test_refuses_the_same_entry_twice(self) -> None:
        """A duplicate id makes a rename indistinguishable from a removal."""
        entry = competitor("Salesforce")
        with pytest.raises(CompetitorsError, match="listed twice"):
            first_competitors(WORKSPACE, (entry, entry), id=uuid4(), by=ACTOR, now=NOW)

    def test_refuses_two_entries_sharing_a_name(self) -> None:
        with pytest.raises(CompetitorsError, match="share a name"):
            declared("Salesforce", "Salesforce")

    def test_compares_names_case_and_whitespace_insensitively(self) -> None:
        """Nothing here resolves a name, so the only defence is refusing the
        collision at the moment somebody types it."""
        with pytest.raises(CompetitorsError, match="share a name"):
            declared("Salesforce", "  salesforce ")

    def test_two_different_technologies_are_both_kept(self) -> None:
        assert len(declared("Salesforce", "HubSpot").competitors) == 2


class TestRevising:
    def test_names_the_version_it_replaces(self) -> None:
        first = declared("Salesforce")
        second = first.revise((competitor("HubSpot"),), id=uuid4(), by=ACTOR, now=NOW)
        assert second.supersedes == first.id

    def test_increments_the_version(self) -> None:
        first = declared("Salesforce")
        assert first.revise((), id=uuid4(), by=ACTOR, now=NOW).version == 2

    def test_keeps_the_workspace(self) -> None:
        first = declared("Salesforce")
        assert first.revise((), id=uuid4(), by=ACTOR, now=NOW).workspace_id == WORKSPACE

    def test_leaves_the_previous_version_untouched(self) -> None:
        """Immutability is the point: the earlier statement is still what was
        said, and a reader citing version 1 must still find version 1."""
        first = declared("Salesforce")
        first.revise((), id=uuid4(), by=ACTOR, now=NOW)
        assert len(first.competitors) == 1

    def test_an_invalid_revision_never_exists(self) -> None:
        """Validation happens in the new declaration's construction, so there
        is no moment at which a bad revision sits in a variable."""
        first = declared("Salesforce")
        duplicate = competitor("HubSpot")
        with pytest.raises(CompetitorsError, match="listed twice"):
            first.revise((duplicate, duplicate), id=uuid4(), by=ACTOR, now=NOW)


class TestTheModuleBoundary:
    def test_nothing_here_resolves_a_technology(self) -> None:
        """**The import contract, asserted from the domain's side.**

        *"commercial_profile declares; it never reads the pipeline"* forbids
        reaching the Knowledge Graph, and `knowledge_graph/public/` publishes
        nothing to reach. A competitor is therefore a name and an id — and if
        a future edit adds a resolved entity reference here, this fails before
        `lint-imports` has to.
        """
        import modules.commercial_profile.domain.competitors as module

        source = module.__file__
        assert source is not None
        with open(source) as handle:
            text = handle.read()
        assert "knowledge_graph" not in text.replace("knowledge_graph/public/", "")
