"""The credential authorising access to a Connected Account.

**A grant is secret material bound to a connection, and nothing about what it is
for.** That sentence is the whole design, and two rules follow from it:

**Nothing here knows how the credential was obtained.** OAuth, an API key pasted
into a form, a service-account file, a client certificate, a JWT assertion — the
mechanism belongs to acquisition, which happens at the frontend edge, and it
must never reach synchronization. An adapter that could ask *"was this OAuth?"*
would be vendor-shaped, and the abstraction would not survive the first
mechanism that is not a bearer token.

**`refreshable` is a property, never a special case.** An API key is a grant
that does not expire and cannot be refreshed. Modelling that as an exception
would put OAuth's shape into the type every other mechanism has to fit.

**No secret material is stored on this aggregate.** A grant carries a
`secret_ref` and the lifecycle facts; resolving it is `SecretStore`'s. That
keeps tokens out of a table that is backed up, replicated and read by anybody
with database access, and it is what lets the eventual vault
([ADR-0022](../../../../docs/architecture/adr/0022-devops-infrastructure-and-deployment-topology.md))
arrive without touching this type.
"""

from __future__ import annotations

import json
from typing import Final

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass(frozen=True, slots=True)
class Credential:
    """Resolved secret material, on its way to a client factory.

    **Opaque by construction, and that is what mTLS forced.** Every other
    mechanism resolves to something an adapter attaches to a request; a client
    certificate configures the TLS context *before* a request exists. An
    abstraction shaped as *"the value for the Authorization header"* cannot
    express that, so this carries material an adapter hands to a factory and
    never formats itself.

    **Never logged, never traced, never persisted.** It exists between
    resolution and use.
    """

    #: What kind of material this is, so a client factory knows what to build.
    #: **The adapter does not branch on it** — the factory does.
    kind: str
    material: bytes

    def __repr__(self) -> str:
        # A credential in a traceback, a log line or a pytest diff is a
        # credential in a log aggregator. The type refuses to render itself.
        return f"Credential(kind={self.kind!r}, material=<redacted>)"

    __str__ = __repr__


#: The kind the OAuth acquisition flow stores: a JSON object carrying the
#: access token and, when the provider issued one, the refresh token.
#:
#: **Named here because it is the credential's own vocabulary**, not an
#: adapter's. `Credential` is opaque so that a kind can be more than one
#: string, and there is exactly one `secret_ref` per grant — so a refresh
#: token has nowhere else to live.
OAUTH2_KIND: Final = "oauth2"


@dataclass(frozen=True, slots=True)
class OAuth2Material:
    """What an `oauth2` credential carries, once read.

    **One parser, and it refuses rather than guessing.** Both the revoker and
    the refresher need to look inside the same material, and two readers of one
    shape are two readers that eventually disagree about it (§2). Anything it
    cannot read returns `None`, because sending part of a credential to a
    vendor on the chance it works is how an operation reports success it never
    achieved.
    """

    access_token: str
    refresh_token: str | None

    @classmethod
    def read(cls, credential: Credential) -> "OAuth2Material | None":
        if credential.kind != OAUTH2_KIND:
            return None
        try:
            payload = json.loads(credential.material)
        except (ValueError, UnicodeDecodeError):
            return None
        if not isinstance(payload, dict):
            return None
        access = payload.get("access_token")
        if not isinstance(access, str) or not access:
            return None
        refresh = payload.get("refresh_token")
        return cls(access, refresh if isinstance(refresh, str) and refresh else None)

    def as_credential(self) -> Credential:
        return Credential(
            kind=OAUTH2_KIND,
            material=json.dumps(
                {"access_token": self.access_token, "refresh_token": self.refresh_token}
            ).encode(),
        )


class GrantExpired(Exception):
    """The grant's lifetime ran out. Recoverable by refresh, if refreshable."""


class GrantRevoked(Exception):
    """Permission was withdrawn at the vendor.

    **Not retryable, and the distinction matters operationally.** A retry loop
    against a revoked grant is a system doing nothing while a dashboard reports
    it healthy.
    """


@dataclass(frozen=True, slots=True)
class IntegrationGrant:
    """What authorises Signora to act on one Connected Account."""

    id: UUID
    workspace_id: UUID
    connected_account_id: UUID
    #: Where the secret lives, not the secret. Opaque to everything but the
    #: `SecretStore` that issued it.
    secret_ref: str
    #: What the customer permitted. Held so a missing scope is a readable
    #: refusal rather than a vendor 403 nobody can explain.
    scopes: tuple[str, ...]
    #: `None` for material that does not expire — an API key, a certificate
    #: with a long life. Absence is a fact, not an unknown.
    expires_at: datetime | None
    #: Whether new material can be obtained without the customer present.
    refreshable: bool
    revoked_at: datetime | None
    #: Who last acted on this grant — authorised it, or withdrew it. Required,
    #: with no default, for the same reason `ConnectedAccount.actor_id` is.
    actor_id: UUID

    def __post_init__(self) -> None:
        if not self.secret_ref:
            raise ValueError("a grant must reference secret material")

    def is_expired(self, *, at: datetime) -> bool:
        return self.expires_at is not None and self.expires_at <= at

    def check_usable(self, *, at: datetime) -> None:
        """Raise if this grant cannot be used now.

        **Two exceptions rather than one boolean**, because the caller must do
        different things: an expired refreshable grant is refreshed, and a
        revoked one needs the customer. A single `is_usable` would collapse
        them and the caller would guess.
        """
        if self.revoked_at is not None:
            raise GrantRevoked("permission was withdrawn at the vendor")
        if self.is_expired(at=at):
            raise GrantExpired("the grant's lifetime ran out")

    def revoke(self, *, at: datetime, by: UUID) -> IntegrationGrant:
        """Record that permission ended. **Idempotent** — the first revocation
        is the one that counts, and a second report of the same withdrawal must
        not move the timestamp, nor reattribute it to whoever reported it last.
        """
        if self.revoked_at is not None:
            return self
        return IntegrationGrant(
            id=self.id,
            workspace_id=self.workspace_id,
            connected_account_id=self.connected_account_id,
            secret_ref=self.secret_ref,
            scopes=self.scopes,
            expires_at=self.expires_at,
            refreshable=self.refreshable,
            revoked_at=at,
            actor_id=by,
        )
