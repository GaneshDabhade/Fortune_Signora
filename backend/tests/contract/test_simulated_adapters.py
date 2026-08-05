"""The shared Provider contract suite, run against every simulated adapter.

**This is the keystone test.** One suite, run against simulated and
production adapters alike, is the only mechanism that catches drift between
the two paths — and drift is the single failure that would invalidate
everything the simulator proves.

Today only simulated adapters exist, so the suite runs against those. When
a production adapter is written it gets a class here too, and any behaviour
that differs shows up immediately rather than during a paid integration.
"""

from __future__ import annotations

import pytest

from modules.provider_platform.infrastructure.adapters.simulated.adapter import (
    SimulatedProviderAdapter,
)
from modules.provider_platform.infrastructure.composition import SIMULATED_PROVIDERS
from modules.provider_platform.public import ProviderAdapter, ProviderName
from signora_platform.simulation import (
    ClockMode,
    DeliveryPlan,
    ReplayRecord,
    VirtualClock,
    build_timeline,
    load,
    load_scenario,
)
from tests.contract.provider_contract import ProviderContractSuite

REPLAY = ReplayRecord(
    scenario="baseline",
    seed=1,
    manifest_version="1",
    generator_version="0.1.0-fixture",
    clock_mode="instant",
    dataset_version="baseline@1",
)


def _adapter(provider: ProviderName) -> ProviderAdapter:
    """One adapter, built exactly as the composition root builds it.

    **The capability and the generator come from `SIMULATED_PROVIDERS`**, which
    is the table `build_provider_registry` reads. This suite used to hand-write
    both per class — five pairs, restated — and a capability moving in
    production would have left the contract suite testing the old one and
    passing (`CLAUDE.md` §2, *truth has exactly one authoritative
    representation*). **A provider added to that table is now contract-tested by
    existing.**
    """
    capability, generator = SIMULATED_PROVIDERS[provider]
    timeline = build_timeline(
        load_scenario("baseline", 1),
        load("baseline", 1),
        VirtualClock(mode=ClockMode.INSTANT),
        seed=1,
        # Restricted to this provider's own events, which is also a live
        # demonstration of Provider Independence: each adapter is built and
        # exercised without any other provider being present.
        providers=[provider.value],
    )
    return SimulatedProviderAdapter(
        provider=provider,
        capabilities=frozenset({capability}),
        generator=generator(),
        plan=DeliveryPlan(timeline, page_size=1),
        replay=REPLAY,
    )


def test_every_recognised_provider_has_an_adapter() -> None:
    """**`ProviderName` and `SIMULATED_PROVIDERS` are equal, and nothing else
    made them stay equal.**

    A provider with a ratified qualification record and no generator can be
    selected in configuration, and `build_provider_registry` refuses it at
    startup — correct, and late. This is the same fact caught in a suite rather
    than in a deployment, and it is the reason that refusal is not the only
    guard.
    """
    assert set(SIMULATED_PROVIDERS) == set(ProviderName)


class TestApolloSimulated(ProviderContractSuite):
    @pytest.fixture
    def adapter(self) -> ProviderAdapter:
        return _adapter(ProviderName.APOLLO)


class TestCoreSignalSimulated(ProviderContractSuite):
    @pytest.fixture
    def adapter(self) -> ProviderAdapter:
        return _adapter(ProviderName.CORESIGNAL)


class TestBomboraSimulated(ProviderContractSuite):
    @pytest.fixture
    def adapter(self) -> ProviderAdapter:
        return _adapter(ProviderName.BOMBORA)


class TestBuiltWithSimulated(ProviderContractSuite):
    @pytest.fixture
    def adapter(self) -> ProviderAdapter:
        # BuiltWith has no step in the baseline scenario; an adapter with an
        # empty timeline must still satisfy the contract. A provider with
        # nothing to report is a normal state, not an error.
        return _adapter(ProviderName.BUILTWITH)


class TestCrunchbaseSimulated(ProviderContractSuite):
    @pytest.fixture
    def adapter(self) -> ProviderAdapter:
        return _adapter(ProviderName.CRUNCHBASE)
