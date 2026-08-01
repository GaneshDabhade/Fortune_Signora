"""The companies a customer wants watched.

**The fifth declaration, and the one the whole pipeline has been waiting
for.** `RunProviderSync` has taken a `subject: str` since M2.1 and nothing has
ever supplied one — the ten-stage machine has had no input stage. This is it.

### It names companies; it finds none

A customer types a company name. This module records it, exactly as typed, and
stops. **It does not resolve the name, look it up, check it exists, decide
when to fetch anything, or know that a provider exists** — every one of those
belongs to Provider Platform or the Knowledge Graph, and
[ADR-0036](../../../../docs/architecture/adr/0036-target-account-contract.md)
makes the boundary permanent rather than conventional.

The temptation here is more specific than in the earlier four: a watch list
*looks* like a job queue. It is not. It is a sentence — *"these are the
companies we care about"* — and what happens next is somebody else's decision
entirely.

### Why an entry has a stable id and a committee role does not

Slice 3 gave `CommitteeRole` no identifier and recorded the trigger for adding
one: *the first consumer that needs to cite a particular entry*. **That
trigger has fired here**, and for the reason ADR-0036 states — without an id,
a customer *renaming* an entry is indistinguishable from *removing one and
adding another*, and those are different instructions about spending money.

The id is **client-chosen**, like `Product`'s, which is what makes the whole
save idempotent: sending the same list twice cannot mint duplicates.

### The name is unresolved on purpose

*"Acme"* is what the customer typed and what travels downstream. Asking them
for a domain, a country or a registration number would be **asking a customer
to do resolution**, and resolution quality is Signora's competence, not
theirs. If an unresolved name is a weak key for some provider, that is the
adapter's problem — which is exactly why `subject` is opaque to the platform.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from modules.commercial_profile.domain.declaration import CommercialProfileError

#: A company name as somebody types it, with room for the long legal ones.
MAX_NAME = 128

#: **A guard against a pasted spreadsheet, not a plan limit.** How many
#: companies a customer is *entitled* to watch is a commercial decision about
#: packaging, and this module does not hold commercial decisions — it would
#: also be a cost model, which belongs to Provider Platform. This number is
#: far above anything a person types deliberately and far below anything that
#: would hurt a JSONB read.
MAX_ACCOUNTS = 1000


class TargetAccountError(CommercialProfileError):
    """A watch list cannot be recorded as stated."""


@dataclass(frozen=True, slots=True)
class TargetAccount:
    """One company the customer wants watched.

    **Deliberately two fields**, and the omissions are the design. A domain, a
    country, a registration number, an industry and an owner were each
    considered: the first three would ask the customer to do resolution, the
    fourth is something Signora will *observe* rather than be told, and the
    fifth is workflow — who works an account is the Opportunity Engine's, and
    it already has an assignment model.
    """

    id: UUID
    name: str

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise TargetAccountError("a company needs a name.")
        if len(self.name) > MAX_NAME:
            raise TargetAccountError(f"a company name is limited to {MAX_NAME} characters.")


@dataclass(frozen=True, slots=True)
class TargetAccountList:
    """Every company this workspace wants watched, as declared at one moment.

    Immutable and versioned on the terms all five declarations share: a
    revision is a new row naming the one it replaces, and the database agrees —
    there is no `UPDATE` grant on the table.

    **The version is not private to this module.** It travels on
    `target_accounts_changed` so a consumer can order two events against each
    other, which idempotency on `event_id` cannot do (ADR-0036). That makes it
    part of a published contract rather than an internal bookkeeping number.
    """

    id: UUID
    workspace_id: UUID
    version: int
    accounts: tuple[TargetAccount, ...]
    created_at: datetime
    #: Who said so. Choosing which companies Signora spends money watching is
    #: a decision, and a customer is entitled to know whose.
    created_by: UUID
    supersedes: UUID | None = None

    def __post_init__(self) -> None:
        if self.version < 1:
            raise TargetAccountError("a stored declaration is at version 1 or above.")
        if len(self.accounts) > MAX_ACCOUNTS:
            raise TargetAccountError(
                f"a watch list is limited to {MAX_ACCOUNTS} companies. Past that this "
                "is a spreadsheet rather than a list of accounts somebody is working."
            )
        ids = [account.id for account in self.accounts]
        if len(set(ids)) != len(ids):
            raise TargetAccountError(
                "the same entry is listed twice. A duplicate id would make a rename "
                "indistinguishable from a removal, which is the one thing a stable "
                "entry identity exists to prevent."
            )
        names = [account.name.strip().casefold() for account in self.accounts]
        if len(set(names)) != len(names):
            raise TargetAccountError(
                "two companies share a name. Nothing here resolves a name, so a seller "
                "reading the list could not tell which of them they had added."
            )

    def revise(
        self,
        accounts: tuple[TargetAccount, ...],
        *,
        id: UUID,
        by: UUID,
        now: datetime,
    ) -> TargetAccountList:
        """The next version of this list.

        Validation happens in the new declaration's own construction, so an
        invalid revision never exists — not even briefly, and not in a
        variable somebody might go on to save and announce.
        """
        return TargetAccountList(
            id=id,
            workspace_id=self.workspace_id,
            version=self.version + 1,
            accounts=accounts,
            created_at=now,
            created_by=by,
            supersedes=self.id,
        )


def first_target_accounts(
    workspace_id: UUID,
    accounts: tuple[TargetAccount, ...],
    *,
    id: UUID,
    by: UUID,
    now: datetime,
) -> TargetAccountList:
    """The first watch list a workspace declares.

    Separate from `revise` because there is nothing to supersede, and a
    `supersedes=None` branch inside `revise` would be a second meaning for one
    method — *"replace that"* and *"there was nothing"* are different
    statements about the past.
    """
    return TargetAccountList(
        id=id,
        workspace_id=workspace_id,
        version=1,
        accounts=accounts,
        created_at=now,
        created_by=by,
        supersedes=None,
    )
