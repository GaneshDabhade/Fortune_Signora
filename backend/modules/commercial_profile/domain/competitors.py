"""Which technologies a customer is up against.

**The sixth declaration.** The catalog says what a customer sells, the ideal
customer says who buys it, the committee says who has to agree, the focus says
which of it matters now, the target accounts say who to watch — and this says
*who else is in the room*.

### It names them; it resolves nothing

**A competitor is a technology name, exactly as the customer typed it, with a
stable id.** The same two fields as a target account, for the reason
[ADR-0036](../../../../docs/architecture/adr/0036-target-account-contract.md)
gives about that one: *"asking them for a domain, a country or a registration
number would be asking a customer to do resolution, and resolution quality is
Signora's competence, not theirs."*

**This module could not resolve one even if it should.** The import contract
*"commercial_profile declares; it never reads the pipeline"* forbids reading
the Knowledge Graph, and `knowledge_graph/public/` publishes nothing to read.
**That is the boundary working, not a gap** — matching *"Salesforce"*,
*"salesforce.com"* and *"SFDC"* to one technology is exactly the job the graph
exists to do, and a second resolver here would be free to disagree with it.

### What detects them, and where the join happens

`business_event_engine` already emits `TECHNOLOGY_ADOPTED` and
`TECHNOLOGY_RETIRED`, and two signals already consume them. **The detection
half shipped long before the declaration did**, and this is the fact it was
missing. But matching a declared name to a detected technology is
`signal_engine`'s, reading this list through `public/` against the graph's
resolution — not this module's.

### It names them; it never grades them

**No `threat_level`, no `severity`, no rank, no ordinal, no position.** A
technology is a competitor or it is not.

This module *"records; it evaluates nobody"*, and the temptation here is the
one `committee.py` names against itself — **one plausible field away from
becoming a scoring model in the module least equipped to review it.** A
`threat_level` would be a weight in the head of the pipeline, declared by a
customer, consumed by a score, reviewed by nobody. `test_boundary.py` already
refuses `priority` and `rank` in a domain identifier, and it refuses them here.

**Where that judgement belongs instead:** what a `competitor_entry` signal
contributes is a weight in `scoring_model@1.json` — a reviewed repository
artifact with a content hash, argued about in a diff. That is the least
powerful author capable of getting it right, and it is not this one.

### Why there is no *lost to* or *won against*

**That is an outcome, and an outcome has a date, an account and an amount.**
A competitive loss is a fact about one deal; this is a standing statement about
a market. Recording the first as a field on the second would be a workflow
event stored as configuration, free to disagree with the system that owns it.
**Trigger for adding one: [E1](../../../../docs/BACKLOG.md) landing**, at
which point a customer's own CRM already holds it and this module should read
rather than restate.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from modules.commercial_profile.domain.declaration import CommercialProfileError

#: A technology name as somebody types it. Shorter than a company's, because
#: these are product names rather than legal entities.
MAX_NAME = 128

#: **A guard against a pasted spreadsheet, not a plan limit** — the same
#: reasoning the watch list gives, and the same refusal to hold a commercial
#: decision. Lower than the watch list's because a market has competitors in
#: the tens; a customer who types a thousand is pasting a category, not
#: naming rivals.
MAX_COMPETITORS = 200


class CompetitorsError(CommercialProfileError):
    """A competitor declaration cannot be recorded as stated."""


@dataclass(frozen=True, slots=True)
class Competitor:
    """One technology the customer competes against.

    **Deliberately two fields**, and the omissions are the design — the same
    ones `TargetAccount` refuses, for the same reasons. A vendor, a category
    and a website would each ask the customer to do resolution; a `since` date
    is something Signora will *observe* from `TECHNOLOGY_ADOPTED` rather than
    be told; and anything ranking one competitor above another is the scoring
    model's, not a declaration's.
    """

    id: UUID
    name: str

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise CompetitorsError("a competitor needs a name.")
        if len(self.name) > MAX_NAME:
            raise CompetitorsError(f"a competitor name is limited to {MAX_NAME} characters.")


@dataclass(frozen=True, slots=True)
class DeclaredCompetitors:
    """Every technology this workspace competes against, as declared at one moment.

    Immutable and versioned on the terms all six declarations share: a revision
    is a new row naming the one it replaces, and the database agrees — there is
    no `UPDATE` grant on the table.

    **Versioned separately from the other five**, for the reason `focus.py`
    gives: these move on their own clock, and folding them together fills one
    declaration's audit history with another's changes.
    """

    id: UUID
    workspace_id: UUID
    version: int
    competitors: tuple[Competitor, ...]
    created_at: datetime
    #: Who said so. Naming a competitor is a commercial judgement, and a
    #: customer is entitled to know whose.
    created_by: UUID
    supersedes: UUID | None = None

    def __post_init__(self) -> None:
        if self.version < 1:
            raise CompetitorsError("a stored declaration is at version 1 or above.")
        if len(self.competitors) > MAX_COMPETITORS:
            raise CompetitorsError(
                f"a competitor list is limited to {MAX_COMPETITORS} technologies. Past "
                "that this is a market category rather than the rivals somebody is "
                "actually losing deals to."
            )
        ids = [competitor.id for competitor in self.competitors]
        if len(set(ids)) != len(ids):
            raise CompetitorsError(
                "the same entry is listed twice. A duplicate id would make a rename "
                "indistinguishable from a removal, which is the one thing a stable "
                "entry identity exists to prevent."
            )
        names = [competitor.name.strip().casefold() for competitor in self.competitors]
        if len(set(names)) != len(names):
            raise CompetitorsError(
                "two competitors share a name. Nothing here resolves a name, so a "
                "seller reading the list could not tell which of them they had added."
            )

    # **An empty declaration is legal**, for the reason the focus gives: the
    # aggregate *is* the statement, so there is nothing to leave out. It is how
    # a customer says *"we do not track competitors"* — and it has an author
    # and a moment, which is what makes it different from never having said
    # anything. A consumer that cannot tell those apart would report an empty
    # result where the truth is an empty input (D6).

    def revise(
        self,
        competitors: tuple[Competitor, ...],
        *,
        id: UUID,
        by: UUID,
        now: datetime,
    ) -> DeclaredCompetitors:
        """The next version of this declaration.

        Validation happens in the new declaration's own construction, so an
        invalid revision never exists — not even briefly, and not in a variable
        somebody might go on to save.
        """
        return DeclaredCompetitors(
            id=id,
            workspace_id=self.workspace_id,
            version=self.version + 1,
            competitors=competitors,
            created_at=now,
            created_by=by,
            supersedes=self.id,
        )


def first_competitors(
    workspace_id: UUID,
    competitors: tuple[Competitor, ...],
    *,
    id: UUID,
    by: UUID,
    now: datetime,
) -> DeclaredCompetitors:
    """The first competitor declaration a workspace makes.

    Separate from `revise` because there is nothing to supersede, and a
    `supersedes=None` branch inside `revise` would be a second meaning for one
    method — *"replace that"* and *"there was nothing"* are different
    statements about the past.
    """
    return DeclaredCompetitors(
        id=id,
        workspace_id=workspace_id,
        version=1,
        competitors=competitors,
        created_at=now,
        created_by=by,
        supersedes=None,
    )
