"""Reading the repository's conditions as they are **now**.

`satisfied` asks whether a run went well. This supplies the other half — what
the repository looks like today — so `certifies()` can decide whether a past
measurement still describes it.

**Everything here is read mechanically.** No value is passed in by a human and
none is defaulted: a condition someone could type is a condition someone could
type wrongly, and a wrong condition makes a stale certification look current.
That is the failure mode the whole design exists to prevent, so the rule is
absolute — **if it cannot be read from the repository, it is not a condition.**

The prompt releases are read from the versions **the pipeline actually
requests**, not from every prompt on disk. A certification should expire when a
prompt the product uses changes; it should not expire because a superseded `@1`
gained a recorded refusal.
"""

from __future__ import annotations

import re
import subprocess
from pathlib import Path

from modules.ai_platform.domain.rendering import PROMPT_RENDERING_PROTOCOL_VERSION
from modules.ai_platform.infrastructure.prompt_loader import load_prompt_registry
from modules.ai_research_engine.application.plan import PROMPT_NAME, PROMPT_VERSION
from modules.ai_research_engine.application.research import SYNTHESIS_PROMPT, SYNTHESIS_VERSION
from tests.certification.record import (
    CertificationError,
    Conditions,
    PromptRelease,
    fingerprint_of,
)
from tests.certification.store import REPOSITORY_ROOT

BACKEND_ROOT = REPOSITORY_ROOT / "backend"
SCENARIO_DIR = BACKEND_ROOT / "signora_platform" / "simulation" / "scenarios"

#: The prompts the pipeline requests, named as `(directory, name, version)`.
#:
#: Read from the constants the request path uses rather than restated, so a
#: version bump moves the condition automatically. M8's narration and M9's
#: reasoning are deliberately absent: both are awaiting re-evaluation under
#: rendering protocol 2, and a condition naming a prompt with no current release
#: would make certification impossible rather than informative. They are added
#: by ADR-0031 Step F, which is what re-releases them.
REQUESTED_PROMPTS: tuple[tuple[str, str, int], ...] = (
    ("modules/ai_research_engine/prompts", PROMPT_NAME, PROMPT_VERSION),
    ("modules/ai_research_engine/prompts", SYNTHESIS_PROMPT, SYNTHESIS_VERSION),
)


def current(*, backend_root: Path = BACKEND_ROOT) -> Conditions:
    """The conditions in force right now."""
    return Conditions(
        rendering_protocol_version=PROMPT_RENDERING_PROTOCOL_VERSION,
        migration_head=migration_head(backend_root=backend_root),
        scenario_fingerprint=scenario_fingerprint(),
        prompt_releases=prompt_releases(backend_root=backend_root),
    )


def prompt_releases(*, backend_root: Path = BACKEND_ROOT) -> tuple[PromptRelease, ...]:
    """Each requested prompt, with the release standing behind it.

    Refuses a prompt with no current release rather than recording it as
    unreleased. **A certification cannot describe a pipeline that could not
    run** — and an empty or partial release set would let the condition hold
    vacuously, which is exactly how a stale certification survives.
    """
    releases: list[PromptRelease] = []
    for directory, name, version in REQUESTED_PROMPTS:
        prompt = load_prompt_registry(backend_root / directory).get(name, version)
        earning = sorted({e.model for e in prompt.evaluations if e.earns_release})
        if not earning:
            raise CertificationError(
                f"prompt {prompt.reference} has no release under rendering protocol "
                f"{PROMPT_RENDERING_PROTOCOL_VERSION}, so the pipeline that requests it "
                "cannot run. Re-evaluate before certifying — a certification of a platform "
                "that would refuse its own prompts would certify nothing."
            )
        releases.extend(
            PromptRelease(reference=prompt.reference, fingerprint=prompt.fingerprint, model=model)
            for model in earning
        )
    return tuple(releases)


def scenario_fingerprint(*, directory: Path = SCENARIO_DIR) -> str:
    """A hash over every simulation scenario.

    The scenarios are the customer journeys certification exercises, so editing
    one changes the experiment. Hashed as a set rather than versioned by hand
    for the reason `20-provider-simulation.md` gives about datasets: a declared
    version agrees with every possible edit, and a content hash does not.
    """
    files = tuple(sorted(directory.glob("*.json")))
    if not files:
        raise CertificationError(
            f"no simulation scenarios found in {directory}. Certification exercises customer "
            "journeys; with no scenario there is no journey and nothing to certify."
        )
    return fingerprint_of(tuple((path.name, path.read_bytes()) for path in files))


def migration_head(*, backend_root: Path = BACKEND_ROOT) -> str:
    """The schema revision the repository declares, read from Alembic itself.

    `alembic heads` rather than a directory listing: a repository with two heads
    is one where a migration was branched and not merged, and it reports that
    instead of silently picking one.
    """
    result = subprocess.run(
        ["uv", "run", "alembic", "heads"],
        cwd=backend_root,
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        raise CertificationError(f"could not read the migration head: {result.stderr.strip()}")
    heads = [line.split(" ")[0] for line in result.stdout.splitlines() if line.strip()]
    if len(heads) != 1:
        raise CertificationError(
            f"the repository declares {len(heads)} migration heads ({heads}). A certification "
            "must name exactly one schema, and a branched head means two are possible."
        )
    return heads[0]


def commit(*, repository_root: Path = REPOSITORY_ROOT) -> str:
    return _git(["rev-parse", "HEAD"], repository_root)


def tree_is_clean(*, repository_root: Path = REPOSITORY_ROOT) -> bool:
    """**Whether the tree certified was actually stored.**

    `--porcelain` covers staged, unstaged and untracked alike: an untracked file
    can change behaviour just as easily as a modified one, and a certification
    that ignored it would describe a tree nobody can check out.
    """
    return _git(["status", "--porcelain"], repository_root) == ""


def dirty_paths(*, repository_root: Path = REPOSITORY_ROOT) -> tuple[str, ...]:
    """**What is dirty**, so the refusal can say so — [B-1038](../../../docs/BUGS.md).

    ⛔ **A failed run writes its own record.** `__main__.py` calls `append()`
    unconditionally, so a run that fails a gate still modifies
    `certification/manifest.json` and writes a report. **The NEXT run then
    refuses with *"the working tree was dirty"* — and the operator reads that
    as a statement about their own uncommitted work.**

    ⚡ **It is a statement about the previous run**, and until now nothing said
    so. The `git checkout --` that clears it is named in a comment inside this
    package and in no runbook.

    ✅ **This changes no verdict.** `tree_is_clean` is unchanged, the run still
    refuses, and `tree_clean` is still recorded false. **Only the diagnostic
    learns to name the cause.**
    """
    # ⚠️ **Not `line[3:]`, and the test is what caught it.** Porcelain v1 is
    # `XY path` with a two-character status — but `_git` **strips the whole
    # output**, so the leading space of an unstaged ` M path` is gone by the
    # time this sees it and a fixed offset eats a character of the path
    # (`ertification/manifest.json`). **Strip the status field, whatever width
    # it arrived at.**
    status = _git(["status", "--porcelain"], repository_root)
    return tuple(
        re.sub(r"^\S{1,2}\s+", "", line.strip())
        for line in status.splitlines()
        if line.strip()
    )


def _git(arguments: list[str], repository_root: Path) -> str:
    result = subprocess.run(
        ["git", *arguments], cwd=repository_root, capture_output=True, text=True, check=False
    )
    if result.returncode != 0:
        raise CertificationError(f"git {' '.join(arguments)} failed: {result.stderr.strip()}")
    return result.stdout.strip()
