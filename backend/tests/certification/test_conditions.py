"""The conditions are read from the repository, never supplied.

**A condition someone can type is a condition someone can type wrongly**, and a
wrong condition makes a stale certification look current — the exact failure the
design exists to prevent. So every one of them is read mechanically, and these
assert that against the real repository rather than a fixture.
"""

from __future__ import annotations

import ast
import subprocess
from pathlib import Path

import pytest

from modules.ai_platform.domain.rendering import PROMPT_RENDERING_PROTOCOL_VERSION
from tests.certification.conditions import (
    BACKEND_ROOT,
    REQUESTED_PROMPTS,
    commit,
    current,
    migration_head,
    prompt_releases,
    scenario_fingerprint,
    tree_is_clean,
)
from tests.certification.record import CertificationError

#: The package no production code may import. Written as a component rather
#: than a dotted path so a relative import cannot slip past by spelling it
#: differently — `from ..certification import x` resolves to the same package.
EVIDENCE_PACKAGE = "certification"


def imports_certification(source: str) -> bool:
    """**Does this source import the evidence package — not mention it?**

    B-254. The predicate this replaces was `"certification" in source`, which
    answered a different question and answered it wrongly in the direction that
    matters: prose failed the gate.

    A `SyntaxError` is deliberately not caught. A production file that does not
    parse is a larger problem than this check, and swallowing it here would let
    an unparseable file report *no imports* — which is the reassuring answer.
    """
    tree = ast.parse(source)

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            if any(EVIDENCE_PACKAGE in alias.name.split(".") for alias in node.names):
                return True
        elif isinstance(node, ast.ImportFrom):
            # `node.module` is None for `from . import x`; the names carry the
            # package in that form, so both are checked.
            module = node.module or ""
            if EVIDENCE_PACKAGE in module.split("."):
                return True
            if any(alias.name == EVIDENCE_PACKAGE for alias in node.names):
                return True

    return False


class TestEveryConditionIsReadFromTheRepository:
    def test_the_protocol_version_comes_from_the_protocol_module(self) -> None:
        """Not restated. One authoritative representation, so a bump moves the
        condition without anyone remembering to."""
        assert current().rendering_protocol_version == PROMPT_RENDERING_PROTOCOL_VERSION

    def test_the_migration_head_is_read_from_alembic(self) -> None:
        assert migration_head() == current().migration_head
        assert migration_head().strip()

    def test_the_commit_is_a_full_sha(self) -> None:
        assert len(commit()) == 40

    def test_the_tree_state_is_a_fact_about_this_checkout(self) -> None:
        """Asserted as a boolean rather than as a value: this suite must pass on
        a dirty tree during development and on a clean one at certification."""
        assert isinstance(tree_is_clean(), bool)


class TestTheScenarioSetIsHashedNotDeclared:
    def test_the_fingerprint_covers_the_shipped_scenarios(self) -> None:
        assert len(scenario_fingerprint()) == 64

    def test_editing_a_scenario_changes_it(self, tmp_path: Path) -> None:
        """A declared version agrees with every possible edit; a content hash
        does not — the reason `20-provider-simulation.md` gives for datasets."""
        (tmp_path / "one@1.json").write_text('{"steps": []}')
        before = scenario_fingerprint(directory=tmp_path)
        (tmp_path / "one@1.json").write_text('{"steps": [1]}')

        assert scenario_fingerprint(directory=tmp_path) != before

    def test_an_empty_scenario_directory_is_refused(self, tmp_path: Path) -> None:
        """With no scenario there is no customer journey, and a certification
        over no journeys would pass by having nothing to check."""
        with pytest.raises(CertificationError, match="no simulation scenarios"):
            scenario_fingerprint(directory=tmp_path)


class TestThePromptConditionsFollowTheRequestPath:
    def test_the_requested_prompts_are_the_ones_the_pipeline_asks_for(self) -> None:
        """Read from the constants the request path uses, so a version bump
        moves the condition rather than leaving it pinned to a dead artifact."""
        assert {(name, version) for _, name, version in REQUESTED_PROMPTS} == {
            ("research_planning", 2),
            ("research_synthesis", 2),
        }

    def test_every_requested_prompt_records_a_current_release(self) -> None:
        releases = prompt_releases()

        assert {r.reference for r in releases} == {
            "research_planning@2",
            "research_synthesis@2",
        }
        assert all(len(r.fingerprint) == 64 for r in releases)
        assert all(r.model == "llama3.1:8b" for r in releases)

    def test_a_prompt_with_no_current_release_refuses_to_certify(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """**A certification of a platform that would refuse its own prompts
        certifies nothing.** `research_planning@1` still holds its protocol-1
        measurement and earns nothing today, so pointing the condition at it is
        a faithful way to reach that state.
        """
        monkeypatch.setattr(
            "tests.certification.conditions.REQUESTED_PROMPTS",
            (("modules/ai_research_engine/prompts", "research_planning", 1),),
        )

        with pytest.raises(CertificationError, match="no release under rendering protocol"):
            prompt_releases()

    def test_the_release_set_is_held_in_a_stable_order(self) -> None:
        """Two processes recording the same conditions must record the same
        conditions, or a certification would expire because of iteration
        order."""
        assert list(current().prompt_releases) == sorted(current().prompt_releases)


class TestCertificationIsEvidenceAndNeverADependency:
    """**No duplicated ownership.** Certification reads the repository; nothing
    in the repository may read certification.

    import-linter analyses `modules`, `signora_platform` and `apps` only, so a
    production import of this package would pass every contract. Asserted here
    instead, at the level where it can actually be checked.
    """

    def test_no_production_package_imports_certification(self) -> None:
        """**B-254: this said *imports* and checked *mentions*.**

        It was `if "certification" in path.read_text()` — a substring match over
        raw source — so any comment, docstring or string carrying the word
        failed the gate. Lane A hit it writing a doc-comment about B-189 and had
        to spell the package name in two halves to describe the defect at all.

        **The name was a false claim about what the code did**, which is the
        tell `CLAUDE.md` §2 names: the sentence describing the guard was
        stronger than the guard. **Third instance of one class in two days** —
        B-162 narrowed a text scan until it stopped firing, B-252 counted an
        identifier in a comment as a caller, and this counted prose as an
        import.

        **So it parses.** An import is a syntactic fact and `ast` is the thing
        that knows it; a text scan over source can be satisfied by prose or
        defeated by it, and no amount of tightening changes that.
        """
        scanned = [
            path
            for package in ("modules", "signora_platform", "apps", "migrations")
            for path in (BACKEND_ROOT / package).rglob("*.py")
        ]

        # **The walk is asserted, not assumed.** `offenders == []` is also what
        # a misspelt package name produces, and an empty corpus passes this test
        # forever while checking nothing.
        assert len(scanned) > 500, f"only {len(scanned)} file(s) scanned — the walk found nothing"

        offenders = sorted(
            str(path.relative_to(BACKEND_ROOT))
            for path in scanned
            if imports_certification(path.read_text())
        )

        assert offenders == [], (
            f"{offenders} import certification. It is evidence *about* the repository, "
            "produced after the fact; a module that could import it would be a module whose "
            "behaviour depended on whether it had been certified."
        )

    def test_the_import_check_reads_imports_and_not_prose(self) -> None:
        """**B-254's proof, and it is two-sided by construction.**

        ⛔ The first assertion is the one the old check failed: this very file's
        name appears in the string below, and naming something is not importing
        it. ✅ The second is what a narrowed guard must keep catching — B-162's
        lesson, that *narrowing is only safe if you measure what stops firing*.
        """
        assert not imports_certification('X = "tests.certification.conditions"')
        assert not imports_certification("# from tests.certification import record")
        assert not imports_certification('"""Explains tests.certification."""')

        assert imports_certification("from tests.certification import record")
        assert imports_certification("import tests.certification.conditions")
        assert imports_certification("from tests.certification.record import X")

    def test_certification_ships_in_no_wheel(self) -> None:
        """It lives under `tests/` deliberately. A production image carrying the
        machinery that judges it is weight with a new import surface and no
        runtime consumer."""
        config = (BACKEND_ROOT / "pyproject.toml").read_text()

        assert 'packages = ["modules", "signora_platform", "apps"]' in config
        assert "tests" not in config.split("packages = ")[1].split("\n")[0]


class TestTheTreeStateCountsEverythingThatCouldChangeBehaviour:
    """**Found by a surviving mutation.** Narrowing `git status --porcelain` to
    ignore untracked files passed every test, and an untracked file changes
    behaviour exactly as readily as a modified one — a certification that
    ignored it would describe a tree nobody can check out.
    """

    def _repository(self, path: Path) -> None:
        for command in (
            ["git", "init", "-q"],
            ["git", "config", "user.email", "certify@signora.test"],
            ["git", "config", "user.name", "certify"],
        ):
            subprocess.run(command, cwd=path, check=True, capture_output=True)
        (path / "committed.txt").write_text("recorded\n")
        subprocess.run(["git", "add", "-A"], cwd=path, check=True, capture_output=True)
        subprocess.run(
            ["git", "commit", "-q", "-m", "initial"], cwd=path, check=True, capture_output=True
        )

    def test_a_committed_tree_is_clean(self, tmp_path: Path) -> None:
        self._repository(tmp_path)

        assert tree_is_clean(repository_root=tmp_path)

    def test_a_modified_file_makes_it_dirty(self, tmp_path: Path) -> None:
        self._repository(tmp_path)
        (tmp_path / "committed.txt").write_text("changed\n")

        assert not tree_is_clean(repository_root=tmp_path)

    def test_an_untracked_file_makes_it_dirty_too(self, tmp_path: Path) -> None:
        self._repository(tmp_path)
        (tmp_path / "new.py").write_text("SECRET = 1\n")

        assert not tree_is_clean(repository_root=tmp_path)
