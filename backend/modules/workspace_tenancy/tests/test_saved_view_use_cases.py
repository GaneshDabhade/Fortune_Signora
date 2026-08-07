"""TASK-451 — the application layer over the saved-view aggregate.

**These test the orchestration, not the rules.** `test_saved_view.py` already
proves what the aggregate refuses; what is unproven until here is that the use
cases *reach* those refusals, scope every read to a workspace, and derive
liveness the way the storage does.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID, uuid4

import pytest

from modules.workspace_tenancy.application.use_cases.saved_views import (
    DeclareSavedViewInput,
    DeclareSavedViewUseCase,
    GetSavedViewUseCase,
    ListSavedViewsInput,
    ListSavedViewsUseCase,
    RetireSavedViewInput,
    RetireSavedViewUseCase,
    ReviseSavedViewInput,
    ReviseSavedViewUseCase,
)
from modules.workspace_tenancy.domain.entities import Workspace
from modules.workspace_tenancy.domain.exceptions import (
    EmptyDeclarationError,
    InvalidSavedViewNameError,
    SavedViewAlreadyRetiredError,
    SavedViewNotFoundError,
    WorkspaceNotFoundError,
)
from modules.workspace_tenancy.domain.saved_view import SavedView
from modules.workspace_tenancy.tests.fakes import (
    FakeSavedViewRepository,
    FakeWorkspaceRepository,
)

MOMENT = datetime(2026, 8, 7, 12, 0, tzinfo=UTC)
AUTHOR = uuid4()
COLLEAGUE = uuid4()


@pytest.fixture
def workspaces() -> FakeWorkspaceRepository:
    return FakeWorkspaceRepository()


@pytest.fixture
def views() -> FakeSavedViewRepository:
    return FakeSavedViewRepository()


@pytest.fixture
async def workspace(workspaces: FakeWorkspaceRepository) -> Workspace:
    space, _ = Workspace.create(name="Acme", created_by=AUTHOR)
    await workspaces.add(space)
    return space


async def _declare(
    workspaces: FakeWorkspaceRepository,
    views: FakeSavedViewRepository,
    workspace_id: UUID,
    *,
    name: str = "Contested accounts",
    declaration: dict[str, Any] | None = None,
    at: datetime = MOMENT,
) -> SavedView:
    use_case = DeclareSavedViewUseCase(workspaces=workspaces, saved_views=views)
    return await use_case.execute(
        DeclareSavedViewInput(
            workspace_id=workspace_id,
            name=name,
            declaration=(
                {"filter": "contested", "sort": "score"} if declaration is None else declaration
            ),
            created_by=AUTHOR,
        ),
        now=at,
    )


class TestDeclaring:
    async def test_records_the_view_under_the_authors_name(
        self,
        workspaces: FakeWorkspaceRepository,
        views: FakeSavedViewRepository,
        workspace: Workspace,
    ) -> None:
        view = await _declare(workspaces, views, workspace.id)
        assert view.created_by == AUTHOR
        assert view.supersedes is None
        assert views.views[view.id] is view

    async def test_the_declaration_is_stored_verbatim_and_uninspected(
        self,
        workspaces: FakeWorkspaceRepository,
        views: FakeSavedViewRepository,
        workspace: Workspace,
    ) -> None:
        """D-091: this module never learns what a key means. **A declaration
        full of words it has never seen stores exactly as given.**"""
        odd: dict[str, Any] = {"zzz_unknown_key": [1, 2, {"nested": True}], "": None}
        view = await _declare(workspaces, views, workspace.id, declaration=odd)
        assert view.declaration == odd

    async def test_a_caller_supplied_id_makes_a_retry_idempotent(
        self,
        workspaces: FakeWorkspaceRepository,
        views: FakeSavedViewRepository,
        workspace: Workspace,
    ) -> None:
        chosen = uuid4()
        use_case = DeclareSavedViewUseCase(workspaces=workspaces, saved_views=views)
        command = DeclareSavedViewInput(
            workspace_id=workspace.id,
            name="Mine",
            declaration={"a": 1},
            created_by=AUTHOR,
            saved_view_id=chosen,
        )
        first = await use_case.execute(command, now=MOMENT)
        second = await use_case.execute(command, now=MOMENT)
        assert first.id == second.id == chosen
        assert len(views.views) == 1

    async def test_an_unnamed_view_is_refused_by_the_aggregate(
        self,
        workspaces: FakeWorkspaceRepository,
        views: FakeSavedViewRepository,
        workspace: Workspace,
    ) -> None:
        with pytest.raises(InvalidSavedViewNameError):
            await _declare(workspaces, views, workspace.id, name="   ")
        assert views.views == {}

    async def test_an_empty_declaration_is_refused(
        self,
        workspaces: FakeWorkspaceRepository,
        views: FakeSavedViewRepository,
        workspace: Workspace,
    ) -> None:
        with pytest.raises(EmptyDeclarationError):
            await _declare(workspaces, views, workspace.id, declaration={})

    async def test_an_invisible_workspace_reads_as_absent(
        self, workspaces: FakeWorkspaceRepository, views: FakeSavedViewRepository
    ) -> None:
        """**Not *forbidden*.** Distinguishing the two would confirm the id
        exists, which is the enumeration 11-tenancy.md refuses."""
        with pytest.raises(WorkspaceNotFoundError):
            await _declare(workspaces, views, uuid4())


class TestRevising:
    async def test_a_revision_names_the_version_it_replaces(
        self,
        workspaces: FakeWorkspaceRepository,
        views: FakeSavedViewRepository,
        workspace: Workspace,
    ) -> None:
        first = await _declare(workspaces, views, workspace.id)
        revision = await ReviseSavedViewUseCase(workspaces=workspaces, saved_views=views).execute(
            ReviseSavedViewInput(
                workspace_id=workspace.id,
                saved_view_id=first.id,
                created_by=COLLEAGUE,
                name="Contested, EMEA",
            ),
            now=MOMENT + timedelta(hours=1),
        )
        assert revision.supersedes == first.id
        assert revision.id != first.id

    async def test_the_earlier_version_stays_readable(
        self,
        workspaces: FakeWorkspaceRepository,
        views: FakeSavedViewRepository,
        workspace: Workspace,
    ) -> None:
        """The whole reason a change is a version: a colleague who acted on
        last week's reading can still explain it."""
        first = await _declare(workspaces, views, workspace.id)
        await ReviseSavedViewUseCase(workspaces=workspaces, saved_views=views).execute(
            ReviseSavedViewInput(
                workspace_id=workspace.id,
                saved_view_id=first.id,
                created_by=COLLEAGUE,
                declaration={"filter": "all"},
            ),
            now=MOMENT + timedelta(hours=1),
        )
        assert views.views[first.id].declaration == {"filter": "contested", "sort": "score"}

    async def test_the_revision_is_attributed_to_whoever_made_it(
        self,
        workspaces: FakeWorkspaceRepository,
        views: FakeSavedViewRepository,
        workspace: Workspace,
    ) -> None:
        """§10 applied to people — inheriting `created_by` would attribute a
        colleague's edit to whoever wrote the first version."""
        first = await _declare(workspaces, views, workspace.id)
        revision = await ReviseSavedViewUseCase(workspaces=workspaces, saved_views=views).execute(
            ReviseSavedViewInput(
                workspace_id=workspace.id, saved_view_id=first.id, created_by=COLLEAGUE
            ),
            now=MOMENT + timedelta(hours=1),
        )
        assert revision.created_by == COLLEAGUE
        assert first.created_by == AUTHOR

    async def test_omitting_both_fields_records_a_reaffirmation(
        self,
        workspaces: FakeWorkspaceRepository,
        views: FakeSavedViewRepository,
        workspace: Workspace,
    ) -> None:
        first = await _declare(workspaces, views, workspace.id)
        revision = await ReviseSavedViewUseCase(workspaces=workspaces, saved_views=views).execute(
            ReviseSavedViewInput(
                workspace_id=workspace.id, saved_view_id=first.id, created_by=COLLEAGUE
            ),
            now=MOMENT + timedelta(hours=1),
        )
        assert revision.name == first.name
        assert revision.declaration == first.declaration
        assert revision.supersedes == first.id

    async def test_a_retired_view_is_not_revived_by_revising_it(
        self,
        workspaces: FakeWorkspaceRepository,
        views: FakeSavedViewRepository,
        workspace: Workspace,
    ) -> None:
        first = await _declare(workspaces, views, workspace.id)
        await RetireSavedViewUseCase(workspaces=workspaces, saved_views=views).execute(
            RetireSavedViewInput(workspace_id=workspace.id, saved_view_id=first.id),
            now=MOMENT + timedelta(hours=1),
        )
        with pytest.raises(SavedViewAlreadyRetiredError):
            await ReviseSavedViewUseCase(workspaces=workspaces, saved_views=views).execute(
                ReviseSavedViewInput(
                    workspace_id=workspace.id, saved_view_id=first.id, created_by=COLLEAGUE
                ),
                now=MOMENT + timedelta(hours=2),
            )

    async def test_revising_a_view_from_another_workspace_is_not_found(
        self,
        workspaces: FakeWorkspaceRepository,
        views: FakeSavedViewRepository,
        workspace: Workspace,
    ) -> None:
        other, _ = Workspace.create(name="Other", created_by=COLLEAGUE)
        await workspaces.add(other)
        mine = await _declare(workspaces, views, workspace.id)
        with pytest.raises(SavedViewNotFoundError):
            await ReviseSavedViewUseCase(workspaces=workspaces, saved_views=views).execute(
                ReviseSavedViewInput(
                    workspace_id=other.id, saved_view_id=mine.id, created_by=COLLEAGUE
                ),
                now=MOMENT,
            )


class TestRetiring:
    async def test_retiring_stamps_the_moment_and_keeps_the_row(
        self,
        workspaces: FakeWorkspaceRepository,
        views: FakeSavedViewRepository,
        workspace: Workspace,
    ) -> None:
        first = await _declare(workspaces, views, workspace.id)
        at = MOMENT + timedelta(days=1)
        retired = await RetireSavedViewUseCase(workspaces=workspaces, saved_views=views).execute(
            RetireSavedViewInput(workspace_id=workspace.id, saved_view_id=first.id), now=at
        )
        assert retired.retired_at == at
        assert first.id in views.views

    async def test_retiring_twice_is_refused_rather_than_re_stamped(
        self,
        workspaces: FakeWorkspaceRepository,
        views: FakeSavedViewRepository,
        workspace: Workspace,
    ) -> None:
        """The first timestamp is the one that happened."""
        first = await _declare(workspaces, views, workspace.id)
        use_case = RetireSavedViewUseCase(workspaces=workspaces, saved_views=views)
        command = RetireSavedViewInput(workspace_id=workspace.id, saved_view_id=first.id)
        await use_case.execute(command, now=MOMENT + timedelta(days=1))
        with pytest.raises(SavedViewAlreadyRetiredError):
            await use_case.execute(command, now=MOMENT + timedelta(days=2))
        assert views.views[first.id].retired_at == MOMENT + timedelta(days=1)

    async def test_retiring_an_absent_view_is_not_found(
        self,
        workspaces: FakeWorkspaceRepository,
        views: FakeSavedViewRepository,
        workspace: Workspace,
    ) -> None:
        with pytest.raises(SavedViewNotFoundError):
            await RetireSavedViewUseCase(workspaces=workspaces, saved_views=views).execute(
                RetireSavedViewInput(workspace_id=workspace.id, saved_view_id=uuid4()),
                now=MOMENT,
            )


class TestListing:
    async def test_the_list_is_shared_rather_than_per_author(
        self,
        workspaces: FakeWorkspaceRepository,
        views: FakeSavedViewRepository,
        workspace: Workspace,
    ) -> None:
        """452: *"a shared view looks the same for everybody"* — so a view a
        colleague declared appears in the same list, and nothing filters by
        author."""
        await _declare(workspaces, views, workspace.id, name="Mine")
        colleague_view = await DeclareSavedViewUseCase(
            workspaces=workspaces, saved_views=views
        ).execute(
            DeclareSavedViewInput(
                workspace_id=workspace.id,
                name="Theirs",
                declaration={"filter": "x"},
                created_by=COLLEAGUE,
            ),
            now=MOMENT + timedelta(minutes=1),
        )
        result = await ListSavedViewsUseCase(workspaces=workspaces, saved_views=views).execute(
            ListSavedViewsInput(workspace_id=workspace.id, limit=10, after=None)
        )
        assert colleague_view.id in {v.id for v in result.views}
        assert len(result.views) == 2

    async def test_a_superseded_version_leaves_the_list(
        self,
        workspaces: FakeWorkspaceRepository,
        views: FakeSavedViewRepository,
        workspace: Workspace,
    ) -> None:
        """**Live is derived from the supersession chain**, never stored — the
        list must show one entry, not two."""
        first = await _declare(workspaces, views, workspace.id)
        revision = await ReviseSavedViewUseCase(workspaces=workspaces, saved_views=views).execute(
            ReviseSavedViewInput(
                workspace_id=workspace.id, saved_view_id=first.id, created_by=COLLEAGUE
            ),
            now=MOMENT + timedelta(hours=1),
        )
        result = await ListSavedViewsUseCase(workspaces=workspaces, saved_views=views).execute(
            ListSavedViewsInput(workspace_id=workspace.id, limit=10, after=None)
        )
        assert [v.id for v in result.views] == [revision.id]

    async def test_a_retired_view_leaves_the_list_but_stays_fetchable(
        self,
        workspaces: FakeWorkspaceRepository,
        views: FakeSavedViewRepository,
        workspace: Workspace,
    ) -> None:
        """Retired, never deleted: a view that explained a decision must still
        explain it afterwards."""
        first = await _declare(workspaces, views, workspace.id)
        await RetireSavedViewUseCase(workspaces=workspaces, saved_views=views).execute(
            RetireSavedViewInput(workspace_id=workspace.id, saved_view_id=first.id),
            now=MOMENT + timedelta(days=1),
        )
        listed = await ListSavedViewsUseCase(workspaces=workspaces, saved_views=views).execute(
            ListSavedViewsInput(workspace_id=workspace.id, limit=10, after=None)
        )
        fetched = await GetSavedViewUseCase(workspaces=workspaces, saved_views=views).execute(
            workspace.id, first.id
        )
        assert listed.views == []
        assert fetched is not None and fetched.is_retired

    async def test_another_workspaces_views_are_never_listed(
        self,
        workspaces: FakeWorkspaceRepository,
        views: FakeSavedViewRepository,
        workspace: Workspace,
    ) -> None:
        other, _ = Workspace.create(name="Other", created_by=COLLEAGUE)
        await workspaces.add(other)
        await _declare(workspaces, views, workspace.id, name="Mine")
        await _declare(workspaces, views, other.id, name="Theirs")
        result = await ListSavedViewsUseCase(workspaces=workspaces, saved_views=views).execute(
            ListSavedViewsInput(workspace_id=workspace.id, limit=10, after=None)
        )
        assert [v.name for v in result.views] == ["Mine"]

    async def test_has_more_is_set_without_returning_the_extra_row(
        self,
        workspaces: FakeWorkspaceRepository,
        views: FakeSavedViewRepository,
        workspace: Workspace,
    ) -> None:
        for index in range(3):
            await _declare(
                workspaces,
                views,
                workspace.id,
                name=f"View {index}",
                at=MOMENT + timedelta(minutes=index),
            )
        result = await ListSavedViewsUseCase(workspaces=workspaces, saved_views=views).execute(
            ListSavedViewsInput(workspace_id=workspace.id, limit=2, after=None)
        )
        assert len(result.views) == 2
        assert result.has_more is True

    async def test_the_page_is_newest_first(
        self,
        workspaces: FakeWorkspaceRepository,
        views: FakeSavedViewRepository,
        workspace: Workspace,
    ) -> None:
        for index in range(3):
            await _declare(
                workspaces,
                views,
                workspace.id,
                name=f"View {index}",
                at=MOMENT + timedelta(minutes=index),
            )
        result = await ListSavedViewsUseCase(workspaces=workspaces, saved_views=views).execute(
            ListSavedViewsInput(workspace_id=workspace.id, limit=10, after=None)
        )
        assert [v.name for v in result.views] == ["View 2", "View 1", "View 0"]


class TestGetting:
    async def test_absence_is_an_answer_rather_than_an_error(
        self,
        workspaces: FakeWorkspaceRepository,
        views: FakeSavedViewRepository,
        workspace: Workspace,
    ) -> None:
        """The contract's own words. The endpoint turns `None` into a 404; the
        read does not pretend it failed."""
        found = await GetSavedViewUseCase(workspaces=workspaces, saved_views=views).execute(
            workspace.id, uuid4()
        )
        assert found is None

    async def test_another_workspaces_view_is_invisible(
        self,
        workspaces: FakeWorkspaceRepository,
        views: FakeSavedViewRepository,
        workspace: Workspace,
    ) -> None:
        other, _ = Workspace.create(name="Other", created_by=COLLEAGUE)
        await workspaces.add(other)
        theirs = await _declare(workspaces, views, other.id)
        found = await GetSavedViewUseCase(workspaces=workspaces, saved_views=views).execute(
            workspace.id, theirs.id
        )
        assert found is None
