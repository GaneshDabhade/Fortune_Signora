"""**One stack per lane, and the arithmetic that makes that true.**

436 change ②, approved 2026-08-05: *"create separate environment for each lane
so that nothing could be shared."*

[B-118](../../../docs/BUGS.md) was four clones running `docker compose` against
one project name, so they shared one PostgreSQL server — **one connection pool,
one lock manager, and one cluster-wide role.** That last one aborted
certification cycle 57 on `ALTER ROLE signora_app NOBYPASSRLS`, and **no
per-database separation could ever have reached it.**

The allocation these tests cover **existed before the defect and nothing read
it**: `compose_project` was derived, printed, and never consumed, while
`docker-compose.yml` hard-coded `name: signora-v2`. So the property under test
is not *"can we compute a port"* — it is **that no two environments can land on
the same one**, which is the only thing standing between four stacks and the
failure they were split up to avoid.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from types import ModuleType

import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]


def _load() -> ModuleType:
    path = REPO_ROOT / "infra" / "environments.py"
    spec = importlib.util.spec_from_file_location("signora_environments", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    # **Registered before execution.** `Environment` is a slots dataclass, and
    # `dataclasses` resolves `__module__` through `sys.modules` while building
    # it — an unregistered module raises during import rather than at use.
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


environments = _load()


class TestNoTwoEnvironmentsCanCollide:
    """**The whole point of an allocation, asserted rather than assumed.**"""

    @pytest.mark.parametrize(
        "port",
        ["web_port", "api_port", "postgres_port", "redis_port",
         "minio_port", "minio_console_port"],
    )
    def test_every_environment_holds_that_port_alone(self, port: str) -> None:
        seen: dict[int, str] = {}
        for environment in environments.ENVIRONMENTS:
            value = getattr(environment, port)
            assert value not in seen, (
                f"{environment.name} and {seen[value]} both bind {port} {value}"
            )
            seen[value] = environment.name

    def test_no_environment_collides_with_another_on_any_port(self) -> None:
        """**Across kinds, not only within one.**

        MinIO's console sits one above its API, so a stride that ever narrowed
        would put one environment's console on the next one's API — and the
        symptom would be an environment answering on a port that is not its own,
        which is the class this change exists to end rather than relocate.
        """
        seen: dict[int, str] = {}
        for environment in environments.ENVIRONMENTS:
            for port in ("web_port", "api_port", "postgres_port",
                         "redis_port", "minio_port", "minio_console_port"):
                value = getattr(environment, port)
                owner = f"{environment.name}.{port}"
                assert value not in seen, f"{owner} collides with {seen[value]}"
                seen[value] = owner

    def test_each_environment_has_its_own_compose_project(self) -> None:
        """**Containers and volumes are scoped by project, so this is the rest.**

        Two containers of the same name in two projects are two containers; in
        one project they are one.
        """
        projects = [e.compose_project for e in environments.ENVIRONMENTS]
        assert len(projects) == len(set(projects))


class TestSlotZeroStillAnswersWhereItAlwaysDid:
    """**A migration nobody has to perform is the only kind that gets performed.**"""

    def test_the_historical_ports_are_unchanged(self) -> None:
        review = environments.BY_NAME["review"]
        assert review.slot == 0
        assert (review.postgres_port, review.redis_port) == (5432, 6379)
        assert (review.minio_port, review.minio_console_port) == (9000, 9001)


class TestTheCloneResolvesItsOwnEnvironment:
    """**A stack per lane is only real if a lane lands on its own by default.**

    A mechanism that must be typed correctly every time is the manual convention
    the directive ruled out, wearing a flag.
    """

    def test_an_explicit_environment_wins(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("SIGNORA_ENVIRONMENT", "lane-b")
        resolved = environments.current()
        assert resolved is not None and resolved.name == "lane-b"

    def test_an_unknown_explicit_environment_resolves_to_nothing(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """**Refuse rather than fall back to a lane that exists.**

        A typo resolving to somebody else's stack is the defect, not the
        recovery.
        """
        monkeypatch.setenv("SIGNORA_ENVIRONMENT", "lane-typo")
        assert environments.current() is None

    def test_a_longer_name_is_not_swallowed_by_a_shorter_prefix(self) -> None:
        """`lane-qe` must not resolve through any shorter environment name.

        The branch match is by prefix, and prefix matching is where this kind of
        table goes wrong quietly.
        """
        names = sorted((e.name for e in environments.ENVIRONMENTS), key=len)
        for short in names:
            for long in names:
                if long != short and long.startswith(short):
                    pytest.fail(f"{short!r} is a prefix of {long!r}; matching is ambiguous")
