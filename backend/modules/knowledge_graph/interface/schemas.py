"""HTTP response schemas for the Knowledge Graph's identity surface.

Separate from the read model, even though they currently carry the same fields:
coupling the wire contract to an internal type makes a refactor a client-breaking
change (19-api-conventions.md).

**The vocabulary changes at this boundary, deliberately.** Inside, this is an
`Entity` and a `ClaimAttribute`. On the wire it is an **account** and a **name**,
because that is what the customer came to look at. A seller has never asked to
see an entity.
"""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from modules.knowledge_graph.application.queries import AccountIdentity
from modules.knowledge_graph.domain.naming import NameAgreement


class AccountIdentityResponse(BaseModel):
    """Who an account is, and how sure Signora is about it."""

    model_config = ConfigDict(frozen=True)

    account_id: UUID = Field(
        description="The account this identity describes. Matches `account_id` on the "
        "attention list, which is how the two are joined."
    )
    name: str | None = Field(
        description="What to call this account, or null when no source has named it. "
        "Null is absence, not an error — render it as such rather than substituting a "
        "placeholder, which would be indistinguishable from a real name."
    )
    agreement: NameAgreement = Field(
        description="Whether your sources agree on the name. `unknown` — nobody has said. "
        "`single_source` — one provider names it, which is uncorroborated rather than "
        "agreed. `agreed` — every provider that names it says the same thing. `disputed` — "
        "they differ, and the name shown is one of several."
    )
    source_count: int = Field(
        description="How many providers have named this account. The denominator behind "
        "`agreement`, so you can say '2 of 3 sources' without a second request."
    )
    source: str | None = Field(
        description="Which provider supplied the name being shown. Null exactly when "
        "`name` is."
    )
    observed_at: datetime | None = Field(
        description="When that provider observed the name — not when Signora stored it. "
        "The distinction matters when judging whether a rename has been picked up."
    )

    @classmethod
    def from_domain(cls, identity: AccountIdentity) -> "AccountIdentityResponse":
        return cls(
            account_id=identity.entity_id,
            name=identity.name,
            agreement=identity.agreement,
            source_count=identity.source_count,
            source=identity.source,
            observed_at=identity.observed_at,
        )


__all__ = ["AccountIdentityResponse"]
