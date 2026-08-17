"""Integration tests for the authenticated HTTP pipeline.

These exercise the full stack a real request traverses — JWT verification,
server-side membership verification, RLS context, Casbin authorization,
domain logic, PostgreSQL — against a real database, as the least-privilege
``signora_app`` role.
"""

import logging
from collections.abc import AsyncIterator
from datetime import timedelta
from typing import Any
from uuid import UUID, uuid4

import pytest
from httpx import ASGITransport, AsyncClient

from apps.api.main import create_app
from signora_platform.observability import JsonFormatter
from signora_platform.settings import Settings
from signora_platform.tests.keys import (
    TEST_AUDIENCE,
    TEST_ISSUER,
    KeyPair,
    generate_key_pair,
    mint_token,
)
from tests.conftest import DEFAULT_APP_DATABASE_URL
from tests.slugs import test_slug as _test_slug

pytestmark = pytest.mark.integration


@pytest.fixture(scope="session")
def key_pair() -> KeyPair:
    return generate_key_pair()


@pytest.fixture
async def client(key_pair: KeyPair) -> AsyncIterator[AsyncClient]:
    """An HTTP client bound to a fully composed app.

    The app is configured with only the *public* key — it cannot mint the
    tokens it accepts, exactly as in production (ADR-0026).
    """
    settings = Settings(
        environment="test",
        database_url=DEFAULT_APP_DATABASE_URL,
        jwt_public_key=key_pair.public_pem,
        jwt_issuer=TEST_ISSUER,
        jwt_audience=TEST_AUDIENCE,
    )
    app = create_app(settings)
    async with app.router.lifespan_context(app):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as http:
            yield http


def _auth(key_pair: KeyPair, user_id: UUID) -> dict[str, str]:
    return {"Authorization": f"Bearer {mint_token(key_pair, user_id=user_id)}"}


async def _create_workspace(
    client: AsyncClient, key_pair: KeyPair, user_id: UUID, name: str = "Acme"
) -> dict[str, Any]:
    response = await client.post(
        "/workspaces", json={"name": name, "slug": _test_slug(name)}, headers=_auth(key_pair, user_id)
    )
    assert response.status_code == 201, response.text
    body: dict[str, Any] = response.json()
    return body


class TestAuthenticationBoundary:
    async def test_rejects_request_with_no_token(self, client: AsyncClient) -> None:
        response = await client.get("/workspaces")

        assert response.status_code == 401
        assert response.json()["error"]["code"] == "unauthenticated"

    async def test_rejects_token_from_a_foreign_signing_key(self, client: AsyncClient) -> None:
        attacker = generate_key_pair()
        token = mint_token(attacker, user_id=uuid4())

        response = await client.get("/workspaces", headers={"Authorization": f"Bearer {token}"})

        assert response.status_code == 401

    async def test_expired_token_is_distinguishable_so_clients_can_refresh(
        self, client: AsyncClient, key_pair: KeyPair
    ) -> None:
        token = mint_token(key_pair, user_id=uuid4(), expires_in=timedelta(minutes=-30))

        response = await client.get("/workspaces", headers={"Authorization": f"Bearer {token}"})

        assert response.status_code == 401
        assert response.json()["error"]["code"] == "token_expired"

    async def test_health_endpoint_remains_unauthenticated(self, client: AsyncClient) -> None:
        assert (await client.get("/health")).status_code == 200


class TestWorkspaceLifecycle:
    async def test_creates_workspace_and_makes_caller_owner(
        self, client: AsyncClient, key_pair: KeyPair
    ) -> None:
        user_id = uuid4()

        workspace = await _create_workspace(client, key_pair, user_id, name="Acme Revenue")
        members = await client.get(
            f"/workspaces/{workspace['id']}/members", headers=_auth(key_pair, user_id)
        )

        assert workspace["name"] == "Acme Revenue"
        body = members.json()
        assert len(body["items"]) == 1
        assert body["items"][0]["user_id"] == str(user_id)
        assert body["items"][0]["role"] == "owner"

    async def test_rejects_blank_workspace_name_with_field_level_detail(
        self, client: AsyncClient, key_pair: KeyPair
    ) -> None:
        response = await client.post(
            "/workspaces", json={"name": "   ", "slug": _test_slug("   ")}, headers=_auth(key_pair, uuid4())
        )

        # Whitespace passes the schema's min_length but fails the domain
        # invariant, so this is the domain error, not a validation error.
        assert response.status_code == 422
        assert response.json()["error"]["code"] == "invalid_workspace_name"

    async def test_rejects_over_long_name_at_the_schema_boundary(
        self, client: AsyncClient, key_pair: KeyPair
    ) -> None:
        response = await client.post(
            "/workspaces", json={"name": "a" * 500, "slug": _test_slug("a" * 500)}, headers=_auth(key_pair, uuid4())
        )

        body = response.json()
        assert response.status_code == 422
        assert body["error"]["code"] == "validation_error"
        assert body["error"]["details"][0]["field"] == "name"

    async def test_adding_a_duplicate_member_conflicts(
        self, client: AsyncClient, key_pair: KeyPair
    ) -> None:
        owner = uuid4()
        workspace = await _create_workspace(client, key_pair, owner)

        response = await client.post(
            f"/workspaces/{workspace['id']}/members",
            json={"user_id": str(owner), "role": "member"},
            headers=_auth(key_pair, owner),
        )

        assert response.status_code == 409
        assert response.json()["error"]["code"] == "membership_already_exists"


class TestTenantIsolationOverHttp:
    async def test_non_member_gets_404_not_403(
        self, client: AsyncClient, key_pair: KeyPair
    ) -> None:
        """The security-critical case: a non-member must not be able to tell
        an existing workspace from a nonexistent one, or workspace ids become
        enumerable (18-authentication.md)."""
        owner, outsider = uuid4(), uuid4()
        workspace = await _create_workspace(client, key_pair, owner)

        real = await client.get(f"/workspaces/{workspace['id']}", headers=_auth(key_pair, outsider))
        fabricated = await client.get(f"/workspaces/{uuid4()}", headers=_auth(key_pair, outsider))

        assert real.status_code == 404
        assert fabricated.status_code == 404
        # Identical bodies apart from the per-request correlation id.
        assert real.json()["error"]["code"] == fabricated.json()["error"]["code"]
        assert real.json()["error"]["message"] == fabricated.json()["error"]["message"]

    async def test_listing_workspaces_returns_only_the_callers_own(
        self, client: AsyncClient, key_pair: KeyPair
    ) -> None:
        user_a, user_b = uuid4(), uuid4()
        workspace_a = await _create_workspace(client, key_pair, user_a, name="A")
        await _create_workspace(client, key_pair, user_b, name="B")

        response = await client.get("/workspaces", headers=_auth(key_pair, user_a))

        items = response.json()["items"]
        assert [item["id"] for item in items] == [workspace_a["id"]]

    async def test_non_member_cannot_add_themselves_to_a_workspace(
        self, client: AsyncClient, key_pair: KeyPair
    ) -> None:
        owner, attacker = uuid4(), uuid4()
        workspace = await _create_workspace(client, key_pair, owner)

        response = await client.post(
            f"/workspaces/{workspace['id']}/members",
            json={"user_id": str(attacker), "role": "owner"},
            headers=_auth(key_pair, attacker),
        )

        assert response.status_code == 404


class TestAuthorization:
    async def test_member_may_read_but_not_add_members(
        self, client: AsyncClient, key_pair: KeyPair
    ) -> None:
        owner, member = uuid4(), uuid4()
        workspace = await _create_workspace(client, key_pair, owner)
        await client.post(
            f"/workspaces/{workspace['id']}/members",
            json={"user_id": str(member), "role": "member"},
            headers=_auth(key_pair, owner),
        )

        read = await client.get(
            f"/workspaces/{workspace['id']}/members", headers=_auth(key_pair, member)
        )
        write = await client.post(
            f"/workspaces/{workspace['id']}/members",
            json={"user_id": str(uuid4()), "role": "member"},
            headers=_auth(key_pair, member),
        )

        assert read.status_code == 200
        # 403, not 404: membership is established, so the caller already
        # knows the workspace exists — only the role is insufficient.
        assert write.status_code == 403
        assert write.json()["error"]["code"] == "forbidden"

    async def test_owner_may_add_members(self, client: AsyncClient, key_pair: KeyPair) -> None:
        owner, invitee = uuid4(), uuid4()
        workspace = await _create_workspace(client, key_pair, owner)

        response = await client.post(
            f"/workspaces/{workspace['id']}/members",
            json={"user_id": str(invitee), "role": "member"},
            headers=_auth(key_pair, owner),
        )

        assert response.status_code == 201
        assert response.json()["user_id"] == str(invitee)


class TestErrorContract:
    async def test_every_error_carries_a_correlation_id_in_body_and_header(
        self, client: AsyncClient
    ) -> None:
        response = await client.get("/workspaces")

        assert response.headers["X-Correlation-ID"]
        assert response.json()["error"]["correlation_id"] == response.headers["X-Correlation-ID"]

    async def test_unrouted_path_uses_the_standard_envelope(self, client: AsyncClient) -> None:
        response = await client.get("/does-not-exist")

        assert response.status_code == 404
        assert response.json()["error"]["code"] == "not_found"


class TestPagination:
    async def test_paginates_workspaces_without_duplicates_or_gaps(
        self, client: AsyncClient, key_pair: KeyPair
    ) -> None:
        user_id = uuid4()
        for index in range(5):
            await _create_workspace(client, key_pair, user_id, name=f"WS {index}")

        first = (await client.get("/workspaces?limit=2", headers=_auth(key_pair, user_id))).json()
        second = (
            await client.get(
                f"/workspaces?limit=2&cursor={first['next_cursor']}",
                headers=_auth(key_pair, user_id),
            )
        ).json()
        third = (
            await client.get(
                f"/workspaces?limit=2&cursor={second['next_cursor']}",
                headers=_auth(key_pair, user_id),
            )
        ).json()

        collected = [w["id"] for page in (first, second, third) for w in page["items"]]
        assert len(collected) == 5
        assert len(set(collected)) == 5, "pages must not overlap"
        assert first["has_more"] is True
        assert third["has_more"] is False
        assert third["next_cursor"] is None

    async def test_rejects_a_malformed_cursor(self, client: AsyncClient, key_pair: KeyPair) -> None:
        response = await client.get(
            "/workspaces?cursor=not-a-real-cursor", headers=_auth(key_pair, uuid4())
        )

        assert response.status_code == 400
        assert response.json()["error"]["code"] == "invalid_cursor"

    async def test_enforces_the_maximum_page_size(
        self, client: AsyncClient, key_pair: KeyPair
    ) -> None:
        """An unbounded limit is a denial-of-service vector, so the ceiling is
        enforced at the schema boundary."""
        response = await client.get("/workspaces?limit=10000", headers=_auth(key_pair, uuid4()))

        assert response.status_code == 422


async def test_openapi_documents_the_authenticated_routes(client: AsyncClient) -> None:
    schema = (await client.get("/openapi.json")).json()

    assert "/workspaces" in schema["paths"]
    assert "/workspaces/{workspace_id}/members" in schema["paths"]


class TestAuthenticationObservability:
    """AUTH_* events must be emitted for the states the API can observe, and
    must never carry a token or PII."""

    async def test_rejected_token_emits_a_failure_event(
        self, client: AsyncClient, caplog: pytest.LogCaptureFixture
    ) -> None:
        with caplog.at_level(logging.WARNING, logger="signora.auth"):
            await client.get("/workspaces", headers={"Authorization": "Bearer garbage"})

        events = [r for r in caplog.records if getattr(r, "auth_event", None)]
        assert any(getattr(e, "auth_event", None) == "AUTH_TOKEN_REJECTED" for e in events)
        assert all(getattr(e, "outcome", None) == "failure" for e in events)

    async def test_missing_credentials_emits_a_rejection_event(
        self, client: AsyncClient, caplog: pytest.LogCaptureFixture
    ) -> None:
        with caplog.at_level(logging.WARNING, logger="signora.auth"):
            await client.get("/workspaces")

        assert any(
            getattr(r, "auth_event", None) == "AUTH_TOKEN_REJECTED"
            and getattr(r, "auth_reason", None) == "missing_credentials"
            for r in caplog.records
        )

    async def test_non_member_access_emits_workspace_access_denied(
        self, client: AsyncClient, key_pair: KeyPair, caplog: pytest.LogCaptureFixture
    ) -> None:
        owner, outsider = uuid4(), uuid4()
        workspace = await _create_workspace(client, key_pair, owner)

        with caplog.at_level(logging.WARNING, logger="signora.auth"):
            await client.get(f"/workspaces/{workspace['id']}", headers=_auth(key_pair, outsider))

        assert any(
            getattr(r, "auth_event", None) == "AUTH_WORKSPACE_ACCESS_DENIED" for r in caplog.records
        )

    async def test_accessing_a_workspace_not_in_the_token_emits_a_switch(
        self, client: AsyncClient, key_pair: KeyPair, caplog: pytest.LogCaptureFixture
    ) -> None:
        """A request naming a workspace other than the token's hint is how a
        user moves between tenants — worth recording."""
        owner = uuid4()
        workspace = await _create_workspace(client, key_pair, owner)

        with caplog.at_level(logging.INFO, logger="signora.auth"):
            await client.get(f"/workspaces/{workspace['id']}", headers=_auth(key_pair, owner))

        assert any(
            getattr(r, "auth_event", None) == "AUTH_WORKSPACE_SWITCH" for r in caplog.records
        )

    async def test_auth_events_never_carry_a_token(
        self, client: AsyncClient, key_pair: KeyPair, caplog: pytest.LogCaptureFixture
    ) -> None:
        token = mint_token(key_pair, user_id=uuid4())

        with caplog.at_level(logging.INFO, logger="signora.auth"):
            await client.get("/workspaces", headers={"Authorization": f"Bearer {token}"})

        rendered = " ".join(JsonFormatter().format(r) for r in caplog.records)
        assert token not in rendered
