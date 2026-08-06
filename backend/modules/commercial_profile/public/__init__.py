"""What the Commercial Profile publishes to other modules.

**The module's first public contract, and it stayed empty for four slices on
purpose.** A product catalog, an ideal customer, a buying committee and a
commercial focus are all declared and none of them is published, because
nothing downstream consumes a declaration yet — a reader with no counterparty
is the speculative abstraction §6 forbids.

`TargetAccountReader` is different: Provider Platform has taken a `subject`
since M2.1 and nothing has ever supplied one. It is published because somebody
is waiting for it, which is the only good reason a contract exists.

**The paragraph above is the record of why this surface was small, and the
rule in it is what widened it.** The buying committee and the product catalog
are published from A-ii, on exactly the test it states: Sales Engagement's
`AssembleApproach` cannot be assembled without them, and its own
`application/ports.py` has named the absence since SE-01 — *"the adapter that
satisfies it is a separate, small change once the export exists."* **The
ideal customer and the commercial focus stay unpublished**, because nothing
consumes them yet and a reader with no counterparty is still the speculative
abstraction §6 forbids.

### What this surface is, and what it can never become

**It answers *"which companies did the customer name?"* and nothing else.**
Governed by [ADR-0036](../../../../docs/architecture/adr/0036-target-account-contract.md),
which makes four ownership boundaries permanent — intent here, synchronization
in Provider Platform, understanding in the Knowledge Graph, relevance in the
Signal Engine.

Three things this port must never grow, each of which would look helpful:

- **A delta.** *What has and has not been fetched is not a fact this module
  holds.* The delta a consumer needs is against its own watermark, not against
  the previous declaration — and a declaration-delta would call a re-added,
  never-fetched account *"no change"*.
- **A resolved company, a domain, or any canonical value.** The name is what
  the customer typed. Resolving it here would make the recording module
  resolve, and it is the one least equipped to review a resolution.
- **Anything about synchronization** — cadence, cost, provider, health,
  priority. None of it is a customer's to declare and none is this module's to
  know.

### Frozen views, never domain objects

The views below are copies, deliberately. Handing a consumer a
`TargetAccountList` would hand it this module's domain — its validation rules,
its constructors, and a shape that must then stay still for reasons outside
this module's control. A view can be widened without touching the aggregate,
and the aggregate can be refactored without touching consumers.

### It is a stable interface from today

The next change to anything in this file is a compatibility question, not an
edit: add fields, never remove or repurpose them, and a breaking change is a
new version with a stated deprecation window (§9). That is the price of being
consumed, and it is why the surface is as small as it is.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol
from uuid import UUID

from modules.commercial_profile.domain.evaluation import (
    CriterionKind,
    CriterionVerdict,
    ObservedAttributes,
    Verdict,
    evaluate,
)
from modules.commercial_profile.domain.icp import EmployeeRange, ProductIcp


@dataclass(frozen=True, slots=True)
class TargetAccountView:
    """One company a customer named.

    `name` is **exactly what they typed** — unresolved, unnormalised, and not
    guaranteed to identify anything. Interpreting it is the consumer's job,
    which is why `ProviderRequest.subject` is opaque to the platform.

    `id` is stable across every revision of the list, which is what lets a
    consumer tell a rename from a remove-and-add.
    """

    id: UUID
    name: str


@dataclass(frozen=True, slots=True)
class TargetAccountListView:
    """Every company a workspace wants watched, in the version in force.

    **The whole list, never a delta** — see the module docstring.

    `version` is the same integer that travels on
    `commercial_profile.target_accounts_changed`. A consumer that reads this
    after handling an event can confirm it is acting on the declaration the
    event announced rather than one that has moved on since.
    """

    workspace_id: UUID
    version: int
    accounts: tuple[TargetAccountView, ...]


class TargetAccountReader(Protocol):
    """The read side of the target account list.

    Implemented in this module's `infrastructure/` and injected by the
    composition root, so a consumer never learns that this is backed by SQL —
    and never learns anything else about this module either.
    """

    async def current(self, workspace_id: UUID) -> TargetAccountListView | None:
        """The list in force, or ``None`` when the workspace has never
        declared one.

        **`None` rather than an empty list**, because the two are different
        facts and a consumer should be able to tell them apart: *"they have
        not told us yet"* is a state to wait in, and *"they told us to watch
        nobody"* is an instruction to act on.
        """
        ...


@dataclass(frozen=True, slots=True)
class DeclaredCompetitorView:
    """One technology a customer named as a rival.

    `name` is **exactly what they typed** — unresolved, unnormalised, and not
    guaranteed to identify anything. Matching it against an adopted technology
    is the consumer's judgement, on the same terms as a target account's name.

    `id` is stable across every revision of the list, which is what lets a
    consumer tell a rename from a remove-and-add.

    **It carries no judgement, and cannot grow one.** Nothing here says how
    much a rival matters: that is a weight in a reviewed scoring model, and a
    field on this view would be the recording module grading its own input.
    """

    id: UUID
    name: str


@dataclass(frozen=True, slots=True)
class DeclaredCompetitorListView:
    """Every technology a workspace competes against, in the version in force.

    **The whole list, never a delta** — see the module docstring.

    **No `version`, and the asymmetry with `TargetAccountListView` is the
    point.** That one carries a version because the same integer travels on
    `commercial_profile.target_accounts_changed`, so a consumer handling that
    event can confirm which declaration it is acting on. **Nothing announces
    this list** ([ADR-0403](../../../../docs/architecture/adr/\
0403-signal-engine-reads-a-declaration.md)):
    it is resolved on demand during a run that was triggered by something
    else, so there is no event to reconcile a version against and a version
    here would be a number with nothing to compare it to.
    """

    workspace_id: UUID
    competitors: tuple[DeclaredCompetitorView, ...]


class DeclaredCompetitorReader(Protocol):
    """The read side of the competitor list.

    Implemented in this module's `infrastructure/` and injected by the
    composition root, so a consumer never learns that this is backed by SQL —
    and never learns anything else about this module either.
    """

    async def current(self, workspace_id: UUID) -> DeclaredCompetitorListView | None:
        """The list in force, or ``None`` when the workspace has never
        declared one.

        **`None` rather than an empty list**, for the reason the target
        account reader gives: *"they have not told us yet"* is a state to wait
        in, and *"they told us they compete with nobody"* is an instruction to
        act on. A consumer that collapsed them would treat a considered answer
        as an unanswered question.
        """
        ...


@dataclass(frozen=True, slots=True)
class BuyingCommitteeRoleView:
    """One seat on a Buying Committee.

    **`part` travels as the string this module declared, never as its enum.**
    Publishing `CommitteePart` would export a vocabulary this module intends to
    extend, and every consumer would then have to be re-released to add a sixth
    value — which is the coupling a published contract exists to avoid. A
    consumer keys on the string and treats one it does not recognise as a seat
    it has no rule for, which is the correct behaviour for a vocabulary that
    grew.

    **No person, and there is no field for one.** A role is a slot, and the
    platform holds no person's name at any point.
    """

    #: **What a consumer cites when it means *this seat*.**
    #:
    #: Derived from the product and the title rather than stored, so every
    #: committee ever declared has one — including the immutable declarations
    #: written before the field existed, which could never have been
    #: backfilled ([TASK-428](../../../../docs/BACKLOG.md)).
    #:
    #: ⚠️ **A renamed seat is a different id.** Carrying identity across a
    #: rename needs somebody to say *"same seat, renamed"*, and no editing
    #: surface exists to say it. **A consumer holding a citation that no longer
    #: resolves should read it as "that seat is gone", which is true.**
    id: UUID
    title: str
    part: str


@dataclass(frozen=True, slots=True)
class ProductCommitteeView:
    """Who decides about one product."""

    product_id: UUID
    roles: tuple[BuyingCommitteeRoleView, ...]


@dataclass(frozen=True, slots=True)
class BuyingCommitteeView:
    """Who decides about each of the workspace's products, in the version in
    force."""

    workspace_id: UUID
    version: int
    committees: tuple[ProductCommitteeView, ...]


class BuyingCommitteeReader(Protocol):
    """The read side of the buying committee.

    **Published because somebody is waiting for it**, which is the only reason
    the header above gives for a contract existing. Sales Engagement's
    `CommitteeReader` has declared this need since SE-01 and named the absence
    in its own docstring; the counterparty this surface was waiting for is
    now built.
    """

    async def current(self, workspace_id: UUID) -> BuyingCommitteeView | None:
        """The declaration in force, or ``None`` when there has never been one.

        **`None` rather than an empty tuple**, on the same terms as the two
        readers above: a workspace that has never described how a purchase gets
        decided is in a state to wait in, not one to reason from.
        """
        ...


@dataclass(frozen=True, slots=True)
class ProductView:
    """One product the customer sells."""

    id: UUID
    name: str


@dataclass(frozen=True, slots=True)
class ProductCatalogView:
    """Everything the workspace sells, in the version in force."""

    workspace_id: UUID
    version: int
    products: tuple[ProductView, ...]


class ProductCatalogReader(Protocol):
    """The read side of the product catalog.

    **Deliberately name and identity, and nothing else.** The catalog also
    holds what a product is for and how it is described; a consumer inferring
    *which* product an account is about needs neither, and a wider view would
    invite one to reason from a description this module never promised to keep
    stable.
    """

    async def current(self, workspace_id: UUID) -> ProductCatalogView | None:
        """The catalog in force, or ``None`` when nothing has been declared."""
        ...



@dataclass(frozen=True, slots=True)
class IcpCriteriaView:
    """What a customer said their ideal customer looks like, for one product.

    **The thirteenth published view and the first that is the ICP.** Thirteen
    views were published before this one and not one carried the criteria, so
    **no module could read them at all** — which is why sixteen consumers were
    counted waiting on a capability nobody could build
    ([443](../../../../docs/architecture/443-account-matching-capability.md)).

    **Free text, and it stays free text across the boundary.** `industries`
    and `countries` are exactly what the seller typed. Normalising them here
    would put a second vocabulary in the module whose whole job is recording
    the first one, and a consumer receiving *"mid-market fintech"* needs to
    know that is a person's phrase rather than a canonical value.

    **`notes` is deliberately absent.** It exists to be read by a human —
    *"only where they already run Salesforce"* — and is explicitly *"never
    parsed"*. Publishing it would invite exactly the parsing it forbids.
    """

    product_id: UUID
    industries: tuple[str, ...]
    countries: tuple[str, ...]
    #: Inclusive bounds, either of which may be absent — *"anything over 500"*
    #: is a real answer. Published as two integers rather than the domain's
    #: `EmployeeRange` for the reason every view here exists: a consumer
    #: should not inherit this module's constructors or its validation.
    employees_minimum: int | None
    employees_maximum: int | None


@dataclass(frozen=True, slots=True)
class IcpView:
    """Every product's ideal customer, in the version in force."""

    workspace_id: UUID
    version: int
    criteria: tuple[IcpCriteriaView, ...]


class IcpReader(Protocol):
    """The read side of the ideal customer.

    **Published because sixteen consumers are waiting**, which is the only
    reason the header above gives for a contract existing — and the largest
    count any surface in this module has had before it was built.

    **A reader, and deliberately not a matcher.** Whether an account satisfies
    these criteria is answered by `evaluate` in this module's `domain`, which
    is pure and takes the observed attributes as an argument. Putting the
    comparison behind this port would make the module *fetch* what it needs to
    compare against, and fetching from the pipeline is precisely what its
    import contract forbids.
    """

    async def current(self, workspace_id: UUID) -> IcpView | None:
        """The declaration in force, or ``None`` when there has never been one.

        **`None` rather than an empty tuple**, on the same terms as every
        reader above: a workspace that has never described who buys from it is
        in a state to wait in, not one to reason from — and an account
        evaluated against no criteria at all would come back `UNMEASURED`
        three times, which is true but useless.
        """
        ...

# ── The predicate, published (TASK-406) ──────────────────────────────────────
#
# ⚡ **`evaluate` shipped in `domain/` at TASK-434 and no consumer could call
# it.** It takes `ProductIcp` — this module's aggregate — so a module holding
# `IcpCriteriaView` had the criteria and no way to ask the question about them.
# **A foundation sixteen consumers were counted waiting on, that none of them
# could reach.**
#
# **Published now on the trigger this module already uses**: *the first
# consumer that needs it* — [TASK-406](../../../../docs/BACKLOG.md), whose own
# row says *"do not inline an in-ICP test here; consume
# `commercial_profile/public/`'s."*
#
# **The verdict types travel as themselves, not as views.** They are value
# objects with no aggregate behind them — the same reason `knowledge_graph`
# publishes `MatchStrength` directly — and wrapping them would create a second
# vocabulary for three words that already mean exactly one thing each.


def evaluate_criteria(
    criteria: IcpCriteriaView,
    *,
    industry: str | None = None,
    country: str | None = None,
    employees: int | None = None,
) -> tuple[CriterionVerdict, ...]:
    """Whether an account satisfies each of one product's declared criteria.

    **Pure**, like the domain function beneath it: no session, no clock, no
    repository. The caller supplies what the pipeline observed — typically
    from `knowledge_graph`'s `AccountAttributesReader`, whose `unknown` is the
    same fact as the `UNMEASURED` that comes back here.

    **Three keyword arguments rather than a published `ObservedAttributes`.**
    A consumer already holds three resolved values and would otherwise
    construct a type solely to pass them one call later — and a published type
    whose only purpose is to be constructed at the call site is ceremony, not a
    contract.

    **Always three verdicts, one per criterion kind**, whether or not the
    declaration mentions them — a criterion the customer did not declare comes
    back `UNMEASURED` rather than being omitted, on the ruling that *"the
    absence of results and the absence of the group represent different
    business meanings."*

    ⛔ **No overall answer, deliberately.** Rolling three verdicts into
    *"matches"* needs a rule for `UNMEASURED`, and every available rule is a
    judgement: treat it as a pass and an unmeasured account looks qualified,
    treat it as a fail and it looks disqualified. **That rule belongs to
    whichever consumer has a reason for it**, stated where a customer can see
    it.
    """
    return evaluate(
        ProductIcp(
            product_id=criteria.product_id,
            industries=criteria.industries,
            countries=criteria.countries,
            employees=(
                EmployeeRange(
                    minimum=criteria.employees_minimum, maximum=criteria.employees_maximum
                )
                if criteria.employees_minimum is not None
                or criteria.employees_maximum is not None
                else None
            ),
        ),
        ObservedAttributes(industry=industry, country=country, employees=employees),
    )


__all__ = [
    "CriterionKind",
    "CriterionVerdict",
    "Verdict",
    "evaluate_criteria",
    "BuyingCommitteeReader",
    "BuyingCommitteeRoleView",
    "BuyingCommitteeView",
    "DeclaredCompetitorListView",
    "DeclaredCompetitorReader",
    "DeclaredCompetitorView",
    "IcpCriteriaView",
    "IcpReader",
    "IcpView",
    "ProductCatalogReader",
    "ProductCatalogView",
    "ProductCommitteeView",
    "ProductView",
    "TargetAccountListView",
    "TargetAccountReader",
    "TargetAccountView",
]
