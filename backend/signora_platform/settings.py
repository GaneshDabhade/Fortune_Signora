"""Process-wide configuration, sourced from environment variables.

This is the one place environment configuration is read from. Modules never
call ``os.environ`` directly — they receive configuration through dependency
injection at the composition boundary (apps/api, apps/worker), consistent
with CLAUDE.md's dependency-injection standard.
"""

from functools import lru_cache

from pydantic import PostgresDsn, RedisDsn
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="SIGNORA_", env_file=".env", extra="ignore")

    environment: str = "local"

    database_url: PostgresDsn
    database_pool_size: int = 10
    database_pool_max_overflow: int = 5

    redis_url: RedisDsn = RedisDsn("redis://localhost:6379/0")

    # --- JWT boundary (ADR-0026) ---
    #
    # The PUBLIC half of the Better Auth signing key, PEM-encoded. This tier
    # verifies tokens and must never be able to mint one, so a private key is
    # never configured here — not in production, not locally, not in tests
    # (tests generate an ephemeral key pair in-process instead).
    # See docs/architecture/18-authentication.md.
    jwt_public_key: str
    jwt_issuer: str
    jwt_audience: str

    # --- Observability (ADR-0018) ---
    #
    # All optional: absent configuration disables the exporter rather than
    # failing startup. A missing telemetry endpoint must never prevent the
    # service from serving traffic.
    service_name: str = "signora"
    log_level: str = "INFO"
    otlp_endpoint: str | None = None
    sentry_dsn: str | None = None
    release_version: str = "dev"


@lru_cache
def get_settings() -> Settings:
    """Cached settings singleton — safe because settings are process-wide and
    do not change after process start; per-request/per-tenant values are
    never read from here."""
    return Settings()
