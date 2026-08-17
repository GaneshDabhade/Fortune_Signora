"""Process-wide configuration, sourced from environment variables.

This is the one place environment configuration is read from. Modules never
call ``os.environ`` directly — they receive configuration through dependency
injection at the composition boundary (apps/api, apps/worker), consistent
with CLAUDE.md's dependency-injection standard.
"""

from functools import lru_cache

from pydantic import PostgresDsn, RedisDsn
from pydantic_settings import BaseSettings, SettingsConfigDict

from signora_platform.rate_limit_settings import RateLimitSettings
from signora_platform.environment import SignoraEnvironment


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="SIGNORA_", env_file=".env", extra="ignore")

    #: **Typed rather than a string** — [ADR-0412](../../docs/architecture/adr/0412-environment-and-secret-safe-logging.md)
    #: §2: *"an unrecognised environment value must be unrepresentable, never
    #: silently treated as development."* ⛔ **A `str` here is exactly the shape
    #: that treats an unknown value as *"not production"* by accident**, and
    #: Pydantic now refuses one at construction.
    #:
    #: ⚡ **Required, with no default** — ADR-0412 §2: *"a missing value FAILS.
    #: It does not default."* 📁 **The precedent is already in this file**:
    #: `redis_url` refuses rather than defaulting to index 0, and its comment
    #: records why — *"it used to default in code, which made the allocation
    #: table advisory."*
    #:
    #: ⚠️ **A default here was doing the same thing to the ADR.** 🔴 **Measured:
    #: `Settings(...)` is constructed in 36 places and NOT ONE passed
    #: `environment`** — so every one of them, including the entire test
    #: suite, silently believed it was `local`. **The right answer by accident,
    #: which is the shape ADR-0412 §5 names**: *"the gap is invisible precisely
    #: because nothing fails."*
    environment: SignoraEnvironment

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

    #: ## Inbound rate limiting — [ADR-0408](../../docs/architecture/adr/0408-inbound-rate-limiting.md) §4
    #:
    #: **The platform's own configuration, and it belongs here for that reason
    #: alone.** ⛔ [§6](../../CLAUDE.md) forbids putting a *module's* settings in
    #: this file *"because it is the file that already exists"* — **the limiter
    #: is not a module's.** It runs before routing, in front of every module,
    #: and no module reads it or configures it.
    #:
    #: ⚡ **Nested rather than four flat fields**, so `SIGNORA_RATE_LIMIT__MAX_REQUESTS`
    #: reads as one subject and a future field lands in the object that owns it
    #: rather than at the top of this class.
    #:
    #: ⚠️ **The defaults are conservative rather than measured** — ADR-0408 §15
    #: refuses to name a budget: *"set from measured traffic, and until traffic
    #: exists a conservative default that is changed without a code change."*
    rate_limit: RateLimitSettings = RateLimitSettings()

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
