"""Inbound rate limiting at the API edge — [ADR-0408](../../../docs/architecture/adr/0408-inbound-rate-limiting.md).

## 🔴 What this protects, and what it deliberately does not

**[C-287](../../../docs/LANE_COORDINATION.md) ruled ⓓ — two policies, product
owner, 2026-08-17.** The two are not interchangeable and neither covers the
other:

| Policy | Where | What it protects |
|---|---|---|
| **Authentication abuse** | **Better Auth, in Next.js** (`lib/auth/server.ts`) | `/signin` · `/register` · reset request · verification resend |
| **Business API throttling** | ⚡ **This file** | Every route the Python tier serves |

⛔ **This middleware can never see `/signin`.** Those routes live in Next.js
permanently ([§13](../../../CLAUDE.md), [ADR-0026](../../../docs/architecture/adr/0026-jwt-boundary-architecture.md)):
Better Auth is the sole Authentication Authority and this tier only verifies
tokens. **ADR-0408 §4 specified an ASGI middleware here and §10 named routes
that are not here — that contradiction is what C-287 raised**, and the ruling
resolved it by building both rather than pretending one covers both.

⚠️ **ADR-0408 §13 places business-API throttling OUTSIDE its own scope** —
*"authenticated routes, capacity protection, fair use … does not belong in the
same slice."* ⛔ **So this file is authorized by the C-287 ⓓ ruling, not by
ADR-0408 alone**, and that is stated rather than blurred. 📁 The measurement
behind it: **all 105 Python-tier routes carry a workspace or user context, so
ADR-0408's own scope — unauthenticated credential-sensitive routes — has no
members in this tier.** A limiter built strictly to §10 here would guard
nothing.

## ⚡ Fail-open, loudly — ADR-0408 §12

**A Redis outage must not become a sign-in outage**, so a limiter that cannot
reach its counters allows the request. ⛔ **But a silent fail-open is the
[§2](../../../CLAUDE.md) decorative guard** — protection that has stopped
protecting with nothing saying so. **Every degraded request emits a `WARNING`
carrying `correlation_id`, and `degraded_checks` counts them for something to
alert on.**

⛔ **No per-process fallback.** ADR-0408 §12 assessed one and rejected it: it
re-introduces the *n* × budget the Redis decision exists to avoid, **exactly
when the system is already degraded.**

## ⛔ What this must never become

**A second authorization layer.** Casbin decides *who may*; this decides *how
often anyone may*. **A limiter that reads a workspace claim to choose a limit
has started making authorization decisions in a component that runs before
authorization** — so the key is derived from the route template and the
caller's transport identity, and **never from a tenancy claim.**
"""

from __future__ import annotations

import asyncio
import logging
import time
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Final, Protocol

from starlette.routing import BaseRoute, Match

from signora_platform.rate_limit_settings import RateLimitSettings
from starlette.types import ASGIApp, Message, Receive, Scope, Send

_LOG: Final = logging.getLogger(__name__)

#: **Bounded, and never the client default** (ADR-0408 §12). A limiter that
#: adds unbounded latency to every request has become the outage it avoided.
COUNTER_TIMEOUT_SECONDS: Final = 0.05

#: The header a refused caller is given. Named here because the value is the
#: same for every route and a per-caller value would be an oracle.
RETRY_AFTER: Final = "retry-after"




class CounterStore(Protocol):
    """The one operation a limiter needs, and nothing else.

    A port rather than a Redis client, so the middleware's own tests never
    need a server and so the failure paths are reachable — ADR-0408 §5 asks
    for the failure mode to be tested, and a real client cannot be made to
    fail on demand.
    """

    async def increment(self, key: str, window_seconds: int) -> int:
        """Requests seen for `key` in the current window, including this one."""
        ...


@dataclass
class Decision:
    """What the limiter concluded, and enough to explain it."""

    allowed: bool
    remaining: int
    retry_after: int


class RateLimiter:
    """The counting, separated from the ASGI plumbing so both are testable."""

    def __init__(self, store: CounterStore, settings: RateLimitSettings) -> None:
        self._store = store
        #: Public because the middleware reads `enabled`, and reaching into a
        #: private attribute across a collaborator is how a boundary rots.
        self.settings = settings
        #: 🔴 **The alertable number** (ADR-0408 §12). *"Rate limiting is
        #: currently not enforced"* is an operational condition somebody must
        #: be able to see — **it is not a log line nobody reads.**
        self.degraded_checks = 0

    async def check(self, key: str, *, correlation_id: str | None = None) -> Decision:
        settings = self.settings
        try:
            async with asyncio.timeout(COUNTER_TIMEOUT_SECONDS):
                seen = await self._store.increment(key, settings.window_seconds)
        except Exception as failure:
            # ⛔ **Broad, and it is the decision rather than laziness.**
            # ADR-0408 §12: *"on timeout or error — allow the request,
            # increment a failure counter, and emit a WARN."* **A timeout, a
            # connection refusal and a protocol error are indistinguishable to
            # a caller** and must not produce different protection; naming a
            # tuple here would mean the next unnamed error type fails CLOSED,
            # turning a Redis fault into the sign-in outage this refuses.
            self.degraded_checks += 1
            _LOG.warning(
                "rate_limit_degraded",
                extra={
                    "correlation_id": correlation_id,
                    "reason": type(failure).__name__,
                    "degraded_checks": self.degraded_checks,
                },
            )
            return Decision(allowed=True, remaining=settings.max_requests, retry_after=0)

        remaining = max(0, settings.max_requests - seen)
        return Decision(
            allowed=seen <= settings.max_requests,
            remaining=remaining,
            # **One window, for everybody.** A per-caller `Retry-After` computed
            # from their own position leaks how much of the budget somebody
            # else has spent — the enumeration oracle ADR-0408 §3 rejects.
            retry_after=settings.window_seconds,
        )


def identity_of(scope: Scope) -> str:
    """What the limiter counts against.

    🔴 **Key on what an attacker cannot choose on somebody else's behalf**
    (ADR-0408 §14). ⛔ **Never a submitted address, never a workspace claim**:
    the first lets anybody spend a customer's budget for them, and the second
    is an authorization read in a component that runs before authorization.

    ⚠️ **The client address is the honest available answer and it is not a
    strong one** — behind a proxy every caller shares it until a trusted
    forwarded-header configuration exists, which is infrastructure and is
    deferred to M14.5 with the rest ([§20b](../../../CLAUDE.md)). **Stated
    rather than hidden**: this bounds a burst, and it does not bound a
    distributed one.
    """
    client = scope.get("client")
    return client[0] if client else "unknown"


def route_of(scope: Scope, routes: Sequence[BaseRoute] = ()) -> str:
    """The route TEMPLATE, never the concrete path.

    ⛔ **`/workspaces/{workspace_id}/products` and not `/workspaces/abc/products`.**
    Keying on the concrete path gives every id its own budget, so an attacker
    walking ids is never limited at all — **a limiter that counts the wrong
    thing is worse than none, because the metric looks healthy throughout.**

    ## 🔴 Why this matches routes itself instead of reading `scope["route"]`

    ADR-0408 §4 puts this middleware **before routing**, and `scope["route"]`
    is populated **by** routing — so the obvious implementation reads a key
    that is always absent and silently falls back to the concrete path.
    ⚠️ **Written that way first, and `test_a_concrete_id_does_not_buy_a_fresh_budget`
    caught it**: three requests to three workspaces all passed a budget of two.

    ⚡ **So the templates are resolved here, against the same route table the
    router will use.** `matches()` is Starlette's own predicate and performs no
    dispatch — this asks *which route would handle this*, without handling it.
    """
    for route in routes:
        match, _ = route.matches(scope)
        if match is not Match.NONE:
            path_format = getattr(route, "path_format", None)
            if isinstance(path_format, str):
                return path_format
    raw = scope.get("path", "/")
    return raw if isinstance(raw, str) else "/"


class RateLimitMiddleware:
    """Pure ASGI, so it runs before routing and before authorization.

    ⚠️ **Registered so that it runs AFTER correlation-id assignment**
    (ADR-0408 §4) — a refused request must still be traceable
    ([§16](../../../CLAUDE.md)).
    """

    def __init__(
        self,
        app: ASGIApp,
        limiter: RateLimiter,
        *,
        routes: Sequence[BaseRoute] = (),
        exempt: frozenset[str] = frozenset({"/health", "/ready"}),
    ) -> None:
        self._app = app
        self._limiter = limiter
        #: **The route table, so templates can be resolved before routing.**
        #: ⛔ Empty means every request keys on its concrete path, which is the
        #: no-limit-at-all failure `route_of` documents — so the composition
        #: root passes `app.routes` and the middleware is useless without it.
        self._routes = routes
        #: **Liveness and readiness are exempt and it is not a convenience.**
        #: An orchestrator polls them continuously from one address; limiting
        #: them makes the limiter restart healthy processes.
        self._exempt = exempt

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http" or not self._limiter.settings.enabled:
            await self._app(scope, receive, send)
            return

        path = scope.get("path", "")
        if path in self._exempt:
            await self._app(scope, receive, send)
            return

        key = f"rl:{route_of(scope, self._routes)}:{identity_of(scope)}"
        decision = await self._limiter.check(key)
        if decision.allowed:
            await self._app(scope, receive, send)
            return

        await self._refuse(decision, send)

    async def _refuse(self, decision: Decision, send: Send) -> None:
        """A `429` that says the same thing to everyone.

        ⛔ **No account state, no whether-this-user-exists, and no timing
        difference between a known and an unknown caller** (ADR-0408 §3) —
        [§7](../../../CLAUDE.md)'s `404`-not-`403` reasoning applied to volume.
        """
        body = b'{"error":{"code":"rate_limited","message":"Too many requests."}}'
        start: Message = {
            "type": "http.response.start",
            "status": 429,
            "headers": [
                (b"content-type", b"application/json"),
                (RETRY_AFTER.encode(), str(decision.retry_after).encode()),
            ],
        }
        await send(start)
        await send({"type": "http.response.body", "body": body})


class RedisPipeline(Protocol):
    """Only the three calls this store makes — never the whole client.

    A narrow Protocol rather than the vendor's type, so `signora_platform`
    keeps no import of a concrete client in a module every request touches
    ([§6](../../../CLAUDE.md): concrete infrastructure never leaks into a
    signature).
    """

    def incr(self, key: str) -> object: ...
    def expire(self, key: str, seconds: int, nx: bool = ...) -> object: ...
    async def execute(self) -> list[object]: ...


class RedisLike(Protocol):
    def pipeline(self) -> RedisPipeline: ...


class RedisCounterStore:
    """A fixed-window counter in Redis — ADR-0408 §2.

    **Redis is already a backing service** (ARQ, the outbox relay), attached by
    URL, so this is a *use* of existing infrastructure rather than a new
    datastore ([§8](../../../CLAUDE.md)). **A lost counter fails open for one
    window and is not data.**
    """

    def __init__(self, client: RedisLike) -> None:
        self._client = client

    async def increment(self, key: str, window_seconds: int) -> int:
        # **`INCR` then `EXPIRE` only on the first hit.** Refreshing the TTL on
        # every request turns a fixed window into a rolling ban: a caller who
        # keeps knocking never falls out of their own window.
        pipeline = self._client.pipeline()
        pipeline.incr(key)
        pipeline.expire(key, window_seconds, nx=True)
        seen, _ = await pipeline.execute()
        # **`int(str(...))` rather than an ignore.** The client's return is
        # untyped at this boundary; converting through `str` is honest about
        # that and fails loudly on anything that is not a number, where a cast
        # would let a surprise through as a silent zero.
        return int(str(seen))


class InMemoryCounterStore:
    """⛔ **Tests and single-process development only.**

    📁 **ADR-0408 §9 is explicit about why this must never be the deployed
    store**: *"an in-process limiter in a horizontally scaled system does not
    provide equivalent protection — it provides a number that is wrong by a
    factor of n and looks right."* **It exists so the middleware's own tests
    need no server**, which is the same reason `CounterStore` is a port.
    """

    def __init__(self) -> None:
        self._counts: dict[str, tuple[int, float]] = {}

    async def increment(self, key: str, window_seconds: int) -> int:
        now = time.monotonic()
        seen, expires = self._counts.get(key, (0, 0.0))
        if now >= expires:
            seen, expires = 0, now + window_seconds
        seen += 1
        self._counts[key] = (seen, expires)
        return seen
