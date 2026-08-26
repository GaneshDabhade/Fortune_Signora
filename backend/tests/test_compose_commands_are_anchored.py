"""Every `docker compose` command the repository prints NAMES its environment.

⛔ **[B-1081](../../docs/BUGS.md).** A bare
`docker compose -f infra/docker-compose.yml up -d` leaves
`COMPOSE_PROJECT_NAME` unset, so Compose derives it **from the directory name**
rather than from the environment the branch selects. The reader creates
containers in a project nobody chose, binding whatever ports the file names.

📁 **[B-141](../../docs/BUGS.md) records the consequence, dated 2026-08-07** — a
lane ran exactly that form and *"recreated a container that was already running
on port 5432"* instead of starting its own on 5732.

⚠️ **The incident was filed as evidence for a contention hypothesis. The cause
was never filed at all**, so the repository went on printing the command for
another nineteen days — including in QE's own Stage 0 runbook and in the message
`make review` hands somebody whose stack is already down.

### ⚡ Why a test rather than a careful edit

**Three of the seven candidate sites were already correct**, and the two-line
shape is why a `grep -v` sweep got it wrong in both directions: the safe
`env $(… --exports)` prefix sits on the **preceding** line, invisible to a
line-based exclusion. ⛔ **A fix nothing enforces is one careless paste from
returning**, and the next person to add a diagnostic will copy the nearest
example.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]

#: Every file that prints a compose command to a human. **Add to this list when
#: a new one is written** — a file absent from it is not checked, which is the
#: `tenancy_policy.py` classification rule applied to diagnostics.
PRINTS_COMPOSE_COMMANDS = [
    "infra/review.py",
    "infra/release-preflight.py",
    "docs/RUNNING.md",
    "docs/QUALITY_ENGINEERING.md",
    "docs/REPOSITORY_RELEASE_CHECKLIST.md",
]

_COMPOSE = re.compile(r"docker compose\s+-f\s+infra/docker-compose\.yml")

#: What makes a call anchored: the environment is named rather than derived.
#: ⚡ **Either form counts** — the `--exports` prefix, or an explicit
#: `COMPOSE_PROJECT_NAME`.
_ANCHORS = ("--exports", "COMPOSE_PROJECT_NAME")


def _unanchored(path: Path) -> list[tuple[int, str]]:
    """Compose calls with no anchor on their own line or the one above.

    ⚠️ **The preceding line is in scope deliberately.** The safe form wraps:

        env $(python3 infra/environments.py --exports | grep -v '^#') \\
          docker compose -f infra/docker-compose.yml up -d --wait

    ⛔ **Judging the matched line alone reports three correct sites as broken**,
    which is exactly what a first sweep did.
    """
    lines = path.read_text(encoding="utf-8").split("\n")
    found = []
    for i, line in enumerate(lines):
        if not _COMPOSE.search(line):
            continue
        window = line + "\n" + (lines[i - 1] if i else "")
        if not any(a in window for a in _ANCHORS):
            found.append((i + 1, line.strip()))
    return found


@pytest.mark.parametrize("relative", PRINTS_COMPOSE_COMMANDS)
def test_every_printed_compose_command_names_its_environment(relative: str) -> None:
    path = REPO_ROOT / relative
    assert path.exists(), f"{relative} is listed here and does not exist"
    offenders = _unanchored(path)
    assert not offenders, (
        f"{relative} prints a compose command with no environment:\n"
        + "\n".join(f"  line {n}: {text}" for n, text in offenders)
        + "\n\nCOMPOSE_PROJECT_NAME would come from the directory name (B-1081)."
    )


def test_the_check_can_fail() -> None:
    """⚠️ **The vacuity guard.** ⛔ A pattern that matched nothing would pass
    every assertion above on any repository at all — the *instrument too narrow*
    failure, which fails silently and reads as success.

    ✅ **So the oracle is shown a bare command and must reject it, and the
    two-line safe form and must accept it.**
    """
    bare = "  docker compose -f infra/docker-compose.yml up -d --wait"
    wrapped = (
        "env $(python3 infra/environments.py --exports | grep -v '^#') \\\n"
        "  docker compose -f infra/docker-compose.yml up -d --wait"
    )
    inline = "COMPOSE_PROJECT_NAME=signora-v2 docker compose -f infra/docker-compose.yml down"

    def offenders(text: str) -> list[tuple[int, str]]:
        lines = text.split("\n")
        out = []
        for i, line in enumerate(lines):
            if not _COMPOSE.search(line):
                continue
            window = line + "\n" + (lines[i - 1] if i else "")
            if not any(a in window for a in _ANCHORS):
                out.append((i + 1, line.strip()))
        return out

    assert offenders(bare), "the oracle no longer rejects a bare compose command"
    assert not offenders(wrapped), "the oracle rejects the documented safe form"
    assert not offenders(inline), "the oracle rejects an explicit project name"
