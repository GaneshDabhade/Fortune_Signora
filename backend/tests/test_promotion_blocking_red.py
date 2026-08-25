"""A promotion cannot proceed past an open 🔴 — `CLAUDE.md` §20e's one blocking rule.

⛔ **The rule was enforced by nothing.** `state-check.py` read it and is
**advisory**: it prints the line among twenty-odd findings that read identically,
and QE scrolled past it at two consecutive promotions ([B-1075](../../docs/BUGS.md)).
`certification-guard.py` — the gate that exits non-zero and means it — asked a
different question: *"was this commit certified?"*

📁 **The same shape as [B-1070](../../docs/BUGS.md)**, where `--audit-main` passed
truthfully about snapshot membership while the reader relied on it for linearity.
**A guard answering a question nobody asked it is not protection.**

⚠️ **Every case below is FIXED TEXT, never the live register.** Asserting that
today's `BUGS.md` reports nothing would pass identically with the whole check
deleted — the Decorative Logic `CLAUDE.md` §2 names, and the warning
`test_verified_bug_regressions.py` already carries one file over.
**Three of these must FIRE.**
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from types import ModuleType

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]

#: One row, one severity, one status — the smallest register that still parses.
ROW = """### B-{identifier} · {severity} a fixture

| | |
|---|---|
| **Severity** | {severity} |
| **Status** | {state} |

"""

OPEN_RED = ROW.format(identifier="901", severity="🔴", state="**`OPEN`**")
FIXING_RED = ROW.format(identifier="902", severity="🔴", state="**`FIXING`** — in progress")
VERIFIED_RED = ROW.format(identifier="903", severity="🔴", state="✅ **`VERIFIED`** — QE")
OPEN_AMBER = ROW.format(identifier="904", severity="🟠", state="**`OPEN`**")


def _load_guard() -> ModuleType:
    path = REPO_ROOT / "infra" / "certification-guard.py"
    spec = importlib.util.spec_from_file_location("guard_blocking_red_under_test", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules["guard_blocking_red_under_test"] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def guard() -> ModuleType:
    return _load_guard()


def _run_promote(
    guard: ModuleType,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    register: str,
) -> tuple[int, str]:
    """Drive `_promote` itself against a candidate whose `BUGS.md` is `register`.

    ⛔ **THIS FILE'S FIRST VERSION CALLED `bug_rows` DIRECTLY AND WAS WORTHLESS.**
    ⚡ **Deleting the gate entirely — `blocking: list[str] = []` — left all seven
    tests GREEN**, because they were exercising `registers.py` and asserting
    nothing about whether the promotion path consults it. **The mutation survived,
    which is `CLAUDE.md` §2's definition of Decorative Logic**, and this file had
    quoted the warning against it in its own docstring.

    ✅ **So the seam is `_git` and `_runs`, and the subject is `_promote`'s
    RETURN VALUE AND ITS STATED REASON.** ⚠️ **The reason matters as much as the
    code**: with the gate deleted `_promote` still returns `1`, because HEAD is
    not `main` in a test run — **asserting the exit code alone would survive the
    mutation exactly as the first version did.**
    """
    everything_certified = [{"commit": "c" * 40}]
    monkeypatch.setattr(guard, "_runs", lambda: everything_certified)
    monkeypatch.setattr(guard, "_promotable", lambda run: (True, []))

    def fake_git(*args: str) -> str:
        if args[:2] == ("rev-parse", "HEAD"):
            return "c" * 40
        if args[0] == "rev-parse":
            return "c" * 40
        if args[:2] == ("rev-parse", "--abbrev-ref"):
            return "main"
        if args[0] == "show" and args[1].endswith("docs/BUGS.md"):
            return register
        if args[0] == "show" and args[1].endswith("docs/BACKLOG.md"):
            return ""
        return ""

    monkeypatch.setattr(guard, "_git", fake_git)
    code = guard._promote("c" * 40)
    return code, capsys.readouterr().out


def test_the_gate_imports_the_parser_at_all(guard: ModuleType) -> None:
    """⛔ **The regression `test_verified_bug_regressions.py` records, one gate over.**

    That fix called `bug_rows` without importing it and the module still LOADED —
    a name is resolved when the function runs — so the defect was invisible until
    `_promote` was exercised, which QE never did.
    """
    assert hasattr(guard, "bug_rows"), "the promotion gate cannot read the register"


def test_an_open_red_REFUSES_the_promotion(
    guard: ModuleType, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    code, out = _run_promote(guard, monkeypatch, capsys, OPEN_RED)
    assert code == 1
    assert "B-901" in out
    assert "unresolved 🔴" in out


def test_a_red_being_fixed_still_REFUSES(
    guard: ModuleType, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """**`FIXING` is not resolved.** A defect somebody is working on is still open."""
    code, out = _run_promote(guard, monkeypatch, capsys, FIXING_RED)
    assert code == 1
    assert "B-902" in out


def test_a_verified_red_does_NOT_refuse(
    guard: ModuleType, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """⚡ **A fixed 🔴 is a record, not a blocker** — otherwise the register would
    block every promotion for ever, and the rule would be abandoned rather than
    obeyed."""
    _, out = _run_promote(guard, monkeypatch, capsys, VERIFIED_RED)
    assert "PASS  no unresolved" in out
    assert "B-903" not in out


def test_an_open_amber_does_NOT_refuse(
    guard: ModuleType, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """📁 §20e: *"🟠 and below are the product owner's call."*"""
    _, out = _run_promote(guard, monkeypatch, capsys, OPEN_AMBER)
    assert "PASS  no unresolved" in out
    assert "B-904" not in out


def test_a_register_holding_all_four_names_only_the_two_that_block(
    guard: ModuleType, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """⛔ **The case a per-row test cannot make**: the gate must SELECT, not count."""
    code, out = _run_promote(
        guard, monkeypatch, capsys, OPEN_RED + FIXING_RED + VERIFIED_RED + OPEN_AMBER
    )
    assert code == 1
    assert "B-901" in out and "B-902" in out
    assert "B-903" not in out and "B-904" not in out


def test_an_absent_register_does_not_raise(
    guard: ModuleType, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """⚠️ **`_promote` passes `cand_bugs` straight from `git show`, which returns
    an empty string when the path is absent.** **An exception there would refuse a
    promotion for a reason that has nothing to do with the register.**"""
    _, out = _run_promote(guard, monkeypatch, capsys, "")
    assert "PASS  no unresolved" in out
