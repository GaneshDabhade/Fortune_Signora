"""The buying committee — who decides about what we sell.

**The third declaration.** The catalog says *what* a customer sells, the ideal
customer says *who buys it*, and this says **who inside that company has to
agree**. All three are sentences somebody typed about their own business.

### It records; it evaluates nobody

Nothing here scores a role's influence, ranks the committee, judges whether
one is complete, or decides who to contact. Those are conclusions about a real
company and a real deal, and every one of them belongs downstream — to modules
that have evidence to reason from, which this one deliberately has none of.

The temptation is specific and worth naming: a committee is *one plausible
field* away from becoming an influence model. `weight`, `seniority`,
`importance`, an ordered list read as a priority — each would turn a
declaration into a scoring input, in the module least equipped to review it.
The structural invariant in `tests/commercial_profile/test_boundary.py`
refuses the words; the shape below refuses the rest.

### Their words for *who*, a small vocabulary for *what part they play*

A role carries a **title the customer typed** — *"VP of Revenue Operations"*,
*"Head of Clinical Informatics"* — and a **part** from a five-value vocabulary
this module owns. The split is the same one the ideal customer makes between
free-text industries and a structured size, and it exists for the same reason:
the customer's language is what makes the declaration true, and a little
structure is what makes it usable by a human reading it later.

**The vocabulary is Signora's own and answers to no provider.** It is ordinary
sales language a seller uses unprompted, not a taxonomy anybody must translate
into — the Canonical Vocabulary Principle in
[40-commercial-profile.md](../../../../docs/architecture/40-commercial-profile.md).

### No person is named here

A committee is a **template of roles**, never a list of people. Person entities
are deferred platform-wide (`EntityKind` has `COMPANY` only), and naming an
individual would put personal data in a module with no lawful basis declared
for holding it and no consumer able to use it.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from typing import Final
from uuid import UUID, uuid5

from modules.commercial_profile.domain.declaration import CommercialProfileError


class BuyingCommitteeError(CommercialProfileError):
    """A committee cannot be recorded as stated.

    Its own type so a refusal names the page it is fixed on, the same reason
    the ideal customer has one.
    """


class CommitteePart(StrEnum):
    """The part a role plays in a purchase.

    **Five values, and the fifth argument for each was the customer's own
    sentence.** A seller says *"the CFO signs it"*, *"my champion is the RevOps
    lead"*, *"security has to sign off"* — these are the parts those sentences
    describe, and nothing here needs a definition a salesperson would ask
    about.

    Deliberately absent: **influencer**, considered and rejected as too vague
    to act on — every role influences, and a value that fits everything sorts
    nothing. **Approver** folded into `GATEKEEPER`, because procurement, legal
    and security are the same shape of obstacle whatever they are called, and
    two values a customer cannot tell apart is a worse answer than one.

    Owned here, versioned here, translated by nobody. Extending it is an
    ordinary change to this module; it is not a canonical platform vocabulary
    and nothing downstream reads it yet.
    """

    ECONOMIC_BUYER = "economic_buyer"
    """Owns the budget. The signature at the end."""

    CHAMPION = "champion"
    """Argues for it internally when nobody from Signora is in the room."""

    EVALUATOR = "evaluator"
    """Judges whether it actually works."""

    USER = "user"
    """Lives with it afterwards."""

    GATEKEEPER = "gatekeeper"
    """Must sign off before it can proceed — security, legal, procurement."""


MAX_TITLE = 96
#: A committee larger than this has stopped being a committee and become an
#: org chart. Not a business rule about the customer's company — a guard
#: against a pasted spreadsheet column, refused where somebody can still see
#: what they meant to paste.
MAX_ROLES = 16

#: The namespace every seat identifier is derived in.
#:
#: **A fixed UUID rather than a random one**, because the whole value of the
#: derivation is that it is the same everywhere and forever: the same product
#: and title must produce the same id in this process, in the next release, and
#: in a customer's database that has not been written to since July.
#:
#: Generated once and pinned. **Changing it re-identifies every seat in every
#: workspace**, which is why it lives here as a constant rather than in
#: configuration where something could vary it.
SEAT_NAMESPACE: Final = UUID("6f8d2c41-9a3e-5b07-8c14-2d9f7e0a5b63")


def seat_id(product_id: UUID, title: str) -> UUID:
    """The identifier for one seat on one product's committee.

    **Case and surrounding space are folded**, so a customer who retypes a
    title with different capitalisation is citing the same seat rather than
    creating a second one. Nothing further is normalised — deciding that two
    *different* words name one seat is the mapping ❓3 of
    [ADR-0400](../../../../docs/architecture/adr/0400-person-as-an-entity.md)
    leaves open, and it is not this module's to invent.

    **Pure and total.** No clock, no randomness, no storage, no session — the
    same inputs give the same id in every process and every release, which is
    the property the whole design rests on.
    """
    return uuid5(SEAT_NAMESPACE, f"{product_id}:{' '.join(title.split()).casefold()}")


@dataclass(frozen=True, slots=True)
class CommitteeRole:
    """One seat at the table.

    **Deliberately two fields**, and the omissions are the design. A seniority
    band, a headcount, a department and an influence weight were each
    considered: the first three are facts about a company that Signora will
    observe rather than be told, and the fourth is a judgement this module is
    forbidden to hold. Each would also be a field nothing reads, and a field
    nothing reads is a field nobody keeps accurate.

    ⚡ **The trigger fired on 2026-08-06 and a seat now has an id.** This
    docstring said *"no stable id, and that is a considered asymmetry with
    `Product`… trigger for adding one: the first consumer that needs to cite a
    particular seat."* **[TASK-428](../../../../docs/BACKLOG.md) is that
    consumer** — a committee seat citing a real affiliation — and the trigger
    is honoured rather than re-argued.

    **The id is *derived*, not stored, and that is what makes it possible at
    all.** Every declaration on disk is immutable and none carries an
    identifier, so a minted id could only ever be assigned going forward and
    **every committee declared before today would have none.** A derivation
    reads the same for a row written in July as for one written tomorrow —
    §2's rule arriving as a practical dividend: *"a stored copy of a derivable
    fact is a defect."*

    ⚠️ **A rename mints a new identity, and that limitation is real.** The id
    is a function of the product and the title, so *"VP Finance"* becoming
    *"CFO"* produces a different seat and a citation to the old one points at
    a seat that no longer exists.

    **The alternatives were considered and each needs something that does not
    exist.** Carrying an id across a rename requires somebody to say *"this is
    the same seat, renamed"* — which only an editing surface knows, and there
    is none. Matching on write by title has this same weakness plus a stored
    field. **Trigger for revisiting: a consumer that needs identity to survive
    a rename, whose own need decides the shape.**
    """

    title: str
    part: CommitteePart

    def seat_id(self, product_id: UUID) -> UUID:
        """This seat's stable identifier, derived from the product and title.

        **`product_id` is a parameter rather than a field** because a role does
        not know which committee it sits on — and giving it one would put the
        same product on every role in the tuple, which is a second
        representation of what `ProductCommittee` already says once.

        **Deterministic, so two processes agree without coordinating** and a
        declaration written before this method existed answers the same as one
        written after.
        """
        return seat_id(product_id, self.title)

    def __post_init__(self) -> None:
        if not self.title.strip():
            raise BuyingCommitteeError("a role needs a title — what they are called.")
        if len(self.title) > MAX_TITLE:
            raise BuyingCommitteeError(f"a role title is limited to {MAX_TITLE} characters.")


@dataclass(frozen=True, slots=True)
class ProductCommittee:
    """Who decides about one product."""

    product_id: UUID
    roles: tuple[CommitteeRole, ...]

    def __post_init__(self) -> None:
        if not self.roles:
            # **The one judgement here, and it is about the statement.** A
            # committee with no seats is not a description of how a purchase
            # gets decided — and it is indistinguishable from leaving the
            # product out, which the customer can already do.
            raise BuyingCommitteeError(
                "a buying committee needs at least one role. An empty one says nothing "
                "that leaving the product out does not say already."
            )
        if len(self.roles) > MAX_ROLES:
            raise BuyingCommitteeError(
                f"a buying committee is limited to {MAX_ROLES} roles. Past that it has "
                "stopped being a committee and become an org chart."
            )
        titles = [role.title.strip().casefold() for role in self.roles]
        if len(set(titles)) != len(titles):
            raise BuyingCommitteeError(
                "two roles share a title. A seller reading the committee could not tell "
                "which of them they had just spoken to."
            )


@dataclass(frozen=True, slots=True)
class BuyingCommittee:
    """Who decides about each of the workspace's products, at one moment.

    Immutable and versioned as a whole, on the catalog's terms: a revision is
    a new declaration naming the one it replaces, and the database agrees —
    there is no `UPDATE` grant on the table.

    **Versioned separately from the ideal customer**, because a committee and
    an ICP change on different days. Somebody adds a security reviewer without
    touching who the product is for, and one shared version would put both
    changes in an audit history that could no longer answer *what changed*.
    """

    id: UUID
    workspace_id: UUID
    version: int
    committees: tuple[ProductCommittee, ...]
    created_at: datetime
    #: Who said so. A commercial declaration is a decision, and a customer is
    #: entitled to know whose.
    created_by: UUID
    supersedes: UUID | None = None

    def __post_init__(self) -> None:
        if self.version < 1:
            raise BuyingCommitteeError("a stored declaration is at version 1 or above.")
        products = [committee.product_id for committee in self.committees]
        if len(set(products)) != len(products):
            raise BuyingCommitteeError(
                "one product has two committees. There would be no answer to which of them decides."
            )

    def revise(
        self,
        committees: tuple[ProductCommittee, ...],
        *,
        id: UUID,
        by: UUID,
        now: datetime,
    ) -> BuyingCommittee:
        """The next version of this declaration.

        Validation happens in the new declaration's own construction, so an
        invalid revision never exists — not even briefly, and not in a
        variable somebody might go on to save.
        """
        return BuyingCommittee(
            id=id,
            workspace_id=self.workspace_id,
            version=self.version + 1,
            committees=committees,
            created_at=now,
            created_by=by,
            supersedes=self.id,
        )


def first_committee(
    workspace_id: UUID,
    committees: tuple[ProductCommittee, ...],
    *,
    id: UUID,
    by: UUID,
    now: datetime,
) -> BuyingCommittee:
    """The first committee a workspace declares.

    Separate from `revise` because there is nothing to supersede, and a
    `supersedes=None` branch inside `revise` would be a second meaning for one
    method — *"replace that"* and *"there was nothing"* are different
    statements about the past.
    """
    return BuyingCommittee(
        id=id,
        workspace_id=workspace_id,
        version=1,
        committees=committees,
        created_at=now,
        created_by=by,
        supersedes=None,
    )
