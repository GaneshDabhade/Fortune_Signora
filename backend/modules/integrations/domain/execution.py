"""Everything an adapter needs to act on a connection.

**Moved into the domain on 2026-08-04**, when [ADR-0300](../../../../docs/architecture/adr/0300-inbound-customer-systems.md)
was ratified and `IntegrationSourceAdapter` — a **domain** port — had to name
it. A domain type cannot be defined in `application/`: the dependency would
point outward, which is the one direction Clean Architecture forbids.

**It was always a domain value and never used an application type.** Its
fields are a workspace, a connection, a catalog slug, an endpoint, scopes and
a `Credential` — every one of them this module's own vocabulary, and
`Credential` has lived in `domain/grant.py` since the module was written.
`ResolveExecutionContext` stays in `application/`, where it belongs: **the
value is domain, the act of resolving it is a use case.**
"""

from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from modules.integrations.domain.grant import Credential


@dataclass(frozen=True, slots=True)
class ExecutionContext:
    """Everything an adapter needs to act, and nothing about how it was
    obtained.

    **The unit of resolution, deliberately larger than a credential.** Resolving
    only a credential would couple every future concern — region, throttling,
    retry policy, audit context — to the one that happened to be first. An
    adapter receives a context and reads what it needs from it, so adding a
    field later changes no signature.

    **It carries no vendor identity a caller can branch on.** `integration` is
    the catalog slug an adapter was chosen *by*; nothing above the adapter is
    expected to read it, and business behaviour that varied on it would be the
    vendor leaking upward — the rule the AI Platform already holds.
    """

    workspace_id: UUID
    connected_account_id: UUID
    integration: str
    #: Where to reach this account, when the vendor is not one fixed host.
    endpoint: str | None
    #: What the customer permitted, so a missing scope is a readable refusal.
    scopes: tuple[str, ...]
    credential: Credential

    def __repr__(self) -> str:
        # The credential redacts itself; this stops a careless container from
        # rendering it by rendering the whole context.
        return (
            f"ExecutionContext(workspace_id={self.workspace_id!r}, "
            f"connected_account_id={self.connected_account_id!r}, "
            f"integration={self.integration!r}, credential=<redacted>)"
        )

    __str__ = __repr__
