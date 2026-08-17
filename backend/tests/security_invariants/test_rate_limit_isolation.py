"""A refused caller must never cause the refusal of a caller they do not control.

**[ADR-0408](../../../docs/architecture/adr/0408-inbound-rate-limiting.md) §5
names this as the Security Invariant the limiter needs, and §14 says why:**

> 🔴 **A limiter is a denial-of-service vector pointed at your own customers if
> the key is attacker-controlled.** ⛔ *"Keying sign-in solely on the submitted
> address lets anybody lock any customer out by spending their budget for
> them — the control becomes the attack."*

⚡ **This is the failure the happy path cannot show.** A limiter that refuses at
the right count looks correct in every test that counts, and is still a weapon
if the count is attributed to the wrong person.
"""

from __future__ import annotations

from signora_platform.api.rate_limit import (
    InMemoryCounterStore,
    RateLimiter,
    RateLimitSettings,
    identity_of,
    route_of,
)

def _limiter(max_requests: int = 2) -> RateLimiter:
    return RateLimiter(
        InMemoryCounterStore(),
        RateLimitSettings(window_seconds=60, max_requests=max_requests),
    )


class TestABudgetIsNotSpendableOnSomebodyElsesBehalf:
    async def test_exhausting_one_identity_leaves_another_untouched(self) -> None:
        """✅ **The invariant itself.**

        ⛔ **If this fails, the limiter is a denial-of-service tool**: an
        attacker exhausts a victim's budget and the victim is refused.
        """
        limiter = _limiter(max_requests=2)
        attacker = "rl:/workspaces/{workspace_id}/products:203.0.113.9"
        victim = "rl:/workspaces/{workspace_id}/products:198.51.100.4"

        for _ in range(6):
            await limiter.check(attacker)

        assert (await limiter.check(attacker)).allowed is False
        assert (await limiter.check(victim)).allowed is True

    async def test_one_route_being_exhausted_does_not_refuse_another(self) -> None:
        """⚡ **Per route, never one global number** — ADR-0408 §4.

        A single global counter means any caller flooding one endpoint refuses
        every caller everywhere, which is the same defect one axis over.
        """
        limiter = _limiter(max_requests=2)
        caller = "203.0.113.9"

        for _ in range(6):
            await limiter.check(f"rl:/workspaces/{{workspace_id}}/products:{caller}")

        hot = await limiter.check(f"rl:/workspaces/{{workspace_id}}/products:{caller}")
        cold = await limiter.check(f"rl:/workspaces/{{workspace_id}}/icp:{caller}")
        assert hot.allowed is False
        assert cold.allowed is True


class TestTheKeyIsNotAttackerChosen:
    def test_identity_comes_from_the_transport_not_the_payload(self) -> None:
        """🔴 **§14's property, asserted on the function that decides it.**

        ⛔ **A submitted address, a header the caller sets, or a workspace claim
        would each let one caller spend another's budget.** The client address
        is weak — behind a proxy every caller shares it — **but it is not
        forgeable by the caller**, and that is the property that matters here.
        """
        scope = {
            "type": "http",
            "client": ("203.0.113.9", 51234),
            "headers": [(b"x-forwarded-for", b"198.51.100.4")],
            "path": "/workspaces/abc/products",
        }

        assert identity_of(scope) == "203.0.113.9"

    def test_a_forwarded_header_is_ignored_until_a_proxy_is_trusted(self) -> None:
        """⛔ **`X-Forwarded-For` is caller-controlled until something strips it.**

        ⚠️ **Trusting it today would hand every caller a free identity** and
        make the limiter unlimited. 📁 A trusted-proxy configuration is
        infrastructure and is deferred to M14.5 with the rest
        ([§20b](../../../CLAUDE.md)) — **so the header is not read, and this
        test is what stops somebody adding it as a convenience.**
        """
        spoofed = {
            "type": "http",
            "client": ("203.0.113.9", 51234),
            "headers": [(b"x-forwarded-for", b"1.1.1.1")],
        }
        honest = {"type": "http", "client": ("203.0.113.9", 51234), "headers": []}

        assert identity_of(spoofed) == identity_of(honest)


class TestTheRouteKeyIsTheTemplate:
    def test_concrete_ids_share_one_budget(self) -> None:
        """🔴 **Keying on the concrete path means no limit at all.**

        ⛔ **An attacker walking account ids would get a fresh budget for every
        id** — and the limiter's own metrics would look healthy throughout,
        which is the worst shape a control can fail in.
        """

        from starlette.routing import Route

        async def _noop(request: object) -> None: ...

        routes = [Route("/workspaces/{workspace_id}/accounts/{account_id}/score", _noop)]
        a = {"type": "http", "method": "GET", "path": "/workspaces/w1/accounts/a1/score"}
        b = {"type": "http", "method": "GET", "path": "/workspaces/w1/accounts/a2/score"}

        assert route_of(a, routes) == route_of(b, routes)
        assert route_of(a, routes) == "/workspaces/{workspace_id}/accounts/{account_id}/score"

    def test_an_unrouted_request_still_keys_on_something(self) -> None:
        """⚠️ **A 404 is still a request and still costs.**

        Falling back to the raw path is deliberate: it is a worse key, and it
        is better than exempting every unmatched path from the limiter, which
        would make `/does-not-exist` an unlimited endpoint.
        """
        assert route_of({"type": "http", "path": "/nope"}) == "/nope"
