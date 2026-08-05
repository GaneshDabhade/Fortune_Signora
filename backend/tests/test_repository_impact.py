"""**A classifier that under-reports is worse than none, and this one reports only.**

TASK-414 — step 1 of `docs/architecture/427-impact-based-validation.md`. The
analysis is emitted and **nothing is skipped**: `REQUIRED_GATES` is still a
frozenset of six, `make certify` still has no options, every gate still runs.

**So what is under test is not what runs — it is whether the classifier could be
trusted later.** Step 1's whole value is that a wrong answer is discovered while
everything is still executing, which costs nothing. These tests fix the three
properties that would make the eventual step 3 unsafe:

**an unknown path must escalate** · **a gate path must escalate unconditionally**
· **no computed profile may omit a Security Invariant.**

The first two are the `missing_gates` rule applied to classification rather than
to execution: *absence is not a pass*. The repository has been bitten by that
exact shape nine times in shipped CHECK constraints
(`36-empty-array-checks.md`), and once already in this file's own history —
B-014, a gate fix classified as a Closeout because `infra/` was not excluded.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from types import ModuleType

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture(scope="module")
def guard() -> ModuleType:
    spec = importlib.util.spec_from_file_location(
        "certification_guard", REPO_ROOT / "infra" / "certification-guard.py"
    )
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules["certification_guard"] = module
    spec.loader.exec_module(module)
    return module


@pytest.mark.parametrize(
    "path",
    [
        "zz_brand_new_directory/thing.py",
        "backend/something_nobody_planned/x.py",
        "a_file_at_the_root.py",
    ],
)
def test_an_unrecognised_path_escalates_to_platform(guard: ModuleType, path: str) -> None:
    """**A new directory must not silently reduce validation.**

    This is how the matrix goes wrong without anybody editing it: somebody adds
    a directory, the classifier does not recognise it, and it contributes
    nothing to the computed set. The failure is invisible because it looks like
    a smaller change.
    """
    assert guard._impacts([path]) == {"platform": {path}}


@pytest.mark.parametrize(
    "path",
    [
        "infra/smoke.sh",
        "infra/docker-compose.yml",
        "Makefile",
        "backend/tests/certification/conditions.py",
    ],
)
def test_a_gate_path_escalates_unconditionally(guard: ModuleType, path: str) -> None:
    """**The classifier cannot be trusted to classify changes to itself.**

    `smoke.sh`, the compose files and the certification package decide whether a
    gate passes, so changing one changes what certification *means*. B-014 is
    what it cost when this was not enforced: two commits calling themselves
    Closeouts while editing the instruments.
    """
    assert "platform" in guard._impacts([path])


def test_no_executable_profile_omits_a_security_invariant(guard: ModuleType) -> None:
    """**`CLAUDE.md` §11 — the Security Invariants are never computed away.**

    *"Claude must never delete, skip, or weaken one of these tests… a failure
    there means a guarantee the architecture depends on has stopped holding."* A
    framework that could reason its way out of them would have inverted their
    purpose.

    Documentation is the one profile without them, and correctly: a docs-only
    change does not open a certification cycle at all.
    """
    for impact, gates in guard.PROFILE_GATES.items():
        if impact == "documentation":
            continue
        assert guard.ALWAYS <= gates, f"{impact} omits {sorted(guard.ALWAYS - gates)}"


def test_profiles_compose_as_a_union_never_an_intersection(guard: ModuleType) -> None:
    """**Union, never intersection** — the single easiest bug to write here.

    A slice touching the frontend and a migration must get both sets. Taking the
    intersection would compute a *smaller* profile for a *larger* change, which
    is the one direction that cannot be allowed to be wrong.
    """
    _, both = guard._profile({"frontend", "persistence"})
    _, frontend = guard._profile({"frontend"})
    _, persistence = guard._profile({"persistence"})
    assert frontend <= both and persistence <= both
    assert both == frontend | persistence


def test_an_empty_change_is_documentation_and_not_platform(guard: ModuleType) -> None:
    """The one place escalation would be wrong.

    No paths means no change, and reporting `platform` there would make the
    analysis noise on every empty range. **Escalation protects against unknown
    paths, not against the absence of any.**
    """
    name, gates = guard._profile(set())
    assert name == "documentation"
    assert "dr" not in gates


def test_a_module_change_names_the_module_impact(guard: ModuleType) -> None:
    """`backend/modules/<m>/**` is a module impact, whatever else it matches."""
    assert "module" in guard._impacts(["backend/modules/signal_engine/domain/rule.py"])


def test_a_public_contract_change_is_more_than_a_module_change(guard: ModuleType) -> None:
    """`public/` is the boundary other modules compile against.

    A change there carries both impacts, and the union is what makes the second
    one load-bearing — `import-linter` and `runtime-composition` come from the
    contract half, not the module half.
    """
    found = guard._impacts(["backend/modules/commercial_profile/public/reader.py"])
    assert {"module", "contract"} <= set(found)


def test_the_analysis_skips_nothing_today(guard: ModuleType) -> None:
    """**Step 1 reports and applies nothing**, and that is a property worth pinning.

    `REQUIRED_GATES` remains the frozenset of six the certification record
    enforces. If a later step makes it computed, this test is the one that
    should fail first and deliberately.
    Written first as ``"REQUIRED_GATES" not in source`` and immediately wrong:
    the name appears in this step's own explanation of what it does not do.
    **That is B-101 exactly** — counting by substring put nine bug rows in two
    lifecycle states at once, because a cell saying *"`FIXED` — `VERIFIED` is
    QE's to set"* contains both words. **A mention is not a definition**, so the
    test asks whether the name is *bound* here.
    """
    import re

    source = (REPO_ROOT / "infra" / "certification-guard.py").read_text()
    bindings = re.findall(r"^REQUIRED_GATES\s*[:=]", source, re.M)
    assert not bindings, (
        "certification-guard.py must not define the required gate set at step 1 — "
        "the analysis reports, and ADR-0032 remains the only place it is stated"
    )


@pytest.mark.parametrize("path", ["CLAUDE.md", "README.md", "PROJECT_STATUS.md", "docs/BACKLOG.md"])
def test_the_two_classifiers_in_this_file_agree(guard: ModuleType, path: str) -> None:
    """**The reason this analysis extends `certification-guard.py` instead of
    living in a new file is that two classifiers eventually disagree** — and the
    unmaintained one is the one that would decide what to skip.

    They disagreed on the very first real run. `CLAUDE.md` is not under `docs/`,
    so the impact rules escalated it to `platform` while `_is_closeout`, three
    hundred lines above, treated it as non-executable. **The rule is now shared
    rather than restated**, and this test is what keeps it shared.
    """
    assert path.startswith(guard.CLOSEOUT_PATHS) and path.endswith(guard.CLOSEOUT_SUFFIXES)
    assert sorted(guard._impacts([path])) == ["documentation"]


# ── Phase 1: skip-note enforcement ───────────────────────────────────────────
# `docs/architecture/434-execution-queue-governance-package.md`. §20e has always
# required that a lane skipping a higher `READY` task say why, and nothing
# checked it. These fix the two properties that make the check trustworthy: it
# must be able to fire, and it must never fire on history it cannot judge.


def test_the_skip_check_can_actually_fire(
    guard: ModuleType, monkeypatch: pytest.MonkeyPatch
) -> None:
    """**A guard that cannot fail is documentation pretending to be code** (§2).

    The first live run reported nothing, which is the correct answer today and
    indistinguishable from a check that is wired up wrong.
    """
    registry = '[signal_engine]\ncurrent_owner = "Lane A"\n'
    backlog = (
        "### TASK-100 · higher\n| **Status** | `READY` |\n| **Module** | `signal_engine` |\n"
        "### TASK-200 · lower\n| **Status** | `READY` |\n| **Module** | `signal_engine` |\n"
    )
    monkeypatch.setattr(
        guard, "_git",
        lambda *a: registry if "modules.toml" in a[-1] else backlog if "BACKLOG" in a[-1] else "",
    )
    assert guard._eligible_above("deadbee", "Lane A", "TASK-200") == ["TASK-100"]


def test_a_skip_is_not_reported_when_the_task_belongs_to_another_lane(
    guard: ModuleType, monkeypatch: pytest.MonkeyPatch
) -> None:
    """**Ownership is joined from the registry, not assumed.**

    A lane cannot skip what it was never allowed to take, and reporting that
    would be the accusation `_eligible_above` exists to avoid.
    """
    registry = '[signal_engine]\ncurrent_owner = "Lane B"\n'
    backlog = "### TASK-100 · higher\n| **Status** | `READY` |\n| **Module** | `signal_engine` |\n"
    monkeypatch.setattr(
        guard, "_git",
        lambda *a: registry if "modules.toml" in a[-1] else backlog if "BACKLOG" in a[-1] else "",
    )
    assert guard._eligible_above("deadbee", "Lane A", "TASK-200") == []


def test_a_claim_older_than_the_registry_yields_no_opinion(
    guard: ModuleType, monkeypatch: pytest.MonkeyPatch
) -> None:
    """**A record of what was true then must not be re-scored against now** (§2).

    The first implementation read the working tree and accused four claims from
    2026-08-02 of skipping tasks that did not exist when they were made. Reading
    at the commit makes history self-limiting: `modules.toml` did not exist
    before 2026-08-04, so an older claim is simply not judged.
    """
    monkeypatch.setattr(guard, "_git", lambda *a: "")
    assert guard._eligible_above("ancient", "Lane A", "TASK-002") == []
