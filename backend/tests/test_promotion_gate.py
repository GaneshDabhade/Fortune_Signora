"""A blocking gate stops promotion, and a status word in prose is not a status.

**[D-228](../../docs/DECISION_REGISTER.md), the product owner**, after QE
promoted while a gate was firing and after that gate turned out to be wrong.

Two defects, one ruling:

* **[B-168](../../docs/BUGS.md)** matched the *word* `VERIFIED` anywhere in a
  removed line, so a `READY` cell whose prose cited a verified row read as a
  regression. **Measured then: 12 `VERIFIED` status cells before, 12 after, no
  row changed.**
* **[B-142](../../docs/BUGS.md)'s class** — the check and the promotion sat in
  one command block with no gate between them. ⛔ *"A check whose output nobody
  is forced to read is a log line, not a gate."*

**Every case below is fixed text.** A test asserting against the live
`BACKLOG.md` would pass today and pass identically with the fix reverted.
"""

from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path
from types import ModuleType

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]


def _load_guard() -> ModuleType:
    """`infra/certification-guard.py`, registered before execution — its
    `@dataclass(slots=True)` resolves annotations through `sys.modules`."""
    path = REPO_ROOT / "infra" / "certification-guard.py"
    spec = importlib.util.spec_from_file_location("certification_guard", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


guard = _load_guard()


def _row(task: str, status: str, extra: str = "") -> str:
    return (
        f"### {task} · a title\n\n"
        "| | |\n|---|---|\n"
        f"| **Status** | {status} |\n"
        f"{extra}"
        "\n"
    )


class TestProseCannotBecomeAStatus:
    """⛔ B-168's false positive, asserted directly."""

    def test_a_reference_to_another_rows_verified_state_is_not_this_rows_state(self) -> None:
        text = _row(
            "TASK-1",
            "✅ **`READY` — Lane C.** ✅ **Released: [TASK-1408] is `VERIFIED` "
            "and promoted at `e72b6af0`.**",
        )

        assert guard.backlog_states(text) == {"TASK-1": "READY"}

    def test_the_exact_cell_that_produced_the_false_positive_reports_no_regression(self) -> None:
        """⚡ The measured case: the row moved `SEQUENCED` -> `READY` and its
        prose names a verified row. **No `VERIFIED` state is lost.**"""
        before = _row("TASK-1", "⏸️ **`SEQUENCED`** — the shell does not exist yet")
        after = _row(
            "TASK-1",
            "✅ **`READY` — Lane C.** ✅ **[TASK-1408] is `VERIFIED` and promoted.**",
        )

        assert guard.verified_regressions(before, after) == []

    def test_a_status_word_in_a_title_or_a_note_is_ignored(self) -> None:
        text = (
            "### TASK-2 · why TASK-9 is VERIFIED and this one is not\n\n"
            "| | |\n|---|---|\n"
            "| **Status** | ✅ **`CLAIMED` — Lane A** |\n"
            "| **Evidence** | it was `VERIFIED` at `abc1234`, see the note |\n"
            "| **Reference** | `VERIFIED` rows are QE's |\n"
        )

        assert guard.backlog_states(text) == {"TASK-2": "CLAIMED"}


class TestEveryStateOnlyQEMayWriteIsWatched:
    """**B-232** — the gate said `PASS  no VERIFIED state is undone` while a
    `PROMOTED` cell was being reverted through it, and the revert reached `main`.

    ⛔ **The gap was the noun, not the logic.** [B-168](../../docs/BUGS.md) named
    the state it had just been burned by; the guard inherited that name as if it
    were the rule. **The rule is *QE's judgement*, and QE writes four states.**
    """

    def test_promoted_reverted_to_in_validation_is_reported(self) -> None:
        """🔴 B-232 itself, as the smallest case that reproduces it."""
        before = _row("TASK-1403", "✅ **`PROMOTED` — QE**, in certified `e71e74d`")
        after = _row("TASK-1403", "✅ **`IN VALIDATION` — Lane A**")

        assert guard.verified_regressions(before, after) == [("TASK-1403", "IN VALIDATION")]

    def test_certified_falling_back_to_verified_is_reported(self) -> None:
        """⚡ A smaller step is the same defect — QE's sequence only runs one way."""
        before = _row("TASK-5", "✅ **`CERTIFIED` — QE**")
        after = _row("TASK-5", "✅ **`VERIFIED` — QE**")

        assert guard.verified_regressions(before, after) == [("TASK-5", "VERIFIED")]

    def test_a_promoted_row_that_disappears_entirely_is_reported(self) -> None:
        before = _row("TASK-6", "✅ **`PROMOTED` — QE**")

        assert guard.verified_regressions(before, "") == [("TASK-6", "ABSENT")]

    def test_advancing_along_qes_own_sequence_is_not_a_regression(self) -> None:
        """⛔ **A guard that fires on progress is one people learn to ignore.**"""
        assert guard.verified_regressions(
            _row("TASK-7", "✅ **`VERIFIED` — QE**"),
            _row("TASK-7", "✅ **`PROMOTED` — QE**"),
        ) == []
        assert guard.verified_regressions(
            _row("TASK-8", "✅ **`PROMOTED` — QE**"),
            _row("TASK-8", "✅ **`DONE` — QE**"),
        ) == []

    def test_a_lanes_own_states_are_not_this_guards_business(self) -> None:
        """✅ `IN VALIDATION` → `CLAIMED` is a lane moving its own row (§20e)."""
        assert guard.verified_regressions(
            _row("TASK-9", "✅ **`IN VALIDATION` — Lane A**"),
            _row("TASK-9", "✅ **`CLAIMED` — Lane A**"),
        ) == []

    def test_the_watched_set_is_exactly_the_states_only_qe_writes(self) -> None:
        """⚠️ Pinned by name rather than by count — a set that grew by accident
        would still satisfy a length assertion."""
        assert guard.QE_TERMINAL_STATES == frozenset(
            {"VERIFIED", "CERTIFIED", "PROMOTED", "DONE"}
        )


class TestARealRegressionStillFires:
    def test_verified_becoming_in_validation_is_reported(self) -> None:
        before = _row("TASK-3", "✅ **`VERIFIED` — QE**, at `1874df08`")
        after = _row("TASK-3", "✅ **`IN VALIDATION` — Lane A**")

        assert guard.verified_regressions(before, after) == [("TASK-3", "IN VALIDATION")]

    def test_a_verified_row_that_disappears_entirely_is_reported(self) -> None:
        before = _row("TASK-4", "✅ **`VERIFIED` — QE**")

        assert guard.verified_regressions(before, "") == [("TASK-4", "ABSENT")]

    def test_the_three_occurrences_that_prompted_b_168_would_now_be_caught(self) -> None:
        """⚡ TASK-1435 and TASK-1436, reverted by a clean rebase and promoted."""
        before = _row("TASK-1435", "✅ **`VERIFIED` — QE**") + _row(
            "TASK-1436", "✅ **`VERIFIED` (the capability) — QE**"
        )
        after = _row("TASK-1435", "✅ **`IN VALIDATION` — Lane A**") + _row(
            "TASK-1436", "🟣 **`IN VALIDATION` (the capability)** · ⏸️ **`BLOCKED`**"
        )

        assert guard.verified_regressions(before, after) == [
            ("TASK-1435", "IN VALIDATION"),
            ("TASK-1436", "IN VALIDATION"),
        ]


class TestValidRowsKeepPassing:
    def test_an_unchanged_verified_row_is_not_a_regression(self) -> None:
        text = _row("TASK-5", "✅ **`VERIFIED` — QE**, at `abc1234`")

        assert guard.verified_regressions(text, text) == []

    def test_a_row_with_no_status_cell_contributes_nothing_rather_than_guessing(self) -> None:
        """⛔ [B-169](../../docs/BUGS.md) — four rows carried their state inside
        the Module cell. **Absent must read as absent, never as a default.**"""
        text = "### TASK-6 · a title\n\n| | |\n|---|---|\n| **Module** | `x` · **Status** `SEQUENCED` |\n"

        assert guard.backlog_states(text) == {}

    def test_progressing_forward_from_verified_is_not_a_regression(self) -> None:
        """⚠️ **This assertion used to say the opposite of its own name, and the
        name was right** — corrected 2026-08-10 with [B-176](../../docs/BUGS.md).

        ⛔ **The original implementation reported ANY departure from `VERIFIED`,
        including QE's own advance to `PROMOTED`**, and this test was written to
        match the implementation rather than the property. **So the gate could
        refuse a correct promotion**, and only the comparison it happens to make
        — `origin/main` against the candidate — kept that from firing.

        ⚡ **A test written to match the code cannot report that the code is
        wrong.** ✅ **The property is the one the name always stated: QE's
        sequence runs one way, and moving along it is not undoing it.**
        """
        before = _row("TASK-7", "✅ **`VERIFIED` — QE**")
        after = _row("TASK-7", "✅ **`PROMOTED` — QE**")

        assert guard.verified_regressions(before, after) == []


def _load_coordination() -> ModuleType:
    path = REPO_ROOT / "infra" / "coordination.py"
    spec = importlib.util.spec_from_file_location("coordination_mod", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


coordination = _load_coordination()


class TestTheLatestLifecycleStateWins:
    """⛔ **[B-163](../../docs/BUGS.md), corrected under
    [D-228](../../docs/DECISION_REGISTER.md)** — *"a stale coordination state
    must not stop a legitimately progressing implementation lane."*

    `_integration_states` reconciles two refs by lifecycle rank, so the rank
    table **is** the reconciliation. A wrong rank is a wrong answer about which
    ref is newer.
    """

    def _resolve(self, a: str, b: str) -> str:
        rank = coordination._LIFECYCLE
        return a if rank.get(a, 0) > rank.get(b, 0) else b

    def test_in_validation_beats_the_older_claimed(self) -> None:
        """⚡ The case D-228 names: `integration` says `CLAIMED`, the lane has
        legitimately progressed. **The newer state wins.**"""
        assert self._resolve("IN VALIDATION", "CLAIMED") == "IN VALIDATION"

    def test_claimed_beats_the_older_ready(self) -> None:
        assert self._resolve("CLAIMED", "READY") == "CLAIMED"

    def test_changes_requested_beats_in_validation(self) -> None:
        """🔴 **The one non-monotonic transition, and the defect.** §20e places
        `CHANGES REQUESTED` AFTER `IN VALIDATION` — QE returned the slice. Ranked
        below, a returned row read as still waiting on QE and the lane could not
        see it had to act."""
        assert self._resolve("CHANGES REQUESTED", "IN VALIDATION") == "CHANGES REQUESTED"

    def test_verified_still_outranks_changes_requested(self) -> None:
        """⛔ **The reverse case, so the fix does not let a stale return
        override a later verification.**"""
        assert self._resolve("VERIFIED", "CHANGES REQUESTED") == "VERIFIED"

    def test_a_stale_earlier_state_never_overrides_a_later_one(self) -> None:
        order = ["READY", "CLAIMED", "IN PROGRESS", "IN VALIDATION",
                 "CHANGES REQUESTED", "VERIFIED", "CERTIFIED", "PROMOTED", "DONE"]
        for index, later in enumerate(order):
            for earlier in order[:index]:
                assert self._resolve(later, earlier) == later, f"{earlier} beat {later}"

    def test_every_state_the_backlog_uses_has_a_rank(self) -> None:
        """⚠️ **An unranked state scores 0 and loses to everything** — silently."""
        for state in ("READY", "SEQUENCED", "BLOCKED", "WAITING", "CLAIMED",
                      "IN PROGRESS", "IN VALIDATION", "CHANGES REQUESTED",
                      "VERIFIED", "CERTIFIED", "PROMOTED", "DONE"):
            assert coordination._LIFECYCLE.get(state, 0) > 0, state




class TestAClaimPushCannotSmuggleASlice:
    """A push moves a branch, so a clean claim can carry a slice in with it.

    **[B-238](../../docs/BUGS.md), reported by Lane A against itself with the
    breach as the evidence** — the third row after [B-161](../../docs/BUGS.md)
    (QE's own diagnosis) and [B-220](../../docs/BUGS.md) (the blind spot named).
    ⛔ **The claim commit was clean, `--audit-claims` passed it correctly, and
    `M12.6 — the keyboard map…` arrived on `integration` underneath it**: 1,148
    lines that had never been validated, certified or promoted.

    ## These build a real repository, deliberately

    ⛔ **A test that stubs `git` proves the function reads a dict.** **The defect
    was never in the function — it was in which object the guard asked about**,
    and only a real branch movement can distinguish those two. So each case
    below `git init`s a repository, makes real commits, and **moves a branch the
    way a push moves it**, then points the guard's `REPO_ROOT` at it.

    **Nothing here touches the Signora repository**, and nothing here is a
    fixture the other classes share: `_LIFECYCLE` and `verified_regressions` are
    about text, and text is correctly tested as text.
    """

    @staticmethod
    def _run(root: Path, *args: str) -> str:
        done = subprocess.run(
            ["git", *args], cwd=root, check=True, capture_output=True, text=True
        )
        return done.stdout.strip()

    @classmethod
    def _repo(cls, tmp_path: Path) -> Path:
        root = tmp_path / "repo"
        root.mkdir()
        cls._run(root, "init", "-q", "-b", "main")
        cls._run(root, "config", "user.email", "qe@example.test")
        cls._run(root, "config", "user.name", "QE")
        cls._run(root, "commit", "-q", "--allow-empty", "-m", "base")
        cls._run(root, "branch", "integration")
        return root

    @classmethod
    def _commit(cls, root: Path, branch: str, subject: str, path: str, body: str) -> str:
        cls._run(root, "checkout", "-q", branch)
        target = root / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(body)
        cls._run(root, "add", path)
        cls._run(root, "commit", "-q", "-m", subject)
        return cls._run(root, "rev-parse", "HEAD")

    @staticmethod
    def _push(root: Path, source: str, target: str) -> None:
        """**What a push actually does** — move `target` to wherever `source` is.

        ⚡ **This is the whole defect in one line.** The lane pushed a branch
        whose tip was a claim; every ancestor not already on `integration` went
        with it, and the guard only ever looked at the tip.
        """
        TestAClaimPushCannotSmuggleASlice._run(root, "branch", "-f", target, source)

    def _guard_on(self, monkeypatch: pytest.MonkeyPatch, root: Path) -> ModuleType:
        guard = _load_guard()
        monkeypatch.setattr(guard, "REPO_ROOT", root)
        return guard

    def test_the_b238_breach_is_detected_through_a_real_branch_move(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """The exact sequence that happened, reproduced rather than described."""
        root = self._repo(tmp_path)
        self._run(root, "checkout", "-q", "-b", "lane")
        self._commit(root, "lane", "M12.6 — the keyboard map says which work",
                     "frontend/lib/shell/shortcuts.ts", "export const SHORTCUTS = [];\n")
        self._commit(root, "lane", "Claim TASK-1458 — the rail's third pinned utility",
                     "docs/BACKLOG.md", "TASK-1458 CLAIMED\n")
        # The lane ran `git push origin HEAD:integration` with the claim at HEAD.
        self._push(root, "lane", "integration")

        guard = self._guard_on(monkeypatch, root)
        claims = guard._claim_commits("main..integration")
        assert len(claims) == 1, "the claim itself is present and well-formed"

        found = guard._claim_stowaways(claims)
        assert len(found) == 1
        riders = [subject for _, subject in found[0][2]]
        assert riders == ["M12.6 — the keyboard map says which work"]

    def test_a_claim_pushed_from_integration_reports_nothing(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """The healthy case — and the one a false positive would destroy.

        ⛔ **A guard that fires on correct behaviour gets switched off, and then
        it protects nothing at all.** This is the case worth more than the one
        above, because the defect it prevents is the gate's own abandonment.
        """
        root = self._repo(tmp_path)
        self._commit(root, "integration", "Claim TASK-9 — something",
                     "docs/BACKLOG.md", "TASK-9 CLAIMED\n")
        guard = self._guard_on(monkeypatch, root)
        claims = guard._claim_commits("main..integration")
        assert len(claims) == 1
        assert guard._claim_stowaways(claims) == []

    def test_a_legitimate_claim_beside_a_stowaway_is_not_itself_flagged(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """**The mixed case, and it is the one that decides the gate is usable.**

        ⚡ **Two claims on `integration`: one pushed correctly, one carrying a
        slice.** A gate that reports both has told the reader nothing about
        which lane to talk to, and a gate that reports neither has missed the
        breach. ⛔ **It must name exactly the second.**
        """
        root = self._repo(tmp_path)
        # Lane A pushes a claim the proper way — its parent is `integration`.
        good = self._commit(root, "integration", "Claim TASK-8 — done properly",
                            "docs/BACKLOG.md", "TASK-8 CLAIMED\n")
        # Lane B branches from there, builds, and pushes claim-at-HEAD.
        self._run(root, "checkout", "-q", "-b", "laneb", good)
        self._commit(root, "laneb", "M12.6 — an unvalidated slice",
                     "frontend/lib/thing.ts", "export const x = 1;\n")
        self._commit(root, "laneb", "Claim TASK-9 — carried a slice",
                     "docs/BACKLOG.md", "TASK-9 CLAIMED\n")
        self._push(root, "laneb", "integration")

        guard = self._guard_on(monkeypatch, root)
        claims = guard._claim_commits("main..integration")
        assert len(claims) == 2, "both claims are on integration"

        found = guard._claim_stowaways(claims)
        assert len(found) == 1, "exactly one claim carried something"
        assert found[0][1] == "Claim TASK-9 — carried a slice"
        assert [s for _, s in found[0][2]] == ["M12.6 — an unvalidated slice"]

    def test_a_claim_riding_another_claim_is_not_a_stowaway(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Two claims in one push is not this defect.

        ⚡ **Both are things a lane may legitimately put on `integration`**, so
        reporting the earlier one is noise — and noise is what makes a real
        finding easy to scroll past.
        """
        root = self._repo(tmp_path)
        self._run(root, "checkout", "-q", "-b", "lane")
        self._commit(root, "lane", "Claim TASK-8 — first", "docs/BACKLOG.md", "8\n")
        self._commit(root, "lane", "Claim TASK-9 — second", "docs/BACKLOG.md", "8\n9\n")
        self._push(root, "lane", "integration")
        guard = self._guard_on(monkeypatch, root)
        assert guard._claim_stowaways(guard._claim_commits("main..integration")) == []


class TestAPromotedBreachIsHistoryNotAFinding:
    """`--audit-claims` refused on commits nobody could ever fix — [B-184].

    ⛔ **It audited `main..integration` *and* `RULE_RATIFIED_AT..main`, and
    refused on both.** The second range is immutable: those commits were
    promoted inside a certified snapshot and **no action by any lane will ever
    clear them.** So the check exited 1 on every invocation, for as long as the
    repository exists, and its own message told the reader to *"validate them
    before the next Certification Snapshot pins them"* — about commits pinned
    weeks earlier.

    ⚡ **The harm was never the false alarm.** It is that the only way to keep
    working was to skip the output, and then the run reporting a real breach
    looks exactly like the two hundred before it. **A gate that cannot pass is
    not a gate** (`CLAUDE.md` §2).

    ## Two-sided, because either half alone would be worthless

    **A check that never refuses is the defect this file exists to catch**, so
    it is not enough to prove the historical case passes. The second test puts
    the identical breach on `integration` and requires a refusal.

    ⛔ **Deliberately not a list of forgiven hashes**, which would silence a
    genuine future breach in the same files — the guard-that-cannot-fail shape
    wearing the opposite coat. **The question is *can this still be fixed*, and
    `main` answers it.**
    """

    @staticmethod
    def _repo_with(tmp_path: Path, branch: str) -> Path:
        """A repository whose only claim carried a document it may not carry.

        `branch` decides whether that claim is history (`main`) or still
        actionable (`integration`) — **the same breach, and the only variable
        is whether anybody can act on it.**
        """
        helper = TestAClaimPushCannotSmuggleASlice
        root = helper._repo(tmp_path)
        helper._run(root, "checkout", "-q", branch)
        helper._run(root, "checkout", "-q", "-b", "lane")
        target = root / "docs"
        target.mkdir(parents=True, exist_ok=True)
        (target / "BACKLOG.md").write_text("TASK-9 CLAIMED\n")
        (target / "LANE_COORDINATION.md").write_text("C-9 opened\n")
        helper._run(root, "add", "docs/BACKLOG.md", "docs/LANE_COORDINATION.md")
        helper._run(root, "commit", "-q", "-m", "Claim TASK-9 — carried a register too")
        helper._push(root, "lane", branch)
        return root

    def _guard(self, monkeypatch: pytest.MonkeyPatch, root: Path) -> ModuleType:
        loaded = _load_guard()
        monkeypatch.setattr(loaded, "REPO_ROOT", root)
        # The rule's start point is a real SHA in the live repository and means
        # nothing in a temp one; the repository's first commit is its analogue.
        base = TestAClaimPushCannotSmuggleASlice._run(
            root, "rev-list", "--max-parents=0", "HEAD"
        )
        monkeypatch.setattr(loaded, "RULE_RATIFIED_AT", base)
        return loaded

    def test_a_breach_already_on_main_is_reported_without_refusing(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """The case that made the gate useless: nothing anybody can do about it."""
        root = self._repo_with(tmp_path, "main")
        loaded = self._guard(monkeypatch, root)

        assert loaded._audit_claims() == 0, (
            "a claim breach that is already on `main` is immutable history. "
            "Refusing on it makes the verdict a foregone conclusion."
        )

    def test_the_same_breach_awaiting_promotion_is_still_refused(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """⛔ **The half that matters.** Scoping must not become forgiving.

        **Identical commit, identical offending path** — the only difference is
        that this one has not been promoted, so it can still be unpicked.
        """
        root = self._repo_with(tmp_path, "integration")
        loaded = self._guard(monkeypatch, root)

        assert loaded._audit_claims() == 1, (
            "an unpromoted claim carrying more than a claim must still refuse — "
            "otherwise scoping the audit has simply switched it off."
        )


class TestAnEmptyClaimAuditDoesNotReadAsACleanOne:
    """**B-1037.** With no claim awaiting promotion, `--audit-claims` printed
    *"0 claim(s) awaiting promotion touch only ACTIVE_ASSIGNMENTS.md and
    BACKLOG.md"* and then *"none of the unpromoted ones carried anything
    else"*.

    ⛔ **Both are vacuously true and together they read as a clean audit of a
    set nobody examined.** ⚡ **A reader cannot tell *nothing was wrong* from
    *nothing was checked*** — B-125's class, and the reason `_plan_shortfall`
    returns `None` rather than an empty list when it cannot measure.

    ⚠️ **This row's original diagnosis was WRONG and is corrected in the
    register.** It claimed the audit read local refs while `--audit-main` did
    not; **both call `_scope_note()` and report staleness identically.** The
    real defect is the vacuous positive, found by trying to fix the reported
    one.
    """

    def test_an_empty_audit_says_it_examined_nothing(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
    ) -> None:
        # ⚠️ **Historical claims and NO pending one — the live repository's
        # ordinary state between cycles, and the only one that produced the
        # misleading line.** A repository with no claims at all takes an
        # earlier branch that was already honest: *"no claim commits to
        # check"*. **My first version of this test built that repository and
        # proved nothing.**
        root = TestAPromotedBreachIsHistoryNotAFinding._repo_with(tmp_path, "main")
        loaded = TestAPromotedBreachIsHistoryNotAFinding()._guard(monkeypatch, root)

        assert loaded._audit_claims() == 0
        out = capsys.readouterr().out
        assert "none was examined" in out, (
            "an audit with nothing to audit must say so. Reporting it as a pass "
            "makes an absent measurement indistinguishable from a clean one."
        )
        assert "carried anything else" not in out, (
            "the reassurance is about a set that was never examined, and it is "
            "exactly what made the empty case read as a clean one."
        )

    def test_a_real_pending_claim_still_gets_the_positive_result(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """⛔ **The half that stops this becoming a check that never affirms.**
        A clean claim awaiting promotion must still be reported as clean."""
        helper = TestAClaimPushCannotSmuggleASlice
        root = helper._repo(tmp_path)
        helper._run(root, "checkout", "-q", "integration")
        helper._run(root, "checkout", "-q", "-b", "lane")
        (root / "docs").mkdir(parents=True, exist_ok=True)
        (root / "docs" / "BACKLOG.md").write_text("TASK-9 CLAIMED\n")
        helper._run(root, "add", "docs/BACKLOG.md")
        helper._run(root, "commit", "-q", "-m", "Claim TASK-9 — a clean claim")
        helper._push(root, "lane", "integration")
        loaded = TestAPromotedBreachIsHistoryNotAFinding()._guard(monkeypatch, root)

        assert loaded._audit_claims() == 0
        out = capsys.readouterr().out
        assert "1 claim(s) awaiting promotion touch only" in out
        assert "none was examined" not in out
