"""The connection lifecycle, and the properties that keep it a business fact."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

import pytest

from modules.integrations.domain.connection import (
    UNUSABLE_STATES,
    ConnectedAccount,
    ConnectionState,
    ConnectionTransitionError,
)

NOW = datetime(2026, 8, 2, 12, 0, tzinfo=UTC)


def _account(state: ConnectionState = ConnectionState.NOT_CONNECTED, **kw: object) -> ConnectedAccount:
    defaults: dict[str, object] = {
        "id": uuid4(),
        "workspace_id": uuid4(),
        "integration": "google_calendar",
        "external_account_id": "acme.example",
        "endpoint": None,
        "label": "Acme calendars",
        "state": state,
        "connected_at": None,
    }
    defaults.update(kw)
    return ConnectedAccount(**defaults)  # type: ignore[arg-type]


class TestItIsAnAccountNotAPerson:
    def test_an_organisation_is_a_connected_account(self) -> None:
        """Domain-wide delegation binds one grant to a whole organisation. A
        model that assumed one human would break on the second integration."""
        assert _account(external_account_id="acme.com").external_account_id == "acme.com"

    def test_the_endpoint_is_not_the_credential(self) -> None:
        """Salesforce returns a per-org `instance_url` with its token. On the
        grant, correcting an address would mean rotating a credential."""
        account = _account(endpoint="https://acme.my.salesforce.com")
        assert account.endpoint == "https://acme.my.salesforce.com"

    def test_a_connection_must_name_a_catalog_entry(self) -> None:
        with pytest.raises(ValueError, match="catalog entry"):
            _account(integration="")

    def test_a_connection_must_identify_the_account(self) -> None:
        with pytest.raises(ValueError, match="external_account_id"):
            _account(external_account_id="")


class TestUsability:
    @pytest.mark.parametrize("state", sorted(UNUSABLE_STATES, key=str))
    def test_an_unusable_state_is_unusable(self, state: ConnectionState) -> None:
        assert _account(state).is_usable is False

    @pytest.mark.parametrize(
        "state", [ConnectionState.CONNECTED, ConnectionState.VALIDATED]
    )
    def test_a_usable_state_is_usable(self, state: ConnectionState) -> None:
        assert _account(state).is_usable is True

    def test_every_state_is_classified(self) -> None:
        """A state in neither set would be usable by omission — the silent
        default that lets a revoked connection keep being called."""
        usable = {ConnectionState.CONNECTED, ConnectionState.VALIDATED}
        assert usable | UNUSABLE_STATES == set(ConnectionState)


class TestTransitions:
    def test_connecting_records_when(self) -> None:
        account = _account(ConnectionState.AUTHORIZING).transition(
            ConnectionState.CONNECTED, at=NOW
        )
        assert account.connected_at == NOW

    def test_reconnecting_keeps_the_first_connection_time(self) -> None:
        """*When did we connect this?* is a fact about the relationship, not
        about the most recent token refresh."""
        first = _account(ConnectionState.AUTHORIZING).transition(
            ConnectionState.CONNECTED, at=NOW
        )
        later = datetime(2026, 9, 1, tzinfo=UTC)
        again = first.transition(ConnectionState.EXPIRED, at=later).transition(
            ConnectionState.CONNECTED, at=later
        )
        assert again.connected_at == NOW

    def test_transitioning_returns_a_new_account(self) -> None:
        before = _account(ConnectionState.CONNECTED)
        after = before.transition(ConnectionState.VALIDATED, at=NOW)
        assert before.state is ConnectionState.CONNECTED
        assert after.state is ConnectionState.VALIDATED

    def test_an_expired_connection_recovers_by_refresh(self) -> None:
        assert (
            _account(ConnectionState.EXPIRED)
            .transition(ConnectionState.CONNECTED, at=NOW)
            .state
            is ConnectionState.CONNECTED
        )

    def test_a_revoked_connection_does_not_recover_by_refresh(self) -> None:
        """**The distinction the whole lifecycle exists for.** Revocation is not
        an expiry: retrying against it is a system doing nothing while a
        dashboard reports it healthy. Only the customer can undo it, and that
        starts at authorization."""
        with pytest.raises(ConnectionTransitionError):
            _account(ConnectionState.REVOKED).transition(ConnectionState.CONNECTED, at=NOW)
        assert (
            _account(ConnectionState.REVOKED)
            .transition(ConnectionState.AUTHORIZING, at=NOW)
            .state
            is ConnectionState.AUTHORIZING
        )

    def test_a_connection_cannot_skip_authorization(self) -> None:
        with pytest.raises(ConnectionTransitionError, match="not_connected to connected"):
            _account(ConnectionState.NOT_CONNECTED).transition(
                ConnectionState.CONNECTED, at=NOW
            )

    def test_validation_requires_a_connection_first(self) -> None:
        """`VALIDATED` means a real call succeeded, so it cannot precede one."""
        with pytest.raises(ConnectionTransitionError):
            _account(ConnectionState.AUTHORIZING).transition(
                ConnectionState.VALIDATED, at=NOW
            )

    def test_every_state_can_be_left(self) -> None:
        """A state with no exit is a connection a customer can never repair."""
        for state in ConnectionState:
            assert _account(state).__class__ is ConnectedAccount
            exits = [
                target
                for target in ConnectionState
                if _can_reach(state, target)
            ]
            assert exits, f"{state.value} is a dead end"


def _can_reach(state: ConnectionState, target: ConnectionState) -> bool:
    try:
        _account(state).transition(target, at=NOW)
    except ConnectionTransitionError:
        return False
    return True
