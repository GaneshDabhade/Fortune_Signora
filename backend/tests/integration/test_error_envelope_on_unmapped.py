"""An unmapped exception still gets the envelope — which is what closes [C-009](../../../docs/LANE_COORDINATION.md).

## 🔴 The obstacle C-009 recorded, and why it no longer exists

**C-009 is real**: `OpportunityError` maps to `422 transition_refused`, and it
serves both a genuine refusal — *"a won deal does not reopen"* — and an internal
invariant violation. ⛔ **A `422` tells a customer they sent something wrong**,
and a support engineer reading `transition_refused` goes to the transition
table, which is fine. 📁 That is [§10](../../../CLAUDE.md)'s failure-attribution
rule in the API layer: *"an incorrect attribution is worse than none, because it
misdirects the investigation."*

⚠️ **But the item then said a lane could not fix it**, on this reasoning:

> *"The correct split is a refusal base that maps to 422 and an invariant base
> that maps to nothing, so it surfaces as a 500 … splitting the hierarchy today
> trades a wrong code for a MISSING ENVELOPE, which is worse: `correlation_id`
> is the only thread between a customer's report and the logs."*

✅ **That premise does not hold.** `register_exception_handlers` installs a
catch-all `Exception` handler that returns the full envelope — `code`,
`message`, `correlation_id` in the body **and** in the `X-Correlation-Id`
header. **An unmapped exception is a `500` WITH the thread, not without it.**

⚡ **So the split is available to any module today**, and these tests are the
evidence rather than the assertion. ⛔ **They are written here rather than as a
note on the item because a claim about the envelope should be checkable by
running something.**
"""

from __future__ import annotations

import httpx
from fastapi import FastAPI

from signora_platform.api import register_exception_handlers


class RefusalError(Exception):
    """What a customer did that the domain declines — maps to a client code."""


class InvariantError(Exception):
    """What the system got wrong — deliberately mapped to NOTHING.

    ⚡ **This is the shape C-009 asks for**: a module splits its hierarchy, maps
    only the refusal half, and lets the other half fall through.
    """


def _app() -> FastAPI:
    app = FastAPI()
    register_exception_handlers(app, domain_errors={RefusalError: (422, "transition_refused")})

    @app.get("/refusal")
    async def refusal() -> None:
        raise RefusalError("a won deal does not reopen")

    @app.get("/invariant")
    async def invariant() -> None:
        raise InvariantError("an opportunity has no account, which cannot happen")

    return app


def _client(app: FastAPI) -> httpx.AsyncClient:
    return httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app, raise_app_exceptions=False),
        base_url="http://testserver",
    )


class TestTheSplitIsAvailableToday:
    async def test_a_mapped_refusal_keeps_its_client_code(self) -> None:
        """✅ **The half that was already right stays right.**"""
        async with _client(_app()) as client:
            response = await client.get("/refusal")

        assert response.status_code == 422
        assert response.json()["error"]["code"] == "transition_refused"

    async def test_an_unmapped_invariant_is_a_500_WITH_the_envelope(self) -> None:
        """🔴 **The claim C-009 rested on, tested.**

        ⛔ **If the envelope were missing here, C-009's reasoning would stand**
        and no module could split its hierarchy without losing the only thread
        between a customer's report and the logs.
        """
        async with _client(_app()) as client:
            response = await client.get("/invariant")

        assert response.status_code == 500
        body = response.json()["error"]
        assert body["code"] == "internal_error"
        assert body["correlation_id"]

    async def test_the_correlation_id_is_on_the_HEADER_too(self) -> None:
        """⚡ **The header is what a support engineer can ask a customer for.**

        A body field requires somebody to have kept the response; a header is
        what a browser's network tab shows and what a proxy log records.
        """
        async with _client(_app()) as client:
            response = await client.get("/invariant")

        assert response.headers["x-correlation-id"]
        assert response.headers["x-correlation-id"] == response.json()["error"]["correlation_id"]

    async def test_the_internal_message_never_reaches_the_caller(self) -> None:
        """⛔ **A 500 must not leak what went wrong internally.**

        ⚠️ **This is the property that makes the 500 acceptable**: the caller
        gets a thread to follow, and the detail stays in the logs. **Without
        it, splitting the hierarchy would trade a misleading code for a leak.**
        """
        async with _client(_app()) as client:
            response = await client.get("/invariant")

        rendered = response.text
        assert "an opportunity has no account" not in rendered
        assert "InvariantError" not in rendered

    async def test_two_requests_get_different_threads(self) -> None:
        """⚠️ **A correlation id shared between requests is not a thread.**

        It would point a support engineer at somebody else's failure, which is
        the misdirection C-009 is about, one layer over.
        """
        async with _client(_app()) as client:
            first = await client.get("/invariant")
            second = await client.get("/invariant")

        assert first.headers["x-correlation-id"] != second.headers["x-correlation-id"]
