"""Unit tests for worker pool resolution.

Pool configuration is deployment-shaping: a wrong pool means a queue nobody
drains, which presents as "events are stuck" long after the misconfiguration.
"""

import pytest

from apps.worker.pools import (
    AI_RESEARCH,
    DEFAULT,
    DEFAULT_POOL_ENV_VAR,
    INGESTION,
    POOLS,
    UnknownPoolError,
    resolve_pool,
)


class TestResolvePool:
    def test_resolves_an_explicit_pool_name(self) -> None:
        assert resolve_pool("ingestion") is INGESTION

    def test_resolves_from_the_environment(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv(DEFAULT_POOL_ENV_VAR, "ai_research")

        assert resolve_pool() is AI_RESEARCH

    def test_falls_back_to_default_when_unset(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv(DEFAULT_POOL_ENV_VAR, raising=False)

        assert resolve_pool() is DEFAULT

    def test_unknown_pool_fails_loudly_at_startup(self) -> None:
        """Silently falling back would leave the intended queue undrained,
        which is very hard to notice."""
        with pytest.raises(UnknownPoolError) as exc_info:
            resolve_pool("typo-pool")

        assert "typo-pool" in str(exc_info.value)
        assert "ingestion" in str(exc_info.value), "error should list valid pools"


class TestPoolConfiguration:
    def test_every_pool_name_matches_its_registry_key(self) -> None:
        for key, pool in POOLS.items():
            assert key == pool.name

    def test_ai_research_has_the_lowest_concurrency_and_longest_timeout(self) -> None:
        """The whole point of per-stage pools: agentic research must not run
        at the same concurrency as fast ingestion, or it starves the budget
        and the rate limits (docs/architecture/12-scalability.md)."""
        assert AI_RESEARCH.max_jobs == min(p.max_jobs for p in POOLS.values())
        assert AI_RESEARCH.job_timeout_seconds == max(p.job_timeout_seconds for p in POOLS.values())

    def test_every_pool_has_positive_limits(self) -> None:
        for pool in POOLS.values():
            assert pool.max_jobs > 0
            assert pool.job_timeout_seconds > 0
            assert pool.description
