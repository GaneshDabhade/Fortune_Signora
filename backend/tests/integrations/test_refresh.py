"""Renewing a grant before a customer has to notice it expired.

**Everything on both sides of one port**, and that port is where the
unresolved architectural boundary sits: a real refresher needs the OAuth
*client* credentials, and where those live is the product owner's decision
([C-327](../../../docs/LANE_COORDINATION.md)). Nothing below waits on it — the
use case is exercised against a substituted `TokenRefresher`, exactly as the
revoker is exercised against a substituted transport.

The properties worth stating in one place, because each is a way the obvious
implementation loses a customer's connection:

- **A refresh never edits material in place.** New `secret_ref`, new grant, old
  grant revoked — so *what was live when* survives a rotation.
- **A provider that issues no new refresh token has not withdrawn the old one.**
  Overwriting with `None` destroys the only thing that could renew again.
- **A withdrawn connection is never renewed.** Doing so would resurrect access
  a customer or a vendor deliberately removed.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID, uuid4

import pytest

from modules.integrations.application.ports import SecretNotFound
from modules.integrations.application.refresh import (
    NoTokenRefresher,
    RefreshGrant,
    RefreshOutcome,
    RenewedMaterial,
)
from modules.integrations.domain.connection import ConnectedAccount, ConnectionState
from modules.integrations.domain.grant import Credential, IntegrationGrant, OAuth2Material

WORKSPACE = uuid4()
ACTOR = uuid4()
ACCOUNT_ID = uuid4()
NOW = datetime(2026, 8, 4, tzinfo=UTC)


def _account(state: ConnectionState = ConnectionState.CONNECTED) -> ConnectedAccount:
    return ConnectedAccount(
        id=ACCOUNT_ID,
        workspace_id=WORKSPACE,
        integration="hubspot",
        external_account_id="24601",
        endpoint=None,
        label="Acme production",
        state=state,
        connected_at=NOW,
        actor_id=ACTOR,
    )


def _grant(*, refreshable: bool = True, secret_ref: str = "integration/old") -> IntegrationGrant:
    return IntegrationGrant(
        id=uuid4(),
        workspace_id=WORKSPACE,
        connected_account_id=ACCOUNT_ID,
        secret_ref=secret_ref,
        scopes=("crm.objects.companies.read",),
        expires_at=NOW + timedelta(minutes=30),
        refreshable=refreshable,
        revoked_at=None,
        actor_id=ACTOR,
    )


class FakeAccounts:
    def __init__(self, account: ConnectedAccount | None) -> None:
        self.account = account

    async def get(self, workspace_id: UUID, account_id: UUID) -> ConnectedAccount | None:
        if self.account is None or self.account.workspace_id != workspace_id:
            return None
        return self.account

    async def find_identity(
        self, workspace_id: UUID, integration: str, external_account_id: str
    ) -> ConnectedAccount | None:
        return None

    async def list_for_workspace(self, workspace_id: UUID) -> list[ConnectedAccount]:
        return [self.account] if self.account else []

    async def save(self, account: ConnectedAccount) -> None:
        self.account = account


class FakeGrants:
    def __init__(self, grant: IntegrationGrant | None) -> None:
        self.saved: list[IntegrationGrant] = []
        self._grant = grant

    async def current_for(
        self, workspace_id: UUID, connected_account_id: UUID
    ) -> IntegrationGrant | None:
        return self._grant

    async def save(self, grant: IntegrationGrant) -> None:
        self.saved.append(grant)


class FakeSecrets:
    def __init__(self, credential: Credential | None) -> None:
        self._credential = credential
        self.written: dict[str, Credential] = {}

    async def resolve(self, secret_ref: str) -> Credential:
        if secret_ref in self.written:
            return self.written[secret_ref]
        if self._credential is None:
            raise SecretNotFound(secret_ref)
        return self._credential

    async def store(
        self,
        *,
        secret_ref: str,
        workspace_id: str,
        connected_account_id: str,
        credential: Credential,
    ) -> None:
        self.written[secret_ref] = credential


class ScriptedRefresher:
    """A `TokenRefresher` that answers without a vendor, or refuses."""

    def __init__(self, renewed: RenewedMaterial | None) -> None:
        self.renewed = renewed
        self.asked: list[tuple[str, str]] = []

    async def renew(self, integration: str, refresh_token: str) -> RenewedMaterial | None:
        self.asked.append((integration, refresh_token))
        return self.renewed


_DEFAULT: Any = object()


def _refresh(
    *,
    account: Any = _DEFAULT,
    grant: Any = _DEFAULT,
    credential: Any = _DEFAULT,
    refresher: Any = _DEFAULT,
) -> tuple[RefreshGrant, FakeAccounts, FakeGrants, FakeSecrets, Any]:
    accounts = FakeAccounts(_account() if account is _DEFAULT else account)
    grants = FakeGrants(_grant() if grant is _DEFAULT else grant)
    secrets = FakeSecrets(
        OAuth2Material("old-access", "old-refresh").as_credential()
        if credential is _DEFAULT
        else credential
    )
    chosen = (
        ScriptedRefresher(RenewedMaterial("new-access", "new-refresh", NOW + timedelta(hours=1)))
        if refresher is _DEFAULT
        else refresher
    )
    return RefreshGrant(accounts, grants, secrets, secrets, chosen), accounts, grants, secrets, chosen


async def _run(use_case: RefreshGrant) -> Any:
    return await use_case.execute(WORKSPACE, ACCOUNT_ID, at=NOW, actor_id=ACTOR)


class TestRenewingAGrant:
    async def test_it_asks_with_the_refresh_token_it_holds(self) -> None:
        use_case, _, _, _, refresher = _refresh()

        result = await _run(use_case)

        assert result.outcome is RefreshOutcome.RENEWED
        assert refresher.asked == [("hubspot", "old-refresh")]

    async def test_the_new_material_replaces_nothing_in_place(self) -> None:
        """**A rotation writes a new ref and leaves the old one** (§3).

        Editing material in place makes the previous value unrecoverable at
        exactly the moment a rotation is being diagnosed.
        """
        use_case, _, grants, secrets, _ = _refresh()

        await _run(use_case)

        written = [ref for ref in secrets.written if ref != "integration/old"]
        assert len(written) == 1
        material = OAuth2Material.read(secrets.written[written[0]])
        assert material is not None
        assert material.access_token == "new-access"
        assert material.refresh_token == "new-refresh"

    async def test_the_old_grant_is_revoked_and_a_new_one_takes_its_place(self) -> None:
        use_case, _, grants, _, _ = _refresh()

        await _run(use_case)

        fresh, revoked = grants.saved
        assert fresh.revoked_at is None and fresh.refreshable is True
        assert revoked.revoked_at == NOW
        assert fresh.id != revoked.id

    async def test_the_new_grant_is_saved_before_the_old_is_revoked(self) -> None:
        """So `current_for` never returns nothing between the two writes."""
        use_case, _, grants, _, _ = _refresh()

        await _run(use_case)

        assert grants.saved[0].revoked_at is None
        assert grants.saved[1].revoked_at is not None

    async def test_the_scopes_are_carried_forward_rather_than_re_derived(self) -> None:
        """**A refresh asks the customer for nothing**, so it cannot change what
        they permitted. A provider echoing a shorter list is describing this
        call, not the grant."""
        use_case, _, grants, _, _ = _refresh()

        await _run(use_case)

        assert grants.saved[0].scopes == ("crm.objects.companies.read",)

    async def test_the_new_expiry_is_the_provider_s(self) -> None:
        use_case, _, grants, _, _ = _refresh()

        await _run(use_case)

        assert grants.saved[0].expires_at == NOW + timedelta(hours=1)


class TestAProviderThatIssuesNoNewRefreshToken:
    async def test_the_old_one_is_kept(self) -> None:
        """**Google does exactly this**, and the old token stays valid.

        Overwriting with `None` would destroy the only thing that could ever
        renew the grant again — and it would do so silently, on a path that
        reports success.
        """
        use_case, _, _, secrets, _ = _refresh(
            refresher=ScriptedRefresher(RenewedMaterial("new-access", None, None))
        )

        await _run(use_case)

        written = [ref for ref in secrets.written if ref != "integration/old"]
        material = OAuth2Material.read(secrets.written[written[0]])
        assert material is not None
        assert material.access_token == "new-access"
        assert material.refresh_token == "old-refresh"


class TestAnExpiredConnectionComesBack:
    async def test_a_renewed_grant_revives_it(self) -> None:
        """`EXPIRED → CONNECTED` was already in the transition table.

        Using it is what makes a refresh invisible to the customer, which is
        the entire reason `refreshable` is recorded.
        """
        use_case, accounts, _, _, _ = _refresh(account=_account(ConnectionState.EXPIRED))

        result = await _run(use_case)

        assert result.outcome is RefreshOutcome.RENEWED
        assert result.account is not None
        assert result.account.state is ConnectionState.CONNECTED
        assert accounts.account is not None
        assert accounts.account.state is ConnectionState.CONNECTED

    async def test_a_healthy_connection_is_left_alone(self) -> None:
        use_case, accounts, _, _, _ = _refresh()

        await _run(use_case)

        assert accounts.account is not None
        assert accounts.account.state is ConnectionState.CONNECTED


class TestWhatItRefusesToRenew:
    @pytest.mark.parametrize(
        "state",
        [ConnectionState.DISCONNECTED, ConnectionState.REVOKED, ConnectionState.NOT_CONNECTED],
    )
    async def test_a_withdrawn_connection_is_never_renewed(
        self, state: ConnectionState
    ) -> None:
        """**Renewing one would resurrect access somebody deliberately removed.**

        `REVOKED` is the sharper case: the customer withdrew Signora at the
        vendor, and a refresh that quietly restored it would be the product
        overriding them.
        """
        use_case, _, grants, _, refresher = _refresh(account=_account(state))

        result = await _run(use_case)

        assert result.outcome is RefreshOutcome.UNUSABLE
        assert grants.saved == []
        assert refresher.asked == []

    async def test_a_connection_in_another_workspace_is_invisible(self) -> None:
        other = ConnectedAccount(
            id=ACCOUNT_ID,
            workspace_id=uuid4(),
            integration="hubspot",
            external_account_id="24601",
            endpoint=None,
            label="Someone else's",
            state=ConnectionState.CONNECTED,
            connected_at=NOW,
            actor_id=ACTOR,
        )
        use_case, _, grants, _, _ = _refresh(account=other)

        assert (await _run(use_case)).outcome is RefreshOutcome.UNUSABLE
        assert grants.saved == []

    async def test_a_grant_marked_unrefreshable_is_not_attempted(self) -> None:
        use_case, _, _, _, refresher = _refresh(grant=_grant(refreshable=False))

        assert (await _run(use_case)).outcome is RefreshOutcome.NOT_REFRESHABLE
        assert refresher.asked == []

    async def test_a_connection_with_no_grant_is_not_attempted(self) -> None:
        use_case, _, _, _, refresher = _refresh(grant=None)

        assert (await _run(use_case)).outcome is RefreshOutcome.NOT_REFRESHABLE
        assert refresher.asked == []

    async def test_material_that_cannot_be_read_is_an_operational_fault(self) -> None:
        """A rotated key or a purged secret. **Distinct from `REFUSED`**,
        because one is Signora's problem and the other is the vendor's."""
        use_case, _, _, _, refresher = _refresh(credential=None)

        assert (await _run(use_case)).outcome is RefreshOutcome.UNREADABLE
        assert refresher.asked == []

    async def test_a_refreshable_grant_with_nothing_to_refresh_says_so(self) -> None:
        """**The flag and the material disagreeing is a defect**, and reporting
        it beats sending `None` to a vendor and reading the refusal as theirs."""
        use_case, _, _, _, refresher = _refresh(
            credential=OAuth2Material("only-access", None).as_credential()
        )

        assert (await _run(use_case)).outcome is RefreshOutcome.NOT_REFRESHABLE
        assert refresher.asked == []

    async def test_a_provider_refusal_changes_nothing(self) -> None:
        """The customer may have withdrawn Signora at the vendor. Either way,
        the grant that still exists is left exactly as it was."""
        use_case, _, grants, secrets, _ = _refresh(refresher=ScriptedRefresher(None))

        assert (await _run(use_case)).outcome is RefreshOutcome.REFUSED
        assert grants.saved == []
        assert secrets.written == {}


class TestTheDefaultRefresher:
    async def test_it_reports_that_it_could_not_renew(self) -> None:
        """**Honest rather than incomplete**, exactly as `NoRevoker` was.

        No adapter can run until the OAuth client credentials have somewhere to
        live, which is an architectural decision and not this module's
        ([C-327](../../../docs/LANE_COORDINATION.md)). A refresher that claimed
        success would leave a connection reading healthy with material that had
        stopped working — which is the one outcome worse than not refreshing.
        """
        assert await NoTokenRefresher().renew("hubspot", "a-token") is None

    async def test_a_use_case_built_without_one_renews_nothing(self) -> None:
        accounts = FakeAccounts(_account())
        grants = FakeGrants(_grant())
        secrets = FakeSecrets(OAuth2Material("a", "b").as_credential())

        result = await RefreshGrant(accounts, grants, secrets, secrets).execute(
            WORKSPACE, ACCOUNT_ID, at=NOW, actor_id=ACTOR
        )

        assert result.outcome is RefreshOutcome.REFUSED
        assert grants.saved == []
