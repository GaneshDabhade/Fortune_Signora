"""Applies the ``security_invariant`` marker to every test in this package.

Done here rather than per-module so that adding a file cannot silently
produce tests that fall outside ``-m security_invariant`` — the suite would
still be green while no longer running what it claims to run.
"""

from pathlib import Path

import pytest
from sqlalchemy.ext.asyncio import AsyncEngine

_PACKAGE_ROOT = Path(__file__).parent


def pytest_collection_modifyitems(items: list[pytest.Item]) -> None:
    """``pytest_collection_modifyitems`` is a session-wide hook: it receives
    every collected item, not only those under this directory. Without the
    path filter this marks the entire test suite, and
    ``-m security_invariant`` then runs everything while appearing to run a
    focused set — green, and meaningless.
    """
    for item in items:
        if _PACKAGE_ROOT in Path(str(item.path)).parents:
            item.add_marker(pytest.mark.security_invariant)


@pytest.fixture
async def app_role_name(app_engine: AsyncEngine) -> str:
    """The role the application actually connects as, read from the live
    connection rather than assumed, so these tests cannot pass by asserting
    facts about a role nothing uses."""
    from sqlalchemy import text

    async with app_engine.connect() as conn:
        return str((await conn.execute(text("SELECT current_user"))).scalar_one())
