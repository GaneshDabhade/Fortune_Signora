"""What is measured, and how — published, versioned, and free of weights.

**The rubric measures; the domain judges.** Everything here turns one run
into numbers. Whether those numbers earn a release is `Evaluation.passed`,
which states the criteria once, in the domain, where the release rule that
consumes them lives. Splitting it the other way would put the release
criteria in two places and let them disagree.

Three deterministic measures, no weighting between them, and no score
combining them into a single figure. That is deliberate: a weighted total
would let strong coverage compensate for a grounding failure, and grounding
failures are not compensable. Each measure is reported and each must be
satisfied on its own terms.

- **Grounding failures** — must be zero. Deterministic, so any failure is a
  defect rather than a low score.
- **Schema failures** — must be zero, for the same reason. Counted
  separately because a model that cannot hold a structure and a model that
  invents facts are different problems with different fixes.
- **Coverage** — the share of a case's *load-bearing* facts the narrative
  actually mentions. The measure that catches the real quality failure:
  output that is perfectly grounded and says nothing.

**Rejected, permanently: LLM-as-judge as a gate.** Scoring one model's output
with another makes the ruler itself non-reproducible and vendor-dependent —
change the judge and every historical score moves, so a quality regression
and a judge upgrade become indistinguishable after the fact. It may be
recorded as a secondary signal; it may never decide a release.
"""

from __future__ import annotations

from modules.ai_platform.domain.grounding import GroundedOutput
from modules.ai_platform.domain.prompt import MINIMUM_COVERAGE

#: Bumped whenever *what is measured* changes — a new measure, a changed
#: definition of coverage, a changed release criterion. Recorded on every
#: evaluation, so a movement in the numbers is attributable to the rubric
#: when it was the rubric that moved.
#:
#: Version 1: grounding failures, schema failures, coverage of load-bearing
#: facts, judged by `Evaluation.passed`.
RUBRIC_VERSION = 1


def coverage(output: GroundedOutput, load_bearing: tuple[str, ...]) -> float:
    """The share of load-bearing facts this output actually cites.

    Measured from **citations**, not from prose. A narrative mentioning a
    figure without citing the fact it came from is not covering that fact —
    it is making an uncited claim, which grounding already refuses. So the
    citation is the only evidence of coverage that means anything, and it is
    the same evidence grounding checks, read for a different question.

    Guaranteed non-vacuous: `GoldenCase` refuses a case with no load-bearing
    facts, so this never divides by zero and never returns a perfect score
    for asking nothing.
    """
    cited: set[str] = set()
    for statement in output.statements():
        cited.update(statement.evidence)
    return len(cited & set(load_bearing)) / len(load_bearing)


def criteria() -> tuple[str, ...]:
    """The published criteria, rendered for the report.

    Read from the domain rather than restated, so the criteria a report
    prints and the criteria a release is granted by cannot drift apart. If
    this function ever contains a number, that number is a second
    representation of a rule.
    """
    return (
        "grounding_failures == 0  (deterministic: any failure is a defect, not a low score)",
        "schema_failures == 0     (deterministic: a model that cannot hold a schema is unusable)",
        f"coverage >= {MINIMUM_COVERAGE}       (share of load-bearing facts cited; see "
        "MINIMUM_COVERAGE for why not 1.0)",
    )
