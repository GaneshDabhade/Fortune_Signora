"""Whether the logs say where an ingested payload actually came from.

**[20-provider-simulation.md](../../../docs/architecture/20-provider-simulation.md)
states this three times**, and the strongest statement is not about
observability at all:

> *"Every ingestion log line marks the payload as simulated, names the dataset
> version, scenario, and seed. **This is a safety control as much as an
> observability one: if simulated data ever reaches a place it should not, the
> logs must say so unambiguously and immediately.**"*

`ProviderResponse.simulated` and `ProviderResponse.replay` have carried that
information since M2.0, `ReplayContext.as_log_fields()` was written to emit it,
and **nothing had ever called it.** The framework's own guard refuses to
*activate* outside development; this is the other half — proving from the record
what a given row was built from.
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from uuid import UUID, uuid4

import pytest

from modules.provider_platform.application.ports import NoPacer, NoSyncReporter
from modules.provider_platform.application.run_sync import (
    RunProviderSync,
    RunProviderSyncInput,
)
from modules.provider_platform.domain.provider import (
    ProviderCapability,
    ProviderDescriptor,
    ProviderName,
    ProviderRecord,
    ProviderRequest,
    ProviderResponse,
    ReplayContext,
)
from tests.provider_platform.test_pacing import (
    FakeRepository,
    NullPublisher,
    NullSession,
)

WORKSPACE = UUID("11111111-1111-4111-8111-111111111111")

REPLAY = ReplayContext(
    scenario="baseline",
    seed=1,
    manifest_version="1",
    generator_version="0.1.0-fixture",
    clock_mode="instant",
    dataset_version="baseline@1",
)


class OnePageAdapter:
    def __init__(self, *, simulated: bool, replay: ReplayContext | None) -> None:
        self._simulated = simulated
        self._replay = replay

    def describe(self) -> ProviderDescriptor:
        return ProviderDescriptor(
            provider=ProviderName.APOLLO,
            capabilities=frozenset({ProviderCapability.COMPANY_ENRICHMENT}),
            simulated=self._simulated,
        )

    async def fetch(self, request: ProviderRequest) -> ProviderResponse:
        return ProviderResponse(
            provider=ProviderName.APOLLO,
            records=(
                ProviderRecord(
                    provider=ProviderName.APOLLO,
                    capability=ProviderCapability.COMPANY_ENRICHMENT,
                    external_id="1",
                    occurred_at=datetime.now(UTC),
                    payload={"name": "Acme"},
                ),
            ),
            simulated=self._simulated,
            replay=self._replay,
        )


async def _run(adapter: OnePageAdapter) -> None:
    await RunProviderSync(
        adapter=adapter,
        repository=FakeRepository(),  # type: ignore[arg-type]
        publisher=NullPublisher(),  # type: ignore[arg-type]
        session=NullSession(),  # type: ignore[arg-type]
        pacer=NoPacer(),
        reporter=NoSyncReporter(),
    ).execute(
        RunProviderSyncInput(
            workspace_id=WORKSPACE,
            capability=ProviderCapability.COMPANY_ENRICHMENT,
            subject="acme-corp",
        ),
        correlation_id=uuid4(),
    )


def _ingestion_line(caplog: pytest.LogCaptureFixture) -> logging.LogRecord:
    lines = [r for r in caplog.records if r.message == "provider page ingested"]
    assert len(lines) == 1, "one line per ingested page, and exactly one"
    return lines[0]


class TestSimulatedPayloadsAreMarked:
    async def test_a_simulated_page_says_so(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        """**The safety control.** If simulated data reaches somewhere it
        should not, the logs must say so immediately — not after somebody
        reconstructs which adapter was configured that day."""
        with caplog.at_level(logging.INFO):
            await _run(OnePageAdapter(simulated=True, replay=REPLAY))

        assert _ingestion_line(caplog).simulated is True  # type: ignore[attr-defined]

    async def test_it_carries_every_replay_field(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        """*"When output changes, what changed?"* — scenario, seed, manifest,
        generator, clock and dataset separate a model change from a prompt
        change from a quietly-updated payload shape. **Separating them after
        the fact is impossible**, which is why they are recorded at ingestion
        rather than derived later."""
        with caplog.at_level(logging.INFO):
            await _run(OnePageAdapter(simulated=True, replay=REPLAY))

        line = _ingestion_line(caplog)
        for field, expected in REPLAY.as_log_fields().items():
            assert getattr(line, field) == expected, field

    async def test_a_real_page_is_marked_not_simulated_rather_than_unmarked(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        """**A field that appears only when true makes its absence
        ambiguous.** *Not simulated* and *logged before this line existed* look
        identical, and an operator filtering for real data would be trusting a
        silence."""
        with caplog.at_level(logging.INFO):
            await _run(OnePageAdapter(simulated=False, replay=None))

        line = _ingestion_line(caplog)
        assert line.simulated is False  # type: ignore[attr-defined]
        assert not hasattr(line, "sim_scenario")

    async def test_the_payload_body_is_never_marked(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Marking the payload would change its shape and defeat the
        identical-contract rule that makes simulation worth having — a
        simulated response must be indistinguishable from a real one to
        everything downstream."""
        adapter = OnePageAdapter(simulated=True, replay=REPLAY)

        response = await adapter.fetch(
            ProviderRequest(
                capability=ProviderCapability.COMPANY_ENRICHMENT,
                workspace_id=WORKSPACE,
                correlation_id=uuid4(),
                subject="acme-corp",
            )
        )

        assert "simulated" not in response.records[0].payload
        assert "replay" not in response.records[0].payload


class TestTheLineIsTraceable:
    async def test_it_names_the_workspace_and_the_correlation(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        # §16: every line emitted from request or event processing carries
        # both, or a pipeline run cannot be followed end to end.
        with caplog.at_level(logging.INFO):
            await _run(OnePageAdapter(simulated=False, replay=None))

        line = _ingestion_line(caplog)
        assert line.workspace_id == str(WORKSPACE)  # type: ignore[attr-defined]
        assert line.correlation_id  # type: ignore[attr-defined]

    async def test_it_names_the_sync_and_how_much_arrived(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        with caplog.at_level(logging.INFO):
            await _run(OnePageAdapter(simulated=False, replay=None))

        line = _ingestion_line(caplog)
        assert line.records == 1  # type: ignore[attr-defined]
        assert line.provider == ProviderName.APOLLO.value  # type: ignore[attr-defined]
