"""A run records the profile the planner computed, and nothing acts on it.

**[427](../../../docs/architecture/427-impact-based-validation.md) step 2** —
*"record the computed profile in the certification record, still running
everything."* ⛔ **The smallest possible change**: `REQUIRED_GATES` is
unchanged, every gate still executes, and `satisfied` never reads this field.

### Why the field has to exist rather than being derived later

**427 gives step 1 an exit criterion**: *"if the classifier disagrees with
reality even once during step 1, the framework is not ready."*

⚠️ **QE tried to answer that by reconstruction and got it wrong.** Re-deriving
each failing run's profile from `<commit>^..<commit>` reported *"the classifier
disagreed"* on **four of seven** runs. **It had not.** Every candidate was
multi-commit and the last commit was usually a doc-only bug row, so the proxy
classified a diff nobody had certified. Recomputed against the real bases, all
three were `platform` and all three named the gate that caught the defect.

> ⚡ **A measurement taken from the wrong range is indistinguishable from a
> finding.** That is the argument for recording the number at the moment it was
> computed, and it is what this field is.

### The two properties that keep it safe

**It must not change any verdict**, and **it must not break a record written
before it existed** — 112 of those, and `_RunRecord` forbids extra keys.
"""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from tests.certification.record import (
    REQUIRED_GATES,
    CertificationRun,
    Conditions,
    GateResult,
    PromptRelease,
    ScenarioResult,
)
from tests.certification.store import _as_json, _run, _RunRecord


def _conditions() -> Conditions:
    return Conditions(
        rendering_protocol_version=2,
        migration_head="0042",
        scenario_fingerprint="f" * 64,
        prompt_releases=(PromptRelease(reference="p@1", fingerprint="a" * 64, model="m"),),
    )


def _run_record(**over: object) -> CertificationRun:
    base: dict[str, object] = dict(
        commit="a" * 40,
        tree_clean=True,
        certified_at=datetime.now(UTC),
        conditions=_conditions(),
        gates=tuple(GateResult(name=g, passed=True, detail="ok") for g in REQUIRED_GATES),
        scenarios=(ScenarioResult(name="baseline@1", passed=True, detail="190"),),
        coverage=95.4,
        tools=(("pytest", "9.1.1"),),
    )
    base.update(over)
    return CertificationRun(**base)  # type: ignore[arg-type]


class TestTheProfileIsRecordedAndNeverActedOn:
    def test_a_run_carries_the_profile_it_was_given(self) -> None:
        assert _run_record(profile="platform").profile == "platform"

    def test_the_profile_does_not_change_the_verdict(self) -> None:
        """⛔ **Step 2's whole discipline.** A run that satisfies must satisfy
        identically whatever the classifier said about it."""
        for profile in ("", "documentation", "platform", "nonsense-profile"):
            assert _run_record(profile=profile).satisfied is True

    def test_a_failing_run_still_fails_whatever_the_profile_says(self) -> None:
        gates = tuple(
            GateResult(name=g, passed=(g != "smoke"), detail="d") for g in REQUIRED_GATES
        )
        run = _run_record(profile="documentation", gates=gates)

        assert run.satisfied is False
        assert any("smoke" in r for r in run.failures)

    def test_a_documentation_profile_does_not_excuse_a_missing_gate(self) -> None:
        """⚡ **The vacuity defect 427 §1 names, checked directly.** Under a
        *computed* required set a gate may be legitimately absent — and a
        mis-classification then reads as a pass. **Step 2 must not open that
        door**, so `missing_gates` still measures against the full set."""
        run = _run_record(
            profile="documentation",
            gates=(GateResult(name="state-check", passed=True, detail="ok"),),
        )

        assert run.satisfied is False
        assert REQUIRED_GATES - {"state-check"} <= run.missing_gates


class TestARecordWrittenBeforeTheFieldStillReads:
    """112 records exist with no `profile` key, and `_RunRecord` forbids extras."""

    def test_a_json_record_without_a_profile_parses(self) -> None:
        payload = _as_json(_run_record())
        del payload["profile"]

        assert _run(_RunRecord.model_validate(payload)).profile == ""

    def test_an_absent_profile_reads_as_empty_never_as_a_guess(self) -> None:
        """⛔ **Empty means *not recorded*, and must never be inferred.** A
        default of `"platform"` would make every historical record claim a
        measurement nobody took — the fabrication `_report_plan_shortfall`
        already refuses when it prints `NOT MEASURED`."""
        payload = _as_json(_run_record())
        del payload["profile"]

        assert _run(_RunRecord.model_validate(payload)).profile == ""

    def test_a_recorded_profile_survives_the_round_trip(self) -> None:
        payload = _as_json(_run_record(profile="frontend"))

        assert _run(_RunRecord.model_validate(payload)).profile == "frontend"

    def test_an_unknown_key_is_still_refused(self) -> None:
        """Adding an optional field must not have loosened the schema."""
        payload = _as_json(_run_record())
        payload["invented"] = "x"

        with pytest.raises(Exception):
            _RunRecord.model_validate(payload)
