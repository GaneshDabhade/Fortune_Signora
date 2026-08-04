"""`make eval-approach` — the composition root for an evaluation run.

**Written for [B-109](../../../docs/BUGS.md)**, which found it at 0%. An entry
point is the easiest file in a repository to leave untested and one of the
worst to get wrong: **nothing else decides whether a measurement is written to
the manifest**, and an off-by-one in that branch is a result recorded from a
run nobody asked to record.

No model is called and no manifest is touched. Everything past argument parsing
is a double, because what this file *is* is the wiring — and the wiring is
exactly what a real run would obscure.

**The exit code is asserted hardest.** It is the only thing `make` sees, and it
is derived from `earns_release` rather than decided here — release is derived
from evaluations, never declared (`CLAUDE.md` §2).
"""

from __future__ import annotations

from contextlib import asynccontextmanager
from datetime import date
from typing import Any
from unittest.mock import patch

import pytest

from modules.ai_platform.public import AIPlatformError
from modules.sales_engagement.application.synthesise import PassOutcome
from modules.sales_engagement.evaluation import __main__ as entry
from modules.sales_engagement.evaluation.report import CaseResult, EvaluationReport

FINGERPRINT = "a" * 64


def _report(*, refused: bool = False) -> EvaluationReport:
    return EvaluationReport(
        prompt_name="executive_summary",
        prompt_version=1,
        prompt_fingerprint=FINGERPRINT,
        model="claude-sonnet-4-5",
        dataset_name="approach",
        dataset_version=1,
        dataset_fingerprint=FINGERPRINT,
        rubric_version=1,
        evaluated_on=date(2026, 8, 4),
        results=(
            CaseResult(
                case="northwind",
                outcome=PassOutcome.REFUSED if refused else PassOutcome.OK,
                coverage=0.0 if refused else 1.0,
            ),
        ),
    )


class FakeHarness:
    """Answers `evaluate`, and records what the entry point asked it for."""

    calls: list[dict[str, Any]] = []
    report: EvaluationReport | None = None
    error: Exception | None = None

    def __init__(self, **kwargs: Any) -> None:
        self.built = kwargs

    async def evaluate(self, **kwargs: Any) -> EvaluationReport:
        FakeHarness.calls.append(kwargs)
        if FakeHarness.error is not None:
            raise FakeHarness.error
        assert FakeHarness.report is not None
        return FakeHarness.report


@asynccontextmanager
async def _no_client(*args: Any, **kwargs: Any) -> Any:
    yield object()


@pytest.fixture(autouse=True)
def wired() -> Any:
    """Every outward edge replaced, and `record` among them.

    **`record` is patched rather than pointed at a copy**: this suite asserts
    *whether* it was called, and a test that also exercised writing would fail
    for two reasons at once.
    """
    FakeHarness.calls = []
    FakeHarness.report = _report()
    FakeHarness.error = None
    recorded: list[Any] = []

    class FakeSettings:
        ollama_model = "llama3.1:8b"

    with (
        patch.object(entry, "Harness", FakeHarness),
        patch.object(entry, "AISettings", FakeSettings),
        patch.object(entry, "prompts", lambda: object()),
        patch.object(entry, "build_provider_registry", lambda *a, **k: object()),
        patch.object(entry, "ProviderSynthesisModel", lambda registry: object()),
        patch.object(entry, "Synthesise", lambda **k: object()),
        patch.object(entry, "load_dataset", lambda name, version: object()),
        patch.object(entry, "record", lambda report, *, manifest: recorded.append(report)),
        patch("modules.sales_engagement.evaluation.__main__.httpx.AsyncClient", _no_client),
    ):
        yield recorded


class TestTheDefaults:
    async def test_it_evaluates_the_executive_summary_unless_told_otherwise(
        self, wired: list[Any]
    ) -> None:
        await entry.main([])

        assert FakeHarness.calls[0]["pass_"].value == "executive_summary"

    async def test_it_uses_the_configured_development_model_by_default(
        self, wired: list[Any]
    ) -> None:
        """A default is not a vendor branch: nothing consults it, and
        registering another adapter requires no edit here (§10)."""
        await entry.main([])

        assert FakeHarness.calls[0]["model"] == "llama3.1:8b"

    async def test_a_named_model_wins(self, wired: list[Any]) -> None:
        await entry.main(["--model", "claude-sonnet-4-5"])

        assert FakeHarness.calls[0]["model"] == "claude-sonnet-4-5"

    async def test_it_runs_each_case_twice(self, wired: list[Any]) -> None:
        """Stability across identical closed sets is the dimension this
        architecture can guarantee most cheaply, and one run measures none."""
        await entry.main([])

        assert FakeHarness.calls[0]["runs_per_case"] == 2

    async def test_the_run_count_can_be_raised(self, wired: list[Any]) -> None:
        await entry.main(["--runs-per-case", "5"])

        assert FakeHarness.calls[0]["runs_per_case"] == 5

    async def test_an_unknown_pass_is_refused_by_the_parser(
        self, wired: list[Any]
    ) -> None:
        """Refused here rather than discovered as a missing artifact later."""
        with pytest.raises(SystemExit):
            await entry.main(["--pass", "not-a-pass"])


class TestWhetherAnythingIsWritten:
    async def test_nothing_is_recorded_unless_asked(self, wired: list[Any]) -> None:
        """**The branch that matters most in this file.** A run that recorded
        by default would put results in the manifest nobody chose to keep."""
        await entry.main([])

        assert wired == []

    async def test_record_writes_the_report_that_was_measured(
        self, wired: list[Any]
    ) -> None:
        await entry.main(["--record"])

        assert len(wired) == 1
        assert wired[0].model == "claude-sonnet-4-5"

    async def test_an_unmeasurable_run_records_nothing(self, wired: list[Any]) -> None:
        """**The one that would be expensive to get wrong.** A run that could
        not reach a model has measured nothing, and writing a row for it would
        put a fabricated result in the repository's evaluation history.
        """
        FakeHarness.error = AIPlatformError("the runtime is unreachable")

        await entry.main(["--record"])

        assert wired == []


class TestTheExitCode:
    async def test_a_passing_run_exits_zero(self, wired: list[Any]) -> None:
        assert await entry.main([]) == 0

    async def test_a_refused_run_exits_one(self, wired: list[Any]) -> None:
        """`REFUSED` is a legitimate outcome, not a crash — a non-zero exit
        that is distinct from the unmeasurable one below."""
        FakeHarness.report = _report(refused=True)

        assert await entry.main([]) == 1

    async def test_an_unmeasurable_run_exits_two(self, wired: list[Any]) -> None:
        """**Distinct from a refusal, deliberately.** *"the model behaved
        badly"* and *"nothing was measured"* have opposite remedies, and one
        exit code for both would make a broken runtime look like a bad prompt.
        """
        FakeHarness.error = AIPlatformError("the runtime is unreachable")

        assert await entry.main([]) == 2

    async def test_an_unmeasurable_run_says_so_on_stderr(
        self, wired: list[Any], capsys: pytest.CaptureFixture[str]
    ) -> None:
        FakeHarness.error = AIPlatformError("the runtime is unreachable")

        await entry.main([])

        assert "UNMEASURABLE" in capsys.readouterr().err
