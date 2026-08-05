"""Composition root for the Provider Platform.

**The only place that knows a simulator exists.** Selection is by
configuration; every layer below receives a `ProviderAdapter` and cannot
tell what is behind it (AC-21).
"""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from modules.provider_platform.application.ports import Pacer, SyncReporter
from modules.provider_platform.application.run_sync import RunProviderSync
from modules.provider_platform.domain.provider import (
    ProviderAdapter,
    ProviderCapability,
    ProviderName,
    ProviderRegistry,
)
from modules.provider_platform.infrastructure.adapters.simulated.adapter import (
    SimulatedProviderAdapter,
)
from modules.provider_platform.infrastructure.adapters.simulated.settings import (
    SimulationSettings,
)
from modules.provider_platform.infrastructure.metrics import build_sync_metrics
from modules.provider_platform.infrastructure.pacing import AsyncioPacer
from modules.provider_platform.infrastructure.repository import ProviderSyncRepository
from modules.provider_platform.infrastructure.settings import ProviderSettings
from signora_platform.event_bus import EventPublisher
from signora_platform.simulation import (
    ClockMode,
    DeliveryPlan,
    ReplayRecord,
    VirtualClock,
    build_timeline,
    load,
    load_scenario,
)
from signora_platform.simulation.generators import (
    GENERATOR_VERSION,
    ApolloFixtureGenerator,
    BomboraFixtureGenerator,
    BuiltWithFixtureGenerator,
    CoreSignalFixtureGenerator,
    CrunchbaseFixtureGenerator,
    PayloadGenerator,
)


class ProviderRegistrationError(RuntimeError):
    """A registry that cannot be built correctly, refusing to be built wrongly.

    **A composition error, raised at startup**, which is the only moment it can
    still be cheap. The alternative is a process that runs, answers, and is
    serving fabricated business data to a customer.
    """


#: What each provider is qualified to report, and what generates its payloads.
#:
#: **One table, and the contract suite is its second reader.** The mapping
#: existed in `tests/contract/test_simulated_adapters.py` as five hand-written
#: fixture classes; a copy here would be a second answer to *"what does Apollo
#: do?"*, and the two would disagree the first time a capability moved
#: (`CLAUDE.md` §2). **This is now the authoritative one** and the suite reads
#: it, so a provider added here is contract-tested by existing.
SIMULATED_PROVIDERS: dict[ProviderName, tuple[ProviderCapability, type[PayloadGenerator]]] = {
    ProviderName.APOLLO: (ProviderCapability.COMPANY_ENRICHMENT, ApolloFixtureGenerator),
    ProviderName.BOMBORA: (ProviderCapability.BEHAVIOURAL_INTENT, BomboraFixtureGenerator),
    ProviderName.BUILTWITH: (ProviderCapability.TECHNOGRAPHICS, BuiltWithFixtureGenerator),
    ProviderName.CORESIGNAL: (ProviderCapability.WORKFORCE, CoreSignalFixtureGenerator),
    ProviderName.CRUNCHBASE: (ProviderCapability.CAPITAL_EVENTS, CrunchbaseFixtureGenerator),
}


def build_provider_registry(
    settings: ProviderSettings, *, simulation: SimulationSettings | None = None
) -> ProviderRegistry:
    """The adapters this process serves, chosen by configuration alone.

    **[ADR-0404](../../../../docs/architecture/adr/0404-platform-composition.md)
    capability 3, and until now no composition root built one** — `TASK-419`
    was sized as *"`WorkerRuntime` gains a `providers` field, built at the
    worker's composition root exactly as the API's registry already is"*, and
    the registry that sentence compared it to is the **AI** provider registry.
    A different thing with a similar name.

    ### A simulated provider outside a local environment is refused, loudly

    **The same invariant §10 states for the AI mock, for the same reason and
    with more at stake.** A deployed service answering from the simulator is
    **indistinguishable from one that is working** — it returns well-formed
    company enrichment, intent and funding events, on a schedule, about real
    companies a customer named. Every score, signal and opportunity built on it
    would be fabricated, and nothing downstream could tell.

    **So this fails at startup rather than serving.** It is the one guard here
    that may never fail open, which is why the environment comes from this
    module's own settings rather than from a parameter a caller could forget.

    ### An unknown provider is a refusal, not a silent omission

    `ProviderName` is the set of providers with a ratified qualification
    record; `SIMULATED_PROVIDERS` is the set with a generator. **They are equal
    today and nothing enforces that they stay equal**, so a name selected with
    no adapter behind it raises here — rather than producing a registry that is
    quietly one provider short, discovered by an account that never enriches.
    """
    if settings.providers and settings.environment != "local":
        raise ProviderRegistrationError(
            f"simulated provider adapters were selected in environment "
            f"'{settings.environment}'. They serve generated company data that is "
            "indistinguishable from a real provider's, so a service running on them "
            "would fabricate every score and signal built on top. No production "
            "provider adapter exists yet; set SIGNORA_PROVIDERS to an empty value to "
            "run without ingestion."
        )

    plan = simulation or SimulationSettings()
    registry = ProviderRegistry()
    for provider in settings.providers:
        pairing = SIMULATED_PROVIDERS.get(provider)
        if pairing is None:
            raise ProviderRegistrationError(
                f"'{provider.value}' has no simulated adapter. It is a recognised "
                "provider with no fixture generator, so nothing can serve it."
            )
        capability, generator = pairing
        registry.register(_simulated(provider, capability, generator(), plan))
    return registry


def _simulated(
    provider: ProviderName,
    capability: ProviderCapability,
    generator: PayloadGenerator,
    settings: SimulationSettings,
) -> ProviderAdapter:
    """One adapter, over a timeline restricted to its own provider's events.

    **Restricted per provider rather than sharing one timeline**, which is a
    live demonstration of Provider Independence rather than an optimisation:
    each adapter is built and served without any other provider being present,
    so nothing can come to depend on a sibling having run.

    `ClockMode.INSTANT` because a composed process consumes as fast as it can;
    `REALTIME` is for watching a scenario unfold, which is a Playground
    concern and not a registry's.
    """
    timeline = build_timeline(
        load_scenario(settings.scenario, settings.scenario_version),
        load(settings.scenario, settings.scenario_version),
        VirtualClock(mode=ClockMode.INSTANT),
        seed=settings.seed,
        providers=[provider.value],
    )
    return SimulatedProviderAdapter(
        provider=provider,
        capabilities=frozenset({capability}),
        generator=generator,
        plan=DeliveryPlan(timeline, page_size=settings.page_size),
        # **The record that makes a run reproducible from itself.** Every field
        # is read from the settings that produced the run rather than restated,
        # so a replay cannot claim a scenario the adapter did not serve.
        replay=ReplayRecord(
            scenario=settings.scenario,
            seed=settings.seed,
            manifest_version=str(settings.scenario_version),
            generator_version=GENERATOR_VERSION,
            clock_mode=ClockMode.INSTANT.value,
            dataset_version=f"{settings.scenario}@{settings.scenario_version}",
        ),
    )


def build_run_sync(
    session: AsyncSession,
    *,
    adapter: ProviderAdapter,
    publisher: EventPublisher,
    reporter: SyncReporter | None = None,
    pacer: Pacer | None = None,
) -> RunProviderSync:
    """**The reporter defaults to the real one.** An observability gap is
    invisible by construction — nothing fails, no test goes red, and the first
    sign is an incident nobody can reconstruct. Making silence the thing you
    have to ask for is the only version that stays true."""
    return RunProviderSync(
        adapter=adapter,
        repository=ProviderSyncRepository(session),
        publisher=publisher,
        session=session,
        reporter=reporter or build_sync_metrics(),
        # **The real pacer by default, like the real reporter.** A provider's
        # declared rate limit is honoured unless a caller deliberately asks
        # not to wait, and the only caller that does is a test.
        pacer=pacer or AsyncioPacer(),
    )
