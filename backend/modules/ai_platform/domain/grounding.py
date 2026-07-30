"""Grounding — does this output correspond to the evidence, or not.

**Where hallucination stops being a quality score and becomes a typed
error.** The Evidence Set defined a closed universe of facts; this module
decides whether a model's output stayed inside it.

> **It may generate language. It must never generate facts.**

What that means precisely, and what it deliberately does not mean:

**Grounding validates truth, not language.** A fluent, well-structured
sentence citing something that does not exist **fails**. A clumsy sentence
fully supported by cited evidence **passes**. This module has no opinion
about prose and contains no notion of quality, tone, or usefulness — those
belong to the evaluation harness, which is the other tier entirely
(``docs/architecture/28-ai-platform.md``).

**It consumes a closed set and asks nothing else.** No repository, no
session, no lookup, no network. Everything needed to reach a verdict is in
the two arguments, which is what makes the verdict reproducible: the same
output against the same evidence always produces the same report.

**It validates; it never repairs.** No trimming, no dropping of bad
citations, no "best effort" salvage. A caller decides what to do with a
failure — retry, escalate, record — and a validator that quietly fixed its
input would make the failure rate unmeasurable, which is the one number this
platform most needs about itself.

**Failures stay distinguishable.** An unresolvable citation, an uncited
statement, an invented quantity and a foreign workspace are four different
problems with four different causes, and collapsing them into "ungrounded"
would discard the diagnosis at the moment it was made. Every violation is
reported, not just the first, and reported in a stable order.

### The honest limit

Grounding is **containment, not comprehension.** A statement can cite the
correct fact and still characterise it wrongly — *"Raised 24M USD"* cited
accurately but described as a down round passes every check here. That
failure is real, it is the residual, and it belongs to the human-rated
sample in the evaluation harness. What grounding buys is that
*mischaracterisation* is the remaining failure mode rather than one of a
dozen including fabricated companies, invented numbers, and another tenant's
data.
"""

from __future__ import annotations

import re
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, ValidationError

from modules.ai_platform.domain.errors import AIPlatformError
from modules.ai_platform.domain.evidence import EvidenceError, EvidenceRef, EvidenceSet

#: Numeric tokens in generated prose. Digits, optional grouping separators,
#: optional decimal part — deliberately *not* anchored to word boundaries on
#: the right, so "24M" yields "24" and "40%" yields "40". Tokenised rather
#: than substring-matched, so "240" never satisfies a claim about "2400".
_NUMBER = re.compile(r"\d[\d,]*(?:\.\d+)?")


class ViolationKind(StrEnum):
    """Why an output failed. Five distinct causes, kept distinct."""

    MALFORMED_CITATION = "malformed_citation"
    """A citation is not a reference at all — it does not parse."""

    UNRESOLVED_CITATION = "unresolved_citation"
    """A citation parses but addresses nothing in the evidence set.
    **The signature of a fabricated fact.**"""

    UNCITED_STATEMENT = "uncited_statement"
    """A statement rests on nothing. Not an unsupported claim — an
    *unsupportable* one, since there is nothing to check it against."""

    UNGROUNDED_QUANTITY = "ungrounded_quantity"
    """A number appears in the prose that appears in none of the facts that
    statement cited. **The characteristic failure of this product** — not an
    invented company, an invented figure."""

    WORKSPACE_ESCAPE = "workspace_escape"
    """A citation resolves to a fact belonging to another workspace.
    Redundant given how an evidence set is built, and asserted anyway."""


class GroundingError(AIPlatformError):
    """Base for grounding failures."""


class SchemaViolationError(GroundingError):
    """The model's output did not parse as the declared structure.

    The *transport* of meaning failing, distinct from
    ``AIOutputUnusableError`` (the vendor's protocol failing) and from
    ``UngroundedOutputError`` (the content failing). Three different things
    break for three different reasons, and one metric covering all of them
    would say nothing useful about any.
    """


class UngroundedOutputError(GroundingError):
    """The output parsed, and does not correspond to the evidence."""

    def __init__(self, report: GroundingReport) -> None:
        summary = "; ".join(f"{v.kind}: {v.detail}" for v in report.violations)
        super().__init__(f"output is not grounded in its evidence — {summary}")
        self.report = report


@dataclass(frozen=True, slots=True, order=True)
class Violation:
    """One specific way an output failed, located precisely enough to fix."""

    #: Index of the offending statement, for a message that says *where*.
    statement: int
    kind: ViolationKind
    detail: str


@dataclass(frozen=True, slots=True)
class GroundingReport:
    """Every violation found, in a stable order.

    All of them, not the first: an output with a fabricated citation *and*
    an invented number has two problems, and reporting one would send
    whoever investigates back for a second round.
    """

    violations: tuple[Violation, ...]

    @property
    def is_grounded(self) -> bool:
        return not self.violations

    def kinds(self) -> frozenset[ViolationKind]:
        return frozenset(v.kind for v in self.violations)


class GroundedStatement(BaseModel):
    """One thing the model says, and what it rests on.

    The unit of grounding. Deliberately **not** a narrative, a summary, or a
    recommendation — this module knows nothing about what an output is
    *for*, only that it is made of statements that must each be supported.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    text: str
    #: Citation tokens (``kind:uuid``), as produced by ``EvidenceRef.token``.
    #: A flat string because a model reproducing a short opaque token gets it
    #: right far more often than one reproducing a nested object, and every
    #: unparseable citation is a usable answer thrown away.
    evidence: tuple[str, ...]


class GroundedOutput(BaseModel):
    """Base for any structure a model returns under grounding.

    Subclasses declare their own shape and say which parts are statements.
    M8's narration, M9's reasoning result and M10's research artifact are
    different shapes with the same obligation, and this is the only thing
    they need to share.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    def statements(self) -> tuple[GroundedStatement, ...]:
        raise NotImplementedError(
            "a grounded output must say which of its parts are statements, or nothing "
            "can be checked against the evidence."
        )


def output_schema(output_type: type[GroundedOutput]) -> Mapping[str, Any]:
    """The JSON Schema to ask a model for.

    Derived from the very type used to validate the response, so the shape
    requested and the shape enforced **cannot drift**. Hand-writing the
    schema would create two definitions of one contract, and within a year
    they would disagree in a way that looked like a model regression.
    """
    return output_type.model_json_schema()


def parse[OutputT: GroundedOutput](output_type: type[OutputT], raw: str) -> OutputT:
    """Read raw model output into the declared structure.

    Raises ``SchemaViolationError`` — never returns a partially populated
    object. ``extra="forbid"`` means a model that invents a *field* fails
    here, just as one inventing a *fact* fails in ``check``.
    """
    try:
        return output_type.model_validate_json(raw)
    except ValidationError as exc:
        raise SchemaViolationError(
            f"model output does not match {output_type.__name__}: {exc.error_count()} "
            f"problem(s). {exc}"
        ) from exc


def check(output: GroundedOutput, evidence: EvidenceSet) -> GroundingReport:
    """Verify correspondence between an output and its evidence.

    Pure: reads nothing beyond its arguments, mutates nothing, and returns
    the same report for the same inputs every time.
    """
    violations: list[Violation] = []
    for index, statement in enumerate(output.statements()):
        violations.extend(_check_statement(index, statement, evidence))
    return GroundingReport(violations=tuple(sorted(violations)))


def verify(output: GroundedOutput, evidence: EvidenceSet) -> None:
    """``check``, raising on failure — for callers that only want the
    happy path to continue."""
    report = check(output, evidence)
    if not report.is_grounded:
        raise UngroundedOutputError(report)


def _check_statement(
    index: int, statement: GroundedStatement, evidence: EvidenceSet
) -> Iterable[Violation]:
    if not statement.evidence:
        yield Violation(
            statement=index,
            kind=ViolationKind.UNCITED_STATEMENT,
            detail=f"'{_excerpt(statement.text)}' cites nothing, so nothing supports it.",
        )
        return

    cited: list[EvidenceRef] = []
    resolvable = True
    for token in statement.evidence:
        try:
            ref = EvidenceRef.parse(token)
        except EvidenceError as exc:
            resolvable = False
            yield Violation(
                statement=index,
                kind=ViolationKind.MALFORMED_CITATION,
                detail=str(exc),
            )
            continue

        fact = evidence.resolve(ref)
        if fact is None:
            resolvable = False
            yield Violation(
                statement=index,
                kind=ViolationKind.UNRESOLVED_CITATION,
                detail=(
                    f"'{token}' addresses nothing in the evidence. Either the fact was "
                    "never provided, or the model invented the reference."
                ),
            )
            continue

        if fact.workspace_id != evidence.workspace_id:
            yield Violation(
                statement=index,
                kind=ViolationKind.WORKSPACE_ESCAPE,
                detail=f"'{token}' belongs to workspace {fact.workspace_id}.",
            )
            continue

        cited.append(ref)

    # Quantities are checked against the facts this statement actually
    # cited, never the whole set: a statement citing fact A may not borrow a
    # number from uncited fact B. Skipped when a citation failed to resolve,
    # because the permitted numbers are then unknown and every quantity
    # would be reported — burying the real problem under noise.
    if resolvable and cited:
        yield from _check_quantities(index, statement, evidence, cited)


def _check_quantities(
    index: int, statement: GroundedStatement, evidence: EvidenceSet, cited: Sequence[EvidenceRef]
) -> Iterable[Violation]:
    permitted = _numbers_in_evidence(evidence, cited)
    for token in sorted(set(_NUMBER.findall(statement.text))):
        if _normalise(token) not in permitted:
            yield Violation(
                statement=index,
                kind=ViolationKind.UNGROUNDED_QUANTITY,
                detail=(
                    f"the figure '{token}' appears in the text but in none of the facts "
                    f"this statement cites."
                ),
            )


def _numbers_in_evidence(evidence: EvidenceSet, cited: Sequence[EvidenceRef]) -> frozenset[str]:
    """Every number the cited facts legitimately contain.

    Drawn from **typed attribute values** and from the numeric tokens in each
    fact's summary. The typed half is why the check is arithmetic rather than
    a guess — a value stored as ``240`` is exactly the number 240, not a
    string that happens to look like one.
    """
    found: set[str] = set()
    for ref in cited:
        fact = evidence.resolve(ref)
        if fact is None:  # pragma: no cover — callers filter unresolved refs first
            continue
        found.update(_normalise(t) for t in _NUMBER.findall(fact.summary))
        for _, value in fact.attributes:
            # No special case for bool. It reads as "True"/"False", which
            # contains no digits, so a boolean attribute licenses no figure —
            # a guard here would be dead code, and dead code carrying a
            # justification is how a false claim survives review.
            found.update(_normalise(t) for t in _NUMBER.findall(str(value)))
    return frozenset(found)


def _normalise(token: str) -> str:
    """One form per number, so ``24,000,000`` and ``24000000`` are the same
    figure and ``1.50`` and ``1.5`` are too."""
    plain = token.replace(",", "")
    if "." in plain:
        plain = plain.rstrip("0").rstrip(".")
    return plain or "0"


def _excerpt(text: str, limit: int = 60) -> str:
    collapsed = " ".join(text.split())
    return collapsed if len(collapsed) <= limit else f"{collapsed[: limit - 1]}…"
