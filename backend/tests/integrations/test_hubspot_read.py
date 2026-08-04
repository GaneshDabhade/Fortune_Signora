"""Reading a customer's companies out of HubSpot.

**Against `httpx.MockTransport`, and none of it waits on anything.** The
fetcher's inputs are a token, a watermark and a cursor; its output is raw
payloads. [ADR-0300](../../../docs/architecture/adr/0300-inbound-customer-systems.md)
decides who calls it and where the file lives — **all three options call
something that does exactly this**, so none of the behaviour below moves with
the ruling.

The one test that matters most is the last: **the properties this asks for and
the properties the mapper reads are the same set.** A CRM returns only what you
request, so a mismatch is a claim that silently never appears — no error, no
rejection, just a thinner record than the customer's CRM actually holds.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from typing import Any

import httpx
import pytest

from modules.integrations.infrastructure.hubspot import (
    MAX_PAGE_SIZE,
    CrmCredentialRejected,
    CrmPayloadInvalid,
    CrmPermanent,
    CrmRateLimited,
    CrmTransient,
    HubSpotCompanies,
)
from modules.provider_normalization.infrastructure.mappers.crm import HubSpotCompanyMapper

PROPERTIES = frozenset({"name", "domain", "industry", "numberofemployees"})
SINCE = datetime(2026, 7, 1, 12, tzinfo=UTC)


def _company(identifier: str = "512") -> dict[str, Any]:
    return {"id": identifier, "properties": {"name": "Acme Corp", "domain": "acme.example"}}


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


def _fetcher(transport: httpx.MockTransport) -> HubSpotCompanies:
    return HubSpotCompanies(PROPERTIES, transport=transport)


class TestAFullRead:
    async def test_it_asks_for_the_properties_it_was_given(self) -> None:
        transport, seen = _transport({"results": [_company()]})

        await _fetcher(transport).page(access_token="the-token")

        assert seen[0].url.params["properties"] == "domain,industry,name,numberofemployees"

    async def test_the_property_order_is_stable_across_runs(self) -> None:
        """**Insertion order is a hidden input** (§2).

        A set's iteration order would make one sync's request differ from
        another's for no declared reason, which defeats replaying a recorded
        run against a recorded response.
        """
        first, seen_first = _transport({"results": []})
        second, seen_second = _transport({"results": []})

        await HubSpotCompanies(PROPERTIES, transport=first).page(access_token="t")
        await HubSpotCompanies(
            frozenset(reversed(sorted(PROPERTIES))), transport=second
        ).page(access_token="t")

        assert seen_first[0].url.params["properties"] == seen_second[0].url.params["properties"]

    async def test_it_carries_the_customers_own_token(self) -> None:
        transport, seen = _transport({"results": []})

        await _fetcher(transport).page(access_token="the-token")

        assert seen[0].headers["authorization"] == "Bearer the-token"

    async def test_it_hands_the_payload_on_untouched(self) -> None:
        """**Interpreting it is the mapper's job.** A fetcher that reshaped
        anything would put HubSpot's contract in two places."""
        record = _company()
        transport, _ = _transport({"results": [record]})

        page = await _fetcher(transport).page(access_token="t")

        assert page.records == (record,)

    async def test_a_cursor_asks_for_the_next_page(self) -> None:
        transport, seen = _transport({"results": []})

        await _fetcher(transport).page(access_token="t", cursor="page-2")

        assert seen[0].url.params["after"] == "page-2"

    async def test_the_cursor_and_has_more_come_from_the_response(self) -> None:
        transport, _ = _transport(
            {"results": [_company()], "paging": {"next": {"after": "page-2"}}}
        )

        page = await _fetcher(transport).page(access_token="t")

        assert page.next_cursor == "page-2"
        assert page.has_more is True

    async def test_a_last_page_says_so(self) -> None:
        transport, _ = _transport({"results": [_company()]})

        page = await _fetcher(transport).page(access_token="t")

        assert page.next_cursor is None
        assert page.has_more is False

    async def test_an_empty_page_is_an_answer(self) -> None:
        """A workspace with no companies. **Not an error, and not a shape
        problem** — the two are distinguished below."""
        transport, _ = _transport({"results": []})

        page = await _fetcher(transport).page(access_token="t")

        assert page.records == ()

    @pytest.mark.parametrize("requested,sent", [(0, "1"), (5, "5"), (500, "100")])
    async def test_the_page_size_is_bounded_by_the_vendors_ceiling(
        self, requested: int, sent: str
    ) -> None:
        """Asking HubSpot for more than 100 is a `400`. Bounding here turns a
        caller's optimism into a smaller page rather than a failed sync."""
        transport, seen = _transport({"results": []})

        await _fetcher(transport).page(access_token="t", limit=requested)

        assert seen[0].url.params["limit"] == sent
        assert int(sent) <= MAX_PAGE_SIZE


class TestAnIncrementalRead:
    async def test_it_uses_the_search_endpoint(self) -> None:
        """**Two endpoints, one shape out.** Which one runs is this file's
        business; a caller that had to know would reimplement the choice."""
        transport, seen = _transport({"results": []})

        await _fetcher(transport).page(access_token="t", since=SINCE)

        assert seen[0].method == "POST"
        assert str(seen[0].url).endswith("/companies/search")

    async def test_it_filters_on_the_watermark_in_epoch_milliseconds(self) -> None:
        transport, seen = _transport({"results": []})

        await _fetcher(transport).page(access_token="t", since=SINCE)

        body = json.loads(seen[0].content)
        filters = body["filterGroups"][0]["filters"][0]
        assert filters["propertyName"] == "hs_lastmodifieddate"
        assert filters["value"] == str(int(SINCE.timestamp() * 1000))

    async def test_the_boundary_is_exclusive(self) -> None:
        """**`GT`, not `GTE`.** A record modified in the same millisecond as
        the previous run's boundary was already delivered, and re-delivering it
        is a duplicate the storage layer would then have to absorb."""
        transport, seen = _transport({"results": []})

        await _fetcher(transport).page(access_token="t", since=SINCE)

        assert json.loads(seen[0].content)["filterGroups"][0]["filters"][0]["operator"] == "GT"

    async def test_it_reads_oldest_first(self) -> None:
        """So a sync interrupted mid-way leaves a watermark that can be resumed
        from rather than a hole in the middle."""
        transport, seen = _transport({"results": []})

        await _fetcher(transport).page(access_token="t", since=SINCE)

        assert json.loads(seen[0].content)["sorts"] == [
            {"propertyName": "hs_lastmodifieddate", "direction": "ASCENDING"}
        ]

    async def test_a_cursor_is_carried_in_the_body(self) -> None:
        transport, seen = _transport({"results": []})

        await _fetcher(transport).page(access_token="t", since=SINCE, cursor="page-2")

        assert json.loads(seen[0].content)["after"] == "page-2"


class TestEveryFailureIsTranslated:
    """**No httpx exception escapes**, and the type says what to do next.

    A caller that had to handle `httpx.ConnectTimeout` alongside a vendor's
    JSON error body has not had the vendor abstracted from it at all (§15).
    """

    async def test_a_rejected_credential_is_its_own_failure(self) -> None:
        """**Retrying burns quota to no purpose.** This connection needs
        renewing or reconnecting, which is a different action from waiting."""
        transport, _ = _transport({"message": "expired"}, status=401)

        with pytest.raises(CrmCredentialRejected):
            await _fetcher(transport).page(access_token="t")

    async def test_a_missing_permission_is_permanent_but_not_a_credential_problem(
        self,
    ) -> None:
        """Reconnecting with the same permissions would fail identically."""
        transport, _ = _transport({"message": "scope"}, status=403)

        with pytest.raises(CrmPermanent) as raised:
            await _fetcher(transport).page(access_token="t")
        assert not isinstance(raised.value, CrmCredentialRejected)
        assert "permission" in str(raised.value)

    async def test_a_rate_limit_carries_the_vendors_own_wait(self) -> None:
        """**Guessing a backoff when the vendor stated one is how an
        integration gets throttled harder.**"""
        transport, _ = _transport({}, status=429, headers={"retry-after": "12"})

        with pytest.raises(CrmRateLimited) as raised:
            await _fetcher(transport).page(access_token="t")
        assert raised.value.retry_after_seconds == 12.0

    async def test_a_rate_limit_without_a_usable_wait_is_still_transient(self) -> None:
        transport, _ = _transport({}, status=429, headers={"retry-after": "soon"})

        with pytest.raises(CrmRateLimited) as raised:
            await _fetcher(transport).page(access_token="t")
        assert raised.value.retry_after_seconds is None
        assert isinstance(raised.value, CrmTransient)

    async def test_a_server_error_is_worth_retrying(self) -> None:
        transport, _ = _transport("<html>502</html>", status=502)

        with pytest.raises(CrmTransient):
            await _fetcher(transport).page(access_token="t")

    async def test_an_unreachable_vendor_is_transient(self) -> None:
        def explode(request: httpx.Request) -> httpx.Response:
            raise httpx.ConnectTimeout("nope", request=request)

        with pytest.raises(CrmTransient):
            await _fetcher(httpx.MockTransport(explode)).page(access_token="t")

    async def test_an_unexpected_refusal_is_permanent(self) -> None:
        transport, _ = _transport({"message": "bad request"}, status=400)

        with pytest.raises(CrmPermanent):
            await _fetcher(transport).page(access_token="t")

    @pytest.mark.parametrize(
        "body",
        ["<html>hello</html>", [1, 2, 3], {"total": 0}],
        ids=["not JSON", "not an object", "no results array"],
    )
    async def test_a_broken_contract_is_not_an_empty_page(self, body: object) -> None:
        """**An alert about the integration, not about one company.**

        Collapsing this into an empty page would make a vendor shape change
        look like a customer with no companies — and nothing would ever
        surface it.
        """
        transport, _ = _transport(body)

        with pytest.raises(CrmPayloadInvalid):
            await _fetcher(transport).page(access_token="t")

    async def test_entries_that_are_not_objects_are_dropped_and_reported(self) -> None:
        """The page is still usable; the anomaly is still visible."""
        transport, _ = _transport({"results": [_company(), "not a company"]})

        page = await _fetcher(transport).page(access_token="t")

        assert page.records == (_company(),)


class TestTheFetcherAndTheMapperAgree:
    def test_it_requests_exactly_what_the_mapper_reads(self) -> None:
        """**The loop between fetching and translating, closed.**

        HubSpot returns only the properties you ask for. A mapper that knows
        `industry` and a fetcher that never requests it produce a claim that
        silently never appears — no error, no rejection, and nothing in the
        product to notice. This is the assertion that makes adding a mapped
        property without requesting it fail loudly.
        """
        wanted = HubSpotCompanyMapper.translated_properties()

        fetcher = HubSpotCompanies(wanted)

        assert set(fetcher._properties) == set(wanted)
        assert "annualrevenue" in wanted
        assert "domain" in wanted
