"""Declaring which companies the customer wants watched.

The fifth write in the module, and the first that anybody downstream hears
about. The discipline is unchanged — it records a complete statement as a new
version — and one thing is added: **it announces that the statement changed.**

### The write and the announcement commit together, or neither does

The event is published on the **request's own session**, inside the same
transaction as the row. That is the whole point of the transactional outbox:
an event published before its cause committed announces something that may
never have happened, and a row committed without its event leaves a consumer
permanently behind. Neither failure is recoverable by retrying.

### It announces every accepted declaration

Including one that removes the last account, and one whose content happens to
match the previous version. Deciding that a restatement changes nothing worth
acting on requires knowing **what has already been synchronized** — a fact
Provider Platform holds and this module does not. Suppressing an event here to
save a consumer some work would be this module reasoning about synchronization
([ADR-0036](../../../../docs/architecture/adr/0036-target-account-contract.md)).
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import UUID, uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from modules.commercial_profile.application.ports import TargetAccountListRepository
from modules.commercial_profile.domain.declaration import (
    UNDECLARED,
    CommercialProfileError,
)
from modules.commercial_profile.domain.events import TargetAccountsChanged
from modules.commercial_profile.domain.target_accounts import (
    TargetAccount,
    TargetAccountList,
    first_target_accounts,
)
from signora_platform.event_bus import EventPublisher

PRODUCER_MODULE = "commercial_profile"


def _changed(
    declaration: TargetAccountList, now: datetime, causation_id: UUID | None
) -> TargetAccountsChanged:
    """The announcement, built from the declaration that was just stored.

    Derived from the saved aggregate rather than from the request, so the
    version announced is always the version written — there is no arrangement
    in which the two can disagree.
    """
    return TargetAccountsChanged(
        event_id=uuid4(),
        workspace_id=declaration.workspace_id,
        occurred_at=now,
        declaration_version=declaration.version,
        causation_id=causation_id,
    )


class TargetAccountsVersionConflictError(CommercialProfileError):
    """Somebody else changed the watch list since this caller read it."""

    def __init__(self, *, expected: int, actual: int) -> None:
        self.expected = expected
        self.actual = actual
        super().__init__(
            f"your list of accounts is at version {actual}, not {expected}. Somebody "
            "else changed it since you opened this page — reload to see their version "
            "before saving yours, so neither of you loses work."
        )


@dataclass(frozen=True, slots=True)
class DeclareTargetAccountsInput:
    workspace_id: UUID
    accounts: tuple[TargetAccount, ...]
    #: The version the caller believes it is replacing. `0` declares the first
    #: list, and is the only value that may be sent by a caller who has never
    #: read one.
    expected_version: int
    #: Taken from the verified caller by the interface layer. There is no
    #: field a request could use to name somebody else as the author.
    actor_id: UUID


class DeclareTargetAccounts:
    def __init__(
        self,
        *,
        repository: TargetAccountListRepository,
        publisher: EventPublisher,
        session: AsyncSession,
        clock: Callable[[], datetime] = lambda: datetime.now(UTC),
    ) -> None:
        self._repository = repository
        self._publisher = publisher
        # The caller's session, not one of this module's making. The row and
        # the event have to land in the same transaction.
        self._session = session
        self._clock = clock

    async def execute(
        self,
        request: DeclareTargetAccountsInput,
        *,
        correlation_id: UUID,
        causation_id: UUID | None = None,
    ) -> TargetAccountList:
        current = await self._repository.current(request.workspace_id)
        actual = current.version if current is not None else UNDECLARED
        if actual != request.expected_version:
            raise TargetAccountsVersionConflictError(
                expected=request.expected_version, actual=actual
            )

        now = self._clock()
        declaration = (
            first_target_accounts(
                request.workspace_id,
                request.accounts,
                id=uuid4(),
                by=request.actor_id,
                now=now,
            )
            if current is None
            else current.revise(request.accounts, id=uuid4(), by=request.actor_id, now=now)
        )
        await self._repository.save(declaration)

        # **After the save, before the commit.** The publisher writes to the
        # outbox on this same session; the relay is what puts it on the bus,
        # and it only ever sees rows that committed.
        await self._publisher.publish(
            # The platform's `PublishableEvent` Protocol declares settable
            # members, which a frozen domain event cannot satisfy. A known
            # platform finding with an open RFC, carried the same way at every
            # other publish site in the codebase rather than worked around —
            # unfreezing this event to please a type checker would break the
            # immutability the architecture actually requires.
            [_changed(declaration, now, causation_id)],  # type: ignore[list-item]
            session=self._session,
            producer_module=PRODUCER_MODULE,
            correlation_id=correlation_id,
        )
        return declaration
