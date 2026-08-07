"""TASK-451 — the `public/` reader and writer, behind the ports slice 1 published.

⚠️ **This adapter has no other-module consumer today**, and that is exactly why
it is tested here rather than left to whoever writes the first one. **A port
whose implementation is unproven is the shape [C-238](../../../../docs/LANE_COORDINATION.md)
was raised about**, seen from the owning side: the contract exists, so the
thing behind it has to work before somebody depends on it.

**The repository is faked, not the service.** What is under test is the
projection and the rules it applies on the way in — not SQL.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest

from modules.workspace_tenancy.domain.exceptions import (
    EmptyDeclarationError,
    InvalidSavedViewNameError,
)
from modules.workspace_tenancy.domain.saved_view import SavedView
from modules.workspace_tenancy.infrastructure.saved_view_service import SavedViewService, to_view
from modules.workspace_tenancy.public.saved_views import (
    SavedViewReader,
    SavedViewView,
    SavedViewWriter,
)
from modules.workspace_tenancy.tests.fakes import FakeSavedViewRepository

MOMENT = datetime(2026, 8, 7, 12, 0, tzinfo=UTC)
WORKSPACE = uuid4()
AUTHOR = uuid4()


def _aggregate(*, name: str = "Contested", at: datetime = MOMENT) -> SavedView:
    return SavedView.declare(
        workspace_id=WORKSPACE,
        name=name,
        declaration={"filter": "contested"},
        created_by=AUTHOR,
        now=at,
    )


@pytest.fixture
def repository() -> FakeSavedViewRepository:
    return FakeSavedViewRepository()


@pytest.fixture
def service(repository: FakeSavedViewRepository) -> SavedViewService:
    return SavedViewService(repository)  # type: ignore[arg-type]


class TestItSatisfiesThePublishedPorts:
    def test_the_service_is_both_a_reader_and_a_writer(self, service: SavedViewService) -> None:
        """⚡ **The check [C-238](../../../../docs/LANE_COORDINATION.md) found
        missing elsewhere**: not that the Protocol exists, but that something
        satisfies it. These assignments fail `mypy --strict` if it does not."""
        reader: SavedViewReader = service
        writer: SavedViewWriter = service
        assert callable(reader.by_id)
        assert callable(writer.save)


class TestReading:
    async def test_by_id_projects_every_published_field(
        self, service: SavedViewService, repository: FakeSavedViewRepository
    ) -> None:
        view = _aggregate()
        await repository.add(view)
        found = await service.by_id(WORKSPACE, view.id)
        assert found == to_view(view)

    async def test_absence_is_none_rather_than_an_error(self, service: SavedViewService) -> None:
        assert await service.by_id(WORKSPACE, uuid4()) is None

    async def test_another_workspaces_view_is_none(
        self, service: SavedViewService, repository: FakeSavedViewRepository
    ) -> None:
        view = _aggregate()
        await repository.add(view)
        assert await service.by_id(uuid4(), view.id) is None

    async def test_live_excludes_retired_and_superseded(
        self, service: SavedViewService, repository: FakeSavedViewRepository
    ) -> None:
        first = _aggregate(name="First")
        await repository.add(first)
        revision = first.revise(created_by=AUTHOR, now=MOMENT + timedelta(hours=1))
        await repository.add(revision)
        retired = _aggregate(name="Gone", at=MOMENT + timedelta(hours=2))
        await repository.add(retired)
        await repository.mark_retired(retired.retire(at=MOMENT + timedelta(hours=3)))

        page = await service.live(WORKSPACE)
        assert [v.id for v in page.items] == [revision.id]

    async def test_a_page_reports_more_and_carries_a_resumable_position(
        self, service: SavedViewService, repository: FakeSavedViewRepository
    ) -> None:
        for index in range(3):
            await repository.add(
                _aggregate(name=f"View {index}", at=MOMENT + timedelta(minutes=index))
            )
        page = await service.live(WORKSPACE, limit=2)
        assert len(page.items) == 2
        assert page.has_more is True
        assert page.next_position is not None
        assert page.next_position.id == page.items[-1].id

    async def test_the_last_page_offers_no_position(
        self, service: SavedViewService, repository: FakeSavedViewRepository
    ) -> None:
        """**`None` means there is nothing after this**, and a cursor here
        would invite a request that returns an empty page forever."""
        await repository.add(_aggregate())
        page = await service.live(WORKSPACE, limit=10)
        assert page.has_more is False
        assert page.next_position is None

    async def test_resuming_from_a_position_continues_without_repeating(
        self, service: SavedViewService, repository: FakeSavedViewRepository
    ) -> None:
        for index in range(3):
            await repository.add(
                _aggregate(name=f"View {index}", at=MOMENT + timedelta(minutes=index))
            )
        first = await service.live(WORKSPACE, limit=2)
        second = await service.live(WORKSPACE, after=first.next_position, limit=2)
        seen = [v.name for v in first.items] + [v.name for v in second.items]
        assert seen == ["View 2", "View 1", "View 0"]
        assert len(set(seen)) == 3


class TestWriting:
    async def test_save_records_a_view_a_consumer_constructed(
        self, service: SavedViewService, repository: FakeSavedViewRepository
    ) -> None:
        incoming = SavedViewView(
            id=uuid4(),
            workspace_id=WORKSPACE,
            name="From another module",
            declaration={"any": "shape"},
            created_by=AUTHOR,
            created_at=MOMENT,
        )
        await service.save(incoming)
        assert await service.by_id(WORKSPACE, incoming.id) == incoming

    async def test_a_nameless_view_is_refused_on_the_way_in(
        self, service: SavedViewService, repository: FakeSavedViewRepository
    ) -> None:
        """⚡ **A `SavedViewView` is a Pydantic model a consumer built**, so it
        carries no guarantee the aggregate's rules were run. Writing through
        `public/` must not store what the use case would refuse."""
        with pytest.raises(InvalidSavedViewNameError):
            await service.save(
                SavedViewView(
                    id=uuid4(),
                    workspace_id=WORKSPACE,
                    name="   ",
                    declaration={"a": 1},
                    created_by=AUTHOR,
                    created_at=MOMENT,
                )
            )
        assert repository.views == {}

    async def test_an_empty_declaration_is_refused_on_the_way_in(
        self, service: SavedViewService, repository: FakeSavedViewRepository
    ) -> None:
        with pytest.raises(EmptyDeclarationError):
            await service.save(
                SavedViewView(
                    id=uuid4(),
                    workspace_id=WORKSPACE,
                    name="Named",
                    declaration={},
                    created_by=AUTHOR,
                    created_at=MOMENT,
                )
            )
        assert repository.views == {}

    async def test_the_stored_declaration_is_a_copy(
        self, service: SavedViewService, repository: FakeSavedViewRepository
    ) -> None:
        """A caller that kept its dict must not be able to edit a stored
        declaration through it."""
        supplied: dict[str, object] = {"filter": "contested"}
        incoming = SavedViewView(
            id=uuid4(),
            workspace_id=WORKSPACE,
            name="Named",
            declaration=supplied,
            created_by=AUTHOR,
            created_at=MOMENT,
        )
        await service.save(incoming)
        supplied["filter"] = "tampered"
        stored = await service.by_id(WORKSPACE, incoming.id)
        assert stored is not None and stored.declaration == {"filter": "contested"}


class TestRetiring:
    async def test_retire_stamps_the_moment(
        self, service: SavedViewService, repository: FakeSavedViewRepository
    ) -> None:
        view = _aggregate()
        await repository.add(view)
        at = MOMENT + timedelta(days=1)
        await service.retire(WORKSPACE, view.id, at=at)
        stored = await service.by_id(WORKSPACE, view.id)
        assert stored is not None and stored.retired_at == at

    async def test_retiring_twice_keeps_the_first_timestamp(
        self, service: SavedViewService, repository: FakeSavedViewRepository
    ) -> None:
        """⛔ **Silent rather than raising**, because the port promises no
        error — and the row guard is `retired_at IS NULL`, so the second
        attempt would match nothing anyway."""
        view = _aggregate()
        await repository.add(view)
        first_at = MOMENT + timedelta(days=1)
        await service.retire(WORKSPACE, view.id, at=first_at)
        await service.retire(WORKSPACE, view.id, at=MOMENT + timedelta(days=2))
        stored = await service.by_id(WORKSPACE, view.id)
        assert stored is not None and stored.retired_at == first_at

    async def test_retiring_an_absent_view_does_nothing(self, service: SavedViewService) -> None:
        await service.retire(WORKSPACE, uuid4(), at=MOMENT)

    async def test_retiring_another_workspaces_view_does_nothing(
        self, service: SavedViewService, repository: FakeSavedViewRepository
    ) -> None:
        view = _aggregate()
        await repository.add(view)
        await service.retire(uuid4(), view.id, at=MOMENT + timedelta(days=1))
        stored = await service.by_id(WORKSPACE, view.id)
        assert stored is not None and stored.retired_at is None
