"""Which provider adapters a process serves, and what it refuses to serve.

**ADR-0404 capability 3.** No composition root built a provider registry before
this, which is why `TASK-419` could size itself as *"the worker gains a field
built exactly as the API's registry already is"* — the registry that sentence
compared it to is the **AI** provider registry, a different thing with a
similar name.

**The tests that matter here are the refusals.** Registering five adapters is
arithmetic; refusing to register a simulated one in production is the whole
reason this function is allowed to exist.
"""

from __future__ import annotations

from uuid import uuid4

import pytest

from modules.provider_platform.domain.provider import (
    ProviderCapability,
    ProviderName,
    ProviderPermanentError,
    ProviderRequest,
)
from modules.provider_platform.infrastructure.adapters.simulated.settings import (
    SimulationSettings,
)
from modules.provider_platform.infrastructure.composition import (
    SIMULATED_PROVIDERS,
    ProviderRegistrationError,
    build_provider_registry,
)
from modules.provider_platform.infrastructure.settings import ProviderSettings


class TestTheRegistryIsBuiltFromConfigurationAlone:
    def test_every_recognised_provider_is_served_by_default(self) -> None:
        """**A fresh clone ingests.** A process that recognises a provider
        architecturally and cannot serve it is half-configured, and every
        provider in `ProviderName` has a generator today."""
        registry = build_provider_registry(ProviderSettings())

        assert set(registry.adapters) == set(ProviderName)

    def test_a_narrowed_selection_serves_only_what_it_names(self) -> None:
        registry = build_provider_registry(
            ProviderSettings(providers=(ProviderName.APOLLO, ProviderName.BOMBORA))
        )

        assert set(registry.adapters) == {ProviderName.APOLLO, ProviderName.BOMBORA}

    def test_selecting_nothing_is_a_configuration_rather_than_an_error(self) -> None:
        """A process that ingests from nobody is legitimate — and it is the
        only configuration that runs outside a local environment today."""
        registry = build_provider_registry(ProviderSettings(providers=()))

        assert registry.adapters == {}

    def test_an_unregistered_provider_is_refused_by_the_registry(self) -> None:
        """The consequence of narrowing, stated where a caller meets it: a
        clear composition error rather than a call nobody can service."""
        registry = build_provider_registry(ProviderSettings(providers=(ProviderName.APOLLO,)))

        with pytest.raises(ProviderPermanentError):
            registry.get(ProviderName.BOMBORA)

    def test_each_adapter_declares_the_capability_its_provider_is_qualified_for(
        self,
    ) -> None:
        registry = build_provider_registry(ProviderSettings())

        for provider, (capability, _) in SIMULATED_PROVIDERS.items():
            assert registry.adapters[provider].describe().capabilities == frozenset({capability})

    def test_capability_lookup_answers_from_what_was_registered(self) -> None:
        registry = build_provider_registry(ProviderSettings())

        assert registry.supporting(ProviderCapability.BEHAVIOURAL_INTENT) == (ProviderName.BOMBORA,)


class TestASimulatedProviderNeverReachesADeployedEnvironment:
    """**The guard this function exists to carry**, and the one that may never
    fail open.

    §10 states the invariant for the AI mock; the stakes are higher here. A
    deployed service answering from the simulator returns well-formed company
    enrichment, intent and funding events, about real companies a customer
    named — **indistinguishable from one that is working**, with every score and
    signal built on top fabricated and nothing downstream able to tell.
    """

    @pytest.mark.parametrize("environment", ["production", "staging", "demo"])
    def test_it_refuses_outside_a_local_environment(self, environment: str) -> None:
        with pytest.raises(ProviderRegistrationError) as refusal:
            build_provider_registry(ProviderSettings(environment=environment))

        assert environment in str(refusal.value)

    def test_the_refusal_says_what_is_wrong_and_what_to_do(self) -> None:
        """A composition error a reader can act on without reading this file."""
        with pytest.raises(ProviderRegistrationError) as refusal:
            build_provider_registry(ProviderSettings(environment="production"))

        message = str(refusal.value)
        assert "fabricate" in message
        assert "SIGNORA_PROVIDERS" in message

    def test_ingesting_from_nobody_is_permitted_anywhere(self) -> None:
        """**The guard is on registering a simulator, not on the environment.**
        A deployed process with no providers selected has nothing to fabricate,
        so refusing it would be the guard exceeding its own reason."""
        registry = build_provider_registry(ProviderSettings(environment="production", providers=()))

        assert registry.adapters == {}


class TestSettingsAreReadFromTheEnvironmentAndNowhereElse:
    def test_providers_are_read_as_a_comma_separated_list(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """**The documented form.** Pydantic parses a tuple field from the
        environment as JSON, so without the validator `SIGNORA_PROVIDERS`
        raises a parse error rather than being read — and the failure would be
        at startup, on the one field an operator is most likely to set."""
        monkeypatch.setenv("SIGNORA_PROVIDERS", "apollo, bombora")

        assert ProviderSettings().providers == (ProviderName.APOLLO, ProviderName.BOMBORA)

    def test_an_empty_value_selects_no_providers(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Distinct from the variable being absent, which takes the default.
        The refusal message tells an operator to do exactly this."""
        monkeypatch.setenv("SIGNORA_PROVIDERS", "")

        assert ProviderSettings().providers == ()

    def test_an_unrecognised_provider_is_refused_when_the_settings_are_built(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Not at the registry — a name that is not a `ProviderName` cannot
        reach it, because the type refuses first."""
        monkeypatch.setenv("SIGNORA_PROVIDERS", "acme")

        with pytest.raises(ValueError):
            ProviderSettings()

    def test_the_environment_is_read_from_the_platform_s_own_variable(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """**One source, several owners.** This module does not store the
        platform's value or reach into `signora_platform.Settings` for it —
        both read `SIGNORA_ENVIRONMENT`, which is what keeps a frozen substrate
        out of a module's configuration path (§6, §20a)."""
        monkeypatch.setenv("SIGNORA_ENVIRONMENT", "production")

        assert ProviderSettings().environment == "production"

    def test_the_settings_cannot_be_mutated_after_construction(self) -> None:
        """Frozen, like every other Settings object here. Configuration that
        changes under a running process is a hidden input (§2)."""
        settings = ProviderSettings()

        with pytest.raises(ValueError):
            settings.environment = "production"  # type: ignore[misc]


class TestARunCanBeReplayedFromItsOwnRecord:
    async def test_the_response_carries_the_settings_that_produced_it(self) -> None:
        """**Read from the settings rather than restated**, so a replay cannot
        claim a scenario the adapter did not serve.

        Asserted on a real `fetch` rather than on the settings object, because
        the settings agreeing with themselves proves nothing — the question is
        whether the provenance a consumer *receives* describes the run that
        produced it.
        """
        registry = build_provider_registry(
            ProviderSettings(),
            simulation=SimulationSettings(scenario="baseline", scenario_version=1, seed=7),
        )

        response = await registry.get(ProviderName.APOLLO).fetch(
            ProviderRequest(
                capability=ProviderCapability.COMPANY_ENRICHMENT,
                workspace_id=uuid4(),
                correlation_id=uuid4(),
                subject="Northwind",
            )
        )

        assert response.simulated is True
        assert response.replay is not None
        assert response.replay.scenario == "baseline"
        assert response.replay.seed == 7
        assert response.replay.dataset_version == "baseline@1"

    async def test_a_different_seed_is_visible_in_the_provenance(self) -> None:
        """The seed is what makes a run reproducible, so a run recording the
        wrong one is worse than one recording none."""
        registry = build_provider_registry(
            ProviderSettings(), simulation=SimulationSettings(seed=99)
        )

        response = await registry.get(ProviderName.APOLLO).fetch(
            ProviderRequest(
                capability=ProviderCapability.COMPANY_ENRICHMENT,
                workspace_id=uuid4(),
                correlation_id=uuid4(),
                subject="Northwind",
            )
        )

        assert response.replay is not None
        assert response.replay.seed == 99


class TestOneImplementationSConfigurationLivesWithIt:
    """**A Security Invariant refused the first draft of this slice**, and it
    was right for a better reason than the one that made it fail.

    `scenario`, `seed` and `page_size` were fields on `ProviderSettings`.
    `TestPipelineNeutrality::test_only_the_composition_root_knows_a_simulator_exists`
    named the file. They are not *provider* configuration — a real vendor
    adapter would need an API key and a base URL and would have no use for a
    seed — so they belong with the implementation that reads them (§6).
    """

    def test_the_provider_settings_name_no_implementation(self) -> None:
        """The property, asserted rather than left to the invariant's regex:
        nothing an operator sets here says what is behind an adapter."""
        assert set(ProviderSettings.model_fields) == {"environment", "providers"}

    def test_a_page_size_below_one_is_refused(self) -> None:
        """A page that carries nothing is not a smaller page; it is a
        pagination loop that never advances."""
        with pytest.raises(ValueError):
            SimulationSettings(page_size=0)

    def test_it_reads_its_own_prefix(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """`SIGNORA_SIMULATION_SEED`, not `SIGNORA_SEED`. A bare `SEED` in a
        shared namespace is a name three owners could each believe is theirs."""
        monkeypatch.setenv("SIGNORA_SIMULATION_SEED", "42")

        assert SimulationSettings().seed == 42

    def test_the_defaults_reproduce_the_scenario_the_suite_runs(self) -> None:
        """`baseline@1`, seed 1 — the same run the contract suite exercises, so
        a developer's process and the suite are describing one thing."""
        settings = SimulationSettings()

        assert (settings.scenario, settings.scenario_version, settings.seed) == (
            "baseline",
            1,
            1,
        )
