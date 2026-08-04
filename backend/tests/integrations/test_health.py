"""Whether a connection actually works, and what the platform does about it.

**The scenario every test here is about.** A customer's HubSpot user loses a
permission. The token still authenticates, the grant has not expired, the state
is `CONNECTED`, and the Connection Center says everything is fine — because
every answer it gives is derived from records, and no record can see this.

**Two halves, deliberately separated.** `health_from` decides what a run of
probes *means* and touches nothing; `ProbeConnection` decides what to *do* about
it. The first is where the two-consecutive-failures rule lives and is tested
without a database, a vendor or a clock.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

import pytest

from modules.integrations.application.disconnect import ConnectionNotFound
from modules.integrations.application.probe import ProbeConnection, Reachability
from modules.integrations.application.queries import Attention, IntegrationQueries
from modules.integrations.application.resolve import (
    ExecutionContext,
    ResolveExecutionContext,
)
from modules.integrations.domain.connection import ConnectedAccount, ConnectionState
from modules.integrations.domain.grant import Credential, IntegrationGrant
from modules.integrations.domain.health import (
    ConnectionHealth,
    ConnectionProbe,
    ProbeResult,
    health_from,
)
from tests.integrations.test_resolve import FakeAccounts, FakeGrants, FakeSecrets

NOW = datetime(2026, 8, 4, 12, 0, tzinfo=UTC)
WORKSPACE = uuid4()
ACTOR = uuid4()


def _probe(result: ProbeResult, *, ago: int = 0) -> ConnectionProbe:
    return ConnectionProbe(
        id=uuid4(),
        workspace_id=WORKSPACE,
        connected_account_id=uuid4(),
        result=result,
        detail=None if result is ProbeResult.REACHABLE else "because",
        probed_at=NOW - timedelta(minutes=ago),
    )


class TestWhatARunOfProbesMeans:
    """`health_from`, newest first. **No I/O, no clock, no vendor.**"""

    def test_nothing_tried_is_not_healthy(self) -> None:
        """**The distinction the whole slice rests on.** An unprobed
        connection is one nobody has established anything about, and calling
        that healthy is the same lie the record-derived view already tells."""
        assert health_from(()) is ConnectionHealth.UNKNOWN

    def test_the_last_call_succeeded(self) -> None:
        assert health_from((_probe(ProbeResult.REACHABLE),)) is ConnectionHealth.HEALTHY

    @pytest.mark.parametrize(
        "conclusive",
        [
            ProbeResult.CREDENTIAL_REJECTED,
            ProbeResult.PERMISSION_MISSING,
            ProbeResult.UNUSABLE_RESPONSE,
        ],
    )
    def test_a_conclusive_failure_degrades_on_its_own(
        self, conclusive: ProbeResult
    ) -> None:
        """**A rejected credential is not flaky.** Waiting for a second one
        would leave a customer's data not flowing while a dashboard said
        nothing was wrong, which is the failure this slice exists to end."""
        assert health_from((_probe(conclusive),)) is ConnectionHealth.DEGRADED

    def test_one_transient_failure_is_not_a_verdict(self) -> None:
        """A vendor having a bad minute must not send somebody to reconnect a
        CRM that is fine. The previous success still stands."""
        probes = (_probe(ProbeResult.UNAVAILABLE), _probe(ProbeResult.REACHABLE, ago=5))

        assert health_from(probes) is ConnectionHealth.HEALTHY

    def test_two_consecutive_transient_failures_are(self) -> None:
        """The approved screen's own rule: *"two consecutive failures"*."""
        probes = (
            _probe(ProbeResult.UNAVAILABLE),
            _probe(ProbeResult.UNAVAILABLE, ago=5),
            _probe(ProbeResult.REACHABLE, ago=10),
        )

        assert health_from(probes) is ConnectionHealth.DEGRADED

    def test_a_success_between_two_failures_breaks_the_run(self) -> None:
        """**Consecutive means consecutive.** Counting failures without
        requiring them to be adjacent would degrade a connection that has been
        working all week because it timed out twice on Tuesday."""
        probes = (
            _probe(ProbeResult.UNAVAILABLE),
            _probe(ProbeResult.REACHABLE, ago=5),
            _probe(ProbeResult.UNAVAILABLE, ago=10),
        )

        assert health_from(probes) is ConnectionHealth.HEALTHY

    def test_a_lone_transient_failure_with_no_history_is_unknown(self) -> None:
        """**Not healthy, and this is the edge worth stating.** One
        inconclusive probe and nothing behind it means nothing has ever been
        established — reporting it as healthy would manufacture an answer out
        of a failure."""
        assert health_from((_probe(ProbeResult.UNAVAILABLE),)) is ConnectionHealth.UNKNOWN

    def test_a_successful_probe_carries_nothing_to_explain(self) -> None:
        """A detail on a success is a contradiction the type refuses, rather
        than one a reader has to notice."""
        with pytest.raises(ValueError):
            ConnectionProbe(
                id=uuid4(),
                workspace_id=WORKSPACE,
                connected_account_id=uuid4(),
                result=ProbeResult.REACHABLE,
                detail="but also it failed",
                probed_at=NOW,
            )

    def test_only_the_inconclusive_result_is_inconclusive(self) -> None:
        """`is_conclusive` is what the two-consecutive rule keys on, so a new
        result defaulting to the wrong side would silently change the rule."""
        inconclusive = [r for r in ProbeResult if not r.is_conclusive]

        assert inconclusive == [ProbeResult.UNAVAILABLE]


class FakeReachability:
    """The vendor, scripted. **Never a real model of HubSpot** — what a
    connection does when the vendor rejects it is deterministic behaviour, and
    §10 keeps that on the fakes side of the line."""

    def __init__(self, *results: Reachability) -> None:
        self._results = list(results)
        self.calls = 0

    async def reach(self, context: ExecutionContext) -> Reachability:
        self.calls += 1
        return self._results.pop(0) if self._results else Reachability(ProbeResult.REACHABLE)


class FakeProbes:
    def __init__(self, *existing: ConnectionProbe) -> None:
        self.recorded: list[ConnectionProbe] = list(existing)

    async def record(self, probe: ConnectionProbe) -> None:
        self.recorded.insert(0, probe)

    async def recent_for(
        self, workspace_id: UUID, connected_account_id: UUID, *, limit: int
    ) -> tuple[ConnectionProbe, ...]:
        return tuple(
            p
            for p in self.recorded
            if p.workspace_id == workspace_id
            and p.connected_account_id == connected_account_id
        )[:limit]


def _account(
    state: ConnectionState = ConnectionState.CONNECTED, **kw: object
) -> ConnectedAccount:
    defaults: dict[str, object] = {
        "id": uuid4(),
        "workspace_id": WORKSPACE,
        "integration": "hubspot",
        "external_account_id": "1234567",
        "endpoint": None,
        "label": "Acme HubSpot",
        "state": state,
        "connected_at": NOW,
        "actor_id": ACTOR,
    }
    defaults.update(kw)
    return ConnectedAccount(**defaults)  # type: ignore[arg-type]


def _grant(account: ConnectedAccount) -> IntegrationGrant:
    return IntegrationGrant(
        id=uuid4(),
        workspace_id=account.workspace_id,
        connected_account_id=account.id,
        secret_ref="vault://grants/1",
        scopes=("crm.objects.companies.read",),
        expires_at=None,
        refreshable=True,
        revoked_at=None,
        actor_id=ACTOR,
    )


def _prober(
    account: ConnectedAccount,
    reachability: FakeReachability,
    probes: FakeProbes | None = None,
    *,
    accounts: FakeAccounts | None = None,
) -> ProbeConnection:
    store = accounts or FakeAccounts(account)
    return ProbeConnection(
        store,
        ResolveExecutionContext(store, FakeGrants(_grant(account)), FakeSecrets()),
        reachability,
        probes or FakeProbes(),
    )


class TestProbingAConnection:
    async def test_a_working_connection_earns_validated(self) -> None:
        """**`VALIDATED` has been in the enum since the module was written and
        no code path could produce it.** Its docstring describes exactly this
        call — *"a real call succeeded with it"* — and until now the state was
        a value nothing could reach."""
        account = _account(ConnectionState.CONNECTED)
        accounts = FakeAccounts(account)
        prober = _prober(account, FakeReachability(), accounts=accounts)

        probe = await prober.execute(WORKSPACE, account.id, at=NOW)

        assert probe.result is ProbeResult.REACHABLE
        assert (await accounts.get(WORKSPACE, account.id)).state is (  # type: ignore[union-attr]
            ConnectionState.VALIDATED
        )

    async def test_a_rejected_credential_does_not_revoke_the_connection(self) -> None:
        """**The first draft revoked it, and that was wrong.** `REVOKED` means
        *the customer withdrew permission at the vendor* and reaches a screen
        as *permission withdrawn* — while a rotated secret, an unreadable
        stored material and a vendor authentication incident are
        indistinguishable from a `401`.

        Telling a customer they revoked Signora when they did not is a worse
        failure than the one this slice set out to fix. **Degraded health says
        what is true**: it is not working.
        """
        account = _account(ConnectionState.VALIDATED)
        accounts = FakeAccounts(account)
        probes = FakeProbes()
        prober = _prober(
            account,
            FakeReachability(Reachability(ProbeResult.CREDENTIAL_REJECTED, "401")),
            probes,
            accounts=accounts,
        )

        await prober.execute(WORKSPACE, account.id, at=NOW)

        assert (await accounts.get(WORKSPACE, account.id)).state is (  # type: ignore[union-attr]
            ConnectionState.VALIDATED
        )
        assert health_from(tuple(probes.recorded)) is ConnectionHealth.DEGRADED

    async def test_a_missing_permission_does_not_revoke_anything(self) -> None:
        """**The credential is fine.** Telling a customer to reconnect would
        waste their time and leave the connection exactly as broken — the
        distinction the adapter's own taxonomy draws between a `401` and a
        `403`, preserved all the way to what the platform does."""
        account = _account(ConnectionState.VALIDATED)
        accounts = FakeAccounts(account)
        probes = FakeProbes()
        prober = _prober(
            account,
            FakeReachability(Reachability(ProbeResult.PERMISSION_MISSING, "403")),
            probes,
            accounts=accounts,
        )

        await prober.execute(WORKSPACE, account.id, at=NOW)

        assert (await accounts.get(WORKSPACE, account.id)).state is (  # type: ignore[union-attr]
            ConnectionState.VALIDATED
        )
        assert probes.recorded[0].result is ProbeResult.PERMISSION_MISSING

    async def test_a_transient_failure_changes_no_state(self) -> None:
        account = _account(ConnectionState.VALIDATED)
        accounts = FakeAccounts(account)
        prober = _prober(
            account,
            FakeReachability(Reachability(ProbeResult.UNAVAILABLE, "timeout")),
            accounts=accounts,
        )

        await prober.execute(WORKSPACE, account.id, at=NOW)

        assert (await accounts.get(WORKSPACE, account.id)).state is (  # type: ignore[union-attr]
            ConnectionState.VALIDATED
        )

    async def test_a_connection_that_cannot_be_asked_is_still_recorded(self) -> None:
        """*"We did not try, and here is why"* is an answer. **An absent probe
        is indistinguishable from one nobody ran**, which is the inversion §17
        exists to prevent."""
        account = _account(ConnectionState.DISCONNECTED)
        reachability = FakeReachability()
        probes = FakeProbes()
        prober = _prober(account, reachability, probes)

        probe = await prober.execute(WORKSPACE, account.id, at=NOW)

        assert reachability.calls == 0, "nothing should have been asked"
        assert probes.recorded == [probe]

    async def test_a_connection_that_does_not_exist_is_not_probed(self) -> None:
        """**Not an outcome, and not a row.** `connected_account_id` is a
        foreign key, so recording a probe for a connection that is not there
        would fail at the database and reach the caller as a `500` for a
        question whose answer is `404`."""
        probes = FakeProbes()
        prober = ProbeConnection(
            FakeAccounts(None),
            ResolveExecutionContext(FakeAccounts(None), FakeGrants(None), FakeSecrets()),
            FakeReachability(),
            probes,
        )

        with pytest.raises(ConnectionNotFound):
            await prober.execute(WORKSPACE, uuid4(), at=NOW)

        assert probes.recorded == []

    async def test_a_revoked_connection_is_recorded_as_a_rejected_credential(self) -> None:
        """**Not `UNAVAILABLE`.** A connection the customer withdrew at the
        vendor has established something: the credential will not work. Filing
        it as inconclusive would let two of them read as *nothing has been
        established* rather than *this is not working*."""
        account = _account(ConnectionState.REVOKED)
        probes = FakeProbes()
        prober = _prober(account, FakeReachability(), probes)

        probe = await prober.execute(WORKSPACE, account.id, at=NOW)

        assert probe.result is ProbeResult.CREDENTIAL_REJECTED

    async def test_a_credential_that_cannot_be_read_is_recorded(self) -> None:
        """**The least explicable failure must not be the least observable**
        (§17). A grant outliving its material means the customer has to
        reconnect, and a probe that returned nothing would leave that
        indistinguishable from one nobody ran."""
        account = _account(ConnectionState.VALIDATED)
        accounts = FakeAccounts(account)
        probes = FakeProbes()
        prober = ProbeConnection(
            accounts,
            ResolveExecutionContext(
                accounts, FakeGrants(_grant(account)), FakeSecrets(holds=False)
            ),
            FakeReachability(),
            probes,
        )

        probe = await prober.execute(WORKSPACE, account.id, at=NOW)

        assert probe.result is ProbeResult.CREDENTIAL_REJECTED
        assert probes.recorded == [probe]

    async def test_probing_an_already_validated_connection_changes_nothing(self) -> None:
        """Re-checking something that works must not rewrite its row — an
        audit trail that records a state change nobody made is worse than one
        that records nothing."""
        account = _account(ConnectionState.VALIDATED)
        accounts = FakeAccounts(account)
        prober = _prober(account, FakeReachability(), accounts=accounts)

        await prober.execute(WORKSPACE, account.id, at=NOW)

        after = await accounts.get(WORKSPACE, account.id)
        assert after is account, "the same object, never re-saved"

    async def test_nothing_about_the_customers_data_moves(self) -> None:
        """**The acceptance criterion that keeps this slice out of C-326's
        way.** The probe reads, classifies and discards: it holds no store for
        a raw record, a claim or an event, and could not write one if it
        wanted to."""
        account = _account()
        prober = _prober(account, FakeReachability())

        await prober.execute(WORKSPACE, account.id, at=NOW)

        collaborators = vars(prober)
        assert set(collaborators) == {
            "_accounts",
            "_resolver",
            "_reachability",
            "_probes",
        }


class TestWhatTheCustomerSees:
    """The Connection Center, which is where all of this has to land."""

    async def _view(
        self, account: ConnectedAccount, *probes: ConnectionProbe
    ) -> object:
        queries = IntegrationQueries(
            FakeAccounts(account), FakeGrants(_grant(account)), FakeProbes(*probes)
        )
        return (await queries.connections(WORKSPACE, at=NOW))[0]

    async def _probes_for(
        self, account: ConnectedAccount, *results: ProbeResult
    ) -> tuple[ConnectionProbe, ...]:
        return tuple(
            ConnectionProbe(
                id=uuid4(),
                workspace_id=WORKSPACE,
                connected_account_id=account.id,
                result=result,
                detail=None if result is ProbeResult.REACHABLE else "because",
                probed_at=NOW - timedelta(minutes=index),
            )
            for index, result in enumerate(results)
        )

    async def test_a_perfect_looking_connection_that_does_not_work_asks_for_attention(
        self,
    ) -> None:
        """**The whole point, in one assertion.** State `VALIDATED`, grant
        unexpired, nothing revoked — and the last thing the platform learned by
        trying is that it does not work. Before this slice the screen said
        nothing was wrong."""
        account = _account(ConnectionState.VALIDATED)
        probes = await self._probes_for(account, ProbeResult.PERMISSION_MISSING)

        view = await self._view(account, *probes)

        assert view.health is ConnectionHealth.DEGRADED  # type: ignore[attr-defined]
        assert view.attention is Attention.NOW  # type: ignore[attr-defined]
        assert view.reason == "not_working"  # type: ignore[attr-defined]

    async def test_an_unprobed_connection_says_unknown_rather_than_healthy(self) -> None:
        account = _account(ConnectionState.VALIDATED)

        view = await self._view(account)

        assert view.health is ConnectionHealth.UNKNOWN  # type: ignore[attr-defined]
        assert view.attention is Attention.NONE  # type: ignore[attr-defined]

    async def test_a_working_connection_needs_nothing(self) -> None:
        account = _account(ConnectionState.VALIDATED)
        probes = await self._probes_for(account, ProbeResult.REACHABLE)

        view = await self._view(account, *probes)

        assert view.health is ConnectionHealth.HEALTHY  # type: ignore[attr-defined]
        assert view.attention is Attention.NONE  # type: ignore[attr-defined]

    async def test_a_composition_with_no_probe_reader_reports_unknown(self) -> None:
        """**The default is honest rather than convenient.** A wiring that had
        not been given a reader knows nothing, and a default of `HEALTHY` would
        make an unwired composition indistinguishable from a working one."""
        account = _account(ConnectionState.VALIDATED)
        queries = IntegrationQueries(FakeAccounts(account), FakeGrants(_grant(account)))

        view = (await queries.connections(WORKSPACE, at=NOW))[0]

        assert view.health is ConnectionHealth.UNKNOWN

    async def test_a_system_with_a_degraded_connection_is_not_working(self) -> None:
        """*"Is my CRM connected?"* — answering *yes* about a connection the
        platform has tried and failed to use is the same lie as answering it
        about a revoked one, one step quieter."""
        account = _account(ConnectionState.VALIDATED)
        probes = await self._probes_for(account, ProbeResult.CREDENTIAL_REJECTED)
        queries = IntegrationQueries(
            FakeAccounts(account), FakeGrants(_grant(account)), FakeProbes(*probes)
        )

        systems = await queries.systems(WORKSPACE, at=NOW)
        hubspot = next(s for s in systems if s.integration == "hubspot")

        assert not hubspot.is_working
        assert hubspot.needs_attention
