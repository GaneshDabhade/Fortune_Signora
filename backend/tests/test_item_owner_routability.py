"""A coordination item's owner is routable when it names a MODULE, not a lane.

`state-check` asked *"does this `Owner` cell name somebody?"* and answered it
with `re.compile(r"Lane [ACD]|QE|product owner|design authority")` — **a literal
lane name inside the cell.** That is the one thing
[C-213](../../docs/LANE_COORDINATION.md) forbids putting there, and §20e says so
directly: *"a coordination item, backlog row or defect names its **module**; the
assignee is joined at render time"*, and *"no document restates an assignee."*

So `C-289` and `C-292`, both written in exactly the required form —
``| **Owner** | **`knowledge_graph`'s current assignee** — joined from
`modules.toml`, not named here (C-213) |`` — were reported as having no owner.

⛔ **The dangerous half is the remediation, which is why this is 🟡 and not 🟢.**
Satisfying the old check meant writing `Lane A` into the cell. **The check would
have gone green and the register would have been one edit further from the rule
it exists to protect** — the edit that blocked `TASK-205` for two days.

**Found by Lane C, who nearly made that edit and filed [B-434](../../docs/BUGS.md)
instead.**

Every case below is fixed text, never the live register. Asserting that today's
`LANE_COORDINATION.md` reports nothing would pass identically with the whole
check deleted — the Decorative Logic `CLAUDE.md` §2 names. **The cases that
distinguish a correct implementation from a permissive one are written out here,
and half of them must FIRE.**
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from types import ModuleType

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]

#: A registry with one real module and no others, so a case naming any other
#: module is genuinely unresolvable rather than accidentally absent.
REGISTRY = """
[meta]
generated = "fixture"

[knowledge_graph]
current_owner = "Lane A"

[signal_engine]
current_owner = "Lane A"

[orphaned_module]
description = "declared, but nobody is assigned — an owner cannot be joined"
"""


def _load_state_check(root: Path) -> ModuleType:
    path = REPO_ROOT / "infra" / "state-check.py"
    spec = importlib.util.spec_from_file_location("state_check_under_test", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules["state_check_under_test"] = module
    spec.loader.exec_module(module)
    module.REPO_ROOT = root
    module.MODULES_TOML = root / "docs" / "coordination" / "modules.toml"
    return module


@pytest.fixture
def check(tmp_path: Path) -> ModuleType:
    (tmp_path / "docs" / "coordination").mkdir(parents=True)
    (tmp_path / "docs" / "coordination" / "modules.toml").write_text(REGISTRY)
    return _load_state_check(tmp_path)


def _findings(check: ModuleType, root: Path, owner: str | None) -> list[str]:
    rows = ["## C-999 · a fixture", "", "| | |", "|---|---|"]
    if owner is not None:
        rows.append(owner)
    rows.append("| **Status** | 🟡 `OPEN` |")
    (root / "docs" / "LANE_COORDINATION.md").write_text("\n".join(rows) + "\n")
    return check._item_owner_findings()


ROUTABLE = [
    pytest.param(
        "| **Owner** | **`knowledge_graph`'s current assignee** — joined from "
        "[`modules.toml`](coordination/modules.toml), ⛔ **not named here** ([C-213](#c-213)) |",
        id="the-C-289-form-a-module-with-an-assignee",
    ),
    pytest.param(
        "| **Owner** | **`signal_engine`'s current assignee** |",
        id="a-module-named-plainly",
    ),
    pytest.param(
        "| **Owner** | **the product owner** |",
        id="an-actor-who-owns-no-module-still-routes",
    ),
    pytest.param(
        "| **Owner** | **Lane C** |",
        id="a-lane-named-directly-is-still-accepted",
    ),
]

NOT_ROUTABLE = [
    pytest.param(
        "| **Owner** | **`ledger_engine`'s current assignee** |",
        id="a-module-the-registry-has-never-heard-of",
    ),
    pytest.param(
        "| **Owner** | **`orphaned_module`'s current assignee** |",
        id="a-module-declared-with-no-current-owner-cannot-be-joined",
    ),
    pytest.param(
        "| **Owner** | **the usual owner**, as before |",
        id="prose-naming-neither-an-actor-nor-a-module",
    ),
    pytest.param(
        "| **Owner** | **[`modules.toml`](coordination/modules.toml)** |",
        id="a-backticked-token-that-is-not-a-module-must-not-satisfy-it",
    ),
    pytest.param(
        None,
        id="no-Owner-cell-at-all",
    ),
]


@pytest.mark.parametrize("owner", ROUTABLE)
def test_a_routable_owner_is_not_reported(
    check: ModuleType, tmp_path: Path, owner: str
) -> None:
    assert _findings(check, tmp_path, owner) == []


@pytest.mark.parametrize("owner", NOT_ROUTABLE)
def test_an_unroutable_owner_is_reported(
    check: ModuleType, tmp_path: Path, owner: str | None
) -> None:
    """**Half the suite must FIRE, or the check is documentation.**

    ⛔ The last case is the one a wider regex would have let through. Admitting
    any lowercase backticked word would accept ``| **Owner** | `modules.toml` |``
    as an owner — which is why B-434's fix is a **join** through the registry and
    never a looser pattern.
    """
    assert _findings(check, tmp_path, owner) != []


def test_lane_b_is_reported_even_though_it_matches_the_actor_pattern(
    check: ModuleType, tmp_path: Path
) -> None:
    """D-165 closed Lane B, and an item assigned to a lane that cannot answer
    *looks answered* — worse than one visibly unowned (§20e)."""
    found = _findings(check, tmp_path, "| **Owner** | **Lane B** |")
    assert found and "Lane B" in found[0]


def test_a_finished_item_needs_no_owner(check: ModuleType, tmp_path: Path) -> None:
    """The state filter stays narrow. A first pass that counted
    `READY FOR IMPLEMENTATION` as open reported 42 items where there were 27,
    **and a check that overstates is one people learn to skim.**"""
    (tmp_path / "docs" / "LANE_COORDINATION.md").write_text(
        "## C-999 · a fixture\n\n| | |\n|---|---|\n"
        "| **Status** | ✅ `CLOSED` |\n"
    )
    assert check._item_owner_findings() == []


def test_the_registry_is_actually_being_read(check: ModuleType) -> None:
    """Guards the fixture itself: if `MODULES_TOML` were mis-pointed, every
    module case would fail to resolve and the routable half would go red for the
    wrong reason — a fixture that makes the condition impossible."""
    routable = check._routable_modules()
    assert "knowledge_graph" in routable
    assert "signal_engine" in routable
    assert "orphaned_module" not in routable, "no current_owner means no join"
