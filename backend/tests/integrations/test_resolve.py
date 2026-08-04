"""Grants, and resolving a connection into an execution context."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID, uuid4

import pytest

from modules.integrations.application.ports import SecretNotFound
from modules.integrations.application.refresh import RefreshOutcome, RefreshResult
from modules.integrations.application.resolve import (
    SYSTEM_ACTOR_ID,
    ConnectionUnusable,
    CredentialUnreadable,
    ExecutionContext,
    ResolveExecutionContext,
)
from modules.integrations.domain.connection import ConnectedAccount, ConnectionState
from modules.integrations.domain.grant import (
    Credential,
    GrantExpired,
    GrantRevoked,
    IntegrationGrant,
)

NOW = datetime(2026, 8, 2, 12, 0, tzinfo=UTC)
WORKSPACE = uuid4()
ACTOR = uuid4()


def _account(state: ConnectionState = ConnectionState.VALIDATED, **kw: object) -> ConnectedAccount:
    defaults: dict[str, object] = {
        "id": uuid4(),
        "workspace_id": WORKSPACE,
        "integration": "salesforce",
        "external_account_id": "00D000000000000",
        "endpoint": "https://acme.my.salesforce.com",
        "label": "Acme production",
        "state": state,
        "connected_at": NOW,
        "actor_id": ACTOR,
    }
    defaults.update(kw)
    return ConnectedAccount(**defaults)  # type: ignore[arg-type]


def _grant(account: ConnectedAccount, **kw: object) -> IntegrationGrant:
    defaults: dict[str, object] = {
        "id": uuid4(),
        "workspace_id": account.workspace_id,
        "connected_account_id": account.id,
        "secret_ref": "vault://grants/1",
        "scopes": ("refresh_token", "api"),
        "expires_at": None,
        "refreshable": True,
        "revoked_at": None,
        "actor_id": ACTOR,
    }
    defaults.update(kw)
    return IntegrationGrant(**defaults)  # type: ignore[arg-type]


class FakeAccounts:
    def __init__(self, account: ConnectedAccount | None) -> None:
        self._account = account

    async def get(self, workspace_id: UUID, account_id: UUID) -> ConnectedAccount | None:
        if self._account is None or self._account.workspace_id != workspace_id:
            return None
        return self._account if self._account.id == account_id else None

    async def list_for_workspace(self, workspace_id: UUID) -> list[ConnectedAccount]:
        return [self._account] if self._account else []

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
                for a in ([self._account] if self._account else [])
                if a.workspace_id == workspace_id
                and a.integration == integration
                and a.external_account_id == external_account_id
            ),
            None,
        )

    async def save(self, account: ConnectedAccount) -> None:
        self._account = account


class FakeGrants:
    def __init__(self, grant: IntegrationGrant | None) -> None:
        self._grant = grant

    async def current_for(
        self, workspace_id: UUID, connected_account_id: UUID
    ) -> IntegrationGrant | None:
        return self._grant

    async def save(self, grant: IntegrationGrant) -> None:
        self._grant = grant


class FakeSecrets:
    def __init__(self, *, holds: bool = True) -> None:
        self._holds = holds

    async def resolve(self, secret_ref: str) -> Credential:
        if not self._holds:
            raise SecretNotFound(secret_ref)
        return Credential(kind="bearer", material=b"s3cret")


def _resolver(
    account: ConnectedAccount | None,
    grant: IntegrationGrant | None,
    *,
    secrets_hold: bool = True,
    grants: FakeGrants | None = None,
    refresher: Any = None,
) -> ResolveExecutionContext:
    return ResolveExecutionContext(
        FakeAccounts(account),
        grants or FakeGrants(grant),
        FakeSecrets(holds=secrets_hold),
        refresher,
    )


class TestCredentialsDoNotLeak:
    def test_a_credential_will_not_render_itself(self) -> None:
        """A credential in a traceback, a log line or a pytest diff is a
        credential in a log aggregator."""
        credential = Credential(kind="bearer", material=b"s3cret")
        assert "s3cret" not in repr(credential)
        assert "s3cret" not in str(credential)
        assert "redacted" in repr(credential)

    def test_an_execution_context_will_not_render_its_credential(self) -> None:
        context = ExecutionContext(
            workspace_id=WORKSPACE,
            connected_account_id=uuid4(),
            integration="salesforce",
            endpoint=None,
            scopes=(),
            credential=Credential(kind="bearer", material=b"s3cret"),
        )
        assert "s3cret" not in repr(context)

    def test_a_grant_carries_a_reference_and_never_material(self) -> None:
        """The property that keeps tokens out of a replicated, backed-up table."""
        grant = _grant(_account())
        assert not hasattr(grant, "token")
        assert grant.secret_ref.startswith("vault://")

    def test_a_grant_must_reference_something(self) -> None:
        with pytest.raises(ValueError, match="secret material"):
            _grant(_account(), secret_ref="")


class TestGrantLifecycle:
    def test_a_grant_without_an_expiry_never_expires(self) -> None:
        """An API key is a grant that does not expire — a value, not a special
        case, and this is what stops OAuth's shape becoming the type."""
        assert _grant(_account(), expires_at=None, refreshable=False).is_expired(at=NOW) is False

    def test_an_elapsed_grant_is_expired(self) -> None:
        grant = _grant(_account(), expires_at=NOW - timedelta(seconds=1))
        assert grant.is_expired(at=NOW) is True

    def test_expiry_and_revocation_raise_differently(self) -> None:
        """**Two exceptions rather than one boolean**, because a caller does
        different things: an expired refreshable grant is refreshed, and a
        revoked one needs the customer back."""
        with pytest.raises(GrantExpired):
            _grant(_account(), expires_at=NOW - timedelta(days=1)).check_usable(at=NOW)
        with pytest.raises(GrantRevoked):
            _grant(_account(), revoked_at=NOW).check_usable(at=NOW)

    def test_revocation_outranks_expiry(self) -> None:
        """A revoked grant that also expired must not look refreshable."""
        grant = _grant(_account(), expires_at=NOW - timedelta(days=1), revoked_at=NOW)
        with pytest.raises(GrantRevoked):
            grant.check_usable(at=NOW)

    def test_revocation_is_idempotent(self) -> None:
        """A second report of one withdrawal must not move the timestamp — it
        is when permission ended, not when Signora last noticed."""
        first = _grant(_account()).revoke(at=NOW, by=ACTOR)
        assert first.revoke(at=NOW + timedelta(days=1), by=ACTOR).revoked_at == NOW


class TestResolution:
    @pytest.mark.asyncio
    async def test_a_usable_connection_resolves(self) -> None:
        account = _account()
        context = await _resolver(account, _grant(account)).execute(
            WORKSPACE, account.id, at=NOW
        )
        assert context.integration == "salesforce"
        assert context.endpoint == "https://acme.my.salesforce.com"
        assert context.scopes == ("refresh_token", "api")
        assert context.credential.material == b"s3cret"

    @pytest.mark.asyncio
    async def test_the_context_carries_no_hint_of_how_it_was_acquired(self) -> None:
        """**The rule that must survive every future mechanism.** An adapter
        able to ask *"was this OAuth?"* is vendor-shaped, and the abstraction
        would not survive mTLS."""
        account = _account()
        context = await _resolver(account, _grant(account)).execute(
            WORKSPACE, account.id, at=NOW
        )
        fields = set(ExecutionContext.__dataclass_fields__)
        assert not fields & {"mechanism", "auth_type", "oauth", "grant_type", "flow"}
        assert context.credential.kind == "bearer"

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "state",
        [ConnectionState.REVOKED, ConnectionState.EXPIRED, ConnectionState.DISCONNECTED],
    )
    async def test_an_unusable_connection_refuses_and_says_which(
        self, state: ConnectionState
    ) -> None:
        account = _account(state)
        with pytest.raises(ConnectionUnusable) as raised:
            await _resolver(account, _grant(account)).execute(WORKSPACE, account.id, at=NOW)
        assert raised.value.state is state

    @pytest.mark.asyncio
    async def test_another_workspace_gets_nothing(self) -> None:
        """Belt and braces beside RLS, and it reads as *no such connection*
        rather than *not yours* — the 404-not-403 rule."""
        account = _account()
        with pytest.raises(ConnectionUnusable, match="no such connection"):
            await _resolver(account, _grant(account)).execute(uuid4(), account.id, at=NOW)

    @pytest.mark.asyncio
    async def test_a_connection_with_no_grant_refuses(self) -> None:
        account = _account()
        with pytest.raises(ConnectionUnusable, match="no grant"):
            await _resolver(account, None).execute(WORKSPACE, account.id, at=NOW)

    @pytest.mark.asyncio
    async def test_a_revoked_grant_refuses_even_on_a_usable_connection(self) -> None:
        """The two lifecycles are independent, so both are checked."""
        account = _account(ConnectionState.VALIDATED)
        with pytest.raises(GrantRevoked):
            await _resolver(account, _grant(account, revoked_at=NOW)).execute(
                WORKSPACE, account.id, at=NOW
            )

    @pytest.mark.asyncio
    async def test_a_purged_secret_surfaces_rather_than_resolving_empty(self) -> None:
        """A grant row can outlive its material when a purge runs at
        offboarding. Resolving to nothing would call a vendor unauthenticated.

        **Surfaced as `CredentialUnreadable`, not as the storage failure.** A
        rotated key and a purged secret are the same fact above the adapter —
        this connection has to be made again — and a customer can act on that.
        """
        account = _account()
        with pytest.raises(CredentialUnreadable):
            await _resolver(account, _grant(account), secrets_hold=False).execute(
                WORKSPACE, account.id, at=NOW
            )


class TestAnExpiredGrantRenewsItself:
    """**Refresh-on-use, and it is the only moment a renewal is needed.**

    A credential is renewed when something is about to use it, so the
    capability needs no scheduler — which the repository does not have and
    which is not this module's to add.

    The property worth protecting hardest is the last one: **revocation is
    never refreshed.** `check_usable` raises revoked before expired, so a
    customer who withdrew Signora at the vendor is not quietly reconnected.
    """

    class _Refresher:
        """A `RefreshGrant` that answers without a vendor, and can renew."""

        def __init__(self, outcome: RefreshOutcome, grants: FakeGrants | None = None) -> None:
            self._outcome = outcome
            self._grants = grants
            self._renewed: IntegrationGrant | None = None
            self.asked: list[tuple[UUID, UUID]] = []

        def renewing_to(self, grant: IntegrationGrant) -> Any:
            self._renewed = grant
            return self

        async def execute(
            self,
            workspace_id: UUID,
            connected_account_id: UUID,
            *,
            at: datetime,
            actor_id: UUID,
        ) -> RefreshResult:
            self.asked.append((workspace_id, actor_id))
            if self._outcome is RefreshOutcome.RENEWED and self._grants and self._renewed:
                await self._grants.save(self._renewed)
            return RefreshResult(self._outcome)

    def _setup(
        self, outcome: RefreshOutcome, *, renewed_expiry: datetime | None
    ) -> tuple[ResolveExecutionContext, Any, UUID]:
        account = _account()
        grants = FakeGrants(_grant(account, expires_at=NOW - timedelta(minutes=1)))
        refresher = self._Refresher(outcome, grants)
        if renewed_expiry is not None:
            refresher.renewing_to(_grant(account, expires_at=renewed_expiry))
        return (
            _resolver(account, None, grants=grants, refresher=refresher),
            refresher,
            account.id,
        )

    async def test_a_caller_never_learns_the_credential_lapsed(self) -> None:
        resolver, _, account_id = self._setup(
            RefreshOutcome.RENEWED, renewed_expiry=NOW + timedelta(hours=1)
        )

        context = await resolver.execute(WORKSPACE, account_id, at=NOW)

        assert context.credential.material == b"s3cret"

    async def test_the_renewal_is_attributed_to_the_platform(self) -> None:
        """**Nobody asked for it**, and the audit columns take no default.

        Attributing an unattended renewal to the customer who consented months
        earlier would put a name on an action they did not take, which is the
        one thing an audit column exists to prevent.
        """
        resolver, refresher, account_id = self._setup(
            RefreshOutcome.RENEWED, renewed_expiry=NOW + timedelta(hours=1)
        )

        await resolver.execute(WORKSPACE, account_id, at=NOW)

        assert refresher.asked == [(WORKSPACE, SYSTEM_ACTOR_ID)]

    async def test_a_refusal_leaves_the_expiry_standing(self) -> None:
        """**The caller's situation is unchanged, so the exception is too.**

        A new type would make *we tried and could not* look different from *we
        never could*, when the customer does the same thing about both.
        """
        resolver, _, account_id = self._setup(RefreshOutcome.REFUSED, renewed_expiry=None)

        with pytest.raises(GrantExpired):
            await resolver.execute(WORKSPACE, account_id, at=NOW)

    async def test_material_that_arrives_already_expired_is_refused(self) -> None:
        """Checked again rather than assumed. A vendor returning something
        already past its expiry would otherwise reach an adapter as working."""
        resolver, _, account_id = self._setup(
            RefreshOutcome.RENEWED, renewed_expiry=NOW - timedelta(seconds=1)
        )

        with pytest.raises(GrantExpired):
            await resolver.execute(WORKSPACE, account_id, at=NOW)

    async def test_without_a_refresher_the_expiry_is_unchanged(self) -> None:
        """The behaviour every existing caller had, preserved exactly."""
        account = _account()
        resolver = _resolver(account, _grant(account, expires_at=NOW - timedelta(minutes=1)))

        with pytest.raises(GrantExpired):
            await resolver.execute(WORKSPACE, account.id, at=NOW)

    async def test_a_revoked_grant_is_never_renewed(self) -> None:
        """**Revocation outranks expiry**, and this is where that matters most.

        A customer who withdrew Signora at the vendor must not be quietly
        reconnected by a renewal running on their behalf.
        """
        account = _account()
        grants = FakeGrants(
            _grant(account, expires_at=NOW - timedelta(minutes=1), revoked_at=NOW)
        )
        refresher = self._Refresher(RefreshOutcome.RENEWED, grants)

        with pytest.raises(GrantRevoked):
            await _resolver(account, None, grants=grants, refresher=refresher).execute(
                WORKSPACE, account.id, at=NOW
            )
        assert refresher.asked == []
