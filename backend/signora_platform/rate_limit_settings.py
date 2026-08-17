"""The limiter's typed configuration — [ADR-0408](../../docs/architecture/adr/0408-inbound-rate-limiting.md) §4.

## ⚠️ Why this is its own module rather than living beside the middleware

**It was written in `api/rate_limit.py` first, and `lint-imports` refused it:**

    signora_platform.settings -> signora_platform.api.rate_limit

⛔ **`settings` is below `api` in the layering**, so a `Settings` field typed by
a class defined in `api` inverts the dependency — and the contract caught it
rather than review. ⚡ **A leaf module both may import is the boring fix**; the
alternative was defining it in `settings.py`, which would put a middleware's
configuration in the file [§6](../../CLAUDE.md) warns about becoming *"the
registry of every module's configuration surface."*
"""

from __future__ import annotations

from pydantic import BaseModel, Field

class RateLimitSettings(BaseModel):
    """The platform's own limiter configuration — [§6](../../CLAUDE.md).

    ⛔ **No module reads this and no module configures it.** It is constructed
    at the composition root and injected, like every other typed Settings
    object in this repository.

    ⚠️ **The numbers are deliberately conservative rather than measured.**
    ADR-0408 §15 refuses to name a budget in the ADR — *"set from measured
    traffic, and until traffic exists a conservative default that is changed
    without a code change."* **These are that default, and they are wrong on
    purpose until real traffic says otherwise.**
    """

    enabled: bool = True
    #: Seconds. A fixed window, because a sliding window costs a sorted set per
    #: caller and buys precision nobody has asked for at this traffic.
    window_seconds: int = Field(default=60, gt=0)
    #: Requests permitted per identity per route template per window.
    max_requests: int = Field(default=300, gt=0)
