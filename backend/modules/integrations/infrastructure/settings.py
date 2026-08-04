"""Configuration Integrations owns.

**A typed Settings object owned by the module whose behaviour it governs**
(`CLAUDE.md` §6), constructed only at the composition root. It is deliberately
not in `signora_platform/settings.py`: that file holds the platform's own
configuration, and a substrate that knows every module's configuration surface
has stopped being a substrate.
"""

from __future__ import annotations

from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class ClientCredentialPair(BaseModel):
    """Signora's own registration with one vendor.

    **Not a customer's grant, and never interchangeable with one** (§13). This
    identifies the *application*: the same pair for every workspace, used to
    acquire and to renew, and stored nowhere near a connection.
    """

    client_id: str
    client_secret: str


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

    client_credentials: dict[str, ClientCredentialPair] = Field(
        default_factory=dict,
        description=(
            "Signora's own OAuth registration per catalog slug, used to renew a "
            "grant (RFC 6749 §6). **Empty by default and that is a working "
            "state**: a vendor with nothing configured is one the product "
            "declines to refresh, which is the same refusal the acquisition "
            "tier performs when its own environment holds no client id. "
            "Deliberately not defaulted per vendor — a defaulted client secret "
            "is a known secret that reads as configuration."
        ),
    )
