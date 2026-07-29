"""The read surface, the taxonomy loader, and the domain's own guards.

These cover the paths a demonstration does not reach: a malformed taxonomy,
a chain walked backwards, an event constructed without the things that make
it traceable.
"""

from __future__ import annotations

import json
from dataclasses import replace
from datetime import UTC, datetime
from pathlib import Path
from uuid import UUID, uuid4

import pytest

from modules.business_event_engine.application.queries import BusinessEventQueries
from modules.business_event_engine.domain.business_event import (
    BusinessEvent,
    BusinessEventError,
    business_event_id,
)
from modules.business_event_engine.domain.taxonomy import (
    BusinessDomain,
    BusinessEventType,
    TaxonomyError,
)
from modules.business_event_engine.infrastructure.taxonomy_loader import load_taxonomy
from modules.business_event_engine.public import BusinessEventQueries as PublicQueries
from tests.business_event_engine.test_detect import (
    FakeBusinessEventRepository,
    FakeObservations,
)

WORKSPACE = uuid4()
ENTITY = uuid4()
NOW = datetime(2026, 6, 1, tzinfo=UTC)


def _event(
    *, evidence: tuple[UUID, ...], supersedes: UUID | None = None, summary: str = "Grew"
) -> BusinessEvent:
    ids = tuple(evidence)
    return BusinessEvent(
        id=business_event_id(
            workspace_id=WORKSPACE,
            entity_id=ENTITY,
            type_key=BusinessEventType.HIRING_SURGE,
            evidence_observation_ids=ids,
        ),
        workspace_id=WORKSPACE,
        entity_id=ENTITY,
        type_key=BusinessEventType.HIRING_SURGE,
        domain=BusinessDomain.WORKFORCE,
        occurred_at=NOW,
        window_start=NOW,
        window_end=NOW,
        detected_at=NOW,
        summary=summary,
        facts={"ratio": 0.4},
        evidence_observation_ids=ids,
        corroborating_providers=("coresignal",),
        taxonomy_version=1,
        supersedes=supersedes,
    )


def _queries(repository: FakeBusinessEventRepository) -> BusinessEventQueries:
    return BusinessEventQueries(
        repository=repository,
        observations=FakeObservations([]),  # type: ignore[arg-type]
        taxonomy=load_taxonomy(),
    )


class TestTheDomainRefusesUntraceableEvents:
    def test_an_event_without_evidence_is_refused(self) -> None:
        """An event that cannot be traced back is an assertion, not
        intelligence."""
        with pytest.raises(BusinessEventError, match="cites no observations"):
            _event(evidence=())

    def test_an_event_without_a_provider_is_refused(self) -> None:
        """Every conclusion in Signora is *according to* someone."""
        base = _event(evidence=(uuid4(),))

        with pytest.raises(BusinessEventError, match="names no provider"):
            replace(base, corroborating_providers=())

    def test_an_event_without_a_summary_is_refused(self) -> None:
        base = _event(evidence=(uuid4(),))

        with pytest.raises(BusinessEventError, match="no customer can read"):
            replace(base, summary="   ")

    def test_a_backwards_window_is_refused(self) -> None:
        base = _event(evidence=(uuid4(),))

        with pytest.raises(BusinessEventError, match="cannot end before it begins"):
            replace(base, window_start=NOW, window_end=datetime(2026, 1, 1, tzinfo=UTC))

    def test_one_provider_is_not_corroboration(self) -> None:
        assert _event(evidence=(uuid4(),)).is_corroborated is False


class TestTheReadSurface:
    async def test_evidence_for_an_unknown_event_is_none_not_empty(self) -> None:
        """Absent and empty mean different things, and only one is a bug."""
        assert (
            await _queries(FakeBusinessEventRepository()).business_event_evidence(
                WORKSPACE, uuid4()
            )
            is None
        )

    async def test_history_walks_the_chain_oldest_first(self) -> None:
        """*"What did we believe about this surge, and when?"*"""
        repository = FakeBusinessEventRepository()
        first_ids = (uuid4(),)
        earlier = _event(evidence=first_ids, summary="Grew 20%")
        later = _event(evidence=first_ids + (uuid4(),), supersedes=earlier.id, summary="Grew 40%")
        repository.rows.extend([earlier, later])

        chain = await _queries(repository).history(WORKSPACE, later.id)

        assert [event.summary for event in chain] == ["Grew 20%", "Grew 40%"]

    async def test_history_of_an_unsuperseded_event_is_just_itself(self) -> None:
        repository = FakeBusinessEventRepository()
        only = _event(evidence=(uuid4(),))
        repository.rows.append(only)

        assert await _queries(repository).history(WORKSPACE, only.id) == (only,)

    async def test_the_taxonomy_is_reachable_through_the_public_surface(self) -> None:
        """The product, analytics, and documentation should read the same
        definitions rather than re-describing them."""
        queries: PublicQueries = _queries(FakeBusinessEventRepository())

        assert queries.taxonomy().version == load_taxonomy().version

    async def test_events_are_filtered_to_the_entity(self) -> None:
        repository = FakeBusinessEventRepository()
        repository.rows.append(_event(evidence=(uuid4(),)))

        assert await _queries(repository).business_events(WORKSPACE, uuid4()) == ()


class TestTheTaxonomyLoader:
    def test_a_missing_version_fails_loudly(self) -> None:
        """A version recorded on historical events must remain loadable, or
        those events become unexplainable."""
        with pytest.raises(TaxonomyError, match="not found"):
            load_taxonomy(999)

    def test_a_malformed_artifact_fails_at_load_rather_than_at_detection(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """A type that silently stops firing is invisible — "no events" looks
        exactly like "nothing happened"."""
        from modules.business_event_engine.infrastructure import taxonomy_loader

        (tmp_path / "business_events@42.json").write_text(
            json.dumps({"version": 42, "types": [{"key": "nonsense"}]})
        )
        monkeypatch.setattr(taxonomy_loader, "TAXONOMY_DIR", tmp_path)

        with pytest.raises(TaxonomyError, match="malformed"):
            taxonomy_loader.load_taxonomy(42)

    def test_a_version_disagreeing_with_its_filename_is_refused(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Otherwise an event's recorded version names the wrong
        definitions."""
        from modules.business_event_engine.infrastructure import taxonomy_loader

        (tmp_path / "business_events@43.json").write_text(json.dumps({"version": 7, "types": []}))
        monkeypatch.setattr(taxonomy_loader, "TAXONOMY_DIR", tmp_path)

        with pytest.raises(TaxonomyError, match="must agree"):
            taxonomy_loader.load_taxonomy(43)

    def test_an_undeclared_type_cannot_be_looked_up(self) -> None:
        taxonomy = load_taxonomy()
        empty = taxonomy.model_copy(update={"types": ()})

        with pytest.raises(TaxonomyError, match="not declared"):
            empty.definition(BusinessEventType.HIRING_SURGE)

    def test_a_rule_with_no_declaration_is_refused(self) -> None:
        taxonomy = load_taxonomy()
        empty = taxonomy.model_copy(update={"types": ()})

        with pytest.raises(TaxonomyError, match="not declared"):
            empty.validate_complete(frozenset({BusinessEventType.HIRING_SURGE}))
