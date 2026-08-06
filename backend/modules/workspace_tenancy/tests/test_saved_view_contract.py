"""The saved view's published contract — **TASK-449, and only the contract.**

**No table, no endpoint, no implementation**, which is the row's deliverable
rather than a staging post: a consumer lane compiles, type-checks and tests
against these types before a row is ever persisted.

**So what is there to test?** The properties that make the contract worth
publishing — and every one of them is a property a later implementation could
quietly break. **A `Protocol` nothing asserts is a suggestion**, and the four
non-responsibilities [455](../../../../docs/architecture/455-context-definitions-r02-r03.md)
names are exactly the kind that erode *"one reasonable exception at a time"*.
"""

from __future__ import annotations

import inspect
from datetime import UTC, datetime
from uuid import uuid4

import pytest
from pydantic import ValidationError

from modules.workspace_tenancy.public import (
    SavedViewListView,
    SavedViewReader,
    SavedViewView,
    SavedViewWriter,
)

WORKSPACE = uuid4()
AUTHOR = uuid4()
NOW = datetime(2026, 8, 6, 9, 0, tzinfo=UTC)


def view(**overrides: object) -> SavedViewView:
    fields: dict[str, object] = {
        "id": uuid4(),
        "workspace_id": WORKSPACE,
        "name": "My accounts, contested first",
        "declaration": {"owner": "mine", "sort": "contested"},
        "created_by": AUTHOR,
        "created_at": NOW,
    }
    fields.update(overrides)
    return SavedViewView(**fields)


class TestTheDeclarationIsOpaque:
    """⛔ *"Never parses, validates, executes, ranks or optimises a
    declaration. Never knows what a filter or a sort means."*

    **The moment this store could call a declaration invalid, it would be
    responsible for another module's semantics** — the boundary
    `commercial_profile` keeps by never reading the pipeline.
    """

    def test_any_shape_of_declaration_is_accepted(self) -> None:
        for declaration in ({}, {"owner": "mine"}, {"nested": {"anything": [1, 2]}}):
            assert view(declaration=declaration).declaration == declaration

    def test_the_contract_names_no_query_vocabulary(self) -> None:
        """**The check that would fail if somebody added `filters` or `sort`
        as fields.** A store with a `sort` column has learned what sorting is,
        and the next screen's sort will not fit it."""
        fields = set(SavedViewView.model_fields)

        assert not fields & {"filters", "sort", "query", "columns", "criteria", "segment"}

    def test_it_holds_no_results(self) -> None:
        """⛔ *"Never materialises results."* A saved view is a question
        somebody wrote down; running it belongs to whoever owns the answer."""
        assert not set(SavedViewView.model_fields) & {"results", "items", "matches", "count"}


class TestAChangeIsAVersionAndNeverAnEdit:
    def test_a_view_cannot_be_mutated(self) -> None:
        """`IcpDeclaration`'s shape for its reason: a colleague who acted on a
        view last week needs it to still mean what it meant."""
        saved = view()

        with pytest.raises(ValidationError):
            saved.name = "something else"  # type: ignore[misc]

    def test_a_new_version_names_the_one_it_replaces(self) -> None:
        first = view()
        second = view(supersedes=first.id)

        assert second.supersedes == first.id
        assert first.supersedes is None

    def test_retiring_is_recorded_rather_than_deleting(self) -> None:
        """A view that explained a decision must still explain it afterwards."""
        retired = view(retired_at=NOW)

        assert retired.retired_at == NOW

    def test_the_writer_offers_no_update(self) -> None:
        """⛔ **The absence is the design.** A port offering `update` would
        make immutability a rule somebody has to remember rather than one the
        contract cannot express."""
        offered = {
            name for name, _ in inspect.getmembers(SavedViewWriter) if not name.startswith("_")
        }

        assert "update" not in offered
        assert {"save", "retire"} <= offered


class TestReadingAndWritingAreSeparateGrants:
    def test_the_reader_cannot_write(self) -> None:
        """Every member reads the views their workspace shares; creating one
        is an act with an author. **One port would make every reader a
        writer.**"""
        offered = {
            name for name, _ in inspect.getmembers(SavedViewReader) if not name.startswith("_")
        }

        assert not offered & {"save", "retire", "update", "delete"}

    def test_every_read_is_workspace_scoped(self) -> None:
        """**A read without a workspace is a read across tenants.** The
        signature is where that is refused, not the implementation."""
        for method in (SavedViewReader.by_id, SavedViewReader.live):
            assert "workspace_id" in inspect.signature(method).parameters

    def test_listing_is_paged(self) -> None:
        """§7 — every collection. Retrofitting pagination onto a shipped read
        is a breaking change; starting paginated costs nothing."""
        parameters = inspect.signature(SavedViewReader.live).parameters

        assert {"after", "limit"} <= set(parameters)
        assert set(SavedViewListView.model_fields) >= {"items", "has_more", "next_position"}
