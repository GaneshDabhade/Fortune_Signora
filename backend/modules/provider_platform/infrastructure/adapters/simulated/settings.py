"""What the simulated adapters serve, and how.

**This file exists because a Security Invariant refused the alternative.**
`scenario`, `seed` and `page_size` were fields on `ProviderSettings` in the
first draft of TASK-436, and `TestPipelineNeutrality` named it: *"only the
composition root knows a simulator exists"*.

**The refusal was right for a better reason than the one that made it fail.**
Those fields are not *provider* configuration — a real vendor adapter would
need an API key and a base URL and would have no use for a seed. They are one
**implementation's** configuration, and §6 puts a module's configuration with
the behaviour it governs. The same rule one level down: **the adapter that
reads these owns them.**

So `ProviderSettings` chooses *which providers exist*, and this chooses *what
the simulated ones serve*. When a production adapter is written it brings its
own settings object beside itself, and neither of the other two changes.
"""

from __future__ import annotations

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class SimulationSettings(BaseSettings):
    """The scenario a simulated adapter replays, and the shape of its pages."""

    model_config = SettingsConfigDict(
        env_prefix="SIGNORA_SIMULATION_", env_file=".env", extra="ignore", frozen=True
    )

    #: The scenario the adapters serve, and the seed that makes it
    #: reproducible. **Pinned rather than floating**: a run that cannot be
    #: replayed from its own record is not evidence of anything, which is what
    #: `ReplayRecord` exists to prevent.
    scenario: str = "baseline"
    scenario_version: int = 1
    seed: int = 1

    #: How many records a page carries. **The page boundary is what rate
    #: limiting and backpressure see**, so it is configuration rather than a
    #: constant — a one-record page is how the contract suite exercises
    #: pagination.
    page_size: int = Field(default=100, ge=1)


__all__ = ["SimulationSettings"]
