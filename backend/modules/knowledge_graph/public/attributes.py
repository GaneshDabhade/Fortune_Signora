"""What another module may ask about an account's attributes.

**One call per entity, not three.** A caller assembling three separate reads —
industry, country, employee count — is a caller with three chances to mismatch
them: three round trips, three moments, and no guarantee they describe the same
state of the graph. [462](../../../../docs/architecture/462-observed-attributes-proposal.md)
required the single call and this is it.

⛔ **`SubjectRef` never crosses this boundary.** A provider identity would let a
consumer fetch the claims and resolve them itself, which is the defect the whole
contract closes. **Provider *names* travel; provider *subjects* do not.**
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol
from uuid import UUID

from modules.knowledge_graph.domain.attributes import ResolvedAttribute


@dataclass(frozen=True, slots=True)
class AccountAttributes:
    """The three attributes an account is described by, each resolved.

    **Three fields rather than a mapping**, so a consumer naming a fourth gets
    a type error rather than a `None` at runtime — and so the set this contract
    publishes is visible in the type instead of in a docstring.

    **Every field is always present.** An attribute nobody has reported comes
    back `UNKNOWN` rather than being absent, which is the same distinction
    TASK-408's ruling drew for search groups: *the absence of results and the
    absence of the group represent different business meanings.*
    """

    entity_id: UUID
    industry: ResolvedAttribute
    country: ResolvedAttribute
    employee_count: ResolvedAttribute


class AccountAttributesReader(Protocol):
    """The port a consumer depends on.

    **A Protocol in `public/`, satisfied by this module's own infrastructure**
    and injected at the composition root — the `View · Reader` shape this
    module and `commercial_profile` both already publish.
    """

    async def for_account(self, workspace_id: UUID, entity_id: UUID) -> AccountAttributes:
        """Everything this contract can say about one account.

        **Never `None`.** An account with no claims at all is not an error and
        not an absence — it is three `UNKNOWN` values, which is a real answer a
        consumer can act on. Returning `None` would make *"we know nothing
        about it"* and *"it does not exist"* the same response.
        """
        ...


__all__ = ["AccountAttributes", "AccountAttributesReader"]
