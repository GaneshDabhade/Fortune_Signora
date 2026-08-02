"""Projecting events onto a feed, and the rules that keep the table honest."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from uuid import UUID, uuid4

import pytest

from modules.timeline.application.ports import EntryStore
from modules.timeline.application.project import (
    ProjectEvent,
    ProjectEventInput,
    UnprojectableEvent,
)
from modules.timeline.domain.entry import EntryKind, TimelineEntry
from modules.timeline.domain.projection import PROJECTIONS, rule_for


class FakeEntryStore:
    """A double, because the projection is domain behaviour and needs no
    database to be wrong (§11)."""

    def __init__(self) -> None:
        self.written: list[TimelineEntry] = []

    async def append(self, entry: TimelineEntry) -> bool:
        if any(existing.id == entry.id for existing in self.written):
            return False
        self.written.append(entry)
        return True

    async def feed(
        self, *, workspace_id: UUID, entity_id: UUID, limit: int
    ) -> list[TimelineEntry]:
        matching = [
            e
            for e in self.written
            if e.workspace_id == workspace_id and e.entity_id == entity_id
        ]
        return sorted(matching, key=lambda e: (e.occurred_at, e.id), reverse=True)[:limit]


def _store() -> tuple[ProjectEvent, FakeEntryStore]:
    store = FakeEntryStore()
    return ProjectEvent(store), store


def _event(event_type: str, payload: dict[str, Any] | None = None, **kw: Any) -> ProjectEventInput:
    base: dict[str, Any] = {
        "event_id": uuid4(),
        "event_type": event_type,
        "workspace_id": uuid4(),
        "occurred_at": datetime(2026, 5, 1, 12, 0, tzinfo=UTC),
        "payload": payload if payload is not None else {"entity_id": str(uuid4())},
    }
    base.update(kw)
    return ProjectEventInput(**base)


class TestTheTableIsComplete:
    """The rules that stop the table and the enum drifting apart."""

    def test_every_kind_has_exactly_one_rule(self) -> None:
        """A kind with no rule can never be projected — a dead branch that
        looks like a feature."""
        mapped = [rule.kind for rule in PROJECTIONS.values()]
        assert sorted(mapped, key=str) == sorted(EntryKind, key=str)
        assert len(mapped) == len(set(mapped)), "two event types share one kind"

    def test_every_rule_names_a_source_reference(self) -> None:
        """An entry that cannot point back to the row that owns its meaning is
        unresolvable — Timeline holds no interpretation to fall back on."""
        assert all(rule.source_ref_key for rule in PROJECTIONS.values())

    def test_no_rule_exists_for_a_deferred_upstream(self) -> None:
        """M11 is deferred, so a `recommendation.*` rule would cite an event
        nothing publishes."""
        assert not [t for t in PROJECTIONS if t.startswith("recommendation.")]

    def test_an_unmapped_event_has_no_rule(self) -> None:
        assert rule_for("commercial_profile.target_accounts_changed") is None


class TestProjection:
    @pytest.mark.asyncio
    async def test_a_mapped_event_becomes_an_entry(self) -> None:
        project, store = _store()
        entity, signal = uuid4(), uuid4()
        written = await project.execute(
            _event(
                "signal.generated",
                {
                    "entity_id": str(entity),
                    "signal_id": str(signal),
                    "signal_type": "funding_round",
                    "relevance": "high",
                },
            )
        )
        assert written is True
        (entry,) = store.written
        assert entry.kind is EntryKind.SIGNAL_GENERATED
        assert entry.entity_id == entity
        assert entry.source_ref == signal
        assert entry.source_module == "signal_engine"

    @pytest.mark.asyncio
    async def test_an_unmapped_event_writes_nothing_and_does_not_raise(self) -> None:
        """**A Timeline gap must not fail a delivery.**

        The envelope carrying an event this module ignores is also carrying it
        to consumers that do care. Raising here would let a read-side
        convenience block an upstream's real consumers.
        """
        project, store = _store()
        assert await project.execute(_event("workspace.created")) is False
        assert store.written == []

    @pytest.mark.asyncio
    async def test_redelivery_writes_once(self) -> None:
        project, store = _store()
        event = _event(
            "opportunity.created",
            {"entity_id": str(uuid4()), "opportunity_id": str(uuid4()), "stage": "open"},
        )
        assert await project.execute(event) is True
        assert await project.execute(event) is False
        assert len(store.written) == 1


class TestDetailIsAnAllowList:
    @pytest.mark.asyncio
    async def test_only_declared_keys_are_carried(self) -> None:
        """**The rule that stops a projection duplicating upstream truth.**

        A payload field nobody declared must not reach the entry — an entry is
        immutable, so anything copied here can never be corrected.
        """
        project, store = _store()
        await project.execute(
            _event(
                "buying_score.updated",
                {
                    "entity_id": str(uuid4()),
                    "score_id": str(uuid4()),
                    "score": 62,
                    "trend": "rising",
                    "model_version": "should-not-be-copied",
                    "source_signal_ids": ["nor", "this"],
                },
            )
        )
        assert set(store.written[0].detail) == {"score", "trend"}

    @pytest.mark.asyncio
    async def test_an_absent_optional_field_is_absent_rather_than_null(self) -> None:
        project, store = _store()
        await project.execute(
            _event(
                "opportunity.stage_changed",
                {
                    "entity_id": str(uuid4()),
                    "opportunity_id": str(uuid4()),
                    "previous_stage": "open",
                    "new_stage": "won",
                    "reason": None,
                },
            )
        )
        assert "reason" not in store.written[0].detail
        assert store.written[0].detail["new_stage"] == "won"


class TestTimeIsTheDomainsNotTheBuss:
    @pytest.mark.asyncio
    async def test_most_events_order_by_the_envelope(self) -> None:
        project, store = _store()
        await project.execute(
            _event(
                "signal.generated",
                {"entity_id": str(uuid4()), "signal_id": str(uuid4())},
                occurred_at=datetime(2026, 5, 1, 12, 0, tzinfo=UTC),
            )
        )
        assert store.written[0].occurred_at == datetime(2026, 5, 1, 12, 0, tzinfo=UTC)

    @pytest.mark.asyncio
    async def test_a_detected_business_event_is_dated_when_it_happened(self) -> None:
        """**Detection lags occurrence, sometimes by days.**

        A funding round announced in March and detected in May belongs on the
        feed in March — a seller reading it is reconstructing what happened to
        the account, not what Signora noticed.
        """
        project, store = _store()
        await project.execute(
            _event(
                "business_event.detected",
                {
                    "entity_id": str(uuid4()),
                    "business_event_id": str(uuid4()),
                    "type_key": "funding_round",
                    "occurred_at": "2026-03-04T09:00:00+00:00",
                },
                occurred_at=datetime(2026, 5, 1, 12, 0, tzinfo=UTC),
            )
        )
        assert store.written[0].occurred_at == datetime(2026, 3, 4, 9, 0, tzinfo=UTC)

    @pytest.mark.asyncio
    async def test_a_missing_override_falls_back_to_the_envelope(self) -> None:
        """An upstream that stops sending the field must not stop the feed."""
        project, store = _store()
        await project.execute(
            _event(
                "business_event.detected",
                {"entity_id": str(uuid4()), "business_event_id": str(uuid4())},
                occurred_at=datetime(2026, 5, 1, 12, 0, tzinfo=UTC),
            )
        )
        assert store.written[0].occurred_at == datetime(2026, 5, 1, 12, 0, tzinfo=UTC)


class TestAContractChangeSurfacesHere:
    @pytest.mark.asyncio
    async def test_a_mapped_event_without_its_entity_is_refused(self) -> None:
        """Better an error on the projection than an unresolvable row a seller
        finds on a feed weeks later."""
        project, _ = _store()
        with pytest.raises(UnprojectableEvent, match="entity_id"):
            await project.execute(_event("signal.generated", {"signal_id": str(uuid4())}))

    @pytest.mark.asyncio
    async def test_a_mapped_event_without_its_source_reference_is_refused(self) -> None:
        project, _ = _store()
        with pytest.raises(UnprojectableEvent, match="signal_id"):
            await project.execute(_event("signal.generated", {"entity_id": str(uuid4())}))

    @pytest.mark.asyncio
    async def test_a_malformed_identifier_is_refused(self) -> None:
        project, _ = _store()
        with pytest.raises(UnprojectableEvent, match="malformed"):
            await project.execute(
                _event("signal.generated", {"entity_id": "not-a-uuid", "signal_id": str(uuid4())})
            )
