"""Where each vendor's grants are managed.

**Management endpoints only, and that is the whole boundary.**
`lib/integrations/providers.ts` holds where a customer is *sent* and where an
authorization code is *exchanged* — acquisition, which
[18-authentication.md](../../../../docs/architecture/18-authentication.md)
reserves to the Next tier. This holds where an existing grant is *renewed* or
*destroyed*, which §5 of
[44-integrations.md](../../../../docs/architecture/44-integrations.md) puts
here. **No URL appears in both tables and neither tier could use the other's.**

**One table rather than one per operation.** Revocation and refresh are two
questions about the same vendor, and two maps keyed on the same slugs would
mean adding a system in two places — with the second one forgotten, silently,
by whoever added the first.

**A system absent from this table simply has neither.** `NoRevoker` and
`NoTokenRefresher` both report that they could not act, which is what the
product already tells the customer and is still true.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Final


@dataclass(frozen=True, slots=True)
class RevocationEndpoint:
    """Where a vendor's grant is destroyed.

    **The token is always the refresh token**, and that is a fact rather than a
    setting. HubSpot revokes a refresh token and the access token will not do;
    Google accepts either, so one value serves both. A configurable field here
    carried a branch no vendor could take — **a guard that cannot fail is
    documentation pretending to be code** (§2), and the note it was carrying is
    worth more as this paragraph.

    Getting it wrong would be the worst available outcome: a cheerful `200`
    that revokes nothing, with the product reporting a credential withdrawn
    while it still worked. **A vendor that genuinely needs the access token is
    the moment to add the field back**, with a test that takes the branch.
    """

    #: `{token}` is replaced with the material, URL-encoded.
    url_template: str
    method: str


@dataclass(frozen=True, slots=True)
class VendorEndpoints:
    """Everything this tier needs to manage one vendor's grants."""

    revocation: RevocationEndpoint
    #: Where a refresh token is exchanged for new material — RFC 6749 §6.
    #:
    #: **The same URL the acquisition flow posts to**, deliberately: §6 is the
    #: same endpoint as §4.1.3 with a different `grant_type`. It is repeated
    #: here rather than imported across the tier boundary, because the two
    #: tiers are separately deployable and a shared constant between them would
    #: be a coupling neither §5 nor the topology allows.
    token_url: str


VENDOR_ENDPOINTS: Final[dict[str, VendorEndpoints]] = {
    "hubspot": VendorEndpoints(
        revocation=RevocationEndpoint(
            url_template="https://api.hubapi.com/oauth/v1/refresh-tokens/{token}",
            method="DELETE",
        ),
        token_url="https://api.hubapi.com/oauth/v1/token",
    ),
    "google_calendar": VendorEndpoints(
        revocation=RevocationEndpoint(
            url_template="https://oauth2.googleapis.com/revoke?token={token}",
            method="POST",
        ),
        token_url="https://oauth2.googleapis.com/token",
    ),
}


__all__ = ["VENDOR_ENDPOINTS", "RevocationEndpoint", "VendorEndpoints"]
