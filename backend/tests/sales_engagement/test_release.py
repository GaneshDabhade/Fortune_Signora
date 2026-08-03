"""Release is earned, never declared — and this module derives it itself.

**The divergence is the interesting part.** `Evaluation` states facts and is
reused whole; the *criteria* are this module's, because one field means the
Commercial Context Protocol here and the AI Platform's evidence rendering
protocol everywhere else.
"""

from __future__ import annotations

from datetime import date

import pytest

from modules.ai_platform.public import Evaluation, PromptNotReleasableError, PromptVersion
from modules.sales_engagement.domain.context import COMMERCIAL_CONTEXT_PROTOCOL_VERSION
from modules.sales_engagement.domain.release import (
    MINIMUM_COVERAGE,
    earns_release,
    released_for,
    require,
)

MODEL = "granite3.3:2b"


def measurement(
    *,
    refusals: int = 0,
    malformed: int = 0,
    coverage: float = 0.9,
    protocol: int = COMMERCIAL_CONTEXT_PROTOCOL_VERSION,
    model: str = MODEL,
    on: date = date(2026, 8, 3),
) -> Evaluation:
    return Evaluation(
        model=model,
        dataset="approach",
        dataset_version=1,
        rubric_version=1,
        evaluated_on=on,
        sample_size=10,
        grounding_failures=refusals,
        schema_failures=malformed,
        coverage=coverage,
        rendering_protocol_version=protocol,
        retries=0,
    )


def prompt(*evaluations: Evaluation) -> PromptVersion:
    return PromptVersion(
        name="executive_summary",
        version=1,
        owner="Sales Engagement",
        text="a prompt with {context}",
        evaluations=evaluations,
    )


class TestTheCriteria:
    def test_a_clean_run_earns_a_release(self) -> None:
        assert earns_release(measurement())

    def test_one_refusal_is_enough_to_refuse(self) -> None:
        """**A definition, not a threshold.** The fence is arithmetic over a
        closed set, so any refusal is a defect and no sample size excuses one."""
        assert not earns_release(measurement(refusals=1))

    def test_one_malformed_draft_is_enough_to_refuse(self) -> None:
        assert not earns_release(measurement(malformed=1))

    def test_coverage_below_the_floor_refuses(self) -> None:
        assert not earns_release(measurement(coverage=MINIMUM_COVERAGE - 0.01))

    def test_coverage_at_the_floor_passes(self) -> None:
        assert earns_release(measurement(coverage=MINIMUM_COVERAGE))

    def test_retries_do_not_affect_the_verdict(self) -> None:
        """Retrying is what the platform is supposed to do about a transient
        failure. Penalising a prompt for its provider's bad afternoon would make
        the criteria measure the wrong thing."""
        noisy = Evaluation(
            model=MODEL,
            dataset="approach",
            dataset_version=1,
            rubric_version=1,
            evaluated_on=date(2026, 8, 3),
            sample_size=10,
            grounding_failures=0,
            schema_failures=0,
            coverage=0.9,
            rendering_protocol_version=COMMERCIAL_CONTEXT_PROTOCOL_VERSION,
            retries=7,
        )

        assert earns_release(noisy)


class TestAMeasurementIsBoundToTheProtocolThatProducedIt:
    def test_a_pass_under_a_superseded_protocol_does_not_release(self) -> None:
        """**Withdrawn by derivation, not by anyone remembering to.** The run
        really did pass; it no longer describes what a model would be shown."""
        assert not earns_release(measurement(protocol=COMMERCIAL_CONTEXT_PROTOCOL_VERSION + 1))

    def test_the_refusal_says_re_run_rather_than_re_author(self) -> None:
        """**Two failures with opposite remedies.** Told only *"has not passed
        for this model"*, an engineer re-authors a prompt that was already
        correct."""
        stale = prompt(measurement(protocol=COMMERCIAL_CONTEXT_PROTOCOL_VERSION + 1))

        with pytest.raises(PromptNotReleasableError, match="do not re-author"):
            require(stale, MODEL)


class TestTheRuntimeQuestion:
    def test_a_prompt_with_no_evaluations_is_not_released(self) -> None:
        """**The correct state for a prompt nobody has evaluated**, and the
        state `executive_summary@1` ships in."""
        assert not released_for(prompt(), MODEL)

    def test_a_model_that_was_never_evaluated_is_refused(self) -> None:
        released = prompt(measurement())

        with pytest.raises(PromptNotReleasableError, match="has not passed evaluation"):
            require(released, "some-other-model")

    def test_the_refusal_names_what_did_pass(self) -> None:
        released = prompt(measurement())

        with pytest.raises(PromptNotReleasableError, match=MODEL):
            require(released, "some-other-model")

    def test_a_released_pairing_passes_the_gate(self) -> None:
        require(prompt(measurement()), MODEL)

    def test_a_failing_run_on_record_does_not_release(self) -> None:
        """A manifest recording only passes would show a prompt with a clean
        history and no way to see it had been measured and found wanting."""
        assert not released_for(prompt(measurement(refusals=2)), MODEL)


class TestTheDivergenceIsVisibleRatherThanSafe:
    """**The two protocols share an integer namespace and nothing coordinates
    them**, which is the whole of C-214.

    An earlier draft of this module claimed the divergence *failed closed* — that
    a Sales Engagement measurement would always make `PromptVersion.is_released`
    read false, so a caller reaching for the platform's gate by mistake would be
    refused. **That was true only while the two constants happened to differ.**
    Bumping the Commercial Context Protocol to 2 made them equal, and the
    platform's gate silently began returning the right answer for the wrong
    reason.

    Neither state is a guarantee. The comparison is meaningless whichever way it
    lands, so the property worth pinning is not *safety* but *visibility*.
    """

    def test_the_two_protocol_constants_currently_coincide(self) -> None:
        """**Pinned so the coupling cannot stay invisible.** When either protocol
        moves, this fails and sends the reader to C-214 — which is the only
        reason a reader would ever discover that an unrelated module's constant
        is being compared against this one's.
        """
        from modules.ai_platform.domain.rendering import PROMPT_RENDERING_PROTOCOL_VERSION

        assert COMMERCIAL_CONTEXT_PROTOCOL_VERSION == PROMPT_RENDERING_PROTOCOL_VERSION, (
            "The two protocols have diverged. Nothing is broken, but "
            "`PromptVersion.is_released` now answers a meaningless question about Sales "
            "Engagement prompts in the other direction. See C-214."
        )

    def test_this_module_never_depends_on_the_platforms_answer(self) -> None:
        """Whatever the platform's gate says, **this module's own derivation is
        the authority** — and it is the one every caller here goes through."""
        measured_elsewhere = prompt(measurement(protocol=COMMERCIAL_CONTEXT_PROTOCOL_VERSION + 5))

        assert not released_for(measured_elsewhere, MODEL)
