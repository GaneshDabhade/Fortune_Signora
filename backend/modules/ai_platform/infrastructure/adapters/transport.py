"""Turning HTTP into Signora vocabulary.

Shared by every adapter, and shared *without branching on vendor* — the
mapping below is the platform's semantics, not any vendor's. A 429 means the
same thing whoever sent it, and a caller decides what to do about it knowing
only that it is transient and how long to wait.

This is the boundary quality 4 of the brief describes: retryability,
timeouts, authentication and malformed responses all become platform
concepts **before** anything crosses the port. Above the adapter line no
caller has ever seen a status code.

Vendor-specific interpretation stays in the adapter that owns it. What lives
here is only what is genuinely identical: the HTTP contract itself.
"""

from __future__ import annotations

import httpx

from modules.ai_platform.domain.provider import (
    AIPermanentError,
    AIProviderError,
    AIRateLimitedError,
    AITransientError,
    AIVendor,
)

#: Statuses worth trying again. 408 and 409 are included because both mean
#: "not now" rather than "not ever", and 5xx is handled by range below.
_RETRYABLE = frozenset({408, 409, 425, 500, 502, 503, 504})


def classify_response(vendor: AIVendor, response: httpx.Response) -> AIProviderError | None:
    """The platform failure this response represents, or ``None`` if it
    succeeded."""
    if response.is_success:
        return None

    detail = _detail(response)

    if response.status_code == 429:
        return AIRateLimitedError(
            vendor,
            f"rate limited: {detail}",
            retry_after_seconds=_retry_after(response),
        )
    if response.status_code in (401, 403):
        # Never retried. A rejected credential does not improve with
        # patience, and retrying one turns a configuration mistake into a
        # burst of authentication failures against the vendor.
        return AIPermanentError(vendor, f"authentication rejected ({response.status_code})")
    if response.status_code in _RETRYABLE or response.status_code >= 500:
        return AITransientError(vendor, f"{response.status_code}: {detail}")
    return AIPermanentError(vendor, f"{response.status_code}: {detail}")


def classify_transport(vendor: AIVendor, error: Exception) -> AIProviderError:
    """The platform failure a transport-level exception represents.

    Every one of these is transient: a timeout, a refused connection, a
    dropped socket. None of them says anything about the request, so none
    justifies giving up on it.
    """
    if isinstance(error, httpx.TimeoutException):
        return AITransientError(vendor, f"timed out: {error}")
    if isinstance(error, httpx.TransportError):
        return AITransientError(vendor, f"transport failure: {error}")
    return AIPermanentError(vendor, f"unexpected transport error: {error}")


def _retry_after(response: httpx.Response) -> float | None:
    """The vendor's stated wait, when it gave one.

    ``None`` means it did not — deliberately distinct from ``0.0``, which
    would mean *retry immediately*. Guessing a backoff when the vendor
    stated one is how an integration gets throttled harder; inventing one
    when it stated nothing is the same mistake in the other direction.
    """
    raw = response.headers.get("retry-after")
    if raw is None:
        return None
    try:
        return float(raw)
    except ValueError:
        # An HTTP-date form. Honouring it needs a clock, which would make
        # this function depend on wall time; the caller's own backoff is a
        # safer answer than a value parsed three ways.
        return None


def _detail(response: httpx.Response) -> str:
    """A short, safe excerpt of the vendor's error body.

    Truncated because a vendor error page can be a full HTML document, and
    a log line carrying one is a log line nobody reads.
    """
    try:
        text = response.text
    except Exception:  # pragma: no cover - defensive; body already consumed
        return "<unreadable body>"
    collapsed = " ".join(text.split())
    return collapsed[:200] if collapsed else "<empty body>"
