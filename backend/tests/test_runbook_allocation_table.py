"""`RUNNING.md`'s allocation table agrees with `infra/environments.py`.

⛔ **[B-1003](../../docs/BUGS.md).** The table carried a `Database` column naming
`signora_lane_a`, `signora_lane_qe`, `signora_lane_c` — **databases no compose
file has ever created** — and **no PostgreSQL or Redis port column at all.**
⚡ **The table WAS the one-server-many-databases model**, which is why two models
coexisted: the `CREATE DATABASE` example beneath it was not a stray stale snippet
but a faithful instance of what the table asserted.

⚠️ **QE then cited the file to a lane as the safe path around a data-destruction
defect ([B-270](../../docs/BUGS.md)) without opening it** — and the warning saying
those lines were stale was already in the document, addressed to QE.

📁 **Why this is a check and not a deletion, which is the opposite of
[B-1001](../../docs/BUGS.md)'s repair.** There the fix was to delete the copy,
because a reference carried everything the copy did. **Here the table earns its
place**: a person opening a runbook wants to see the allocation, and
`eval "$(python3 infra/environments.py --exports)"` answers only for the clone
they are standing in — **it cannot show them that Lane A is slot 2.** ⚡ **So the
copy stays and stops being trusted**: this test is what makes its drift a failing
gate rather than a discovery.

⛔ **The table is NOT the source.** `infra/environments.py` is. If they disagree,
this fails and **the table is what changes.**
"""

from __future__ import annotations

import importlib.util
import re
import sys
from pathlib import Path
from types import ModuleType

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
RUNBOOK = REPO_ROOT / "docs" / "RUNNING.md"

#: The rows that name a real environment. The production stack has no slot — it
#: lives in its own compose project with its own everything — so it is
#: deliberately absent from `ENVIRONMENTS` and from this map.
ROW_TO_ENVIRONMENT = {
    "Human review": "review",
    "QE": "lane-qe",
    "Lane A": "lane-a",
    "Lane B": "lane-b",
    "Lane C": "lane-c",
    "Lane D": "lane-d",
    "Lane E": "lane-e",
    "Demo": "demo",
}


def _environments() -> ModuleType:
    path = REPO_ROOT / "infra" / "environments.py"
    spec = importlib.util.spec_from_file_location("environments_under_test", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules["environments_under_test"] = module
    spec.loader.exec_module(module)
    return module


def _table_rows() -> dict[str, tuple[int, int, int, int, int, int]]:
    """Every allocation row, as `(slot, web, api, postgres, redis, minio)`.

    **Parsed from the document rather than from a fixture**, because a fixture
    copy of the table would be the very thing this test exists to catch.
    """
    rows: dict[str, tuple[int, int, int, int, int, int]] = {}
    for line in RUNBOOK.read_text().splitlines():
        if not line.startswith("| **"):
            continue
        cells = [c.strip() for c in line.strip("|").split("|")]
        if len(cells) != 8:
            continue
        label = re.sub(r"[*`]", "", cells[0]).split("—")[0].strip()
        if label not in ROW_TO_ENVIRONMENT:
            continue
        numbers = [re.sub(r"[^\d/]", "", c) for c in cells[2:]]
        if not all(n and n[0].isdigit() for n in numbers):
            continue  # the production-stack row, whose cells are prose
        slot, web, api, pg, redis, minio = (int(n.split("/")[0]) for n in numbers)
        rows[ROW_TO_ENVIRONMENT[label]] = (slot, web, api, pg, redis, minio)
    return rows


@pytest.fixture(scope="module")
def table() -> dict[str, tuple[int, int, int, int, int, int]]:
    return _table_rows()


def test_the_table_was_found_and_parsed(table: dict[str, tuple[int, ...]]) -> None:
    """⛔ **Guards the parser, because every case below would pass vacuously.**

    A regex that silently matches nothing turns this whole file green while
    checking nothing — the Decorative Logic `CLAUDE.md` §2 names, and the exact
    failure `_backlog_states` had one register over.
    """
    assert len(table) == len(ROW_TO_ENVIRONMENT), (
        f"parsed {sorted(table)}, expected {sorted(ROW_TO_ENVIRONMENT.values())} — "
        "the table's shape changed and this parser did not"
    )


@pytest.mark.parametrize("name", sorted(ROW_TO_ENVIRONMENT.values()))
def test_every_row_matches_the_derivation(
    table: dict[str, tuple[int, int, int, int, int, int]], name: str
) -> None:
    module = _environments()
    e = next(x for x in module.ENVIRONMENTS if x.name == name)
    derived = (e.slot, e.web_port, e.api_port, e.postgres_port, e.redis_port, e.minio_port)
    assert table[name] == derived, (
        f"RUNNING.md's {name} row disagrees with infra/environments.py. "
        "The derivation is the source; the table is what changes."
    )


def test_no_live_instruction_quotes_slot_zeros_port() -> None:
    """🔴 **The defect that produced B-1003, asserted directly.**

    ⛔ **Prose may discuss `localhost:5432`; a RUNNABLE COMMAND may not contain
    it.** Three mentions remain and all three are history — the discharged note,
    the record of what the `CREATE DATABASE` step used to do, and the annotation
    on the variables table.

    ⚡ **Fence-aware, and that is the whole of the technique.** A first attempt
    excluded blockquotes and lines saying *"used to"*, which is a heuristic about
    how somebody phrased a sentence rather than about what a reader can execute —
    **and it failed on the variables-table annotation, correctly.** 📁 **The same
    repair Lane C made when three `>>>>>>>` in `BUGS.md` turned out to be quoted
    evidence inside fences: read the structure, not the substring.**
    """
    live: list[str] = []
    in_fence = False
    for n, line in enumerate(RUNBOOK.read_text().splitlines(), 1):
        if line.lstrip().startswith("```"):
            in_fence = not in_fence
            continue
        if in_fence and "localhost:5432" in line:
            live.append(f"{n}: {line.strip()[:90]}")
    assert not live, (
        "a runnable command quotes localhost:5432 — human review's cluster:\n" + "\n".join(live)
    )


def test_every_environment_has_a_row(table: dict[str, tuple[int, ...]]) -> None:
    """**A new environment must reach the runbook in the same change.**

    ⛔ `lane-e` existed in `environments.py` and appeared in no table until
    2026-08-15 — **QE wrote the corrected table from inference and omitted it**,
    one minute after writing *"no lane types a port."* ⚡ **This is the case that
    would have caught that**, and it is why the table is generated from the
    derivation rather than typed.
    """
    module = _environments()
    missing = sorted({e.name for e in module.ENVIRONMENTS} - set(table))
    assert not missing, f"environments with no row in RUNNING.md: {missing}"
