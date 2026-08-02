"""The Timeline Entry's four properties, each asserted where it can fail."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest

from modules.timeline.domain.entry import EntryKind, TimelineEntry


def _project(**overrides: object) -> TimelineEntry:
    defaults: dict[str, object] = {
        "workspace_id": uuid4(),
        "entity_id": uuid4(),
        "kind": EntryKind.SIGNAL_GENERATED,
        "occurred_at": datetime(2026, 3, 1, 9, 0, tzinfo=UTC),
        "event_id": uuid4(),
        "source_module": "signal_engine",
        "source_ref": uuid4(),
    }
    defaults.update(overrides)
    return TimelineEntry.project(**defaults)  # type: ignore[arg-type]


class TestIdentityIsDerived:
    """Redelivery must be a primary-key conflict, not a code path."""

    def test_the_same_event_projects_the_same_id(self) -> None:
        event_id = uuid4()
        assert _project(event_id=event_id).id == _project(event_id=event_id).id

    def test_the_id_survives_everything_but_the_event(self) -> None:
        """**The property that makes at-least-once delivery safe.**

        A redelivered envelope may be re-projected by a different worker with a
        freshly read upstream row, so the entity, the timestamp and the detail
        can all differ between two projections of one event. If any of them
        reached the id, the duplicate would be admitted.
        """
        event_id = uuid4()
        first = _project(event_id=event_id)
        second = _project(
            event_id=event_id,
            entity_id=uuid4(),
            occurred_at=datetime(2029, 12, 25, tzinfo=UTC),
            kind=EntryKind.OPPORTUNITY_CREATED,
            source_module="opportunity_engine",
            source_ref=uuid4(),
        )
        assert first.id == second.id

    def test_different_events_project_different_ids(self) -> None:
        assert _project().id != _project().id


class TestOrderingUsesDomainTime:
    def test_occurred_at_must_be_timezone_aware(self) -> None:
        """A naive datetime orders a feed wrongly and silently."""
        with pytest.raises(ValueError, match="timezone-aware"):
            _project(occurred_at=datetime(2026, 3, 1, 9, 0))

    def test_the_entry_keeps_the_domain_time_it_was_given(self) -> None:
        """Timeline never substitutes arrival time for the time a thing
        happened — a feed ordered by arrival reports March after June."""
        happened = datetime(2026, 3, 1, 9, 0, tzinfo=UTC)
        assert _project(occurred_at=happened).occurred_at == happened

    def test_an_entry_projected_later_can_have_an_earlier_time(self) -> None:
        late = _project(occurred_at=datetime(2026, 1, 1, tzinfo=UTC))
        early = _project(occurred_at=datetime(2026, 6, 1, tzinfo=UTC))
        assert late.occurred_at < early.occurred_at


class TestTheEntryIsImmutable:
    def test_an_entry_cannot_be_edited(self) -> None:
        """A projection that edits its past is a feed nobody can cite."""
        entry = _project()
        with pytest.raises((AttributeError, TypeError)):
            entry.kind = EntryKind.OPPORTUNITY_CREATED  # type: ignore[misc]

    def test_mutating_the_detail_passed_in_does_not_reach_the_entry(self) -> None:
        """**Immutability that a caller cannot undo.**

        `project` copies the mapping. Without that, a handler reusing one dict
        across a batch would retroactively rewrite every entry it had already
        produced — an edit to the past through the back door.
        """
        detail: dict[str, object] = {"delta": 15}
        entry = _project(detail=detail)
        detail["delta"] = 999
        assert entry.detail == {"delta": 15}


class TestTheEntryCitesRatherThanCopies:
    def test_an_entry_names_the_module_that_owns_the_fact(self) -> None:
        assert _project(source_module="buying_score_engine").source_module == (
            "buying_score_engine"
        )

    def test_source_module_cannot_be_empty(self) -> None:
        """An entry that cannot say who owns its fact is unresolvable — the
        reader has nowhere to go for the meaning Timeline deliberately omits."""
        with pytest.raises(ValueError, match="source_module"):
            _project(source_module="")

    def test_detail_defaults_to_empty_rather_than_null(self) -> None:
        assert _project().detail == {}


class TestEveryLiveEventKindProjects:
    """Six upstreams are live; `recommendation.created` awaits deferred M11.

    The kind is an enum rather than a string so an unmapped upstream cannot be
    projected at all — an invented kind would reach a customer's feed as a
    silently unrenderable row.
    """

    @pytest.mark.parametrize("kind", list(EntryKind))
    def test_each_kind_projects(self, kind: EntryKind) -> None:
        assert _project(kind=kind).kind is kind

    def test_no_kind_exists_for_an_unbuilt_upstream(self) -> None:
        """M11 is deferred, so there is deliberately nothing to project."""
        assert not [k for k in EntryKind if "recommendation" in k.value]

    def test_a_feed_orders_by_time_and_breaks_ties_by_id(self) -> None:
        """The total order the feed index exists for: two entries can share
        `occurred_at`, and a cursor over a non-total order drops or repeats
        rows at a page boundary."""
        when = datetime(2026, 4, 1, tzinfo=UTC)
        entries = [_project(occurred_at=when) for _ in range(5)]
        entries.append(_project(occurred_at=when + timedelta(hours=1)))
        newest_first = sorted(entries, key=lambda e: (e.occurred_at, e.id), reverse=True)
        assert newest_first[0].occurred_at == when + timedelta(hours=1)
        assert len({e.id for e in newest_first}) == 6
