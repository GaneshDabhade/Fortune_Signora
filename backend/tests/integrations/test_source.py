"""The inbound source port, and HubSpot wearing it.

**[ADR-0300](../../../docs/architecture/adr/0300-inbound-customer-systems.md)
Option A, approved by the product owner 2026-08-04** and awaiting integration
synchronization, specified by
[409](../../../docs/architecture/409-inbound-source-port-contract.md).

**Two things are under test and they are different.** The port's *boundaries*
are architectural guarantees — no subject, this module's `Capability` and not
Provider Platform's, no dependency on the driver — and they are asserted
structurally, because a violation would be ordinary code that happens to be
wrong. The wrapper's *translation* is behaviour, and it is exercised against
`httpx.MockTransport` with no vendor, no credential and no developer
application.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

import httpx
import pytest

from modules.integrations.domain.catalog import (
    CATALOG,
    LIVE_CAPABILITIES,
    Capability,
)
from modules.integrations.domain.execution import ExecutionContext
from modules.integrations.domain.grant import OAUTH2_KIND, Credential
from modules.integrations.domain.source import (
    IntegrationCapabilityUnsupportedError,
    IntegrationFetchRequest,
    IntegrationPage,
    IntegrationPayloadInvalidError,
    IntegrationRecord,
    IntegrationSourceAdapter,
    IntegrationSourceError,
    IntegrationSourcePermanentError,
    IntegrationSourceRateLimitedError,
    IntegrationSourceTransientError,
)
from modules.integrations.infrastructure.hubspot import HubSpotCompanies
from modules.integrations.infrastructure.hubspot_source import (
    HUBSPOT,
    HubSpotCompanySource,
)

WORKSPACE = uuid4()
ACCOUNT = uuid4()
MODIFIED = "2026-07-01T09:00:00Z"


def _context() -> ExecutionContext:
    return ExecutionContext(
        workspace_id=WORKSPACE,
        connected_account_id=ACCOUNT,
        integration=HUBSPOT,
        endpoint=None,
        scopes=("crm.objects.companies.read",),
        credential=Credential(
            kind=OAUTH2_KIND,
            material=json.dumps({"access_token": "at-1"}).encode(),
        ),
    )


def _company(identifier: str = "512", modified: object = MODIFIED) -> dict[str, Any]:
    return {
        "id": identifier,
        "properties": {"name": "Acme Corp", "hs_lastmodifieddate": modified},
    }


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


def _source(transport: httpx.MockTransport) -> HubSpotCompanySource:
    return HubSpotCompanySource(
        HubSpotCompanies(frozenset({"name", "hs_lastmodifieddate"}), transport=transport)
    )


def _request(**kw: Any) -> IntegrationFetchRequest:
    return IntegrationFetchRequest(
        context=_context(), capability=Capability.CRM_RECORDS, **kw
    )


class TestThePortIsASiblingAndNotAnExtension:
    """**The boundaries that made a new port worth its cost.** Each is a
    property a reviewer would otherwise have to notice in a diff."""

    def test_a_fetch_request_has_no_subject(self) -> None:
        """**The whole distinction, asserted.** A provider is asked about one
        company; a source is asked for the customer's own records, and an
        enumeration has no subject. A `subject` field appearing here would be
        the Provider Port arriving under a different name."""
        assert "subject" not in IntegrationFetchRequest.__dataclass_fields__

    def test_a_record_does_not_name_its_own_provider(self) -> None:
        """`ProviderRecord` carries one because the adapter knows which
        supplier it is. Here the slug is on `context.integration` — **one
        authoritative place**, and a record that carried its own could
        disagree with the connection it came from (§2)."""
        assert "provider" not in IntegrationRecord.__dataclass_fields__

    def test_the_port_uses_this_modules_capability(self) -> None:
        """**Two vocabularies, two owners.** `ProviderCapability` enumerates
        what suppliers sell — enrichment, technographics, workforce — and a
        CRM read is none of them. The type keeps them apart rather than a
        comment asking people to."""
        annotation = IntegrationFetchRequest.__annotations__["capability"]

        assert annotation is Capability or annotation == "Capability"

    def test_a_page_separates_the_cursor_from_whether_more_exists(self) -> None:
        """A source legitimately returns a cursor with no further records.
        Conflating them costs one empty request per sync, every sync."""
        page = IntegrationPage(records=(), next_cursor="abc", has_more=False)

        assert page.next_cursor == "abc"
        assert not page.has_more

    def test_the_port_imports_nothing_from_provider_platform(self) -> None:
        """**Integrations depends on nothing** — the ownership ruling of
        2026-08-02 made physical. Provider Platform drives this port; the port
        must not know that, or the dependency runs both ways and the modules
        stop being separable."""
        import modules.integrations.domain.source as source

        reached = {
            getattr(value, "__module__", "")
            for value in vars(source).values()
            if getattr(value, "__module__", None)
        }

        assert not [name for name in reached if name.startswith("modules.provider_platform")]

    def test_every_error_is_one_a_caller_can_classify(self) -> None:
        """The platform's decision is only *resume later* or *stop and
        alert*, so every failure must land on one side of that line."""
        transient = {IntegrationSourceTransientError, IntegrationSourceRateLimitedError}
        permanent = {IntegrationSourcePermanentError, IntegrationCapabilityUnsupportedError}

        for error in transient | permanent | {IntegrationPayloadInvalidError}:
            assert issubclass(error, IntegrationSourceError)
        assert issubclass(IntegrationSourceRateLimitedError, IntegrationSourceTransientError)
        assert issubclass(IntegrationCapabilityUnsupportedError, IntegrationSourcePermanentError)


class TestTheCapabilityIsAddedWithoutBeingPromised:
    def test_crm_records_exists(self) -> None:
        assert Capability.CRM_RECORDS.value == "crm_records"

    def test_it_is_not_advertised_until_something_drives_it(self) -> None:
        """**The honesty rule the Connection Center is built on.** The port
        exists and nothing runs it — the runner is 409 step 4, in another
        module. Advertising the capability now would promise a customer
        something the pipeline cannot deliver."""
        assert Capability.CRM_RECORDS not in LIVE_CAPABILITIES

    def test_no_catalog_entry_offers_it_yet(self) -> None:
        """A catalog entry claiming it would reach a screen through
        `live_capabilities`, which filters on the set above — so this asserts
        the same promise one layer up, where a customer would read it."""
        offering = [e.slug for e in CATALOG.values() if Capability.CRM_RECORDS in e.capabilities]

        assert offering == []


class TestHubSpotWearingThePort:
    def test_it_describes_itself_without_a_network_call(self) -> None:
        """A descriptor a caller cannot obtain while the vendor is down is a
        descriptor that fails exactly when somebody is diagnosing an outage."""
        transport, seen = _transport({"results": []})

        descriptor = _source(transport).describe()

        assert descriptor.integration == HUBSPOT
        assert descriptor.capabilities == (Capability.CRM_RECORDS,)
        assert seen == []

    async def test_a_page_becomes_records_with_their_own_identity_and_time(self) -> None:
        transport, _ = _transport({"results": [_company("512")]})

        page = await _source(transport).fetch(_request())

        assert len(page.records) == 1
        assert page.records[0].external_id == "512"
        assert page.records[0].occurred_at == datetime(2026, 7, 1, 9, 0, tzinfo=UTC)

    async def test_the_payload_arrives_untouched(self) -> None:
        """**Nothing is stripped, renamed or normalised.** Interpreting it is
        `HubSpotCompanyMapper`'s job, and a wrapper that reshaped anything
        would put the vendor's contract in two places."""
        raw = _company("512")
        transport, _ = _transport({"results": [raw]})

        page = await _source(transport).fetch(_request())

        assert page.records[0].payload == raw

    async def test_epoch_milliseconds_are_read_too(self) -> None:
        """HubSpot's search endpoint answers in epoch milliseconds and its
        listing endpoint in ISO-8601. **Both are read and neither is
        guessed** — the field is what a watermark advances on."""
        transport, _ = _transport({"results": [_company("512", modified=1782000000000)]})

        page = await _source(transport).fetch(_request())

        assert page.records[0].occurred_at.tzinfo is not None

    async def test_the_loop_parameters_pass_through_unchanged(self) -> None:
        """`since` selects the incremental endpoint inside the fetcher. **The
        wrapper does not choose** — a wrapper that did would reimplement a
        choice the fetcher already owns, and the two would drift."""
        transport, seen = _transport({"results": [], "paging": {}})

        await _source(transport).fetch(
            _request(since=datetime(2026, 6, 1, tzinfo=UTC), limit=25)
        )

        assert seen[0].method == "POST", "an incremental read is the search endpoint"

    async def test_a_full_snapshot_reads_the_listing_endpoint(self) -> None:
        transport, seen = _transport({"results": []})

        await _source(transport).fetch(_request())

        assert seen[0].method == "GET"

    async def test_a_capability_it_does_not_answer_for_is_refused(self) -> None:
        """**Permanent by construction.** Asking again changes nothing, and
        the honest response is that this source does not offer it."""
        transport, seen = _transport({"results": []})

        with pytest.raises(IntegrationCapabilityUnsupportedError):
            await _source(transport).fetch(
                IntegrationFetchRequest(
                    context=_context(), capability=Capability.MEETINGS
                )
            )

        assert seen == [], "nothing should have been asked"


class TestEveryVendorFailureBecomesOneThePlatformCanActOn:
    """One-to-one, per 409 §3. **A vendor exception escaping the wrapper
    would make Provider Platform import this module's infrastructure to catch
    it**, which is the boundary the port exists to hold."""

    async def test_a_rate_limit_keeps_the_vendors_own_wait(self) -> None:
        transport, _ = _transport(
            {"message": "slow down"}, status=429, headers={"retry-after": "30"}
        )

        with pytest.raises(IntegrationSourceRateLimitedError) as raised:
            await _source(transport).fetch(_request())

        assert raised.value.retry_after_seconds == 30.0

    async def test_an_outage_is_transient(self) -> None:
        transport, _ = _transport({"message": "oops"}, status=503)

        with pytest.raises(IntegrationSourceTransientError):
            await _source(transport).fetch(_request())

    async def test_a_rejected_credential_is_permanent(self) -> None:
        transport, _ = _transport({"message": "expired"}, status=401)

        with pytest.raises(IntegrationSourcePermanentError):
            await _source(transport).fetch(_request())

    async def test_a_missing_permission_is_permanent_too(self) -> None:
        """Both stop the sync, and **the distinction that decides what a
        customer is told survives on the connection's health** — reconnecting
        fixes one and not the other."""
        transport, _ = _transport({"message": "missing scope"}, status=403)

        with pytest.raises(IntegrationSourcePermanentError):
            await _source(transport).fetch(_request())

    async def test_something_that_is_not_json_is_a_payload_problem(self) -> None:
        transport, _ = _transport("<html>maintenance</html>")

        with pytest.raises(IntegrationPayloadInvalidError):
            await _source(transport).fetch(_request())

    async def test_no_vendor_exception_escapes(self) -> None:
        """The property the wrapper exists to hold, over every status a
        vendor can return."""
        for status in (400, 401, 403, 409, 429, 500, 503):
            transport, _ = _transport({"message": "no"}, status=status)

            with pytest.raises(IntegrationSourceError):
                await _source(transport).fetch(_request())


class TestARecordThatCannotBeTrusted:
    async def test_a_record_with_no_id_stops_the_page(self) -> None:
        """**A record with no identity cannot be deduplicated**, so it is not
        a record. Raised rather than dropped: a silently shrinking page reads
        as a quiet one."""
        transport, _ = _transport({"results": [{"properties": {"hs_lastmodifieddate": MODIFIED}}]})

        with pytest.raises(IntegrationPayloadInvalidError):
            await _source(transport).fetch(_request())

    async def test_a_record_with_no_modified_time_stops_the_page(self) -> None:
        """**The single most important line in the wrapper.** `occurred_at` is
        what the watermark advances on, and defaulting it to `now()` would
        move the position past records nobody has seen — a silent skip, which
        is exactly [B-004](../../../docs/BUGS.md)'s class."""
        transport, _ = _transport({"results": [{"id": "512", "properties": {}}]})

        with pytest.raises(IntegrationPayloadInvalidError):
            await _source(transport).fetch(_request())

    async def test_an_unreadable_modified_time_is_not_guessed(self) -> None:
        transport, _ = _transport({"results": [_company("512", modified="not a date")]})

        with pytest.raises(IntegrationPayloadInvalidError):
            await _source(transport).fetch(_request())

    @pytest.mark.parametrize("modified", [99999999999999999999, True, {"nested": 1}])
    async def test_a_time_that_cannot_be_a_time_is_refused(self, modified: object) -> None:
        """**Each of these would otherwise become a date.** An epoch beyond
        the calendar overflows, `True` is an `int` in Python and would read as
        1970, and an object is not a timestamp at all — and every one of them
        would advance the watermark to a moment that never happened."""
        transport, _ = _transport({"results": [_company("512", modified=modified)]})

        with pytest.raises(IntegrationPayloadInvalidError):
            await _source(transport).fetch(_request())

    async def test_a_credential_the_source_cannot_read_asks_nothing(self) -> None:
        transport, seen = _transport({"results": []})
        context = ExecutionContext(
            workspace_id=WORKSPACE,
            connected_account_id=ACCOUNT,
            integration=HUBSPOT,
            endpoint=None,
            scopes=(),
            credential=Credential(kind="bearer", material=b"not-oauth2"),
        )

        with pytest.raises(IntegrationSourcePermanentError) as raised:
            await _source(transport).fetch(
                IntegrationFetchRequest(context=context, capability=Capability.CRM_RECORDS)
            )

        assert seen == []
        assert "not-oauth2" not in str(raised.value), "§16 — no material in a message"


class TestTheWrapperSatisfiesThePort:
    def test_it_is_usable_wherever_the_port_is_named(self) -> None:
        """**Structural, because the Protocol is.** A wrapper that drifted
        from the signature would still import cleanly and fail at whatever
        runner tried to use it."""
        source: IntegrationSourceAdapter = _source(_transport({"results": []})[0])

        assert source.describe().integration == HUBSPOT
