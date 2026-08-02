"""Configuration Integrations owns.

**A typed Settings object owned by the module whose behaviour it governs**
(`CLAUDE.md` §6), constructed only at the composition root. It is deliberately
not in `signora_platform/settings.py`: that file holds the platform's own
configuration, and a substrate that knows every module's configuration surface
has stopped being a substrate.
"""

from __future__ import annotations

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class IntegrationSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="SIGNORA_INTEGRATIONS_", extra="ignore")

    secret_key: str = Field(
        description=(
            "Fernet key encrypting integration credentials at rest. Injected as "
            "configuration and never defaulted — a default here would ship a "
            "known key, which is worse than no encryption because it reads as "
            "protection."
        )
    )
