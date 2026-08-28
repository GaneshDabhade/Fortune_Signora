"""HTTP response schemas for the Knowledge Graph's identity surface.

Separate from the read model, even though they currently carry the same fields:
coupling the wire contract to an internal type makes a refactor a client-breaking
change (19-api-conventions.md).

**The vocabulary changes at this boundary, deliberately.** Inside, this is an
`Entity` and a `ClaimAttribute`. On the wire it is an **account** and a **name**,
because that is what the customer came to look at. A seller has never asked to
see an entity.
"""

from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from modules.knowledge_graph.application.queries import (
    AccountCommercial,
    AccountIdentity,
    AccountIdentityEntry,
    ListedAccount,
    AccountMatch,
    AccountMatchGroup,
    SearchCoverage,
)
from modules.provider_normalization.public import CommercialStage
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


class SearchGroupResponse(BaseModel):
    """One kind of thing, what Signora did about it, and what it found.

    **The group is present whether or not it has results**, on the product
    owner's ruling of 2026-08-05: *"the absence of results and the absence of
    the group represent different business meanings."*

    A surface reads `coverage` before it reads `results`, and says a different
    sentence for each — *"no companies match «acme»"*, *"Signora does not
    search technologies by name"*, *"you excluded this"*. **Rendering an empty
    list without reading `coverage` reproduces exactly the collapse the ruling
    forbids**, which is why the field is required and carries no default.
    """

    model_config = ConfigDict(frozen=True)

    result_type: EntityKind = Field(
        description="What kind of thing this group is about."
    )
    coverage: SearchCoverage = Field(
        description="Whether Signora looked for this kind, and if not, why not. "
        "`searched` means it looked and `results` is the answer, empty or not. "
        "`not_applicable` means it cannot look — search matches a legal name and "
        "only a company has one. `not_requested` means the caller excluded it. "
        "Read this before `results`: an empty list means something different in "
        "each case."
    )
    results: list[SearchResultResponse] = Field(
        description="The matches, in matched-name order. Always empty unless "
        "`coverage` is `searched`, and empty is a real answer when it is."
    )

    @classmethod
    def from_domain(cls, group: AccountMatchGroup) -> "SearchGroupResponse":
        return cls(
            result_type=group.kind,
            coverage=group.coverage,
            results=[SearchResultResponse.from_domain(m) for m in group.matches],
        )

class MoneyResponse(BaseModel):
    """A figure and the currency it is in — **never one without the other**."""

    model_config = ConfigDict(frozen=True)

    amount: int = Field(
        description="In the source system's own minor units, uninterpreted. Signora "
        "carries what the customer's system said and does not decide whether 1200 is "
        "twelve dollars or twelve hundred."
    )
    currency: str = Field(
        description="ISO code, as the source stated it. Never converted: a rate is "
        "applied at a moment, so a converted figure is correct briefly and wrong "
        "permanently."
    )


class CommercialStageResponse(BaseModel):
    """Where this relationship stands, **in Signora's word and the customer's**."""

    model_config = ConfigDict(frozen=True)

    position: CommercialStage | None = Field(
        description="The canonical pipeline position, or null when the customer's own "
        "stage maps to nothing Signora knows. Null means *mapped to nothing* — not "
        "unknown, not missing — and a screen shows it as unmapped rather than hiding "
        "the row. Reasoning reads this; it never reads the label."
    )
    label: str = Field(
        description="What the customer's own system calls this stage. Provenance, for "
        "display. Never branch on it."
    )


class AccountCommercialResponse(BaseModel):
    """What this account is worth, and where it stands.

    **Every field is nullable and null means nothing has been said.** Signora
    does not infer, default or zero-fill a commercial fact: an account with no
    connected system of record comes back with three nulls, and a surface
    renders that as absence rather than as zero.
    """

    model_config = ConfigDict(frozen=True)

    open_acv: MoneyResponse | None = Field(
        default=None,
        description="Open annual contract value, or null when no source has stated one. "
        "Never a bare number — the currency travels with it or the fact does not.",
    )
    renewal_date: date | None = Field(
        default=None, description="When this account renews, or null when unstated."
    )
    stage: CommercialStageResponse | None = Field(
        default=None,
        description="The commercial position, or null when unstated. Present but "
        "unmapped is a different state, carried on the object itself.",
    )

    @classmethod
    def from_domain(cls, commercial: AccountCommercial) -> "AccountCommercialResponse":
        return cls(
            open_acv=(
                MoneyResponse(
                    amount=commercial.open_acv.amount,
                    currency=commercial.open_acv.currency,
                )
                if commercial.open_acv
                else None
            ),
            renewal_date=commercial.renewal_date,
            stage=(
                CommercialStageResponse(
                    position=commercial.stage.position, label=commercial.stage.label
                )
                if commercial.stage
                else None
            ),
        )


class ListedAccountResponse(BaseModel):
    """One account on the list: **who it is, and what kind of thing.**

    **Not a search result.** `matched_name`, `matched_source` and `is_renamed`
    are absent because a browse row is in the list *because it exists*, not
    because something matched — and a field that is null wherever it is not a
    search is a field in the wrong schema.
    """

    model_config = ConfigDict(frozen=True)

    account: AccountIdentityResponse = Field(
        description="Who this account is — the same shape search and the brief return, "
        "so a caller reads one identity everywhere."
    )
    kind: EntityKind = Field(
        description="What kind of thing this is. Read it rather than assuming: the list "
        "answers for companies today and the graph knows more kinds than it can search."
    )
    commercial: AccountCommercialResponse = Field(
        description="What this account is worth and where it stands. Always present as "
        "an object; its fields are null until a source states them, which is how a "
        "caller tells *nothing said* from *not asked*."
    )

    @classmethod
    def from_domain(cls, listed: ListedAccount) -> "ListedAccountResponse":
        return cls(
            account=AccountIdentityResponse.from_domain(listed.account),
            kind=listed.kind,
            commercial=AccountCommercialResponse.from_domain(listed.commercial),
        )


class AccountIdentityEntryResponse(BaseModel):
    """Who one requested account is, **and what kind of thing it is.**

    🔴 **[B-261](../../../../docs/BUGS.md).** Account 360 persists a collapsed
    section *per account **type***, and until this field existed the page could
    not read one — so it stored nothing rather than store a preference under a
    guessed type, which is a preference a rep cannot get back.

    **`kind` sits beside the identity rather than inside it**, which is
    `ListedAccountResponse`'s arrangement and for its reason: an identity
    answers *who is this*, and a classification is a different question about
    the same account.
    """

    model_config = ConfigDict(frozen=True)

    account: AccountIdentityResponse = Field(
        description="Who this account is — the same shape the list, search and the "
        "brief return, so a caller reads one identity everywhere."
    )
    kind: EntityKind = Field(
        description="What kind of thing this is. Read it rather than assuming: the "
        "graph knows more kinds than any one surface asks for."
    )

    @classmethod
    def from_domain(cls, entry: AccountIdentityEntry) -> "AccountIdentityEntryResponse":
        return cls(
            account=AccountIdentityResponse.from_domain(entry.account), kind=entry.kind
        )


class AccountCommercialEntryResponse(BaseModel):
    """What one requested account is worth, with the id it answers.

    **The id is on the row rather than implied by position.** This read is a
    plain list joined by `account_id`, exactly like `/account-identities`, and
    a caller relying on order would be relying on something the contract does
    not promise.
    """

    model_config = ConfigDict(frozen=True)

    account_id: UUID = Field(description="Which account this answers for.")
    commercial: AccountCommercialResponse = Field(
        description="Always present as an object; its fields are null until a source "
        "states them, which is how a caller tells *nothing said* from *not asked*."
    )


__all__ = [
    "AccountCommercialEntryResponse",
    "AccountIdentityEntryResponse",
    "AccountCommercialResponse",
    "AccountIdentityResponse",
    "SearchGroupResponse",
    "SearchResultResponse",
]
