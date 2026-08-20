"""What a certification run recorded, and what the repository derives from it.

**Every gate this repository has is ephemeral.** `pytest`, `mypy`, `lint-imports`,
the Security Invariants and `make smoke` all pass in a terminal and leave nothing
behind, so nothing can say that commit *X* satisfied guarantee *Y* on date *Z*.
`PROJECT_STATUS.md` has been carrying hand-copied numbers describing runs nobody
can point to — a claim, not a measurement.

This module is the same correction M9.5 made one level down, applied to the
platform (ADR-0032). The shape is deliberately the one prompts already proved:

    PromptVersion → Evaluation → passed        → earns_release
    commit        → CertificationRun → satisfied → is_certified

**Facts are recorded; verdicts are derived.** `PromptVersion` has no `status`
field because *"a declared status could say released while no evaluation
supported it — a field that can lie about the thing beside it"*, and a
`CERTIFIED.md` a human edits would be that field at repository scale. So there
is no `outcome` here, and nothing anywhere can mark a version certified.

---

### Two fields deliberately absent

**An overall outcome.** It is `satisfied`, derived below from the gates and
scenarios. Recording it would create a second representation of one fact, and
the two would eventually disagree in the direction nobody wanted to look at.

**A mutation-testing identifier.** Mutation testing here is a manual discipline
with no mechanical output, so the field could only ever be filled in by hand —
which is the editable status field arriving through a side door. It is added the
day a mutation runner produces a result something else can read, and not before.

### And one that carries the whole weight

`tree_clean`. **A certification of uncommitted work certifies nothing anyone can
retrieve**, because the tree it describes was never stored. It is checked in
`satisfied` rather than merely recorded.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime
from typing import Final

#: The gates a run must have executed before `satisfied` can be true.
#:
#: **Named rather than counted, because an omitted gate is invisible to
#: `all()`.** A run recording no gates at all would otherwise satisfy "every
#: gate passed" vacuously — the same defect `36-empty-array-checks.md` found in
#: nine shipped CHECK constraints, where `array_length(x, 1) >= 1` cannot reject
#: the empty array.
#: ⚡ **`frontend-suite` and `eslint` added 2026-08-15 on the product owner's
#: ruling** ([B-122](../../../docs/BUGS.md)). **A CERTIFIED commit reached `main`
#: with a deterministically failing frontend test** — `385970bf`,
#: `auth-mode.test.ts`, `expected 'production' to be 'development'` — and
#: neither gate had run in any of the 228 recorded runs. ⛔ **`tsc` passed
#: throughout and could not have caught it: a type-checker cannot see a wrong
#: assertion.**
#:
#: ⚠️ **Widening re-judges history, and that effect is accepted rather than
#: overlooked.** `satisfied` is derived and never stored, so records made under
#: the narrower set now re-read as unsatisfied. **They are not retrospectively
#: fraudulent** — each recorded truthfully what it ran, under the gate set that
#: existed then. 📁 **The precedent is `tsc`'s own addition at `4e43da17`**,
#: which did exactly this to 41 earlier runs without anybody rewriting a record.
REQUIRED_GATES: Final = frozenset(
    {
        "pytest",
        "mypy",
        "tsc",
        "import-linter",
        "security-invariants",
        "smoke",
        "frontend-suite",
        "eslint",
    }
)

#: The coverage floor, mirroring `fail_under` in `pyproject.toml`.
#:
#: Duplicated deliberately and asserted equal by test rather than imported: the
#: pytest gate enforces it during the run, and this re-derives it when a record
#: is *read back*, possibly by a reader who no longer has that configuration.
MINIMUM_COVERAGE: Final = 95.0

#: The record format. Bumped when a field's meaning changes, so that a reader
#: can tell a missing field from one that never existed — the same reason an
#: evaluation names its dataset and rubric version.
RECORD_VERSION: Final = 1


class CertificationError(ValueError):
    """A certification record could not be built or read as declared."""


@dataclass(frozen=True, slots=True, order=True)
class GateResult:
    """One lower gate, and what it reported.

    `detail` is the gate's own summary — *"1763 passed"*, *"29 kept, 0 broken"* —
    kept as text because it is the gate's language, not this module's, and
    parsing it into fields here would make certification the second author of
    every gate's output.
    """

    name: str
    passed: bool
    detail: str

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise CertificationError("a gate result must name the gate that produced it.")
        if not self.detail.strip():
            raise CertificationError(
                f"gate '{self.name}' recorded no detail. A result nobody can read back is a "
                "line in a manifest that proves only that something ran."
            )


@dataclass(frozen=True, slots=True, order=True)
class ScenarioResult:
    """One certification scenario, and whether the customer's journey held."""

    name: str
    passed: bool
    detail: str

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise CertificationError("a scenario result must name its scenario.")


@dataclass(frozen=True, slots=True, order=True)
class PromptRelease:
    """One prompt the pipeline requests, and the release standing behind it.

    **A condition, not a result.** If a prompt is re-released, re-authored or
    re-measured, a certification taken against the previous one no longer
    describes the system — which is what `Conditions` compares.
    """

    reference: str
    fingerprint: str
    model: str

    def __post_init__(self) -> None:
        if len(self.fingerprint) != 64:
            raise CertificationError(
                f"prompt {self.reference} recorded a fingerprint of "
                f"{len(self.fingerprint)} characters; a SHA-256 is 64. A condition that "
                "cannot be compared cannot invalidate anything."
            )


@dataclass(frozen=True, slots=True)
class Conditions:
    """The state of the repository a measurement was taken under.

    **The half that makes a record expire.** `satisfied` says the run went well;
    this says whether it still describes the system now. Exactly the distinction
    `Evaluation.passed` and `earns_release` draw, and for the same reason: a
    measurement whose conditions have moved is still true and no longer
    applicable.
    """

    #: The Prompt Rendering Protocol in force. Bumping it changed what every
    #: model is shown (ADR-0031), so it changes what any run measured.
    rendering_protocol_version: int
    #: The schema the run executed against.
    migration_head: str
    #: SHA-256 over the simulation scenarios, so an edited scenario is a
    #: different experiment rather than a quiet one.
    scenario_fingerprint: str
    #: Held sorted, so two processes recording the same conditions in different
    #: order record the same conditions.
    prompt_releases: tuple[PromptRelease, ...]

    def __post_init__(self) -> None:
        if self.rendering_protocol_version < 1:
            raise CertificationError("rendering protocol versions start at 1.")
        if not self.migration_head.strip():
            raise CertificationError(
                "a run must name the migration head it executed against; a certification of "
                "an unknown schema is not reproducible."
            )
        if not self.prompt_releases:
            raise CertificationError(
                "a run must record the prompt releases in force. An empty set would make "
                "every future prompt change invisible to certification — the condition would "
                "hold vacuously, which is how a stale certification survives."
            )
        object.__setattr__(self, "prompt_releases", tuple(sorted(self.prompt_releases)))


@dataclass(frozen=True, slots=True)
class CertificationRun:
    """One certification execution. **Facts only.**"""

    commit: str
    tree_clean: bool
    certified_at: datetime
    conditions: Conditions
    gates: tuple[GateResult, ...]
    scenarios: tuple[ScenarioResult, ...]
    coverage: float
    #: Sorted `(tool, version)` pairs — the toolchain a reader would need to
    #: reproduce this. Small on purpose: a full lockfile belongs in the lockfile.
    tools: tuple[tuple[str, str], ...]
    #: The impact profile the Validation Planner computed for this run's diff —
    #: **[427](../../../docs/architecture/427-impact-based-validation.md) step 2,
    #: and it changes nothing about what runs.**
    #:
    #: ⛔ **Recorded, never applied.** `REQUIRED_GATES` is unchanged and every
    #: gate still executes. What this buys is that step 1's exit question —
    #: *"did the classifier ever disagree with reality?"* — becomes answerable
    #: **from the record** instead of reconstructed afterwards.
    #:
    #: ⚠️ **And reconstruction is why this field exists.** QE tried to answer it
    #: by re-deriving each failing run's profile from `<commit>^..<commit>`, and
    #: got *"the classifier disagreed"* four times out of seven. **It had not.**
    #: Every candidate was multi-commit and the last commit was usually a
    #: doc-only bug row, so the proxy classified the wrong diff. Recomputed
    #: against the real bases, all three were `platform` and all three named the
    #: gate that caught the defect. **A measurement taken from the wrong range is
    #: indistinguishable from a finding**, which is the whole argument for
    #: recording the number at the moment it was computed.
    #:
    #: **Empty on records written before this field existed**, and `satisfied`
    #: does not read it — an older record is judged by exactly the rule it was
    #: judged by then.
    profile: str = ""
    #: The gates the Validation Planner required for this run's diff that this
    #: record does **not** contain — **B-131, and the reason this field exists
    #: rather than a print statement.**
    #:
    #: ⛔ **Until now the shortfall was reported to stdout and nowhere else.**
    #: On 2026-08-19 a run announced *"9 planned gate(s) NOT recorded"*,
    #: including `migration-reversibility` and `dr` — **the two gates
    #: `REPOSITORY_RELEASE_CHECKLIST.md` makes mandatory** — and the record it
    #: wrote carried no trace of that. **A reader of the manifest could not tell
    #: a gate that was never planned from one that was planned and skipped.**
    #:
    #: ⚡ **With this field the four states are distinguishable from the record
    #: alone**, which is the whole requirement:
    #:
    #: | State | How it reads |
    #: |---|---|
    #: | **passed** | a `GateResult` with `passed=True` |
    #: | **failed or refused** | a `GateResult` with `passed=False` |
    #: | **planned, not executed** | named here |
    #: | **not applicable** | in neither — the planner did not require it |
    #: | **plan not computable** | `profile` is empty, so this is meaningless |
    #:
    #: ⛔ **Recorded, never applied** — exactly as `profile` is. `satisfied`
    #: does not read it and `REQUIRED_GATES` is unchanged, because widening what
    #: certification *requires* is an ADR-0032 decision and not one a run may
    #: take about itself. **What this buys is that a missing gate can no longer
    #: disappear**, not that it now blocks.
    #:
    #: ⚠️ **Empty on every record written before this field existed**, and
    #: indistinguishable there from *"nothing was missing"*. 📁 `profile` has the
    #: same property for the same reason: an older record is read by exactly the
    #: rule it was written under.
    planned_not_recorded: tuple[str, ...] = ()
    record_version: int = RECORD_VERSION

    def __post_init__(self) -> None:
        overlap = sorted({g.name for g in self.gates} & set(self.planned_not_recorded))
        if overlap:
            raise CertificationError(
                f"gate(s) {', '.join(overlap)} are recorded as executed AND as planned-but-not-"
                "recorded. A gate is one or the other, and a record that says both describes no "
                "run at all."
            )
        if len(self.commit) != 40:
            raise CertificationError(
                f"'{self.commit}' is not a full commit SHA. An abbreviated one is ambiguous "
                "in a repository nobody has pruned yet, and a record must name exactly one tree."
            )
        if self.certified_at.tzinfo is None:
            raise CertificationError(
                "certified_at has no timezone. A naive timestamp is a different instant on "
                "every machine that reads it."
            )
        if not 0.0 <= self.coverage <= 100.0:
            raise CertificationError(f"coverage of {self.coverage} is not a percentage.")
        if not self.scenarios:
            raise CertificationError(
                "a run recorded no scenarios. 'every scenario passed' is vacuously true of "
                "none, so a run that executed nothing would otherwise certify everything."
            )
        if self.record_version < 1:
            raise CertificationError("record versions start at 1.")
        object.__setattr__(self, "gates", tuple(sorted(self.gates)))
        object.__setattr__(self, "scenarios", tuple(sorted(self.scenarios)))
        object.__setattr__(self, "tools", tuple(sorted(self.tools)))

    @property
    def missing_gates(self) -> frozenset[str]:
        """Required gates this run never executed. **Absence is not a pass.**"""
        return REQUIRED_GATES - {gate.name for gate in self.gates}

    @property
    def failures(self) -> tuple[str, ...]:
        """Every reason this run does not satisfy certification, in a stable
        order — all of them, not the first.

        The same choice `GroundingReport` makes: reporting one failure sends
        whoever investigates back for a second round.
        """
        reasons: list[str] = []
        if not self.tree_clean:
            reasons.append("the working tree was dirty, so the tree certified was never stored")
        for name in sorted(self.missing_gates):
            reasons.append(f"required gate '{name}' did not run")
        for gate in self.gates:
            if not gate.passed:
                reasons.append(f"gate '{gate.name}' failed: {gate.detail}")
        for scenario in self.scenarios:
            if not scenario.passed:
                reasons.append(f"scenario '{scenario.name}' failed: {scenario.detail}")
        if self.coverage < MINIMUM_COVERAGE:
            reasons.append(f"coverage {self.coverage:.2f}% is below {MINIMUM_COVERAGE}%")
        return tuple(reasons)

    @property
    def satisfied(self) -> bool:
        """Whether this run went well. **A fact about the past**, true forever.

        Never stored — derived from the facts above, so a change to what
        certification *means* re-reads history correctly rather than leaving a
        stratum of records judged by a rule nobody remembers.
        """
        return not self.failures

    def is_current(self, conditions: Conditions) -> bool:
        """Whether this run still describes the repository as it is now."""
        return self.conditions == conditions

    def certifies(self, conditions: Conditions) -> bool:
        """Both halves. **The only question a release should ask.**"""
        return self.satisfied and self.is_current(conditions)


def certified(
    runs: tuple[CertificationRun, ...], conditions: Conditions
) -> CertificationRun | None:
    """The most recent run that certifies these conditions, or nothing.

    Returning the run rather than a boolean, so a caller reporting *"certified"*
    can name the evidence. A verdict nobody can trace back to a measurement is
    the declaration this whole design exists to refuse.
    """
    qualifying = [run for run in runs if run.certifies(conditions)]
    return max(qualifying, key=lambda run: run.certified_at) if qualifying else None


def fingerprint_of(paths: tuple[tuple[str, bytes], ...]) -> str:
    """A stable hash over named file contents — used for the scenario set.

    Sorted by name and length-delimited, so neither the order a caller walked
    the directory in nor a rename that shifts bytes between files can produce a
    collision.
    """
    digest = hashlib.sha256()
    for name, content in sorted(paths):
        digest.update(f"{len(name)}:{name}:{len(content)}:".encode())
        digest.update(content)
    return digest.hexdigest()


def canonical_json(document: object) -> str:
    """One byte sequence per record.

    Certification evidence is committed, so a record that serialised differently
    on two machines would show as a diff nobody made — and a reviewer who learns
    to ignore that diff is a reviewer who will ignore the next one.
    """
    return json.dumps(document, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
