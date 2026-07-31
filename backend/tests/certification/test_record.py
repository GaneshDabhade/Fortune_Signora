"""What a certification record must guarantee.

The design goal in one line: **facts are recorded, verdicts are derived, and
nothing can declare itself certified.** These assert it from both directions —
a run that should certify does, and every way of certifying something that did
not happen is refused.

Nothing here runs a certification; it exercises the record. The suite that
*produces* records is `make certify`.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from tests.certification.record import (
    MINIMUM_COVERAGE,
    REQUIRED_GATES,
    CertificationError,
    CertificationRun,
    Conditions,
    GateResult,
    PromptRelease,
    ScenarioResult,
    canonical_json,
    certified,
    fingerprint_of,
)
from tests.certification.store import append, load, render

NOW = datetime(2026, 7, 31, 12, 0, tzinfo=UTC)
COMMIT = "a" * 40


def _conditions(**overrides: object) -> Conditions:
    defaults: dict[str, object] = {
        "rendering_protocol_version": 2,
        "migration_head": "0018",
        "scenario_fingerprint": "f" * 64,
        "prompt_releases": (
            PromptRelease(
                reference="research_planning@2", fingerprint="1" * 64, model="llama3.1:8b"
            ),
        ),
    }
    return Conditions(**{**defaults, **overrides})  # type: ignore[arg-type]


def _run(**overrides: object) -> CertificationRun:
    defaults: dict[str, object] = {
        "commit": COMMIT,
        "tree_clean": True,
        "certified_at": NOW,
        "conditions": _conditions(),
        "gates": tuple(
            GateResult(name=name, passed=True, detail="ok") for name in sorted(REQUIRED_GATES)
        ),
        "scenarios": (ScenarioResult(name="research-lifecycle", passed=True, detail="ok"),),
        "coverage": 95.85,
        "tools": (("python", "3.13.1"),),
    }
    return CertificationRun(**{**defaults, **overrides})  # type: ignore[arg-type]


class TestAVerdictIsDerivedAndNeverStored:
    def test_a_complete_run_satisfies_certification(self) -> None:
        run = _run()

        assert run.satisfied
        assert run.failures == ()
        assert run.certifies(_conditions())

    def test_there_is_nowhere_to_write_an_outcome(self) -> None:
        """**The `status` field `PromptVersion` refused, refused again.**

        The field list this record was designed from included an "overall
        outcome". It is derived from the gates and scenarios, so storing it
        would be a second representation of one fact — and the copy that can
        disagree is always the one somebody edits.
        """
        with pytest.raises(TypeError):
            _run(outcome="certified")

        assert not hasattr(_run(), "outcome")

    def test_a_failed_gate_is_still_recorded_and_simply_does_not_certify(self) -> None:
        """A failing run belongs in the manifest. One holding only successes
        claims a platform that never failed to certify."""
        run = _run(
            gates=tuple(
                GateResult(name=name, passed=name != "mypy", detail="3 errors")
                for name in sorted(REQUIRED_GATES)
            )
        )

        assert not run.satisfied
        assert any("mypy" in reason for reason in run.failures)

    def test_every_reason_is_reported_not_just_the_first(self) -> None:
        """The choice `GroundingReport` makes: one failure at a time sends
        whoever investigates back for a second round."""
        run = _run(tree_clean=False, coverage=10.0)

        assert len(run.failures) == 2
        assert any("dirty" in reason for reason in run.failures)
        assert any("coverage" in reason for reason in run.failures)


class TestAbsenceIsNeverAPass:
    def test_a_run_that_skipped_a_gate_does_not_certify(self) -> None:
        """**`all()` is vacuously true of nothing.** Without a required set, a
        run recording no gates would satisfy 'every gate passed' — the defect
        `36-empty-array-checks.md` found in nine shipped CHECK constraints."""
        run = _run(gates=(GateResult(name="pytest", passed=True, detail="ok"),))

        assert not run.satisfied
        assert run.missing_gates == REQUIRED_GATES - {"pytest"}
        assert all(
            any(name in reason for reason in run.failures) for name in run.missing_gates
        )

    def test_a_run_with_no_scenarios_is_refused_at_construction(self) -> None:
        with pytest.raises(CertificationError, match="no scenarios"):
            _run(scenarios=())

    def test_a_failed_scenario_never_certifies(self) -> None:
        """**The whole point of certification, and it had no test.** Found by a
        surviving mutation: every gate could pass while the customer journey
        failed, and the run would still have certified.
        """
        run = _run(
            scenarios=(
                ScenarioResult(name="research-lifecycle", passed=False, detail="brief ungrounded"),
            )
        )

        assert not run.satisfied
        assert not run.certifies(_conditions())
        assert any("research-lifecycle" in reason for reason in run.failures)

    def test_one_failed_scenario_among_several_is_enough(self) -> None:
        run = _run(
            scenarios=(
                ScenarioResult(name="baseline", passed=True, detail="ok"),
                ScenarioResult(name="displacement", passed=False, detail="no opportunity"),
            )
        )

        assert not run.satisfied
        assert any("displacement" in reason for reason in run.failures)

    def test_conditions_naming_no_prompt_release_are_refused(self) -> None:
        """An empty release set would hold vacuously against every future
        prompt change — which is how a stale certification survives."""
        with pytest.raises(CertificationError, match="prompt releases"):
            _conditions(prompt_releases=())

    def test_a_dirty_tree_never_certifies(self) -> None:
        """**The one fact that carries the whole weight.** A certification of
        uncommitted work describes a tree nobody can check out."""
        run = _run(tree_clean=False)

        assert not run.satisfied
        assert not run.certifies(_conditions())

    def test_coverage_below_the_floor_never_certifies(self) -> None:
        assert not _run(coverage=MINIMUM_COVERAGE - 0.01).satisfied
        assert _run(coverage=MINIMUM_COVERAGE).satisfied

    def test_the_floor_matches_the_gate_that_enforces_it(self) -> None:
        """Duplicated on purpose — the pytest gate enforces it during a run and
        this re-derives it on read — so the two are asserted equal here rather
        than trusted to stay so."""
        config = (Path(__file__).resolve().parents[2] / "pyproject.toml").read_text()

        assert f"fail_under = {int(MINIMUM_COVERAGE)}" in config


class TestAMeasurementExpiresWhenItsConditionsMove:
    @pytest.mark.parametrize(
        "moved",
        [
            {"rendering_protocol_version": 3},
            {"migration_head": "0019"},
            {"scenario_fingerprint": "e" * 64},
            {
                "prompt_releases": (
                    PromptRelease(
                        reference="research_planning@3", fingerprint="2" * 64, model="llama3.1:8b"
                    ),
                )
            },
        ],
    )
    def test_any_changed_condition_expires_the_certification(
        self, moved: dict[str, object]
    ) -> None:
        """**The Step C property, at platform scale.** A protocol bump or a
        prompt re-release withdraws a certification by derivation — nobody edits
        a manifest, and nobody has to remember."""
        run = _run()

        assert run.satisfied
        assert not run.certifies(_conditions(**moved))

    def test_the_run_still_records_that_it_succeeded(self) -> None:
        """Expiry is not retroactive failure. The measurement stays true; it
        stops applying."""
        run = _run()
        moved = _conditions(rendering_protocol_version=3)

        assert run.satisfied
        assert not run.is_current(moved)
        assert run.failures == ()

    def test_the_newest_qualifying_run_is_the_evidence(self) -> None:
        older = _run(certified_at=NOW - timedelta(days=1))
        newer = _run(certified_at=NOW, commit="b" * 40)
        stale = _run(
            certified_at=NOW + timedelta(days=1),
            conditions=_conditions(migration_head="0019"),
        )

        assert certified((older, newer, stale), _conditions()) is newer

    def test_nothing_certifies_when_nothing_qualifies(self) -> None:
        assert certified((_run(tree_clean=False),), _conditions()) is None
        assert certified((), _conditions()) is None


class TestTheRecordRefusesWhatCannotBeCompared:
    def test_an_abbreviated_commit_is_refused(self) -> None:
        with pytest.raises(CertificationError, match="commit SHA"):
            _run(commit="abc1234")

    def test_a_naive_timestamp_is_refused(self) -> None:
        with pytest.raises(CertificationError, match="timezone"):
            _run(certified_at=datetime(2026, 7, 31, 12, 0))

    def test_a_prompt_release_without_a_full_fingerprint_is_refused(self) -> None:
        with pytest.raises(CertificationError, match="SHA-256"):
            PromptRelease(reference="p@1", fingerprint="short", model="m")

    def test_a_gate_with_no_detail_is_refused(self) -> None:
        """A result nobody can read back proves only that something ran."""
        with pytest.raises(CertificationError, match="no detail"):
            GateResult(name="pytest", passed=True, detail="  ")

    def test_conditions_with_no_migration_head_are_refused(self) -> None:
        with pytest.raises(CertificationError, match="migration head"):
            _conditions(migration_head="")


class TestSerialisationIsDeterministic:
    def test_the_same_record_always_writes_the_same_bytes(self, tmp_path: Path) -> None:
        """Certification evidence is committed, so a record that serialised
        differently on two machines would show as a diff nobody made — and a
        reviewer who learns to ignore that diff will ignore the next one."""
        first, second = tmp_path / "a.json", tmp_path / "b.json"
        append(_run(), manifest=first)
        append(_run(), manifest=second)

        assert first.read_text() == second.read_text()

    def test_a_record_round_trips_through_the_manifest(self, tmp_path: Path) -> None:
        manifest = tmp_path / "manifest.json"
        run = _run()
        append(run, manifest=manifest)

        (restored,) = load(manifest)

        assert restored == run
        assert restored.certifies(_conditions())

    def test_key_order_does_not_depend_on_construction_order(self) -> None:
        assert canonical_json({"b": 1, "a": 2}) == canonical_json({"a": 2, "b": 1})

    def test_the_fingerprint_distinguishes_a_moved_byte(self) -> None:
        """Length-delimited, so shifting content between two files changes the
        hash rather than producing a collision."""
        assert fingerprint_of((("a.json", b"xy"), ("b.json", b"z"))) != fingerprint_of(
            (("a.json", b"x"), ("b.json", b"yz"))
        )

    def test_the_fingerprint_ignores_the_order_files_were_walked_in(self) -> None:
        assert fingerprint_of((("a", b"1"), ("b", b"2"))) == fingerprint_of(
            (("b", b"2"), ("a", b"1"))
        )


class TestTheManifestAccumulates:
    def test_a_second_run_is_appended_never_substituted(self, tmp_path: Path) -> None:
        manifest = tmp_path / "manifest.json"
        append(_run(), manifest=manifest)
        append(_run(commit="b" * 40, certified_at=NOW + timedelta(hours=1)), manifest=manifest)

        assert len(load(manifest)) == 2

    def test_recording_one_run_twice_is_refused(self, tmp_path: Path) -> None:
        manifest = tmp_path / "manifest.json"
        append(_run(), manifest=manifest)

        with pytest.raises(CertificationError, match="already"):
            append(_run(), manifest=manifest)

    def test_a_repository_that_never_certified_reads_as_no_runs(self, tmp_path: Path) -> None:
        """A legitimate state, not an error — and distinguishable from a
        manifest that cannot be read, which is a different problem."""
        assert load(tmp_path / "absent.json") == ()

    def test_an_unknown_field_is_refused_rather_than_ignored(self, tmp_path: Path) -> None:
        manifest = tmp_path / "manifest.json"
        append(_run(), manifest=manifest)
        document = json.loads(manifest.read_text())
        document["runs"][0]["verdict"] = "certified"
        manifest.write_text(json.dumps(document))

        with pytest.raises(CertificationError, match="malformed"):
            load(manifest)


class TestTheReportCannotOutrunTheEvidence:
    def test_a_certifying_run_renders_as_certified(self) -> None:
        assert "**CERTIFIED**" in render(_run(), _conditions())

    def test_a_satisfied_run_whose_conditions_moved_says_which(self) -> None:
        report = render(_run(), _conditions(rendering_protocol_version=3))

        assert "AWAITING RE-CERTIFICATION" in report
        assert "do not edit this record" in report

    def test_a_failed_run_renders_its_reasons(self) -> None:
        report = render(_run(tree_clean=False), _conditions())

        assert "NOT CERTIFIED" in report
        assert "dirty" in report

    def test_every_report_states_what_certification_does_not_prove(self) -> None:
        """Zero production traffic. Evidence of discipline, not of field
        reliability — and the report says so rather than leaving a reader to
        infer it."""
        assert "zero production traffic" in render(_run(), _conditions())


class TestTheGateParsersReadWhatTheGatesActuallyPrint:
    """**The part of `make certify` that can be wrong quietly.**

    A failing gate is loud. A parser that silently stops matching writes
    `no summary line` into a detail field beside a passing run, and nobody reads
    a detail field on a green record. So each parser is fed the real output
    shape, and each is asserted to report its own failure rather than a zero.
    """

    def test_a_pytest_summary_is_read_as_its_own_count(self) -> None:
        from tests.certification.__main__ import summarise_suite

        assert summarise_suite("1763 passed, 4 warnings in 74.50s") == "1763 passed"
        assert summarise_suite("== 3 failed, 12 passed ==") == "12 passed"

    def test_coverage_is_read_from_the_gate_line(self) -> None:
        from tests.certification.__main__ import coverage_of

        assert coverage_of("Required test coverage of 95.0% reached. "
                           "Total coverage: 95.85%") == 95.85

    def test_contracts_are_read_with_both_numbers(self) -> None:
        from tests.certification.__main__ import contracts_of

        assert contracts_of("Contracts: 29 kept, 0 broken.") == "29 kept, 0 broken"

    def test_mypy_reports_the_file_count_it_checked(self) -> None:
        from tests.certification.__main__ import files_checked

        assert files_checked("Success: no issues found in 448 source files") == (
            "strict, clean over 448 files"
        )

    def test_smoke_stages_are_counted_including_lettered_ones(self) -> None:
        """`14b.` through `14k.` are stages too — counting only `\\d+\\.` would
        under-report the pipeline half of the gate by nine."""
        from tests.certification.__main__ import stage_count

        assert stage_count("0. Preflight\n14b. Ingestion\n15b. JWT\n16. Teardown\n") == 4

    @pytest.mark.parametrize(
        ("parser", "expected"),
        [
            ("summarise_suite", "no summary line"),
            ("contracts_of", "no summary line"),
            ("files_checked", "no summary line"),
        ],
    )
    def test_an_unrecognised_output_says_so_rather_than_inventing_a_number(
        self, parser: str, expected: str
    ) -> None:
        import tests.certification.__main__ as certify

        assert getattr(certify, parser)("the tool changed its output format") == expected

    def test_unreadable_coverage_reads_as_zero_and_therefore_fails(self) -> None:
        """**Zero rather than a guess**, and zero is below the floor — so a
        parser that stops matching makes the run fail loudly instead of
        certifying on a number nobody measured."""
        from tests.certification.__main__ import coverage_of

        assert coverage_of("no coverage line here") == 0.0
        assert not _run(coverage=0.0).satisfied
