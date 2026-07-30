"""The catalog loader, the supersession chain, and the profile surface.

These cover the paths a demonstration does not reach: a malformed catalog,
a chain walked backwards, and the distinction between what a customer has
configured and what they have inherited.
"""

from __future__ import annotations

import json
from collections.abc import Sequence
from datetime import UTC, datetime, timedelta
from pathlib import Path
from uuid import UUID, uuid4

import pytest

from modules.business_event_engine.public import BusinessEventType
from modules.signal_engine.application.queries import SignalQueries
from modules.signal_engine.domain.catalog import CatalogError, Relevance, SignalType
from modules.signal_engine.domain.profile import ProfileEntry, SignalProfile, default_profile
from modules.signal_engine.domain.signal import Signal, signal_id
from modules.signal_engine.infrastructure.catalog_loader import load_catalog
from modules.signal_engine.public import SignalQueries as PublicQueries
from tests.signal_engine.test_generate import (
    FakeBusinessEvents,
    FakeProfileRepository,
    FakeSignalRepository,
)

WORKSPACE = uuid4()
ENTITY = uuid4()
NOW = datetime(2026, 3, 1, tzinfo=UTC)


def _signal(
    *,
    evidence: tuple[UUID, ...],
    supersedes: UUID | None = None,
    rationale: str = "Because.",
) -> Signal:
    ids = tuple(evidence)
    return Signal(
        id=signal_id(
            workspace_id=WORKSPACE,
            entity_id=ENTITY,
            signal_type=SignalType.BUDGET_UNLOCKED,
            contributing_event_ids=ids,
        ),
        workspace_id=WORKSPACE,
        entity_id=ENTITY,
        signal_type=SignalType.BUDGET_UNLOCKED,
        relevance=Relevance.SUPPORTING,
        occurred_at=NOW,
        window_start=NOW,
        window_end=NOW,
        generated_at=NOW,
        relevant_until=NOW + timedelta(days=30),
        rationale=rationale,
        contributing_event_ids=ids,
        contributing_event_types=(BusinessEventType.FUNDING_ROUND_CLOSED,),
        supersedes=supersedes,
    )


def _queries(
    repository: FakeSignalRepository, profile: SignalProfile | None = None
) -> SignalQueries:
    return SignalQueries(
        repository=repository,
        profiles=FakeProfileRepository(profile),
        business_events=FakeBusinessEvents([]),  # type: ignore[arg-type]
        catalog=load_catalog(),
    )


class TestTheCatalogLoader:
    def test_a_missing_version_fails_loudly(self) -> None:
        """A version recorded on historical signals must remain loadable, or
        those signals become unexplainable."""
        with pytest.raises(CatalogError, match="not found"):
            load_catalog(999)

    def test_a_malformed_catalog_fails_at_load_rather_than_at_generation(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """A type that silently stops being produced is invisible — "no
        signals" looks exactly like "nothing happened"."""
        from modules.signal_engine.infrastructure import catalog_loader

        (tmp_path / "signals@42.json").write_text(
            json.dumps({"version": 42, "types": [{"key": "nonsense"}]})
        )
        monkeypatch.setattr(catalog_loader, "CATALOG_DIR", tmp_path)

        with pytest.raises(CatalogError, match="malformed"):
            catalog_loader.load_catalog(42)

    def test_a_version_disagreeing_with_its_filename_is_refused(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        from modules.signal_engine.infrastructure import catalog_loader

        (tmp_path / "signals@43.json").write_text(json.dumps({"version": 7, "types": []}))
        monkeypatch.setattr(catalog_loader, "CATALOG_DIR", tmp_path)

        with pytest.raises(CatalogError, match="must agree"):
            catalog_loader.load_catalog(43)

    def test_an_undeclared_type_cannot_be_looked_up(self) -> None:
        empty = load_catalog().model_copy(update={"types": ()})

        with pytest.raises(CatalogError, match="not declared"):
            empty.definition(SignalType.BUDGET_UNLOCKED)

    def test_a_type_with_no_rule_is_refused(self) -> None:
        """A type nobody produces is a promise the product cannot keep."""
        with pytest.raises(CatalogError, match="no rule to produce"):
            load_catalog().validate_complete(frozenset())

    def test_a_rule_with_no_declaration_is_refused(self) -> None:
        empty = load_catalog().model_copy(update={"types": ()})

        with pytest.raises(CatalogError, match="not declared"):
            empty.validate_complete(frozenset({SignalType.BUDGET_UNLOCKED}))


class TestTheReadSurface:
    async def test_an_explanation_for_an_unknown_signal_is_none(self) -> None:
        """Absent and empty mean different things, and only one is a bug."""
        assert await _queries(FakeSignalRepository()).explanation(WORKSPACE, uuid4()) is None

    async def test_history_walks_the_chain_oldest_first(self) -> None:
        repository = FakeSignalRepository()
        first_ids = (uuid4(),)
        earlier = _signal(evidence=first_ids, rationale="One ground.")
        later = _signal(
            evidence=first_ids + (uuid4(),), supersedes=earlier.id, rationale="Two grounds."
        )
        repository.rows.extend([earlier, later])

        chain = await _queries(repository).history(WORKSPACE, later.id)

        assert [s.rationale for s in chain] == ["One ground.", "Two grounds."]

    async def test_history_of_an_unsuperseded_signal_is_just_itself(self) -> None:
        repository = FakeSignalRepository()
        only = _signal(evidence=(uuid4(),))
        repository.rows.append(only)

        assert await _queries(repository).history(WORKSPACE, only.id) == (only,)

    async def test_an_unconfigured_workspace_reads_the_catalog_defaults(self) -> None:
        """Every type is present with its declared default — the out-of-box
        reading is reviewable rather than emergent."""
        profile = await _queries(FakeSignalRepository()).profile(WORKSPACE)

        assert profile == default_profile(load_catalog())
        assert len(profile) == len(SignalType)

    async def test_a_configured_workspace_reads_its_own_entries_over_defaults(self) -> None:
        stored = SignalProfile(
            id=uuid4(),
            workspace_id=WORKSPACE,
            version=1,
            entries=(ProfileEntry(SignalType.BUDGET_UNLOCKED, Relevance.IGNORED),),
            created_at=NOW,
            created_by=uuid4(),
        )

        profile = await _queries(FakeSignalRepository(), stored).profile(WORKSPACE)

        by_type = {entry.signal_type: entry for entry in profile}
        assert by_type[SignalType.BUDGET_UNLOCKED].relevance is Relevance.IGNORED
        assert len(profile) == len(SignalType), "types it has not configured still appear"

    async def test_the_stored_profile_is_distinguishable_from_the_default(self) -> None:
        """What a customer has *authored* is different from what they have
        inherited, and only the first is theirs to back up."""
        assert await _queries(FakeSignalRepository()).stored_profile(WORKSPACE) is None

    async def test_the_catalog_is_reachable_through_the_public_surface(self) -> None:
        queries: PublicQueries = _queries(FakeSignalRepository())

        assert queries.catalog().version == load_catalog().version


@pytest.mark.parametrize("constituents", [(), (uuid4(),)], ids=["none", "one"])
def test_a_signal_is_composite_when_it_names_constituents(
    constituents: Sequence[UUID],
) -> None:
    """Enrichment is visible on the signal itself, without a join."""
    signal = _signal(evidence=(uuid4(),))

    assert signal.enriched_by(tuple(constituents)).is_composite is bool(constituents)


class TestEveryTypeStatesItsLimitsAndHowToCheckIt:
    """Added at T126 (ADR-0030, Decision 5).

    A signal type with no stated limitations is an authoring omission, and
    the enterprise customers these exist for will ask the question whether or
    not it has been answered. Required by the type; asserted here against the
    **shipped artifact**, because a `min_length` constraint proves nothing
    about a catalog nobody filled in.
    """

    def test_every_type_says_what_it_does_not_imply(self) -> None:
        for definition in load_catalog().types:
            assert definition.limitations, f"{definition.key.value} states no limitations"
            for limitation in definition.limitations:
                assert limitation.strip(), f"{definition.key.value} has a blank limitation"

    def test_every_type_says_how_a_human_checks_it(self) -> None:
        for definition in load_catalog().types:
            assert definition.suggested_validation, (
                f"{definition.key.value} offers no way to independently validate it"
            )

    def test_validation_never_tells_a_seller_what_to_do(self) -> None:
        """It says what to *verify*, never what to do about it. Recommending
        is the Recommendation Engine's (M11); a module that told a seller what
        to do would make that module a formatting layer."""
        forbidden = ("reach out", "call them", "email", "pitch", "offer them", "propose")
        for definition in load_catalog().types:
            for step in definition.suggested_validation:
                lowered = step.lower()
                assert not any(phrase in lowered for phrase in forbidden), (
                    f"{definition.key.value} suggests a commercial action rather than a check: "
                    f"{step!r}"
                )
