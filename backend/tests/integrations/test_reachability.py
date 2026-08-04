"""Translating what HubSpot said into what the platform concluded.

**Against `httpx.MockTransport`, and nothing waits on anything.** These are the
deterministic half of §10: what a connection concludes from a `401` is
engineering behaviour, and a fake produces it faithfully. Whether HubSpot
actually returns `401` for a revoked token is the vendor's contract, and no
test here claims to know it.

**The whole file is about one property**: no failure escapes as an exception.
A raised error here would make *"the connection is broken"* indistinguishable
from *"the probe is broken"*, and only one of those is something a customer can
act on.
"""

from __future__ import annotations

import json
from typing import Any
from uuid import uuid4

import httpx
import pytest

from modules.integrations.application.resolve import ExecutionContext
from modules.integrations.domain.grant import OAUTH2_KIND, Credential
from modules.integrations.domain.health import ProbeResult
from modules.integrations.infrastructure.reachability import HubSpotReachability

WORKSPACE = uuid4()
ACCOUNT = uuid4()


def _context(credential: Credential | None = None) -> ExecutionContext:
    return ExecutionContext(
        workspace_id=WORKSPACE,
        connected_account_id=ACCOUNT,
        integration="hubspot",
        endpoint=None,
        scopes=("crm.objects.companies.read",),
        credential=credential
        or Credential(
            kind=OAUTH2_KIND,
            material=json.dumps({"access_token": "at-1"}).encode(),
        ),
    )


def _transport(
    body: object, status: int = 200, headers: dict[str, str] | None = None
) -> tuple[httpx.MockTransport, list[httpx.Request]]:
    seen: list[httpx.Request] = []

    def handle(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        if isinstance(body, str):
            return httpx.Response(status, text=body, headers=headers)
        return httpx.Response(status, json=body, headers=headers)

    return httpx.MockTransport(handle), seen


_PAGE: dict[str, Any] = {"results": [{"id": "1", "properties": {"name": "Acme"}}]}


class TestWhatHubSpotSaidBecomesWhatWeConcluded:
    async def test_a_successful_call_is_reachable(self) -> None:
        transport, _ = _transport(_PAGE)

        result = await HubSpotReachability(transport=transport).reach(_context())

        assert result.result is ProbeResult.REACHABLE
        assert result.detail is None

    async def test_an_empty_workspace_is_still_reachable(self) -> None:
        """**A customer with no companies in HubSpot has a working
        connection.** Treating an empty page as a failure would send somebody
        to reconnect an integration that is answering perfectly."""
        transport, _ = _transport({"results": []})

        result = await HubSpotReachability(transport=transport).reach(_context())

        assert result.result is ProbeResult.REACHABLE

    async def test_a_rejected_token_is_a_rejected_credential(self) -> None:
        transport, _ = _transport({"message": "expired"}, status=401)

        result = await HubSpotReachability(transport=transport).reach(_context())

        assert result.result is ProbeResult.CREDENTIAL_REJECTED

    async def test_a_missing_scope_is_not_a_rejected_credential(self) -> None:
        """**The distinction that decides what a customer is told.** A `403`
        means the token works and may not do this; reconnecting with the same
        permissions would fail identically, so calling it a credential problem
        sends them round a loop that cannot end."""
        transport, _ = _transport({"message": "missing scope"}, status=403)

        result = await HubSpotReachability(transport=transport).reach(_context())

        assert result.result is ProbeResult.PERMISSION_MISSING

    @pytest.mark.parametrize("status", [500, 502, 503])
    async def test_a_vendor_outage_establishes_nothing(self, status: int) -> None:
        transport, _ = _transport({"message": "oops"}, status=status)

        result = await HubSpotReachability(transport=transport).reach(_context())

        assert result.result is ProbeResult.UNAVAILABLE

    async def test_a_rate_limit_establishes_nothing_either(self) -> None:
        """**The vendor's business, not the customer's.** Rate limiting says
        Signora asked too often; it says nothing about whether the connection
        works, and degrading on it would blame a customer for the platform's
        pacing."""
        transport, _ = _transport({"message": "slow down"}, status=429)

        result = await HubSpotReachability(transport=transport).reach(_context())

        assert result.result is ProbeResult.UNAVAILABLE

    async def test_a_response_that_is_not_json_is_the_integrations_problem(self) -> None:
        transport, _ = _transport("<html>maintenance</html>")

        result = await HubSpotReachability(transport=transport).reach(_context())

        assert result.result is ProbeResult.UNUSABLE_RESPONSE

    async def test_a_dropped_connection_establishes_nothing(self) -> None:
        def explode(request: httpx.Request) -> httpx.Response:
            raise httpx.ConnectError("no route to host")

        result = await HubSpotReachability(transport=httpx.MockTransport(explode)).reach(
            _context()
        )

        assert result.result is ProbeResult.UNAVAILABLE

    async def test_no_failure_escapes_as_an_exception(self) -> None:
        """**The property the whole adapter exists to hold.** Every status a
        vendor can return, and none of them raises — because a raised error
        would make an unreachable connection indistinguishable from a broken
        probe, and the second is the one nobody would notice."""
        for status in (400, 401, 403, 404, 409, 418, 429, 500, 503):
            transport, _ = _transport({"message": "no"}, status=status)

            result = await HubSpotReachability(transport=transport).reach(_context())

            assert result.result is not ProbeResult.REACHABLE, status


class TestTheProbeAsksTheSmallestQuestionItCan:
    async def test_it_reads_one_record_with_one_property(self) -> None:
        """**Not the mapper's full property set.** A probe that asked for
        everything a sync asks for would fail differently from a sync for
        reasons that have nothing to do with the connection — and it would
        spend a customer's quota on Signora's bookkeeping."""
        transport, seen = _transport(_PAGE)

        await HubSpotReachability(transport=transport).reach(_context())

        assert len(seen) == 1
        assert seen[0].url.params["limit"] == "1"
        assert seen[0].url.params["properties"] == "name"

    async def test_it_reads_rather_than_writes(self) -> None:
        """A probe that mutated a customer's CRM to prove it could reach it
        would be the worst possible way to answer this question."""
        transport, seen = _transport(_PAGE)

        await HubSpotReachability(transport=transport).reach(_context())

        assert seen[0].method == "GET"


class TestAnUnreadableCredential:
    async def test_it_is_conclusive_and_nothing_is_asked(self) -> None:
        transport, seen = _transport(_PAGE)
        credential = Credential(kind="bearer", material=b"not-oauth2")

        result = await HubSpotReachability(transport=transport).reach(
            _context(credential)
        )

        assert result.result is ProbeResult.CREDENTIAL_REJECTED
        assert seen == [], "nothing should have been sent"

    async def test_the_reason_names_no_part_of_the_credential(self) -> None:
        """**§16.** A detail is stored on the probe and read by whoever is
        debugging; a reason that quoted the material would put a customer's
        credential in a table that is backed up and replicated."""
        transport, _ = _transport(_PAGE)
        credential = Credential(
            kind=OAUTH2_KIND, material=json.dumps({"access_token": ""}).encode()
        )

        result = await HubSpotReachability(transport=transport).reach(
            _context(credential)
        )

        assert result.detail is not None
        assert "access_token" not in result.detail
