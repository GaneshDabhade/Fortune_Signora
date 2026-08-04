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

from modules.knowledge_graph.application.queries import AccountIdentity, AccountMatch
from modules.knowledge_graph.domain.identity import EntityKind
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
    last_observed_at: datetime | None = Field(
        description=(
            "When the newest evidence about this account was observed, across every "
            "attribute rather than only the name. Null when no source has ever reported "
            "anything about it. Read this to judge how current the rest of the page is: "
            "a score built on evidence nobody has refreshed since March is a different "
            "thing from the same score built this morning. It is not a record of when "
            "Signora last looked — an account nobody found anything about cannot "
            "currently be distinguished from one nobody checked."
        )
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
            last_observed_at=identity.last_observed_at,
        )


class SearchResultResponse(BaseModel):
    """One search result: **the account, its type, and why it is here.**

    **A wrapper rather than three more fields on `AccountIdentityResponse`.**
    That schema answers *"who is this account?"* and is returned by two other
    surfaces which have no match to explain; giving it `matched_name` would
    make the field null on every one of them, and a field that is null
    wherever it is not a search is a field in the wrong schema.
    """

    model_config = ConfigDict(frozen=True)

    account: AccountIdentityResponse = Field(
        description="Who this account is — the same shape the accounts list and "
        "the brief return, so a caller reads one identity everywhere."
    )
    result_type: EntityKind = Field(
        description="What kind of thing this result is. Group your results by it "
        "rather than by which endpoint you called: this one answers for companies "
        "today, and a type Signora cannot search yet is absent rather than returned "
        "empty — an empty group would claim it looked and found nothing."
    )
    matched_name: str = Field(
        description="The name that actually matched, exactly as a source claimed it. "
        "Often the same as the name being displayed; when it differs, this is why the "
        "row is in the list — a company found under a name it no longer goes by."
    )
    matched_source: str = Field(
        description="Which provider claimed the matched name. Read it to weigh a "
        "match you did not expect."
    )
    is_renamed: bool = Field(
        description="Whether this row matched under a name it is not being shown "
        "under. The one case worth annotating in a list; the rest need no explanation, "
        "and a surface that annotates every row teaches people to stop reading it."
    )

    @classmethod
    def from_domain(cls, match: AccountMatch) -> "SearchResultResponse":
        return cls(
            account=AccountIdentityResponse.from_domain(match.account),
            result_type=match.kind,
            matched_name=match.matched_name,
            matched_source=match.matched_source,
            is_renamed=match.is_renamed,
        )


__all__ = ["AccountIdentityResponse", "SearchResultResponse"]
