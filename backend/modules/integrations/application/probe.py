"""Asking a connection whether it still works.

**The connection surface has always answered from records.** A grant exists,
it has not expired, the state is `CONNECTED` — and none of that is evidence.
The commonest integration failure is a credential that authenticates perfectly
and lacks a permission it had yesterday, and no record anywhere can see it.

**So the platform makes a real call and records what happened.** That is the
only thing that can distinguish *"the connection looks right"* from *"the
connection works"*, and `ConnectionState.VALIDATED` has been waiting for it
since the module was written.

**Nothing enters the pipeline.** The probe reads, classifies and discards: no
raw record, no claim, no event, no watermark. It answers one question about the
connection and has no opinion about the customer's data — which is why it can
exist while [C-326](../../../../docs/LANE_COORDINATION.md) is unruled. The
source port and the runner decide how a customer's records *travel*; this
decides whether the door is open.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Protocol
from uuid import UUID, uuid4

from modules.integrations.application.disconnect import ConnectionNotFound
from modules.integrations.application.ports import ConnectedAccountRepository
from modules.integrations.application.resolve import (
    ConnectionUnusable,
    CredentialUnreadable,
    ResolveExecutionContext,
)
from modules.integrations.domain.execution import ExecutionContext
from modules.integrations.domain.connection import ConnectedAccount, ConnectionState
from modules.integrations.domain.health import ConnectionProbe, ProbeResult


@dataclass(frozen=True, slots=True)
class Reachability:
    """What one attempt established, in this module's vocabulary.

    **The adapter's return, not its exceptions.** A vendor's failure hierarchy
    stops at the adapter; what crosses this port is the classification, so
    nothing above it can branch on a `Crm*` type and nothing below has to
    invent a second one.
    """

    result: ProbeResult
    detail: str | None = None


class ConnectionReachability(Protocol):
    """Can this connection be used, right now, with this credential?

    **A port in the module that owns the language** (§6). Its implementations
    live in `infrastructure/` and know one vendor each; this signature knows
    none.
    """

    async def reach(self, context: ExecutionContext) -> Reachability:
        """Make the smallest real call the vendor offers, and classify it.

        **Smallest, deliberately.** The question is whether the door opens,
        and reading a customer's book of business to answer it would be both
        slow and a use of their quota for the platform's bookkeeping.

        **It does not raise for a failed probe.** A failure is the answer, not
        an error — an exception here would make an unreachable connection
        indistinguishable from a broken probe, and the second is the one
        nobody would notice.
        """
        ...


class ProbeStore(Protocol):
    """Where probes are kept. Append-only, because a probe is a fact (§2)."""

    async def record(self, probe: ConnectionProbe) -> None: ...

    async def recent_for(
        self, workspace_id: UUID, connected_account_id: UUID, *, limit: int
    ) -> tuple[ConnectionProbe, ...]:
        """The most recent probes, newest first.

        **Bounded, and the bound is the domain's.** Health needs exactly as
        many as the consecutive-failure threshold; fetching a connection's
        whole history to answer a yes/no is the N+1 in aggregate clothing that
        §14 calls a defect at write time.
        """
        ...


class ProbeConnection:
    """Probe one connection and record what happened.

    **The state change is a consequence, never the goal.** The probe's job is
    to produce a record; moving the connection is what the platform owes a
    customer once it *knows* something, and it happens only for a result that
    settles the question.

    **It does not report health, deliberately.** Health is derived from the
    probe *run*, and `IntegrationQueries` already derives it — a second method
    here would be the same behaviour in two places (§2), and the copy nobody
    calls is the one that drifts.
    """

    def __init__(
        self,
        accounts: ConnectedAccountRepository,
        resolver: ResolveExecutionContext,
        reachability: ConnectionReachability,
        probes: ProbeStore,
    ) -> None:
        self._accounts = accounts
        self._resolver = resolver
        self._reachability = reachability
        self._probes = probes

    async def execute(
        self, workspace_id: UUID, connected_account_id: UUID, *, at: datetime
    ) -> ConnectionProbe:
        """Establish whether this connection works, and record the answer.

        **Every outcome is recorded, including the ones that failed before a
        call was made.** A connection whose credential cannot be decrypted has
        told us something real about itself, and a probe that quietly returned
        nothing in that case would leave the least explicable failure the least
        observable — which is the inversion §17 exists to prevent.

        **Except one, and it is not an outcome.** A connection that does not
        exist has told us nothing about itself, and there is nothing for a
        probe to be *about* — `connection_probe.connected_account_id` is a
        foreign key, so recording one would fail at the database anyway and
        reach the caller as a `500` for a question whose answer is `404`.
        """
        account = await self._accounts.get(workspace_id, connected_account_id)
        if account is None:
            # The 404-not-403 rule, one layer in: a caller who names a
            # connection in a workspace they cannot see learns nothing.
            raise ConnectionNotFound("no such connection in this workspace")
        try:
            context = await self._resolver.execute(
                workspace_id, connected_account_id, at=at
            )
        except ConnectionUnusable as exc:
            # The connection was never in a state to be asked. **Recorded
            # rather than skipped**: *"we did not try, and here is why"* is an
            # answer, and an absent probe is indistinguishable from one nobody
            # ran.
            return await self._record(
                workspace_id,
                connected_account_id,
                Reachability(_result_for(exc.state), str(exc)),
                at=at,
            )
        except CredentialUnreadable as exc:
            return await self._record(
                workspace_id,
                connected_account_id,
                Reachability(ProbeResult.CREDENTIAL_REJECTED, str(exc)),
                at=at,
            )

        reachability = await self._reachability.reach(context)
        probe = await self._record(
            workspace_id, connected_account_id, reachability, at=at
        )
        await self._apply(account, probe, at=at)
        return probe

    async def _record(
        self,
        workspace_id: UUID,
        connected_account_id: UUID,
        reachability: Reachability,
        *,
        at: datetime,
    ) -> ConnectionProbe:
        probe = ConnectionProbe(
            id=uuid4(),
            workspace_id=workspace_id,
            connected_account_id=connected_account_id,
            result=reachability.result,
            detail=reachability.detail,
            probed_at=at,
        )
        await self._probes.record(probe)
        return probe

    async def _apply(
        self, account: ConnectedAccount, probe: ConnectionProbe, *, at: datetime
    ) -> None:
        """Move the connection, when the probe settled something.

        **`VALIDATED` is earned here and nowhere else.** It is the difference
        between *a grant exists* and *a grant works*, and until this ran the
        state was unreachable — a value in an enum that no code path could
        produce.

        **A missing permission does not revoke anything.** The credential is
        fine; what changed is what the customer's user may do with it, and
        telling them to reconnect would waste their time and leave the
        connection exactly as broken. It surfaces as degraded health instead.
        """
        target = _TRANSITIONS[probe.result]
        if target is None or account.state is target:
            return
        # **The account `execute` already read, not a second read.** It is the
        # same unit of work, so nothing can have moved it — and re-reading it
        # invited a `ConnectionTransitionError` branch that could never fire,
        # which is Decorative Logic (§2). An illegal transition here would be
        # a real defect and the domain will raise rather than be caught.
        await self._accounts.save(account.transition(target, at=at, by=_PROBE_ACTOR_ID))


#: Who a probe's state change is attributed to.
#:
#: **The same constant and value `resolve.py` already uses for its unattended
#: renewals**, and declared here for the same reason it is declared there: the
#: convention is the shared thing, not the symbol. A probe is the platform's
#: own action, and attributing it to whichever customer last touched the
#: connection would put a name on something they did not do.
_PROBE_ACTOR_ID = UUID("00000000-0000-0000-0000-000000000001")


#: Which state each conclusive result moves the connection to, or `None` where
#: the probe learned something without changing what the connection *is*.
#:
#: **A table rather than a chain of `if`s**, matching `_ALLOWED` in the domain:
#: adding a result is a row, and a result nobody mapped is refused by the
#: lookup rather than by whichever branch happened to be written last.

_TRANSITIONS: dict[ProbeResult, ConnectionState | None] = {
    # **The only state a probe earns**, and it is the one the enum was written
    # for: a real call succeeded with this credential.
    ProbeResult.REACHABLE: ConnectionState.VALIDATED,
    # **A probe does not revoke a connection, and the first draft did.**
    # `REVOKED` means *the customer withdrew permission at the vendor* — its
    # reason reaches a screen as *permission withdrawn* — and a rejected
    # credential is not evidence of that. A rotated secret, an unreadable
    # stored material and a vendor having an authentication incident all look
    # identical here, and telling a customer they revoked Signora when they
    # did not is a worse failure than the one this slice set out to fix.
    #
    # **Degraded health carries it instead**, which is what the customer can
    # act on: *this is not working*, without a diagnosis nobody established.
    ProbeResult.CREDENTIAL_REJECTED: None,
    # The credential works. Nothing about the *connection* changed.
    ProbeResult.PERMISSION_MISSING: None,
    # The vendor is misbehaving, not the customer.
    ProbeResult.UNUSABLE_RESPONSE: None,
    ProbeResult.UNAVAILABLE: None,
}

def _result_for(state: ConnectionState) -> ProbeResult:
    """What an unusable connection's state means as a probe result.

    A revoked connection **is** a rejected credential; everything else — never
    connected, half-authorized, disconnected — is a connection nobody can
    conclude anything about, because nobody asked the vendor anything.
    """
    if state is ConnectionState.REVOKED:
        return ProbeResult.CREDENTIAL_REJECTED
    return ProbeResult.UNAVAILABLE
