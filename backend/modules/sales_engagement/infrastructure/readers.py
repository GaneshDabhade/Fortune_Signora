"""The three ports `AssembleApproach` has declared since SE-01, satisfied.

**Adapters, and deliberately nothing more.** `application/ports.py` says what
commercial reasoning needs in its own vocabulary — a Buying Committee Role,
evidence that names a title, a product the customer sells — and predicted this
file in its own words: *"the adapter that satisfies it is a separate, small
change once the export exists."* The export exists from A-ii, and this is that
change.

**Every one of them reads another module through `public/` only**, which the
import contract enforces rather than trusts (`pyproject.toml`, *"sales
engagement reaches every module it reasons from only through public/"*). No
storage shape crosses this boundary, so a conclusion can never come to depend
on one.

**They translate; they do not decide.** Filtering the committee to one product
is selection, not judgement — the ranking, the parts that bear on a purchase
and the reasons a role did not rank all live in `domain/`, where they are
reviewed as reasoning rather than as plumbing.
"""

from __future__ import annotations

from uuid import UUID

from modules.business_event_engine.public import BusinessEventQueries
from modules.commercial_profile.public import BuyingCommitteeReader, ProductCatalogReader
from modules.sales_engagement.domain.fit import ProductRef
from modules.sales_engagement.domain.reasoning import CommitteeRoleRef, Evidence

#: The fact key a `role_change` event carries its job title under, written by
#: the Business Event Engine's own point rule. **Read rather than assumed
#: everywhere**: an event type that names no title simply has no entry, and
#: `names_title` is then `None` — which is what `domain/reasoning.py` already
#: expects, and the case its rank-on-title-evidence rule is written for.
_TITLE = "title"


class CommercialProfileCommittee:
    """`CommitteeReader`, over the Commercial Profile's published committee.

    **Roles, never people.** The published view has no field for a person and
    this module could not carry one if it did.
    """

    def __init__(self, committees: BuyingCommitteeReader) -> None:
        self._committees = committees

    async def committee(
        self, workspace_id: UUID, *, product_id: UUID
    ) -> tuple[CommitteeRoleRef, ...]:
        """The seats declared for one product, or none.

        **A workspace that has declared nothing and a product with no
        committee are the same answer here**, and correctly so: the caller
        asked who decides about this product, and in both cases nobody has
        said. The distinction between *"never asked"* and *"answered
        emptily"* is one the declaring module keeps; it does not change what
        reasoning can do, which is rank on title evidence alone.
        """
        declaration = await self._committees.current(workspace_id)
        if declaration is None:
            return ()

        return tuple(
            CommitteeRoleRef(title=role.title, part=role.part)
            for committee in declaration.committees
            if committee.product_id == product_id
            for role in committee.roles
        )


class BusinessEventEvidenceReader:
    """`EvidenceReader`, over the Business Event Engine's published queries.

    **Citations, never copies.** `event_id` travels and the observations
    behind it do not: a reader follows the identifier back to the evidence,
    and this module reproduces nothing it would then have to keep in step.
    """

    def __init__(self, events: BusinessEventQueries) -> None:
        self._events = events

    async def evidence(self, workspace_id: UUID, *, account_id: UUID) -> tuple[Evidence, ...]:
        """Everything recorded about one account, as this module cites it.

        **`corroborating_providers` becomes a count**, which is all the
        reasoning uses and all it should see. The provider names are the
        Business Event Engine's to publish and nothing here is entitled to
        branch on which vendor agreed.
        """
        events = await self._events.business_events(workspace_id, account_id)
        return tuple(
            Evidence(
                event_id=event.id,
                type_key=str(event.type_key.value),
                summary=event.summary,
                occurred_at=event.occurred_at,
                corroborating_providers=len(event.corroborating_providers),
                names_title=_title(event.facts),
            )
            for event in events
        )


class CommercialProfilePortfolio:
    """`PortfolioReader`, over the Commercial Profile's published catalog."""

    def __init__(self, catalog: ProductCatalogReader) -> None:
        self._catalog = catalog

    async def portfolio(self, workspace_id: UUID) -> tuple[ProductRef, ...]:
        """What the workspace sells, or nothing when it has never said.

        **An empty portfolio is a usable answer.** The reasoning reads this
        only to infer which product an account is about, and when it cannot
        infer one it says so rather than guessing — which is the same outcome
        as a seller who has already told it.
        """
        catalog = await self._catalog.current(workspace_id)
        if catalog is None:
            return ()

        return tuple(ProductRef(id=product.id, name=product.name) for product in catalog.products)


def _title(facts: dict[str, object]) -> str | None:
    """The job title an event named, where it named one.

    **A missing title and a blank one are the same fact** — no title was
    named — and collapsing them here stops `domain/reasoning.py` matching a
    declared role against an empty string, which every role would tie on.
    """
    raw = facts.get(_TITLE)
    if not isinstance(raw, str) or not raw.strip():
        return None
    return raw
