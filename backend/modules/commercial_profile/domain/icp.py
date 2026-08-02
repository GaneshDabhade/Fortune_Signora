"""The ideal customer — the kind of company that buys what we sell.

**The second declaration, and the one the pipeline has been waiting for.** The
product catalog says *what* a customer sells; this says *who buys it*. Neither
is derived from anything: both are sentences somebody typed, and that is the
whole boundary of this module.

### It records a description; it never matches anybody against it

Nothing here compares a company to a profile. Matching needs a *resolved*
attribute value for a real company — most-recently-observed industry, current
employee count — and resolution is the Knowledge Graph's, deliberately
separate ([ADR-0035](../../../../docs/architecture/adr/0035-commercial-profile.md)).
That separation is what lets the declaration ship and be useful before
anything can match against it, and it is why no word in this file names a
score, a rank or a fit.

### Stated in the customer's words, on purpose

`industries` and `countries` are free text. A seller says *"mid-market fintech
in the US and UK"*, and recording that faithfully is what a module whose job
is recording should do. Signora's canonical claim vocabulary — the controlled
language providers are normalized into — belongs to Provider Normalization,
and this module may not import it: the head of the pipeline reads no pipeline
module, enforced by contract. **Reconciling the two is what matching does**,
and matching is not built, is not this module's, and has no owner today. That
is recorded as a finding rather than pre-solved here.

### Revenue band is deliberately absent

Company size is declarable, as a plain employee range: an integer needs no
vocabulary and cannot diverge from one. **Revenue is the dimension that
would**, because `RevenueBand` already exists as a controlled enum in the
canonical vocabulary — so declaring revenue here would mean either importing a
pipeline module (which the boundary forbids) or defining a second
`RevenueBand` (which *truth has exactly one authoritative representation*
forbids more firmly). Neither is acceptable, so revenue waits for the ADR that
resolves it rather than arriving as a quiet copy.

### One profile per product

An ICP is *"the kind of company that buys **this**"*, so each profile names a
product from the catalog, and a product must be one the workspace currently
sells — you cannot describe who buys something you have not said you sell.
A product's id is stable across every catalog revision, which is what lets a
profile keep pointing at the same product twelve revisions on.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from modules.commercial_profile.domain.declaration import CommercialProfileError


class IcpError(CommercialProfileError):
    """A description of an ideal customer cannot be recorded as stated.

    **Its own type so the refusal can name the right page.** A catalog
    refusal and an ideal-customer refusal are fixed in different places, and
    a client that cannot tell them apart can only say *"something was
    wrong"*.
    """


#: One industry or country, as typed. Long enough for "Financial services and
#: insurance", short enough that a paragraph is obviously the wrong field.
MAX_CRITERION = 64
MAX_CRITERIA = 24
MAX_NOTES = 1024
#: Larger than any employer on earth. Not a business rule — a typo guard, so
#: that a stray keypress is refused where somebody can still see what they
#: meant to type.
MAX_EMPLOYEES = 10_000_000


@dataclass(frozen=True, slots=True)
class EmployeeRange:
    """How big the companies you sell to are.

    **A count, not a band.** Providers report employee counts as numbers and
    the canonical vocabulary carries them as numbers, so a range of integers
    needs no shared vocabulary and cannot drift from one. Either bound may be
    left out — *"anything over 500"* and *"under 50"* are both real answers.
    """

    minimum: int | None = None
    maximum: int | None = None

    def __post_init__(self) -> None:
        if self.minimum is None and self.maximum is None:
            raise IcpError(
                "a size range needs a lower bound, an upper bound, or both. Having no "
                "size preference is said by leaving size out, not by an empty range."
            )
        for bound in (self.minimum, self.maximum):
            if bound is None:
                continue
            if bound < 0:
                raise IcpError("a company size cannot be negative.")
            if bound > MAX_EMPLOYEES:
                raise IcpError(f"a company size is limited to {MAX_EMPLOYEES:,} employees.")
        if self.minimum is not None and self.maximum is not None and self.minimum > self.maximum:
            raise IcpError("the smallest company you sell to cannot be larger than the largest.")


def validate_criterion_list(values: tuple[str, ...], *, what: str) -> None:
    """Check a list of stated criteria without changing what was stated.

    **Validated, never normalised.** The customer's own capitalisation and
    spacing are part of what they said, and a module that records has no
    business tidying it. Comparison for duplicates folds case; storage does
    not.
    """
    if len(values) > MAX_CRITERIA:
        raise IcpError(
            f"an ideal customer is limited to {MAX_CRITERIA} {what} entries. Past that "
            "the description has stopped narrowing anything."
        )
    for value in values:
        if not value.strip():
            raise IcpError(f"a blank {what} says nothing — remove it.")
        if len(value) > MAX_CRITERION:
            raise IcpError(f"one {what} is limited to {MAX_CRITERION} characters.")
    folded = [value.strip().casefold() for value in values]
    if len(set(folded)) != len(folded):
        raise IcpError(f"the same {what} is listed twice.")


@dataclass(frozen=True, slots=True)
class ProductIcp:
    """Who buys one product, as the customer describes them."""

    product_id: UUID
    industries: tuple[str, ...] = ()
    countries: tuple[str, ...] = ()
    employees: EmployeeRange | None = None
    #: Anything the criteria above cannot hold — *"only where they already run
    #: Salesforce"*. Read by a human, and by whoever writes the ICP into a
    #: prompt later; never parsed.
    notes: str = ""

    def __post_init__(self) -> None:
        validate_criterion_list(self.industries, what="industry")
        validate_criterion_list(self.countries, what="country")
        if len(self.notes) > MAX_NOTES:
            raise IcpError(f"a note about an ideal customer is limited to {MAX_NOTES} characters.")
        if not self.industries and not self.countries and self.employees is None:
            # **The one judgement this file makes, and it is about the
            # statement rather than the world.** A description with no
            # criteria describes every company, which is the one thing the
            # customer cannot have meant — and it would be indistinguishable
            # from having said nothing at all, which they can already do by
            # leaving the product out.
            raise IcpError(
                "say at least one thing about who buys this. A description with no "
                "criteria would fit every company on earth."
            )


@dataclass(frozen=True, slots=True)
class IcpDeclaration:
    """Who buys each of the workspace's products, as declared at one moment.

    Immutable, and versioned as a whole for the same reason the catalog is:
    everything declared later cites a version, and an edited one would make
    those citations unresolvable. `revise` returns a **new** declaration
    naming the one it replaces, and the database agrees — there is no `UPDATE`
    grant on the table.
    """

    id: UUID
    workspace_id: UUID
    version: int
    profiles: tuple[ProductIcp, ...]
    created_at: datetime
    #: Who described them. A commercial declaration is a decision, and a
    #: customer is entitled to know whose.
    created_by: UUID
    supersedes: UUID | None = None

    def __post_init__(self) -> None:
        if self.version < 1:
            raise IcpError("a stored declaration is at version 1 or above.")
        products = [profile.product_id for profile in self.profiles]
        if len(set(products)) != len(products):
            raise IcpError(
                "one product is described twice. Two ideal customers for the same "
                "product would leave no answer to which one it has."
            )

    def revise(
        self,
        profiles: tuple[ProductIcp, ...],
        *,
        id: UUID,
        by: UUID,
        now: datetime,
    ) -> IcpDeclaration:
        """The next version of this declaration.

        Validation happens in the new declaration's own construction, so an
        invalid revision never exists — not even briefly, and not in a
        variable somebody might go on to save.
        """
        return IcpDeclaration(
            id=id,
            workspace_id=self.workspace_id,
            version=self.version + 1,
            profiles=profiles,
            created_at=now,
            created_by=by,
            supersedes=self.id,
        )


def first_declaration(
    workspace_id: UUID,
    profiles: tuple[ProductIcp, ...],
    *,
    id: UUID,
    by: UUID,
    now: datetime,
) -> IcpDeclaration:
    """The first ideal customer a workspace declares.

    Separate from `revise` because there is nothing to supersede, and a
    `supersedes=None` branch inside `revise` would be a second meaning for one
    method — *"replace that"* and *"there was nothing"* are different
    statements about the past.
    """
    return IcpDeclaration(
        id=id,
        workspace_id=workspace_id,
        version=1,
        profiles=profiles,
        created_at=now,
        created_by=by,
        supersedes=None,
    )
