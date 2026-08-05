"""The Provider Platform's own configuration.

**Configuration is a typed `Settings` object owned by the module that owns the
behaviour** (`CLAUDE.md` §6, ratified 2026-07-30). This is the Provider
Platform's; the platform's own lives in `signora_platform/settings.py`; the AI
Platform's is `AISettings`. **The rule was never *"everything goes through that
one file"*** — following that reading would make the frozen substrate the
registry of every module's configuration surface, and `signora_platform/` is
frozen under §20a precisely so it does not become one.

Constructed **only at the composition root**, never reached for from domain or
application code, and never read from `os.environ` anywhere else. **No module
ever learns where another module's configuration came from.**

`SIGNORA_` prefix, matching the platform's and the AI Platform's, because these
are the same process's environment — **one namespace, several owners.**

### What is deliberately not here

**Nothing in this file knows what is behind an adapter.** The first draft held
a scenario name, a seed and a page size, and a Security Invariant refused it —
correctly, and for a better reason than the one that made it fail. Those are
not *provider* configuration; they are one **implementation's** configuration,
and a real vendor adapter would need an API key and a base URL instead. A
settings object holding them is a settings object that knows a simulator
exists, which is the leak `TestPipelineNeutrality` exists to catch.

**They live beside the adapter that reads them**, in
`adapters/simulated/settings.py`. When a production adapter is written it
brings its own, and this file does not change.
"""

from __future__ import annotations

from typing import Annotated

from pydantic import field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict

from modules.provider_platform.domain.provider import ProviderName


class ProviderSettings(BaseSettings):
    """Which providers this process serves, and where it is running.

    ### Two fields, and neither names an implementation

    **There is no adapter-kind switch, and its absence is deliberate.** No
    production provider adapter exists in this repository, so a
    `Literal["simulated", "real"]` field would have exactly one reachable
    value — the decorative class §2 forbids, and a guard that cannot fail.
    **The selector arrives with the first real adapter**, which is the change
    that makes it mean something.

    What this object chooses is *which providers this process serves at all*,
    which is a real choice with an observable consequence: an unregistered
    provider produces *"no adapter registered"* at the registry rather than a
    call nobody can service.
    """

    model_config = SettingsConfigDict(
        env_prefix="SIGNORA_", env_file=".env", extra="ignore", frozen=True
    )

    #: Which environment this process is. **Read from `SIGNORA_ENVIRONMENT`,
    #: the same variable `signora_platform.Settings` and `AISettings` read.**
    #:
    #: **Not a copy of the platform's field.** Neither object stores the
    #: other's value; all three read one source. A module reaching into
    #: `signora_platform.Settings` for it would be the cross-module
    #: configuration read §6 forbids, and would touch a frozen substrate
    #: (§20a) to do it.
    #:
    #: It exists for exactly one guard, which the composition root carries —
    #: and a test constructs this object directly, so that guard can be made to
    #: fail without mutating a global.
    environment: str = "local"

    #: Which providers this process serves. **Every provider with a ratified
    #: qualification record**, because an adapter exists for each one today; a
    #: process that recognises a provider architecturally and cannot serve it
    #: is half-configured.
    #:
    #: Narrow it to exercise one provider in isolation:
    #: `SIGNORA_PROVIDERS=apollo,bombora`.
    providers: Annotated[tuple[ProviderName, ...], NoDecode] = tuple(ProviderName)

    @field_validator("providers", mode="before")
    @classmethod
    def _split(cls, value: object) -> object:
        """`SIGNORA_PROVIDERS=apollo,bombora` — a comma-separated list.

        **`NoDecode` is what makes this validator reachable.** pydantic-settings
        JSON-decodes a complex field *before* any validator runs, so without it
        the documented form above raises `SettingsError` rather than being read
        — and the failure lands at startup, on the one field an operator is
        most likely to set. Found by writing the test first and watching it
        fail on the parse rather than on the value.

        An empty string means *no providers*, which is a legitimate
        configuration — a process that ingests nothing — and is distinct from
        the field being absent, which takes the default.
        """
        if isinstance(value, str):
            return tuple(part.strip() for part in value.split(",") if part.strip())
        return value


__all__ = ["ProviderSettings"]
