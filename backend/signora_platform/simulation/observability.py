"""Simulation observability — marking payloads and recording replay.

Two jobs, and the first is as much a **safety control** as an
observability one: if simulated data ever reaches somewhere it should not,
the logs must say so unambiguously and immediately, not after someone
reconstructs the run.

The second is what makes AI evaluation possible at all. With scenario,
seed, manifest version, generator version, clock, and dataset recorded
against every run, a change in downstream output is attributable to
exactly one of them. Without it, a quality shift is an anecdote.
"""

from __future__ import annotations

from dataclasses import dataclass

from signora_platform.observability import get_logger

logger = get_logger(__name__)


@dataclass(frozen=True, slots=True)
class ReplayRecord:
    """Everything needed to reproduce a run from its record alone.

    ``generator_version`` earns its place: without it, a change in
    downstream output could come from a model change, a prompt change, a
    dataset change, *or* a quietly-updated payload shape — and separating
    them after the fact is impossible.
    """

    scenario: str
    seed: int
    manifest_version: str
    generator_version: str
    clock_mode: str
    dataset_version: str

    def as_log_fields(self) -> dict[str, str | int]:
        return {
            "simulated": "true",
            "sim_scenario": self.scenario,
            "sim_seed": self.seed,
            "sim_manifest_version": self.manifest_version,
            "sim_generator_version": self.generator_version,
            "sim_clock_mode": self.clock_mode,
            "sim_dataset_version": self.dataset_version,
        }


def log_run_started(record: ReplayRecord, *, event_count: int) -> None:
    logger.info("simulation run started", extra={**record.as_log_fields(), "events": event_count})


def log_payload_emitted(record: ReplayRecord, *, provider: str, event_ref: str) -> None:
    """Marks every emitted payload.

    Logged rather than embedded in the payload: marking the payload body
    would change its shape and defeat the identical-contract rule — the
    very thing this marking exists to make safe.
    """
    logger.info(
        "simulated provider payload emitted",
        extra={**record.as_log_fields(), "provider": provider, "sim_event_ref": event_ref},
    )


def log_run_finished(record: ReplayRecord, *, emitted: int, faults: int) -> None:
    logger.info(
        "simulation run finished",
        extra={**record.as_log_fields(), "emitted": emitted, "faults_injected": faults},
    )
