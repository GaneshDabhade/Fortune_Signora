"""Provider Simulation Framework.

Produces realistic provider payloads without a provider
(docs/architecture/20-provider-simulation.md).

**This package must never import a module.** It is platform
infrastructure, and the simulator having no privileged downstream
knowledge (principle 2) is enforced by an import-linter contract rather
than by convention — reading a Signal to decide what payload to emit next
would make every scenario pass while proving nothing about the pipeline.
"""

from signora_platform.simulation.clock import ClockMode, VirtualClock
from signora_platform.simulation.dataset import Dataset, DatasetError, content_hash, load
from signora_platform.simulation.delivery import (
    DeliveryMode,
    DeliveryPage,
    DeliveryPlan,
)
from signora_platform.simulation.faults import (
    FaultInjector,
    FaultKind,
    FaultProfile,
    FaultProfileError,
    FaultRule,
    InjectedFault,
)
from signora_platform.simulation.observability import (
    ReplayRecord,
    log_payload_emitted,
    log_run_finished,
    log_run_started,
)
from signora_platform.simulation.safety import (
    PERMITTED_ENVIRONMENTS,
    SimulationForbiddenError,
    SimulationStatus,
    enforce,
    evaluate,
    is_permitted,
)
from signora_platform.simulation.scenario import (
    Scenario,
    ScenarioError,
    ScenarioEvent,
    ScenarioStep,
    build_timeline,
)
from signora_platform.simulation.scenario import load as load_scenario

__all__ = [
    "PERMITTED_ENVIRONMENTS",
    "ClockMode",
    "DeliveryMode",
    "DeliveryPage",
    "DeliveryPlan",
    "FaultInjector",
    "FaultKind",
    "FaultProfile",
    "FaultProfileError",
    "FaultRule",
    "InjectedFault",
    "Dataset",
    "DatasetError",
    "SimulationForbiddenError",
    "SimulationStatus",
    "VirtualClock",
    "content_hash",
    "enforce",
    "evaluate",
    "is_permitted",
    "ReplayRecord",
    "Scenario",
    "ScenarioError",
    "ScenarioEvent",
    "ScenarioStep",
    "build_timeline",
    "load",
    "load_scenario",
    "log_payload_emitted",
    "log_run_finished",
    "log_run_started",
]
