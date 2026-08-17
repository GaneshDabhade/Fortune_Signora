"""The limiter at the edge — refusal, exemption, and the degraded path.

**[ADR-0408](../../../docs/architecture/adr/0408-inbound-rate-limiting.md) §5:**
*"the failure mode this must be tested for, and it is not the happy path."*

⚡ **The degraded path is why `CounterStore` is a port.** A real Redis cannot be
made to time out on demand, so a limiter built directly against a client has a
fail-open branch that no test ever executes — **and a fail-open that has never
run is indistinguishable from one that fails closed** until the outage.
"""

from __future__ import annotations

import asyncio
import logging

import httpx
import pytest
from fastapi import FastAPI

from signora_platform.api.rate_limit import (
    COUNTER_TIMEOUT_SECONDS,
    InMemoryCounterStore,
    RateLimiter,
    RateLimitMiddleware,
    RateLimitSettings,
)


class _Refusing:
    """A store that cannot answer — a Redis outage, in one class."""

    def __init__(self, failure: Exception) -> None:
        self._failure = failure

    async def increment(self, key: str, window_seconds: int) -> int:
        raise self._failure


class _Hanging:
    """A store that answers too late, which is the worse outage."""

    async def increment(self, key: str, window_seconds: int) -> int:
        await asyncio.sleep(COUNTER_TIMEOUT_SECONDS * 20)
        return 1


def _app(limiter: RateLimiter) -> FastAPI:
    app = FastAPI()

    @app.get("/health")
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/workspaces/{workspace_id}/products")
    async def products(workspace_id: str) -> dict[str, str]:
        return {"workspace": workspace_id}

    # **`app.routes` is passed deliberately** — without it the middleware
    # keys on the concrete path and limits nothing.
    app.add_middleware(RateLimitMiddleware, limiter=limiter, routes=app.routes)
    return app


def _client(app: FastAPI) -> httpx.AsyncClient:
    return httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app, client=("203.0.113.9", 5000)),
        base_url="http://testserver",
    )


class TestItRefusesAtTheBudget:
    async def test_the_request_past_the_budget_gets_429(self) -> None:
        limiter = RateLimiter(
            InMemoryCounterStore(), RateLimitSettings(window_seconds=60, max_requests=3)
        )
        async with _client(_app(limiter)) as client:
            codes = [
                (await client.get("/workspaces/w1/products")).status_code
                for _ in range(5)
            ]

        assert codes == [200, 200, 200, 429, 429]

    async def test_the_refusal_carries_retry_after_and_says_nothing_else(self) -> None:
        """⛔ **ADR-0408 §3: a refusal must not be an enumeration oracle.**

        **No account state, no whether-this-caller-is-known.** The body is the
        same bytes for everybody, and `Retry-After` is the window rather than
        the caller's own position — **which would leak how much budget somebody
        else had spent.**
        """
        limiter = RateLimiter(
            InMemoryCounterStore(), RateLimitSettings(window_seconds=30, max_requests=1)
        )
        async with _client(_app(limiter)) as client:
            await client.get("/workspaces/w1/products")
            refused = await client.get("/workspaces/w1/products")

        assert refused.status_code == 429
        assert refused.headers["retry-after"] == "30"
        assert refused.json() == {
            "error": {"code": "rate_limited", "message": "Too many requests."}
        }

    async def test_a_concrete_id_does_not_buy_a_fresh_budget(self) -> None:
        """🔴 **The route TEMPLATE is the key**, so walking ids does not evade it.

        ⚡ **This is the one that would have made the limiter decorative**: with
        a per-path key, `/accounts/a1`, `/accounts/a2`, … each get a full
        budget and nothing is ever limited, while the counter graph looks busy
        and healthy.
        """
        limiter = RateLimiter(
            InMemoryCounterStore(), RateLimitSettings(window_seconds=60, max_requests=2)
        )
        async with _client(_app(limiter)) as client:
            await client.get("/workspaces/w1/products")
            await client.get("/workspaces/w2/products")
            third = await client.get("/workspaces/w3/products")

        assert third.status_code == 429


class TestTheProbesAreExempt:
    async def test_liveness_is_never_limited(self) -> None:
        """⛔ **An orchestrator polls `/health` continuously from one address.**

        Limiting it means the limiter eventually reports the process unhealthy
        and something restarts it — **a control that causes the outage it was
        added to prevent.**
        """
        limiter = RateLimiter(
            InMemoryCounterStore(), RateLimitSettings(window_seconds=60, max_requests=2)
        )
        async with _client(_app(limiter)) as client:
            codes = [(await client.get("/health")).status_code for _ in range(10)]

        assert codes == [200] * 10


class TestItFailsOpenAndSaysSo:
    async def test_an_unreachable_store_allows_the_request(self) -> None:
        """✅ **ADR-0408 §12's ruling, and it is deliberately asymmetric.**

        ⛔ **Fail-closed would turn a Redis outage into a total API outage for
        every legitimate customer**, which is the larger harm.
        """
        limiter = RateLimiter(
            _Refusing(ConnectionError("redis is gone")),
            RateLimitSettings(window_seconds=60, max_requests=1),
        )
        async with _client(_app(limiter)) as client:
            codes = [
                (await client.get("/workspaces/w1/products")).status_code
                for _ in range(4)
            ]

        assert codes == [200] * 4

    async def test_a_slow_store_is_bounded_rather_than_waited_on(self) -> None:
        """⚠️ **A limiter that adds unbounded latency has become the outage.**

        The store here sleeps twenty times the budget; the request must still
        complete promptly, on the timeout rather than on the store.
        """
        limiter = RateLimiter(
            _Hanging(), RateLimitSettings(window_seconds=60, max_requests=1)
        )
        started = asyncio.get_running_loop().time()
        async with _client(_app(limiter)) as client:
            response = await client.get("/workspaces/w1/products")
        elapsed = asyncio.get_running_loop().time() - started

        assert response.status_code == 200
        assert elapsed < COUNTER_TIMEOUT_SECONDS * 10

    async def test_the_degradation_is_LOUD_rather_than_silent(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        """🔴 **A silent fail-open is the [§2](../../../CLAUDE.md) decorative guard.**

        ⛔ **Protection that has stopped protecting, with nothing saying so.**
        ⚡ **Both halves are asserted: a WARNING a human can see, and a counter
        something can alert on** — ADR-0408 §12 asks for the second because
        *"it is not a log line nobody reads."*
        """
        limiter = RateLimiter(
            _Refusing(ConnectionError("redis is gone")),
            RateLimitSettings(window_seconds=60, max_requests=1),
        )
        with caplog.at_level(logging.WARNING):
            async with _client(_app(limiter)) as client:
                await client.get("/workspaces/w1/products")
                await client.get("/workspaces/w1/products")

        assert limiter.degraded_checks == 2
        assert any(r.message == "rate_limit_degraded" for r in caplog.records)

    async def test_recovery_resumes_enforcement_without_a_restart(self) -> None:
        """⚡ **Degraded is a state, not a latch.**

        A limiter that stayed open after one failure would be permanently
        disabled by a single blip, which is the quiet way a control dies.
        """
        store = InMemoryCounterStore()
        limiter = RateLimiter(store, RateLimitSettings(window_seconds=60, max_requests=1))
        limiter._store = _Refusing(ConnectionError("blip"))  # type: ignore[assignment]

        assert (await limiter.check("k")).allowed is True

        limiter._store = store  # type: ignore[assignment]
        assert (await limiter.check("k")).allowed is True
        assert (await limiter.check("k")).allowed is False


class TestDisablingIsAnExplicitChoice:
    async def test_disabled_lets_everything_through(self) -> None:
        """⚠️ **`enabled: false` is a configuration decision, not a default.**

        It exists so an operator can turn the control off deliberately; the
        test is here so that turning it off is visible rather than a side
        effect of a missing setting.
        """
        limiter = RateLimiter(
            InMemoryCounterStore(),
            RateLimitSettings(enabled=False, window_seconds=60, max_requests=1),
        )
        async with _client(_app(limiter)) as client:
            codes = [
                (await client.get("/workspaces/w1/products")).status_code
                for _ in range(5)
            ]

        assert codes == [200] * 5
