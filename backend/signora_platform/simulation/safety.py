"""Guards preventing the simulator from running where it must not.

**The highest-risk control in M2.0.** A simulator active in production
fabricates customer intelligence — recommendations about companies that
did nothing, based on events that never happened. That is a trust failure,
not a bug, and it is not recoverable by fixing the code afterwards.

Built before any payload generator exists, deliberately: a simulator that
works before its guard does is one that can be run somewhere it should not
during the window between.

Four controls, all test-enforced (docs/architecture/20-provider-simulation.md):

1. Refuses activation in production, absent an explicit and logged override
2. Marks simulated payloads unambiguously in ingestion logs
3. Exposes simulator state in non-production health output
4. Provides the signal an alert fires on

All four fail **closed**: an environment that cannot be determined is
treated as production.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Final

from signora_platform.observability import get_logger

logger = get_logger(__name__)

#: Environments where simulation is permitted without an override. Anything
#: not on this list — including a typo, an empty string, or a new
#: environment nobody thought to add — is treated as production.
PERMITTED_ENVIRONMENTS: Final[frozenset[str]] = frozenset(
    {"local", "test", "ci", "development", "production-local"}
)

PRODUCTION_OVERRIDE_FLAG: Final = "SIGNORA_SIMULATION_ALLOW_IN_PRODUCTION"


class SimulationForbiddenError(RuntimeError):
    """The simulator was activated where it is not permitted."""


@dataclass(frozen=True, slots=True)
class SimulationStatus:
    """Simulator state, for health output and alerting."""

    enabled: bool
    environment: str
    permitted: bool
    override_in_use: bool

    @property
    def should_alert(self) -> bool:
        """True when the simulator is running somewhere it should not be.

        Covers the override case too: an override is a deliberate,
        temporary act, and an operator needs to know it is still in force —
        the dangerous version of this is an override applied during an
        incident and never removed.
        """
        return self.enabled and (not self.permitted or self.override_in_use)


def is_permitted(environment: str) -> bool:
    """Whether simulation may run in this environment.

    Fails closed. An unrecognised value is not an implicit "not
    production" — that reasoning is how a new environment silently gains
    permission it was never granted.
    """
    return environment.strip().lower() in PERMITTED_ENVIRONMENTS


def evaluate(*, enabled: bool, environment: str, override: bool = False) -> SimulationStatus:
    return SimulationStatus(
        enabled=enabled,
        environment=environment,
        permitted=is_permitted(environment),
        override_in_use=override and not is_permitted(environment),
    )


def enforce(*, enabled: bool, environment: str, override: bool = False) -> SimulationStatus:
    """Raise unless simulation is permitted here. Called at startup.

    An override is honoured but **never silent** — it is logged at ERROR
    with the environment named, so the decision appears in the same place
    an operator would look when asking why the data is wrong.
    """
    status = evaluate(enabled=enabled, environment=environment, override=override)

    if not status.enabled:
        return status

    if status.permitted:
        logger.info(
            "provider simulation enabled",
            extra={"environment": environment, "simulated": True},
        )
        return status

    if override:
        logger.error(
            "provider simulation running in a NON-PERMITTED environment via explicit override",
            extra={
                "environment": environment,
                "override_flag": PRODUCTION_OVERRIDE_FLAG,
                "simulated": True,
                "consequence": "ingested intelligence is fabricated",
            },
        )
        return status

    raise SimulationForbiddenError(
        f"Provider simulation is not permitted in environment '{environment}'. "
        f"A simulator active outside {sorted(PERMITTED_ENVIRONMENTS)} fabricates customer "
        f"intelligence. Set {PRODUCTION_OVERRIDE_FLAG}=1 only if that is genuinely intended; "
        "the override is logged at ERROR every start."
    )
