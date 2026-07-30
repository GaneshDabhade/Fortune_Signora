"""Prompts as first-class engineering artifacts.

A prompt changes program behaviour without changing a line of Python, which
makes it code in the only sense that matters — and it is treated
accordingly: versioned, owned, reviewed, hashed, and unusable until it has
been shown to work.

Four properties, each chosen so a violation is refused rather than
discouraged:

**Immutable once written.** A version is never edited in place. Editing one
silently invalidates every result recorded against it, and those results are
the entire provenance chain — so a change is always a new version.

**Content identity outranks version identity.** ``version`` is for humans;
the **SHA-256 of the text is the architectural identity**. Two prompts with
the same version and different text are two different prompts, whatever the
manifest says, and the loader refuses the pair outright.

**Release is earned, not declared.** A prompt may be used only with the exact
``(model, dataset)`` pairs it has been *evaluated against and passed*. This
is an enforceable rule, not a note: developing against a small local model
demonstrates nothing about a frontier hosted one (ADR-0028), and the gap is
made structural rather than remembered.

**Evaluations accumulate; they never overwrite.** They are evidence *about*
an artifact rather than part of it — the same distinction the pipeline draws
between an observation and the thing observed. Which is also why they sit
outside the content hash: appending one must not change the identity of the
prompt it describes.

Nothing here knows about a vendor. A prompt declares what it needs; who
serves that model is resolved at runtime, by the registry, from
configuration.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from datetime import date
from typing import Final

from modules.ai_platform.domain.errors import AIPlatformError


class PromptError(AIPlatformError):
    """A prompt artifact could not be used as declared."""


class PromptNotFoundError(PromptError):
    """No prompt of that name and version exists.

    Loud rather than a fallback to "latest": a result recording version 3
    must be reproducible from version 3, and silently serving 4 would make
    the recorded provenance a lie.
    """


class PromptTamperedError(PromptError):
    """A prompt's text does not match the hash its manifest declares."""


class PromptNotReleasableError(PromptError):
    """A prompt was requested for a pairing it has not earned."""


#: The proportion of a case's **load-bearing** facts a narrative must
#: mention to count as useful.
#:
#: This is the one number in the release criteria that is a judgement rather
#: than a definition, so it is stated here, once, with its reasoning, rather
#: than appearing as a literal inside the harness. An output can cite
#: perfectly and still say nothing: grounding bounds what a narrative *may*
#: claim and says nothing about whether it claimed anything worth reading.
#:
#: Not 1.0, because a narrative that must mention every load-bearing fact is
#: a list rather than a summary, and the harness would then be measuring
#: length. Not lower, because below two thirds the strongest contribution to
#: a score can go unmentioned while the run still passes.
MINIMUM_COVERAGE: Final = 0.66


@dataclass(frozen=True, slots=True, order=True)
class Evaluation:
    """One measurement of one prompt against one model and dataset.

    Records **what was measured**, not a verdict. Eligibility is derived
    from these facts, so a change to what "fit for use" means re-reads
    history correctly instead of leaving a stratum of rows judged by a rule
    nobody remembers — the same reasoning that keeps money off
    ``InferenceUsage``.

    **Release is earned here or nowhere.** Nothing in the system can mark a
    prompt released; a prompt is usable exactly where a measurement of this
    shape satisfies the criteria below.
    """

    model: str
    dataset: str
    #: Which revision of the golden set produced these numbers. A dataset is
    #: an engineering asset that changes under review, and a result that
    #: cannot name the expectations it was measured against is not evidence
    #: of anything (AC-73).
    dataset_version: int
    #: Which published criteria were applied. Recorded so a rubric change is
    #: legible as a rubric change rather than as a quality movement.
    rubric_version: int
    evaluated_on: date
    #: How many outputs were checked. A perfect run over one sample is not
    #: evidence, and recording the denominator is what lets a reader tell.
    sample_size: int
    #: Grounding is deterministic, so the only acceptable number is zero.
    #: Not a tuned threshold — a definition (28-ai-platform.md).
    grounding_failures: int
    #: Output that did not parse as the declared structure. Also zero: a
    #: model that cannot hold a schema is not usable behind this prompt, and
    #: a retry rate that hides it is a cost signal, not a pass.
    schema_failures: int
    #: Mean proportion of load-bearing facts mentioned, across the run.
    coverage: float
    #: Retries the run needed to complete. Recorded, and deliberately **not
    #: part of the release criteria** below: retrying is what the platform is
    #: supposed to do about a transient failure, and penalising a prompt for
    #: its provider's bad afternoon would make the criteria measure the wrong
    #: thing. It is a cost and reliability signal (R-01), durable here so a
    #: run that needed retries stays distinguishable from a clean one after
    #: the terminal that printed it is closed.
    retries: int = 0

    def __post_init__(self) -> None:
        if not self.model.strip() or not self.dataset.strip():
            raise PromptError("an evaluation must name both a model and a dataset.")
        if self.dataset_version < 1 or self.rubric_version < 1:
            raise PromptError(
                "an evaluation must name the dataset revision and rubric it applied; "
                "versions start at 1."
            )
        if self.sample_size <= 0:
            raise PromptError(f"an evaluation over {self.sample_size} samples measured nothing.")
        if self.grounding_failures < 0 or self.schema_failures < 0:
            raise PromptError("failure counts cannot be negative.")
        if self.retries < 0:
            raise PromptError("a run cannot have retried a negative number of times.")
        if not 0.0 <= self.coverage <= 1.0:
            raise PromptError(
                f"coverage of {self.coverage} is not a proportion. It is the share of "
                "load-bearing facts mentioned, so it lies between 0 and 1."
            )

    @property
    def passed(self) -> bool:
        """The release criteria, in one place and stated positively.

        Two of the three are definitions rather than thresholds: grounding
        and schema validity are deterministic, so any failure is a defect
        and no number of samples excuses one. The third is the judgement,
        and it lives on ``MINIMUM_COVERAGE`` where it can be read.

        ``retries`` is deliberately absent. It describes what the *provider*
        did, not what the prompt did.
        """
        return (
            self.grounding_failures == 0
            and self.schema_failures == 0
            and self.coverage >= MINIMUM_COVERAGE
        )


@dataclass(frozen=True, slots=True)
class PromptVersion:
    """One immutable version of one prompt."""

    name: str
    version: int
    #: Who reviews a change to this. No code reads it; a person does, and
    #: an unowned artifact that shapes model behaviour is unmaintained.
    owner: str
    text: str
    #: Append-only. Held sorted so two manifests recording the same history
    #: in different orders are the same history.
    evaluations: tuple[Evaluation, ...] = ()

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise PromptError("a prompt version has no name.")
        if self.version < 1:
            raise PromptError(
                f"prompt '{self.name}' has version {self.version}; versions start at 1."
            )
        if not self.text.strip():
            raise PromptError(f"prompt {self.reference} has no text.")
        if not self.owner.strip():
            raise PromptError(
                f"prompt {self.reference} has no owner. An artifact that changes model "
                "behaviour without changing code needs someone who reviews changes to it."
            )
        seen = [(e.model, e.dataset, e.dataset_version, e.evaluated_on) for e in self.evaluations]
        if len(seen) != len(set(seen)):
            raise PromptError(
                f"prompt {self.reference} records the same evaluation twice. Evaluations "
                "accumulate; a repeat means one overwrote another rather than appending."
            )
        object.__setattr__(self, "evaluations", tuple(sorted(self.evaluations)))

    @property
    def reference(self) -> str:
        """How a prompt is named everywhere else — in provenance, in logs,
        and on every inference record."""
        return f"{self.name}@{self.version}"

    @property
    def fingerprint(self) -> str:
        """SHA-256 over name, version and text: the artifact's identity.

        Evaluations are excluded deliberately. They are observations about
        this prompt, and appending one must not change what it *is* — a
        fingerprint that moved every time the prompt was measured could not
        identify anything.
        """
        return hashlib.sha256(f"{self.name}\x1d{self.version}\x1d{self.text}".encode()).hexdigest()

    @property
    def is_released(self) -> bool:
        """Released means *usable somewhere*, and it is derived rather than
        declared — a status field could say "released" while no evaluation
        supported it."""
        return any(e.passed for e in self.evaluations)

    def supports(self, *, model: str, dataset: str) -> bool:
        return any(e.passed and e.model == model and e.dataset == dataset for e in self.evaluations)

    def is_released_for(self, model: str) -> bool:
        """Released for this model, on any dataset it was evaluated against.

        The **runtime** question. At the point of use there is no dataset —
        the dataset is what an evaluation was *conducted on*, and it lives in
        the record supporting the release rather than in the call relying on
        it.
        """
        return any(e.passed and e.model == model for e in self.evaluations)

    def require_model(self, model: str) -> None:
        """Raise unless this prompt has earned the model.

        ADR-0028's release rule at the point of use: *a prompt may not be
        used with a model it was never evaluated on.*
        """
        if self.is_released_for(model):
            return
        earned = sorted({e.model for e in self.evaluations if e.passed})
        raise PromptNotReleasableError(
            f"prompt {self.reference} has not passed evaluation for model '{model}'. "
            f"Passed for: {earned or 'nothing yet'}. A prompt tuned against one model has "
            "not been shown to behave on another."
        )

    def require(self, *, model: str, dataset: str) -> None:
        """Raise unless this prompt has earned the pairing.

        The enforceable form of ADR-0028's release rule.
        """
        if self.supports(model=model, dataset=dataset):
            return
        earned = sorted(f"{e.model}/{e.dataset}" for e in self.evaluations if e.passed)
        raise PromptNotReleasableError(
            f"prompt {self.reference} has not passed evaluation for model '{model}' on "
            f"dataset '{dataset}'. Passed: {earned or 'nothing yet'}. A prompt tuned against "
            "one model has not been shown to behave on another."
        )


@dataclass(frozen=True, slots=True)
class PromptRegistry:
    """Every prompt version this process can serve.

    Read-only after loading, like the provider registry and for the same
    reason: an artifact store that changes under a running process makes the
    provenance recorded against it unreliable.
    """

    versions: tuple[PromptVersion, ...]

    def __post_init__(self) -> None:
        references = [v.reference for v in self.versions]
        if len(references) != len(set(references)):
            raise PromptError(
                f"the registry holds {sorted(references)} — a reference appears twice, so "
                "provenance recording it would not identify one artifact."
            )

    def get(self, name: str, version: int) -> PromptVersion:
        for candidate in self.versions:
            if candidate.name == name and candidate.version == version:
                return candidate
        known = sorted(v.reference for v in self.versions)
        raise PromptNotFoundError(f"no prompt '{name}@{version}'. Known: {known or 'none'}.")

    def resolve(self, name: str, version: int, *, model: str, dataset: str) -> PromptVersion:
        """Fetch a prompt for a specific use, refusing an unearned pairing.

        The only path a caller should take to obtain a prompt it intends to
        send: ``get`` returns an artifact, this returns one that is allowed
        to be used.
        """
        prompt = self.get(name, version)
        prompt.require(model=model, dataset=dataset)
        return prompt
