"""Assembling a measurement from two other modules' published contracts.

**Fakes, not a database.** Every dependency is a `public/` Protocol, and the
M5B finding applies: *if a fake cannot stand in for a dependency, the
dependency was never really a boundary.*
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Sequence
from uuid import UUID, uuid4

from modules.commercial_profile.public import IcpCriteriaView, IcpView
from modules.knowledge_graph.domain.attributes import (
    ResolvedAttribute,
    ValueAgreement,
)
from modules.knowledge_graph.public import AccountAttributes
from modules.opportunity_engine.application.measure_icp import MeasureIcp
from modules.opportunity_engine.domain.opportunity import (
    Opportunity,
    OpportunityState,
    Qualification,
    Stage,
)

NOW = datetime(2026, 8, 6, tzinfo=UTC)
WORKSPACE = uuid4()
PRODUCT = uuid4()


def _resolved(value: object | None) -> ResolvedAttribute:
    if value is None:
        return ResolvedAttribute(
            value=None, agreement=ValueAgreement.UNKNOWN, providers=(), observed_at=None
        )
    return ResolvedAttribute(
        value=value,
        agreement=ValueAgreement.SINGLE_SOURCE,
        providers=("apollo",),
        observed_at=NOW,
    )


class FakeIcp:
    def __init__(self, view: IcpView | None) -> None:
        self._view = view

    async def current(self, workspace_id: UUID) -> IcpView | None:
        return self._view


class FakeAttributes:
    def __init__(self, by_entity: dict[UUID, tuple[object | None, object | None, object | None]]):
        self._by_entity = by_entity
        self.calls = 0

    async def for_accounts(
        self, workspace_id: UUID, entity_ids: Sequence[UUID]
    ) -> dict[UUID, AccountAttributes]:
        self.calls += 1
        answered: dict[UUID, AccountAttributes] = {}
        for entity_id in entity_ids:
            industry, country, employees = self._by_entity.get(entity_id, (None, None, None))
            answered[entity_id] = AccountAttributes(
                entity_id=entity_id,
                industry=_resolved(industry),
                country=_resolved(country),
                employee_count=_resolved(employees),
            )
        return answered

    async def for_account(self, workspace_id: UUID, entity_id: UUID) -> AccountAttributes:
        return (await self.for_accounts(workspace_id, [entity_id]))[entity_id]


class FakeDecided:
    def __init__(self, rows: list[tuple[UUID, Stage]]) -> None:
        self._rows = rows

    async def decided_page(
        self, workspace_id: UUID, *, after: object, limit: int
    ) -> tuple[tuple[Opportunity, OpportunityState], ...]:
        made = []
        for entity_id, stage in self._rows[:limit]:
            opportunity = Opportunity(
                id=uuid4(),
                workspace_id=workspace_id,
                entity_id=entity_id,
                generation=1,
                originating_buying_score_id=uuid4(),
                score_at_creation=70,
                contested_at_creation=False,
                qualification=Qualification.AUTOMATIC,
                policy_version=1,
                created_at=NOW,
                created_by=uuid4(),
            )
            made.append(
                (
                    opportunity,
                    OpportunityState(
                        id=uuid4(),
                        opportunity_id=opportunity.id,
                        workspace_id=workspace_id,
                        sequence=1,
                        stage=stage,
                        owner_id=None,
                        actor_id=uuid4(),
                        reason="decided",
                        occurred_at=NOW,
                    ),
                )
            )
        return tuple(made)

    def __getattr__(self, name: str) -> object:  # pragma: no cover - unused port methods
        raise AttributeError(name)


def _icp(**overrides: object) -> IcpView:
    defaults: dict[str, object] = {
        "industries": ("Fintech",),
        "countries": (),
        "employees_minimum": None,
        "employees_maximum": None,
    }
    return IcpView(
        workspace_id=WORKSPACE,
        version=1,
        criteria=(
            IcpCriteriaView(product_id=PRODUCT, **{**defaults, **overrides}),  # type: ignore[arg-type]
        ),
    )


def _measure(icp: IcpView | None, rows: list[tuple[UUID, Stage]], attributes: dict[UUID, tuple[object | None, object | None, object | None]]) -> MeasureIcp:
    return MeasureIcp(
        repository=FakeDecided(rows),  # type: ignore[arg-type]
        icp=FakeIcp(icp),
        attributes=FakeAttributes(attributes),
    )


class TestAWorkspaceWithNoDeclarationIsNotAnError:
    async def test_no_icp_measures_nothing(self) -> None:
        """**A state to wait in, not zeroes.** A workspace that has not
        described who buys from it has nothing to be measured against."""
        assert await _measure(None, [], {}).for_workspace(WORKSPACE) == ()


class TestItMeasuresWhatTheSellerActuallyDid:
    async def test_a_predictive_criterion_measures_above_one(self) -> None:
        won, lost = uuid4(), uuid4()
        found = await _measure(
            _icp(),
            [(won, Stage.CLOSED_WON), (lost, Stage.CLOSED_LOST)],
            {won: ("Fintech", None, None), lost: ("Retail", None, None)},
        ).for_workspace(WORKSPACE)

        industry = next(c for c in found[0].criteria if c.kind.value == "industry")
        assert industry.lift is not None and industry.lift > 1.0
        assert found[0].decided == 2

    async def test_an_account_nobody_described_leaves_the_denominator(self) -> None:
        known, unknown = uuid4(), uuid4()
        found = await _measure(
            _icp(),
            [(known, Stage.CLOSED_WON), (unknown, Stage.CLOSED_LOST)],
            {known: ("Fintech", None, None)},
        ).for_workspace(WORKSPACE)

        industry = next(c for c in found[0].criteria if c.kind.value == "industry")
        assert industry.unmeasured == 1
        assert industry.measured == 1

    async def test_every_criterion_kind_is_reported_even_when_undeclared(self) -> None:
        """A criterion the customer did not declare comes back `UNMEASURED`
        rather than being omitted."""
        account = uuid4()
        found = await _measure(
            _icp(), [(account, Stage.CLOSED_WON)], {account: ("Fintech", None, None)}
        ).for_workspace(WORKSPACE)

        assert {c.kind.value for c in found[0].criteria} == {
            "industry",
            "country",
            "employees",
        }

    async def test_the_order_is_stable_across_requests(self) -> None:
        account = uuid4()
        service = _measure(
            _icp(), [(account, Stage.CLOSED_WON)], {account: ("Fintech", None, None)}
        )

        first = await service.for_workspace(WORKSPACE)
        second = await service.for_workspace(WORKSPACE)

        assert [c.kind for c in first[0].criteria] == [c.kind for c in second[0].criteria]


class TestItReadsEveryAccountInOneCall:
    async def test_the_batch_is_used_rather_than_a_loop(self) -> None:
        """⚡ **The N+1 §14 calls a defect at write time.** Three accounts, one
        call — asserted, because a loop would pass every other test here."""
        accounts = [uuid4() for _ in range(3)]
        attributes = FakeAttributes({a: ("Fintech", None, None) for a in accounts})
        service = MeasureIcp(
            repository=FakeDecided([(a, Stage.CLOSED_WON) for a in accounts]),  # type: ignore[arg-type]
            icp=FakeIcp(_icp()),
            attributes=attributes,
        )

        await service.for_workspace(WORKSPACE)

        assert attributes.calls == 1
