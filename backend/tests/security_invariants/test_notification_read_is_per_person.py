"""**One person's read state is not another's, and the badge is bounded.**

📁 **[TASK-480](../../../docs/BACKLOG.md), on
[D-239](../../../docs/DECISION_REGISTER.md)** — `workspace_tenancy` owns
per-person, per-workspace notification state, following `person_preferences`.

## 🔴 Why this is a Security Invariant

⚡ **The narrowing is the guarantee.** 📁 492 §0: *"a NARROWING of tenant-owned,
never a parallel to it… one predicate is added."* ⛔ **A defect here does not
render a wrong number — it shows one person what another has and has not
read**, which is a disclosure inside a workspace where every other control
assumes the workspace is the boundary.

⚠️ **Two people in one workspace is the case that matters**, because tenant
isolation does not help: **they are legitimately in the same tenant, and only
the person predicate separates them.**
"""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

import pytest

from modules.workspace_tenancy.domain.notification_state import (
    CAP,
    NotificationRead,
    NotificationStateError,
    UnreadCount,
    unread,
)
from modules.workspace_tenancy.infrastructure.repositories import (
    SqlAlchemyNotificationReadRepository,
)
from modules.workspace_tenancy.public import (
    NotificationReadWriter,
    NotificationStateReader,
)

NOW = datetime(2026, 8, 16, 12, 0, tzinfo=UTC)


class TestTheBadgeIsBounded:
    """⚡ **The cap is in the domain so the QUERY can be bounded by it.**"""

    def test_a_count_below_the_cap_is_exact_and_not_capped(self) -> None:
        assert unread(total=3) == UnreadCount(value=3, capped=False)

    def test_exactly_the_cap_is_not_capped(self) -> None:
        """🔴 **The off-by-one that decides whether the badge reads `9` or `9+`.**"""
        assert unread(total=CAP) == UnreadCount(value=CAP, capped=False)

    def test_one_past_the_cap_is_capped(self) -> None:
        """⚡ **The extra row the query fetches is what distinguishes these two.**"""
        assert unread(total=CAP + 1) == UnreadCount(value=CAP, capped=True)

    def test_far_past_the_cap_is_indistinguishable_from_one_past(self) -> None:
        """✅ **Which is the point** — ⛔ **a query that counted further would be
        answering a question the badge cannot render.**"""
        assert unread(total=CAP + 1) == unread(total=10_000)

    def test_nothing_unread_is_zero_rather_than_absent(self) -> None:
        assert unread(total=0) == UnreadCount(value=0, capped=False)

    def test_a_negative_total_is_refused_rather_than_clamped(self) -> None:
        """🔴 **A negative badge means the derivation subtracted reads from a
        total it did not have** — ⛔ **a defect to surface, never a number to
        clamp to zero and render.**"""
        with pytest.raises(NotificationStateError, match="not a count"):
            unread(total=-1)

    def test_a_count_cannot_be_built_above_the_cap_directly(self) -> None:
        """⛔ **The constructor refuses it, not only the factory.**

        ⚡ **A repository building an `UnreadCount` by hand would bypass
        `unread()`** — and the value that reaches the badge is what matters.
        """
        with pytest.raises(NotificationStateError, match="exceeds the cap"):
            UnreadCount(value=CAP + 1, capped=True)

    def test_a_negative_count_cannot_be_built_directly_either(self) -> None:
        with pytest.raises(NotificationStateError, match="not a count"):
            UnreadCount(value=-1, capped=False)


class TestAReadIsAFactAndCarriesBothIdentities:
    def test_a_read_names_a_workspace_and_a_person(self) -> None:
        """🔴 **Both required, no defaults.**

        ⛔ **A read that names no workspace is a cross-tenant fact; one that
        names no person is the collective state D-239 refuses.**
        """
        read = NotificationRead(
            workspace_id=uuid4(),
            user_id=uuid4(),
            notification_id=uuid4(),
            read_at=NOW,
        )
        assert read.workspace_id is not None
        assert read.user_id is not None

    def test_a_naive_read_time_is_refused(self) -> None:
        """⚠️ **A time without a timezone is a claim about no particular
        moment**, and it would be the only one a report could not order.
        """
        with pytest.raises(NotificationStateError, match="without a timezone"):
            NotificationRead(
                workspace_id=uuid4(),
                user_id=uuid4(),
                notification_id=uuid4(),
                read_at=datetime(2026, 8, 16, 12, 0),  # noqa: DTZ001
            )

    def test_there_is_no_way_to_un_read_a_read(self) -> None:
        """⛔ **The absence IS the invariant, so it is asserted.**

        📁 **A read is a record of something that happened** ([§2](../../../CLAUDE.md)),
        the table has no `UPDATE` grant, and **a method offering one would
        promise what the database refuses.** ⚡ ***Mark as unread*, if the
        product ever asks for it, is a DELETE** — the row stops existing, which
        is the same shape as *an unread is the absence of a row*.
        """
        surface = {n for n in dir(NotificationRead) if not n.startswith("_")}

        assert not {n for n in surface if "unread" in n.lower() or "undo" in n.lower()}
        # ⚡ **Frozen, so a caller cannot edit the moment either.**
        read = NotificationRead(
            workspace_id=uuid4(), user_id=uuid4(), notification_id=uuid4(), read_at=NOW
        )
        with pytest.raises((AttributeError, TypeError)):
            read.read_at = NOW  # type: ignore[misc]


def _the_repository_is_a_reader(
    repository: SqlAlchemyNotificationReadRepository,
) -> NotificationStateReader:
    """🔴 **The structural check, and it is `mypy --strict` that performs it.**

    ⛔ **`hasattr` was the first version of this and it was decorative**: it
    passes for a method with the wrong signature, the wrong argument names or
    the wrong return type — ⚡ **which are exactly the three ways a port and its
    implementation drift.**

    ✅ **Returning the repository AS the protocol is the real assertion.**
    **`mypy` resolves it here, so a signature change on either side fails the
    type gate rather than waiting for slice ⓑ to import it.**
    """
    return repository


def _the_repository_is_a_writer(
    repository: SqlAlchemyNotificationReadRepository,
) -> NotificationReadWriter:
    """The same check for the write half."""
    return repository


class TestThePublishedContractAndTheImplementationCannotDrift:
    """🔴 **A `Protocol` is checked where it is CONSUMED, and nothing consumes
    this yet** — [TASK-480](../../../docs/BACKLOG.md) slice ⓑ builds the shell.

    ⛔ **So until a caller exists, the port and the repository can drift and
    `mypy` will not say a word**: structural typing verifies at the assignment,
    and there is no assignment. ⚡ **This is that assignment, written as a
    test**, so the contract is load-bearing from the moment it is published
    rather than from the moment somebody imports it.
    """

    def test_the_conformance_functions_exist_so_mypy_has_something_to_check(
        self,
    ) -> None:
        """⚡ **The functions above are the check; this makes their DELETION
        visible in a test run** — ⛔ otherwise removing them would silently
        remove the only place the protocols are resolved.
        """
        assert _the_repository_is_a_reader.__annotations__["return"] is not None
        assert _the_repository_is_a_writer.__annotations__["return"] is not None

    def test_the_port_offers_no_way_to_unread(self) -> None:
        """⛔ **The absence is the contract.** ⚡ **A `mark_unread` added here
        would promise what the table's missing `UPDATE` grant refuses.**"""
        from modules.workspace_tenancy.public import NotificationReadWriter

        surface = {n for n in dir(NotificationReadWriter) if not n.startswith("_")}
        assert surface == {"mark_read"}, (
            "a new method on the published writer may promise something the "
            "database refuses — this table has no UPDATE grant"
        )
