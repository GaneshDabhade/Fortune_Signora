"""The AI Platform's own configuration.

**Ratified 2026-07-30: configuration is a typed Settings object owned by the
module that owns the behaviour.** This is the AI Platform's; the platform's
own lives in `signora_platform/settings.py`; M9's will be its own again. The
rule was never *"everything goes through that one file"* — that was a file
mistaken for a principle, and following it would have made the frozen
substrate the registry of every module's configuration surface.

Constructed **only at the composition root**, never reached for from domain
or application code, and never read from `os.environ` anywhere else. No
module ever learns where another module's configuration came from.

`SIGNORA_` prefix, matching the platform's, because these are the same
process's environment — one namespace, several owners.
"""

from __future__ import annotations

from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class AISettings(BaseSettings):
    """What the AI Platform needs to reach a model.

    Development is Ollama and production is a hosted commercial model
    (ADR-0028). There is deliberately **no fallback between them**: a
    production service that could quietly reach a local runtime when its
    vendor was unreachable would serve customers from a model nothing
    evaluated.
    """

    model_config = SettingsConfigDict(
        env_prefix="SIGNORA_", env_file=".env", extra="ignore", frozen=True
    )

    #: Which environment this process is. **Read from `SIGNORA_ENVIRONMENT`,
    #: the same variable `signora_platform.Settings` reads** — the prefixes
    #: are identical because these are one process's environment with several
    #: owners, which is what the header above describes.
    #:
    #: **Not a copy of the platform's field, and the distinction matters
    #: under §2.** Neither object stores the other's value; both read one
    #: source. A module reaching into `signora_platform.Settings` for this
    #: would be the cross-module configuration read §6 forbids, and would
    #: touch a frozen substrate (§20a) to do it.
    #:
    #: It exists for exactly one guard — the mock must never be registered
    #: outside a local environment — and a test constructs this object
    #: directly, so that guard can be made to fail without mutating a global.
    environment: str = "local"

    #: Which provider serves the development model. **Defaults to the
    #: deterministic mock**, which is what makes a fresh clone productive
    #: with no local model (`CLAUDE.md` §10). Set to `"ollama"` to select a
    #: local runtime deliberately — *"no implementation may assume Ollama is
    #: installed unless a developer explicitly selects it"*, and before this
    #: field existed the registry assumed it unconditionally.
    #:
    #: **Not a fallback chain.** Exactly one of the two is registered for the
    #: development model, because the registry refuses two adapters claiming
    #: one model and would be right to.
    development_provider: Literal["mock", "ollama"] = "mock"

    #: Where a local Ollama server is, for development and evaluation.
    ollama_base_url: str = "http://localhost:11434"
    #: The model evaluation and local development run against. Pinned, never
    #: a floating alias: a vendor-side update to a tag changes behaviour with
    #: no code change, and the pin is what makes that traceable.
    ollama_model: str = "llama3.1:8b"

    #: Production. Absent in development, and absent is correct — an
    #: adapter is registered only when its credentials exist, so a missing
    #: key produces "no provider serves this model" rather than a call that
    #: fails at the vendor.
    anthropic_api_key: str | None = Field(default=None)
    anthropic_base_url: str = "https://api.anthropic.com"
    anthropic_model: str = "claude-sonnet-4-5"
