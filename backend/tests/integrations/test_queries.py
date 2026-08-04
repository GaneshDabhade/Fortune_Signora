"""What a customer reads on the connections screen.

Validated against the six integrations Signora expects to support first —
Salesforce, HubSpot, Google Workspace, Microsoft 365, Slack and calendars —
rather than against a hypothetical fiftieth.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

import pytest

from modules.integrations.application.queries import (
    EXPIRY_WARNING,
    Attention,
    IntegrationQueries,
)
from modules.integrations.domain.connection import ConnectedAccount, ConnectionState
from modules.integrations.domain.grant import IntegrationGrant

NOW = datetime(2026, 8, 2, 12, 0, tzinfo=UTC)
WORKSPACE = uuid4()
ACTOR = uuid4()


def _account(
    integration: str = "salesforce",
    state: ConnectionState = ConnectionState.VALIDATED,
    label: str = "Acme production",
    external: str = "00D000000000000",
) -> ConnectedAccount:
    return ConnectedAccount(
        id=uuid4(),
        workspace_id=WORKSPACE,
        integration=integration,
        external_account_id=external,
        endpoint=None,
        label=label,
        state=state,
        connected_at=NOW - timedelta(days=30),
        actor_id=ACTOR,
    )


def _grant(
    account: ConnectedAccount,
    *,
    expires_at: datetime | None = None,
    refreshable: bool = True,
) -> IntegrationGrant:
    return IntegrationGrant(
        id=uuid4(),
        workspace_id=account.workspace_id,
        connected_account_id=account.id,
        secret_ref=f"vault://{account.id}",
        scopes=("read",),
        expires_at=expires_at,
        refreshable=refreshable,
        revoked_at=None,
        actor_id=ACTOR,
    )


class FakeAccounts:
    def __init__(self, accounts: list[ConnectedAccount]) -> None:
        self._accounts = accounts

    async def get(self, workspace_id: UUID, account_id: UUID) -> ConnectedAccount | None:
        return next((a for a in self._accounts if a.id == account_id), None)

    async def list_for_workspace(self, workspace_id: UUID) -> list[ConnectedAccount]:
        return [a for a in self._accounts if a.workspace_id == workspace_id]

    async def find_identity(
        self, workspace_id: UUID, integration: str, external_account_id: str
    ) -> ConnectedAccount | None:
        """Unused by this file's subject, and present because the port has it.

        **The cost of a Protocol growing**, paid honestly: a double that
        declined to implement it would type-check only by loosening the
        annotation on the thing under test, which is how a fake stops
        resembling the contract it stands in for.
        """
        return next(
            (
                a
                for a in self._accounts
                if a.workspace_id == workspace_id
                and a.integration == integration
                and a.external_account_id == external_account_id
            ),
            None,
        )

    async def save(self, account: ConnectedAccount) -> None: ...


class FakeGrants:
    def __init__(self, grants: dict[UUID, IntegrationGrant]) -> None:
        self._grants = grants

    async def current_for(
        self, workspace_id: UUID, connected_account_id: UUID
    ) -> IntegrationGrant | None:
        return self._grants.get(connected_account_id)

    async def save(self, grant: IntegrationGrant) -> None: ...


def _queries(
    accounts: list[ConnectedAccount], grants: dict[UUID, IntegrationGrant] | None = None
) -> IntegrationQueries:
    return IntegrationQueries(FakeAccounts(accounts), FakeGrants(grants or {}))


class TestDayOneIntegrations:
    """The six the product expects first, and the shapes they actually take."""

    @pytest.mark.asyncio
    async def test_many_calendars_for_one_organization_is_the_normal_case(self) -> None:
        """**Not an edge case — the expected shape.** Every rep connects their
        own calendar, so one organization has many connections of one kind. A
        model that assumed one connection per system would break on the second
        salesperson.
        """
        accounts = [
            _account("google_calendar", label="Jane", external="jane@acme.example"),
            _account("google_calendar", label="Sam", external="sam@acme.example"),
            _account("google_calendar", label="Ravi", external="ravi@acme.example"),
        ]
        views = await _queries(accounts).connections(WORKSPACE, at=NOW)
        assert len(views) == 3
        assert {v.label for v in views} == {"Jane", "Sam", "Ravi"}

    @pytest.mark.asyncio
    async def test_a_domain_wide_connection_is_a_single_row(self) -> None:
        """Google Workspace and Microsoft 365 also permit one grant covering an
        entire domain. The same model holds with no special case."""
        views = await _queries(
            [_account("google_workspace", label="Acme", external="acme.example")]
        ).connections(WORKSPACE, at=NOW)
        assert len(views) == 1

    @pytest.mark.asyncio
    async def test_two_crms_at_once_are_two_rows(self) -> None:
        """A customer migrating from HubSpot to Salesforce runs both."""
        views = await _queries(
            [_account("salesforce", label="Acme"), _account("hubspot", label="Acme legacy")]
        ).connections(WORKSPACE, at=NOW)
        assert {v.integration for v in views} == {"salesforce", "hubspot"}


class TestTheBrokenOnesAreVisible:
    @pytest.mark.asyncio
    async def test_a_revoked_connection_is_listed_and_flagged(self) -> None:
        """**The most important row on the screen.** Omitting it would leave a
        customer believing their data was still flowing."""
        views = await _queries([_account(state=ConnectionState.REVOKED)]).connections(
            WORKSPACE, at=NOW
        )
        assert views[0].attention is Attention.NOW
        assert views[0].reason == "permission_withdrawn"

    @pytest.mark.asyncio
    async def test_an_expired_connection_needs_action_now(self) -> None:
        views = await _queries([_account(state=ConnectionState.EXPIRED)]).connections(
            WORKSPACE, at=NOW
        )
        assert views[0].attention is Attention.NOW
        assert views[0].reason == "credential_expired"

    @pytest.mark.asyncio
    async def test_an_unfinished_authorization_needs_action_now(self) -> None:
        """A customer who closed the tab mid-flow has a connection that will
        never work and no reason to suspect it."""
        views = await _queries([_account(state=ConnectionState.AUTHORIZING)]).connections(
            WORKSPACE, at=NOW
        )
        assert views[0].attention is Attention.NOW
        assert views[0].reason == "authorization_unfinished"

    @pytest.mark.asyncio
    async def test_a_deliberately_disconnected_system_is_not_nagged_about(self) -> None:
        """Nothing is broken. Nagging about a system somebody chose to
        disconnect is noise, and noise is what makes a real warning invisible."""
        views = await _queries([_account(state=ConnectionState.DISCONNECTED)]).connections(
            WORKSPACE, at=NOW
        )
        assert views[0].attention is Attention.NONE
        assert views[0].reason is None


class TestAttentionIsDerived:
    @pytest.mark.asyncio
    async def test_a_healthy_connection_needs_nothing(self) -> None:
        account = _account()
        views = await _queries([account], {account.id: _grant(account)}).connections(
            WORKSPACE, at=NOW
        )
        assert views[0].attention is Attention.NONE

    @pytest.mark.asyncio
    async def test_a_credential_expiring_soon_and_unable_to_refresh_warns(self) -> None:
        account = _account()
        grant = _grant(
            account,
            expires_at=NOW + timedelta(seconds=EXPIRY_WARNING - 60),
            refreshable=False,
        )
        views = await _queries([account], {account.id: grant}).connections(WORKSPACE, at=NOW)
        assert views[0].attention is Attention.SOON
        assert views[0].reason == "credential_expiring"

    @pytest.mark.asyncio
    async def test_a_refreshable_credential_does_not_warn(self) -> None:
        """It renews itself. Warning about it would train the customer to
        ignore the warning that matters."""
        account = _account()
        grant = _grant(account, expires_at=NOW + timedelta(minutes=1), refreshable=True)
        views = await _queries([account], {account.id: grant}).connections(WORKSPACE, at=NOW)
        assert views[0].attention is Attention.NONE

    @pytest.mark.asyncio
    async def test_the_same_data_reads_differently_as_time_passes(self) -> None:
        """**Why it is derived rather than stored.** Nothing writes a row when a
        credential expires overnight, and the answer must still be right in the
        morning."""
        account = _account()
        grant = _grant(account, expires_at=NOW + timedelta(days=10), refreshable=False)
        queries = _queries([account], {account.id: grant})
        assert (await queries.connections(WORKSPACE, at=NOW))[0].attention is Attention.NONE
        later = NOW + timedelta(days=9)
        assert (await queries.connections(WORKSPACE, at=later))[0].attention is Attention.SOON


class TestTheViewShowsNoBookkeeping:
    @pytest.mark.asyncio
    async def test_no_secret_reference_or_vendor_identifier_reaches_the_view(self) -> None:
        """A screen showing a Salesforce org id is showing the customer
        Signora's bookkeeping."""
        account = _account()
        views = await _queries([account], {account.id: _grant(account)}).connections(
            WORKSPACE, at=NOW
        )
        fields = set(type(views[0]).__dataclass_fields__)
        assert not fields & {"secret_ref", "external_account_id", "endpoint", "grant_id"}

    @pytest.mark.asyncio
    async def test_another_organizations_connections_are_not_listed(self) -> None:
        other = ConnectedAccount(
            id=uuid4(),
            workspace_id=uuid4(),
            integration="salesforce",
            external_account_id="other",
            endpoint=None,
            label="Someone else",
            state=ConnectionState.VALIDATED,
            connected_at=None,
            actor_id=ACTOR,
        )
        views = await _queries([_account(), other]).connections(WORKSPACE, at=NOW)
        assert len(views) == 1
