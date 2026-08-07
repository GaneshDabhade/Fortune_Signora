"""The Saved View aggregate — **TASK-450, slice 2**.

`test_saved_view_contract.py` asserts the *shape* [TASK-449] published. These
assert the rules behind it: that a declaration is never edited, that the
author of a revision is the person who made it, that retirement is recorded
rather than reversed — **and the one that matters most, that this module still
does not know what a declaration means.**

[TASK-449]: ../../../../docs/BACKLOG.md
"""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID, uuid4

import pytest

from modules.workspace_tenancy.domain.exceptions import (
    EmptyDeclarationError,
    InvalidSavedViewNameError,
    SavedViewAlreadyRetiredError,
)
from modules.workspace_tenancy.domain.saved_view import (
    MAX_SAVED_VIEW_NAME_LENGTH,
    SavedView,
)

WORKSPACE = UUID("11111111-1111-4111-8111-111111111111")
AUTHOR = UUID("22222222-2222-4222-8222-222222222222")
COLLEAGUE = UUID("33333333-3333-4333-8333-333333333333")
NOW = datetime(2026, 8, 7, 9, 0, tzinfo=UTC)


def _view(**overrides: object) -> SavedView:
    kwargs: dict[str, object] = {
        "workspace_id": WORKSPACE,
        "name": "My accounts, contested first",
        "declaration": {"owner": "me", "sort": "contested"},
        "created_by": AUTHOR,
        "now": NOW,
    }
    kwargs.update(overrides)
    return SavedView.declare(**kwargs)  # type: ignore[arg-type]


class TestTheDeclarationStaysOpaque:
    """[D-091] — *"the storage layer never interprets the saved declaration
    itself"*. **These are the tests that fail if somebody adds validation.**"""

    @pytest.mark.parametrize(
        "declaration",
        [
            {"nonsense": object.__name__},
            {"sort": ["not", "a", "string"]},
            {"deeply": {"nested": {"and": {"meaningless": True}}}},
            {"": ""},
        ],
    )
    def test_any_shape_is_accepted(self, declaration: dict[str, object]) -> None:
        """**No key here means anything to this module**, so none of these can
        be refused without it learning what a filter is."""
        assert _view(declaration=declaration).declaration == declaration

    def test_the_only_refusal_is_that_there_is_no_question(self) -> None:
        with pytest.raises(EmptyDeclarationError):
            _view(declaration={})

    def test_no_error_exists_for_an_invalid_declaration(self) -> None:
        """⛔ **The absence is the assertion.** An `InvalidDeclarationError`
        would be this module claiming it can tell — and the first caller to
        catch it would make that claim load-bearing."""
        from modules.workspace_tenancy.domain import exceptions

        named = [name for name in dir(exceptions) if "Declaration" in name]
        assert named == ["EmptyDeclarationError"]

    def test_the_stored_declaration_cannot_be_changed_through_the_caller_s_mapping(
        self,
    ) -> None:
        """A frozen dataclass does not freeze the dict inside it. **Without the
        copy, a caller mutating what it passed in edits a stored view** — the
        immutability the contract promises, defeated by aliasing."""
        supplied = {"owner": "me"}
        view = _view(declaration=supplied)

        supplied["owner"] = "somebody else"

        assert view.declaration == {"owner": "me"}


class TestVersioning:
    def test_a_change_is_a_new_version_naming_the_one_it_replaces(self) -> None:
        first = _view()

        second = first.revise(declaration={"owner": "team"}, created_by=AUTHOR, now=NOW)

        assert second.supersedes == first.id
        assert second.id != first.id
        # The earlier reading survives, which is the whole reason for the chain.
        assert first.declaration == {"owner": "me", "sort": "contested"}

    def test_the_first_version_supersedes_nothing(self) -> None:
        assert _view().supersedes is None

    def test_a_revision_is_attributed_to_whoever_made_it(self) -> None:
        """§10 applied to people: **inheriting the original author would name
        somebody who was not involved in this change.**"""
        first = _view()

        second = first.revise(name="Contested accounts", created_by=COLLEAGUE, now=NOW)

        assert second.created_by == COLLEAGUE
        assert first.created_by == AUTHOR

    def test_revising_only_the_name_keeps_the_question(self) -> None:
        first = _view()
        second = first.revise(name="Renamed", created_by=AUTHOR, now=NOW)

        assert second.name == "Renamed"
        assert second.declaration == first.declaration

    def test_the_aggregate_is_frozen(self) -> None:
        view = _view()
        with pytest.raises(AttributeError):
            view.name = "edited"  # type: ignore[misc]

    def test_there_is_no_stored_live_flag(self) -> None:
        """**Live is derived from the chain, never stored** — a column beside
        it would be one fact twice, and they would disagree the first time a
        version landed (§2)."""
        fields = set(SavedView.__dataclass_fields__)
        assert not {name for name in fields if "live" in name or "current" in name}
        assert not {name for name in fields if "superseded_by" in name}


class TestRetirement:
    def test_retiring_records_when_rather_than_removing(self) -> None:
        retired = _view().retire(at=NOW)

        assert retired.retired_at == NOW
        assert retired.is_retired
        # Everything it explained is still readable.
        assert retired.declaration == {"owner": "me", "sort": "contested"}

    def test_retiring_twice_raises_rather_than_moving_the_timestamp(self) -> None:
        """**The first timestamp is the one that happened**, and re-stamping
        would quietly move a fact about the past."""
        retired = _view().retire(at=NOW)

        with pytest.raises(SavedViewAlreadyRetiredError):
            retired.retire(at=datetime(2026, 9, 1, tzinfo=UTC))

    def test_a_retired_view_is_not_revised(self) -> None:
        """Reviving through `revise` would make retirement reversible without
        saying so. The honest way back is a new declaration."""
        retired = _view().retire(at=NOW)

        with pytest.raises(SavedViewAlreadyRetiredError):
            retired.revise(created_by=AUTHOR, now=NOW)

    def test_is_retired_is_derived_from_the_timestamp(self) -> None:
        assert not _view().is_retired


class TestTheName:
    def test_it_is_trimmed(self) -> None:
        assert _view(name="  Contested  ").name == "Contested"

    @pytest.mark.parametrize("name", ["", "   ", "\n\t"])
    def test_a_view_needs_a_name_somebody_chose(self, name: str) -> None:
        with pytest.raises(InvalidSavedViewNameError):
            _view(name=name)

    def test_it_is_bounded(self) -> None:
        with pytest.raises(InvalidSavedViewNameError):
            _view(name="x" * (MAX_SAVED_VIEW_NAME_LENGTH + 1))

    def test_the_boundary_itself_is_accepted(self) -> None:
        assert len(_view(name="x" * MAX_SAVED_VIEW_NAME_LENGTH).name)


class TestIdentity:
    def test_the_caller_may_supply_it_so_a_retry_is_idempotent(self) -> None:
        chosen = uuid4()
        assert _view(saved_view_id=chosen).id == chosen

    def test_a_revision_belongs_to_the_same_workspace(self) -> None:
        """A version cannot move a view between tenants — the RLS policy
        forbids it at the table, and the aggregate does not offer it either."""
        first = _view()
        assert first.revise(created_by=AUTHOR, now=NOW).workspace_id == WORKSPACE
