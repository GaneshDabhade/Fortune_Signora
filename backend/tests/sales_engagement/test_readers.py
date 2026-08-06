"""The three adapters that satisfy `AssembleApproach`'s ports.

**Fakes, not a database.** These translate one module's published view into
another's vocabulary; a test needing PostgreSQL to prove a mapping would be
testing SQLAlchemy. The wiring is proven end to end in
`tests/integration/test_api_approach.py`, where the declarations arrive through
the product's own API.
"""

from datetime import UTC, datetime
from uuid import UUID, uuid4

from modules.business_event_engine.domain.business_event import BusinessEvent
from modules.business_event_engine.domain.taxonomy import BusinessDomain, BusinessEventType
from modules.commercial_profile.domain.committee import seat_id
from modules.commercial_profile.public import (
    BuyingCommitteeRoleView,
    BuyingCommitteeView,
    ProductCatalogView,
    ProductCommitteeView,
    ProductView,
)
from modules.sales_engagement.infrastructure.readers import (
    BusinessEventEvidenceReader,
    CommercialProfileCommittee,
    CommercialProfilePortfolio,
)

WORKSPACE = uuid4()


class FakeCommittees:
    def __init__(self, view: BuyingCommitteeView | None) -> None:
        self._view = view

    async def current(self, workspace_id: UUID) -> BuyingCommitteeView | None:
        return self._view


class FakeCatalog:
    def __init__(self, view: ProductCatalogView | None) -> None:
        self._view = view

    async def current(self, workspace_id: UUID) -> ProductCatalogView | None:
        return self._view


class FakeEvents:
    def __init__(self, *events: BusinessEvent) -> None:
        self._events = events

    async def business_events(
        self, workspace_id: UUID, entity_id: UUID, **kwargs: object
    ) -> tuple[BusinessEvent, ...]:
        return self._events


def _event(*, facts: dict[str, object], providers: tuple[str, ...] = ("clearbit",)) -> BusinessEvent:
    now = datetime(2026, 8, 5, tzinfo=UTC)
    return BusinessEvent(
        id=uuid4(),
        workspace_id=WORKSPACE,
        entity_id=uuid4(),
        type_key=BusinessEventType.LEADERSHIP_APPOINTED,
        domain=BusinessDomain.LEADERSHIP,
        occurred_at=now,
        window_start=now,
        window_end=now,
        detected_at=now,
        summary="A VP of Engineering was appointed.",
        facts=facts,
        evidence_observation_ids=(uuid4(),),
        corroborating_providers=providers,
        taxonomy_version=1,
    )


class TestTheCommitteeAdapter:
    async def test_it_returns_the_seats_declared_for_one_product(self) -> None:
        wanted, other = uuid4(), uuid4()
        reader = CommercialProfileCommittee(
            FakeCommittees(
                BuyingCommitteeView(
                    workspace_id=WORKSPACE,
                    version=1,
                    committees=(
                        ProductCommitteeView(
                            product_id=other,
                            roles=(
                                BuyingCommitteeRoleView(
                                    id=seat_id(other, "CTO"), title="CTO", part="evaluator"
                                ),
                            ),
                        ),
                        ProductCommitteeView(
                            product_id=wanted,
                            roles=(
                                BuyingCommitteeRoleView(
                                    id=seat_id(wanted, "CFO"),
                                    title="CFO",
                                    part="economic_buyer",
                                ),
                            ),
                        ),
                    ),
                )
            )
        )

        roles = await reader.committee(WORKSPACE, product_id=wanted)

        assert [(role.title, role.part) for role in roles] == [("CFO", "economic_buyer")]

    async def test_a_workspace_that_declared_nothing_yields_no_seats(self) -> None:
        """**`None` from the published reader is not an error here.** A
        workspace that has never described how a purchase gets decided still
        gets an approach — one that ranks on title evidence alone."""
        reader = CommercialProfileCommittee(FakeCommittees(None))

        assert await reader.committee(WORKSPACE, product_id=uuid4()) == ()

    async def test_a_product_with_no_committee_yields_no_seats(self) -> None:
        reader = CommercialProfileCommittee(
            FakeCommittees(
                BuyingCommitteeView(
                    workspace_id=WORKSPACE,
                    version=1,
                    committees=(
                        ProductCommitteeView(
                            product_id=(unread := uuid4()),
                            roles=(
                                BuyingCommitteeRoleView(
                                    id=seat_id(unread, "CFO"),
                                    title="CFO",
                                    part="economic_buyer",
                                ),
                            ),
                        ),
                    ),
                )
            )
        )

        assert await reader.committee(WORKSPACE, product_id=uuid4()) == ()

    async def test_an_unrecognised_part_crosses_unchanged(self) -> None:
        """**The whole reason `part` is a string.** Commercial Profile may
        declare a sixth part without this module being re-released; the rule
        table has no entry and the role ranks on title evidence alone."""
        product = uuid4()
        reader = CommercialProfileCommittee(
            FakeCommittees(
                BuyingCommitteeView(
                    workspace_id=WORKSPACE,
                    version=1,
                    committees=(
                        ProductCommitteeView(
                            product_id=product,
                            roles=(
                                BuyingCommitteeRoleView(
                                    id=seat_id(product, "Head of AI"),
                                    title="Head of AI",
                                    part="a_part_from_2027",
                                ),
                            ),
                        ),
                    ),
                )
            )
        )

        roles = await reader.committee(WORKSPACE, product_id=product)

        assert roles[0].part == "a_part_from_2027"


class TestTheEvidenceAdapter:
    async def test_it_cites_rather_than_copies(self) -> None:
        event = _event(facts={"title": "VP of Engineering"}, providers=("clearbit", "crunchbase"))
        reader = BusinessEventEvidenceReader(FakeEvents(event))  # type: ignore[arg-type]

        (evidence,) = await reader.evidence(WORKSPACE, account_id=uuid4())

        assert evidence.event_id == event.id
        assert evidence.summary == event.summary
        assert evidence.type_key == "leadership_appointed"
        # **A count of agreement, never a weight, and never the names.**
        assert evidence.corroborating_providers == 2
        assert evidence.names_title == "VP of Engineering"

    async def test_an_event_naming_no_title_carries_none(self) -> None:
        reader = BusinessEventEvidenceReader(FakeEvents(_event(facts={"amount": "40000000"})))  # type: ignore[arg-type]

        (evidence,) = await reader.evidence(WORKSPACE, account_id=uuid4())

        assert evidence.names_title is None

    async def test_a_blank_title_is_the_same_fact_as_no_title(self) -> None:
        """**Collapsed deliberately.** An empty string would match every
        declared role equally in `domain/reasoning.py`, which is worse than
        admitting no title was named."""
        reader = BusinessEventEvidenceReader(FakeEvents(_event(facts={"title": "   "})))  # type: ignore[arg-type]

        (evidence,) = await reader.evidence(WORKSPACE, account_id=uuid4())

        assert evidence.names_title is None

    async def test_a_title_that_is_not_a_string_is_no_title(self) -> None:
        """`facts` is untyped by design — it holds whatever the rule computed."""
        reader = BusinessEventEvidenceReader(FakeEvents(_event(facts={"title": 7})))  # type: ignore[arg-type]

        (evidence,) = await reader.evidence(WORKSPACE, account_id=uuid4())

        assert evidence.names_title is None

    async def test_an_account_with_nothing_recorded_yields_no_evidence(self) -> None:
        reader = BusinessEventEvidenceReader(FakeEvents())  # type: ignore[arg-type]

        assert await reader.evidence(WORKSPACE, account_id=uuid4()) == ()


class TestThePortfolioAdapter:
    async def test_it_returns_what_the_workspace_sells(self) -> None:
        first, second = uuid4(), uuid4()
        reader = CommercialProfilePortfolio(
            FakeCatalog(
                ProductCatalogView(
                    workspace_id=WORKSPACE,
                    version=1,
                    products=(
                        ProductView(id=first, name="Revenue Cloud"),
                        ProductView(id=second, name="Service Cloud"),
                    ),
                )
            )
        )

        portfolio = await reader.portfolio(WORKSPACE)

        assert [(product.id, product.name) for product in portfolio] == [
            (first, "Revenue Cloud"),
            (second, "Service Cloud"),
        ]

    async def test_a_workspace_that_declared_nothing_sells_nothing_here(self) -> None:
        """**An empty portfolio is a usable answer**: the reasoning reads it
        only to infer which product an account is about, and when it cannot it
        says so rather than guessing."""
        reader = CommercialProfilePortfolio(FakeCatalog(None))

        assert await reader.portfolio(WORKSPACE) == ()
