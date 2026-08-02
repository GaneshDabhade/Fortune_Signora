"""Synchronise the companies a customer asked Signora to watch.

**The module's first real input.** `RunProviderSync` has taken a `subject`
since M2.1 and nothing outside the Provider Simulation Framework has ever
supplied one; every company the platform has processed arrived from a seeder.
This is where a customer's own answer to *which companies* starts costing
money.

**Specified by
[ADR-0036](../../../../docs/architecture/adr/0036-target-account-contract.md),
and the two rules that decide the shape are §4 and §7.**

The event is the *trigger* and the port is the *payload*: the envelope names a
workspace and a version, and the whole declaration is read through
`TargetAccountReader` on demand. Nothing about accounts travels on the bus, so
adding a field to a declaration is never an event-contract change.

**Provider Platform computes its own delta**, against what it has actually
read rather than against the previous declaration. Those are different sets,
and only one of them is this module's to know.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Protocol
from uuid import UUID

from modules.commercial_profile.public import TargetAccountReader
from modules.provider_platform.application.ports import TargetSyncStateRepository
from modules.provider_platform.domain.targets import (
    DeclaredAccount,
    subjects_needing_sync,
)
from signora_platform.observability import get_logger

logger = get_logger(__name__)


class SyncDispatcher(Protocol):
    """How one company's first read is started.

    **A port because the mechanism is infrastructure and the decision is not
    this use case's.** What matters here is that each company is read
    *somewhere else* — a declaration of fifty companies must not become fifty
    paged HTTP conversations inside one event handler.
    """

    async def sync(self, *, workspace_id: UUID, subject: str, correlation_id: UUID) -> None: ...


@dataclass(frozen=True, slots=True)
class SyncDeclaredTargetsInput:
    workspace_id: UUID
    #: The version the event announced. Compared against what this module has
    #: already acted on — never trusted as *the* current version, because the
    #: declaration may have moved on since it was published.
    declaration_version: int


@dataclass(frozen=True, slots=True)
class SyncDeclaredTargetsResult:
    """What the run decided, in terms a caller can log and a test can assert.

    **`skipped` is a first-class outcome, not an error.** Three ordinary
    things produce no work — a stale event, a workspace that has declared
    nothing, and a declaration whose companies have all been read — and
    collapsing them into *"nothing happened"* would make the one case worth
    investigating indistinguishable from the two that are routine.
    """

    #: Companies dispatched for a first read, in the customer's own order.
    dispatched: tuple[str, ...]
    #: Why nothing was dispatched, when nothing was. `None` when work was done.
    skipped: str | None = None
    #: The version now recorded as acted-on. `None` when the run changed nothing.
    acted_on: int | None = None


#: An event announcing a version this module has already acted on.
STALE = "stale"
#: The workspace has never declared a target account list. Distinct from
#: declaring an empty one, which is an instruction rather than a silence.
NEVER_DECLARED = "never_declared"
#: Every declared company has already been read at least once.
NOTHING_NEW = "nothing_new"


class SyncDeclaredTargets:
    """Read the declaration, decide what has never been fetched, dispatch it."""

    def __init__(
        self,
        *,
        targets: TargetAccountReader,
        state: TargetSyncStateRepository,
        dispatch: SyncDispatcher,
    ) -> None:
        self._targets = targets
        self._state = state
        self._dispatch = dispatch

    async def execute(
        self, request: SyncDeclaredTargetsInput, *, correlation_id: UUID
    ) -> SyncDeclaredTargetsResult:
        state = await self._state.get(request.workspace_id)

        # **§7, and it is checked before anything is read.** Two declarations
        # in quick succession are two workspace-level events, and nothing
        # orders them against each other — so version 5 arriving after 6 has
        # been handled must do nothing at all, not even a read.
        if state.is_stale(request.declaration_version):
            logger.info(
                "target sync skipped: stale declaration",
                extra={
                    "workspace_id": str(request.workspace_id),
                    "announced": request.declaration_version,
                    "already_acted_on": state.declaration_version,
                },
            )
            return SyncDeclaredTargetsResult(dispatched=(), skipped=STALE)

        view = await self._targets.current(request.workspace_id)
        if view is None:
            return SyncDeclaredTargetsResult(dispatched=(), skipped=NEVER_DECLARED)

        # **The version acted on is the one that was read, not the one that
        # was announced.** A declaration can move on between publication and
        # handling, and recording the announced version would claim this run
        # had seen a list it never read — which would then let the newer
        # event be discarded as stale. The port publishes its version for
        # exactly this comparison.
        declared = tuple(
            DeclaredAccount(id=account.id, subject=account.name) for account in view.accounts
        )
        already_read = await self._state.subjects_with_a_position(request.workspace_id)
        needing = subjects_needing_sync(declared, already_read)

        if not needing:
            await self._state.save(replace(state, declaration_version=view.version))
            return SyncDeclaredTargetsResult(
                dispatched=(), skipped=NOTHING_NEW, acted_on=view.version
            )

        for subject in needing:
            await self._dispatch.sync(
                workspace_id=request.workspace_id,
                subject=subject,
                correlation_id=correlation_id,
            )

        # **Recorded after dispatch, deliberately.** If this fails, the event
        # redelivers, the delta is recomputed against the same watermarks and
        # the same companies are dispatched again — wasteful once, and every
        # layer below is idempotent. Recording first and failing to dispatch
        # would lose the work silently, and nothing downstream would notice a
        # company that was never fetched.
        await self._state.save(replace(state, declaration_version=view.version))

        logger.info(
            "target sync dispatched",
            extra={
                "workspace_id": str(request.workspace_id),
                "subjects": len(needing),
                "declaration_version": view.version,
            },
        )
        return SyncDeclaredTargetsResult(dispatched=needing, acted_on=view.version)


__all__ = [
    "NEVER_DECLARED",
    "NOTHING_NEW",
    "STALE",
    "SyncDeclaredTargets",
    "SyncDeclaredTargetsInput",
    "SyncDeclaredTargetsResult",
    "SyncDispatcher",
]
