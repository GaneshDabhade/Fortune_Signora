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


@dataclass(frozen=True, slots=True, order=True)
class Evaluation:
    """One measurement of one prompt against one model and dataset.

    Records **what was measured**, not a verdict. Eligibility is derived
    from these facts, so a change to what "fit for use" means re-reads
    history correctly instead of leaving a stratum of rows judged by a rule
    nobody remembers — the same reasoning that keeps money off
    ``InferenceUsage``.
    """

    model: str
    dataset: str
    evaluated_on: date
    #: How many outputs were checked. A perfect run over one sample is not
    #: evidence, and recording the denominator is what lets a reader tell.
    sample_size: int
    #: Grounding is deterministic, so the only acceptable number is zero.
    #: Not a tuned threshold — a definition (28-ai-platform.md).
    grounding_failures: int

    def __post_init__(self) -> None:
        if not self.model.strip() or not self.dataset.strip():
            raise PromptError("an evaluation must name both a model and a dataset.")
        if self.sample_size <= 0:
            raise PromptError(f"an evaluation over {self.sample_size} samples measured nothing.")
        if self.grounding_failures < 0:
            raise PromptError("grounding failures cannot be negative.")

    @property
    def passed(self) -> bool:
        return self.grounding_failures == 0


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
        seen = [(e.model, e.dataset, e.evaluated_on) for e in self.evaluations]
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
