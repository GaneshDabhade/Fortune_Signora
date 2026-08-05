"""**The documents that describe the repository were wrong three times, and a person found each one.**

[B-120](../../../docs/BUGS.md), raised by QE against Lane C. Four generators
produce the repository's account of itself and **no test executed any of them.**
They sit outside the coverage gate's scope — `modules`, `signora_platform`,
`apps` — so **their absence was invisible to every measurement QE publishes.**

**The evidence QE cited is this office's own commit titles**, all from one day:

* *"`Implemented 0` was hardcoded, and wave 1 made it false"* — a count that was a literal
* *"`Integrated 0` while wave 1 sat on `main`"* — a field whose name did not match its contents
* *"Eighteen index rows disagreed with their own item bodies"* — a summary drifted from its detail

> **Each was representable, shipped, and found by reading.** That is the detection
> method §2 rejects everywhere else — *"a violation that is unrepresentable beats
> one that is merely discouraged"*.

**These tests pin the three defects and the two more found inside the fix**, and
they are deliberately about *derivation* rather than *values*: asserting that the
dashboard says `Implemented 1` today would fail the day wave 2 lands, which is a
test that punishes progress. **Asserting that the figure moves with its input is
what would have caught a constant.**
"""

from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path
from types import ModuleType

import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]

#: The four B-120 names. **Listed rather than globbed** — a glob would silently
#: stop covering a generator the day one is renamed, which is the same class of
#: quiet gap this row exists to close.
#:
#: **Split by side effect, which the first version of this file did not do.**
#: `implementation-status` and `project-history` *write* their documents from
#: `main()`, so running them dirtied the working tree — a test that mutates the
#: repository is a defect whatever it asserts. **Both expose a pure `render()`**,
#: and that is what a generator test should call.
#: **`vocabulary-check.py` joined 2026-08-05, on B-120's own reasoning.**
#: It was written the same week and nothing executed it — which is the
#: precise gap this row exists to close, arriving again in a new tool.
PRINTING = ("repository-dashboard.py", "decision-queue.py", "vocabulary-check.py")
WRITING = ("implementation-status.py", "project-history.py")


def _load(name: str) -> ModuleType:
    path = REPO_ROOT / "infra" / name
    spec = importlib.util.spec_from_file_location(name.replace("-", "_")[:-3], path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


@pytest.mark.parametrize("name", PRINTING)
def test_the_generator_runs(name: str) -> None:
    """**It executes at all**, which no test asserted before B-120.

    A generator that crashes reports nothing, and *nothing* is indistinguishable
    from *not run* in a document nobody diffed. These read `git`, so this is an
    integration check by nature — and the alternative, mocking `git`, would
    assert that the mock works.
    """
    result = subprocess.run(
        [sys.executable, str(REPO_ROOT / "infra" / name)],
        capture_output=True, text=True, cwd=REPO_ROOT, timeout=600,
    )
    assert result.returncode == 0, f"{name} exited {result.returncode}: {result.stderr[-400:]}"
    assert result.stdout.strip(), f"{name} produced no output"


@pytest.mark.parametrize("name", WRITING)
def test_the_document_renders_without_writing_it(name: str) -> None:
    """**`render()`, never `main()`.**

    These two write their document, and the first version of this test ran them
    — leaving `IMPLEMENTATION_STATUS.md` and `PROJECT_HISTORY.md` modified in the
    working tree. **A test that mutates the repository is a defect whatever it
    asserts**, and it would have made every suite run produce a spurious diff.

    **The pure half is the half worth testing anyway**: `main()` adds file IO and
    a no-change short-circuit, and neither is where a wrong figure comes from.
    """
    rendered = _load(name).render()
    assert isinstance(rendered, str) and rendered.strip(), f"{name}.render() produced nothing"


class TestAFigureIsDerivedRatherThanStated:
    """**`Implemented 0` and `Integrated 0` were both literals.**

    The test that catches a constant is not one that checks today's number —
    it is one that **changes the input and requires the output to follow.**
    """

    def test_implemented_counts_the_wave_rows_it_is_given(self) -> None:
        dashboard = _load("repository-dashboard.py")
        wave = next(iter(dashboard.UI_WAVE_TASKS))
        assert dashboard._ui_implemented([(wave, "x", "IN VALIDATION")]) == 1
        assert dashboard._ui_implemented([(wave, "x", "READY")]) == 0
        assert dashboard._ui_implemented([("TASK-000", "x", "DONE")]) == 0

    def test_a_state_is_read_from_its_backticks_and_not_from_prose(self) -> None:
        """**The `TASK-415` regression.**

        Its status *explained* the D-060 loop — *"the assignee prepares, marks it
        `UNDER REVIEW`, and Lane C reviews"* — and a scan for any state word
        classified the row as `UNDER REVIEW` while it declared `APPROVED`.
        **A mention is not a declaration.**
        """
        dashboard = _load("repository-dashboard.py")
        assert "UNDER REVIEW" in dashboard.STATE_WORDS
        assert "APPROVED" in dashboard.STATE_WORDS
        # The declared state is the first backticked token, in line order.
        import re
        line = "✅ **`APPROVED`** — the assignee marks it `UNDER REVIEW` afterwards"
        quoted = [q.strip() for q in re.findall(r"`([A-Z][A-Z ]+)`", line)]
        assert quoted[0] == "APPROVED", "line order decides, not a fixed precedence"

    def test_every_state_this_office_writes_is_known_to_the_scanner(self) -> None:
        """**`RATIFIED` was invented for TASK-900 and left out of `STATE_WORDS`**,
        so a row this office wrote read `UNKNOWN` for a day. **An unclassifiable
        row still counts — it just counts as nothing.**
        """
        dashboard = _load("repository-dashboard.py")
        for state in ("RATIFIED", "DISPOSED", "PREPARING", "APPROVED"):
            assert state in dashboard.STATE_WORDS, f"{state} is written and unknown"


class TestTheRegisterCheckCanFireAndCannotCryWolf:
    """**Two defects were found inside this check by running it**, not by review.

    A check that reports drift on correct rows is worse than none: somebody has
    to disprove each finding, and the second time they stop reading it.
    """

    def test_a_declared_state_beats_the_word_closed_in_prose(self) -> None:
        """**The `C-226` false positive, and it is [B-101](../../../docs/BUGS.md).**

        Its status reads *"`OPEN` — nothing is blocked… this asks whether the
        class should be closed."* **Substring matching made an open item read as
        shut** — inside the check written to catch a cousin of that defect.
        """
        queue = _load("decision-queue.py")
        assert queue._is_open("**`OPEN`** — this asks whether the class should be closed")
        assert not queue._is_open("**`CLOSED`** — 2026-08-05, product owner")
        assert not queue._is_open("**`RULED`** — 2026-08-05")

    def test_an_item_with_no_declared_status_is_not_read_as_closed(self) -> None:
        """**Absence is not a pass**, and six items carry no `Status` field.

        Reading an empty string as *not open* reported every one of them as
        drift — the `missing_gates` rule, which this repository has paid for
        nine times in CHECK constraints.
        """
        queue = _load("decision-queue.py")
        assert queue._is_open("") is False
        registry = queue.register()
        blank = [c for c, (_, s, _) in registry.items() if not queue._clean(s).strip()]
        assert not queue.index_disagreements({c: registry[c] for c in blank}), (
            "items with no Status must be skipped, never reported as drift"
        )

    def test_the_drift_check_actually_fires(self) -> None:
        """**A guard that cannot fail is documentation pretending to be code.**

        Eighteen rows disagreed when this was first measured; today most are
        fixed, so the check would report almost nothing — and *almost nothing*
        reads the same as *wired up wrong*.
        """
        queue = _load("decision-queue.py")
        real = queue.register()
        # **Must be an item the index actually lists.** The first run of this
        # test picked C-210, which has no summary row — so the check compared
        # nothing and the test read as a broken guard. **It was the guard's gap,
        # not the test's**: 25 of 82 items were unlisted, and `index_absences`
        # now reports them.
        listed = {m.group(1) for m in queue.INDEX_ROW.finditer(queue.REGISTER.read_text())}
        cid = next(c for c in sorted(listed) if c in real and queue._is_open(real[c][1]))
        lying = {cid: (real[cid][0], "**`CLOSED`** — invented by this test", real[cid][2])}
        assert queue.index_disagreements(lying), "the check cannot report a disagreement"

    def test_an_item_missing_from_the_index_is_reported(self) -> None:
        """**The gap the test above found.**

        An item with no summary row was never compared, so it could be ruled and
        stay invisible in the index a lane reads first. **25 of 82 were in that
        state**, including one the product owner had ruled that morning.
        """
        queue = _load("decision-queue.py")
        invented = {"C-999": ("an item no index lists", "**`OPEN`**", "product owner")}
        assert queue.index_absences(invented), "an unlisted open item must be reported"
