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

    # The outbox relay connects under its own identity (`signora_relay`),
    # which is the only runtime role permitted to READ platform
    # infrastructure tables. The application role may publish into the
    # outbox but never read it back — those tables span every workspace and
    # deliberately carry no RLS (migration 0006,
    # docs/architecture/11-tenancy.md).
    #
    # Optional so that a single-role local setup still starts; the relay
    # falls back to `database_url` and logs that it is doing so. In a
    # deployed environment it is always set, and the Security Invariants
    # assert the two roles are distinct.
    relay_database_url: PostgresDsn | None = None

    # **No default, because a queue default is worse than a database default.**
    #
    # This was `redis://localhost:6379/0` — logical index 0 — while
    # `docs/RUNNING.md` allocates an index per environment and states that no
    # lane shares one. **The allocation table existed and the code did not
    # require anybody to use it**, so any environment that had not set the
    # variable joined index 0 with every other.
    #
    # A shared database corrupts data; **a shared queue executes it.** Redis
    # carries the ARQ job queue and the outbox relay, so two environments on
    # one index means one environment's workers consume the other's jobs — and
    # the resulting failures look random, which makes them the hardest kind to
    # investigate.
    #
    # **Optional here, required where it connects** (`require_redis_url()`).
    # The same asymmetry as the auth tier's ([B-104](../../docs/BUGS.md)): a
    # test that constructs `Settings` to check an unrelated field should not
    # have to supply a queue it never opens.
    redis_url: RedisDsn | None = None

    def require_redis_url(self) -> RedisDsn:
        """The queue this environment owns. **Refuses rather than guessing.**

        Called by the worker and the relay — the only two things that connect.
        """
        if self.redis_url is None:
            raise ValueError(
                "SIGNORA_REDIS_URL is required and is not set. It has no default: "
                "index 0 is another environment's queue, and sharing one means this "
                "process would consume that environment's jobs. See docs/RUNNING.md "
                "for the index allocated to yours."
            )
        return self.redis_url

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
