"""Commercial Fit Reasoning — which of the Signora Customer's products fits.

**Likely, never certain**, and the wording is the design. A Buying Committee is
declared *per product*; an Opportunity has no product; so *"which committee
applies to this Target Account?"* is unanswerable until something infers one.

**Deterministic, and the explanation is structural rather than prose.** A
`ProductFit` carries the reasons that produced it, so *why this product* is
answered by the same value that answers *which product* — and a seller can
disagree with a specific reason rather than with a verdict.

### One dimension today, and the frame for more

The product owner's list of fit dimensions is longer than what the platform can
support: ICP match, technology overlap, intent topics, historical conversions,
strategic initiatives. **Every one of them needs a declaration or a record that
does not exist** — a `Product` is an id, a name and a description, and nothing
links one to a technology or to the ICP that discovered a Target Account.

So this implements the dimension the repository genuinely holds:

> **Committee overlap.** The evidence names the Buying Committee Roles declared
> for one product and not another. That is the same join SE-02 already
> performs, asked of a different question.

**A `FitDimension` value with no code path that emits it would be Decorative
Logic** — the defect found and fixed in `reasoning.py` an hour before this file
was written. Future dimensions are described in
[50-sales-engagement.md](../../../../docs/architecture/50-sales-engagement.md)
§23 with their triggers, and each arrives with the declaration that makes it
computable.

### A tie is an unknown, never a coin toss

Two products fitting equally well is **a question for the seller**, and
guessing between them would be the platform inventing a commercial decision it
has no evidence for. `likely` returns `None`, and the caller surfaces it.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from uuid import UUID

from modules.sales_engagement.domain.reasoning import (
    CommitteeRoleRef,
    Evidence,
    ReasoningError,
    Strength,
    rank_roles,
)


class FitDimension(StrEnum):
    """A kind of reason one product fits a Target Account better than another.

    **Exactly one value, and that is honest rather than unfinished.** Each
    dimension needs a declaration the Signora Customer has actually made or a
    record the pipeline actually keeps; adding values ahead of those would put
    reasons in an enum that nothing could ever produce.
    """

    COMMITTEE_OVERLAP = "committee_overlap"
    """The evidence names roles this product's Buying Committee declares."""


@dataclass(frozen=True, slots=True)
class ProductRef:
    """One product in the Signora Customer's portfolio."""

    id: UUID
    name: str

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise ReasoningError("a product has no name.")


@dataclass(frozen=True, slots=True)
class FitReason:
    """Why a product fits, in a form a seller can disagree with specifically.

    **Structural rather than prose.** *"Because the evidence names your VP of
    Engineering, who is on Revenue Cloud's committee"* is a claim with parts; a
    paragraph saying the same thing is one a seller can only accept or reject
    whole.
    """

    dimension: FitDimension
    detail: str


@dataclass(frozen=True, slots=True)
class ProductFit:
    """How well one product fits, and why."""

    product: ProductRef
    strength: Strength
    reasons: tuple[FitReason, ...]

    def __post_init__(self) -> None:
        if not self.reasons:
            raise ReasoningError(
                "a product fit states no reason. **Which product** and **why that product** "
                "are the same answer here, and one without the other is a verdict."
            )


def fit(
    committees: Mapping[ProductRef, tuple[CommitteeRoleRef, ...]],
    evidence: tuple[Evidence, ...],
    *,
    now: datetime,
) -> tuple[ProductFit, ...]:
    """Rank the portfolio by how well the evidence fits each product.

    **Reuses the role ranking rather than repeating it.** A product fits to the
    degree its declared committee is named by what has happened at the Target
    Account — so this asks `rank_roles` the same question per product and reads
    the answer. Two implementations of the same join would disagree the first
    time either changed.

    Products with no named role are **absent** rather than present at zero: a
    portfolio of nine with one fit should read as one fit, not as nine rows of
    which eight say nothing.
    """
    fits: list[ProductFit] = []
    for product, committee in committees.items():
        ranked = tuple(one for one in rank_roles(committee, evidence, now=now) if one.strength)
        if not ranked:
            continue

        best = ranked[0].strength
        assert best is not None  # filtered above; narrowing only
        fits.append(
            ProductFit(
                product=product,
                strength=best,
                reasons=tuple(
                    FitReason(
                        dimension=FitDimension.COMMITTEE_OVERLAP,
                        detail=(
                            f"{one.role.title} is on this product's buying committee, and "
                            f"{one.support[-1].summary.lower()}."
                        ),
                    )
                    for one in ranked
                ),
            )
        )

    fits.sort(key=lambda one: (_ORDER[one.strength], -len(one.reasons)))
    return tuple(fits)


def likely(fits: tuple[ProductFit, ...]) -> ProductRef | None:
    """The product this Target Account is probably about, or `None`.

    **`None` on a tie is the whole point.** Two products fitting equally well
    is a question for the seller, and picking one would be the platform
    inventing a commercial decision it has no evidence for — the same refusal
    that stops it resolving a disagreement between two providers.

    **`None` also when the portfolio fits nothing**, which is a different
    sentence with the same shape: *Signora cannot tell*, said out loud rather
    than by omission.
    """
    if not fits:
        return None
    if len(fits) > 1 and _tied(fits[0], fits[1]):
        return None
    return fits[0].product


def _tied(first: ProductFit, second: ProductFit) -> bool:
    return first.strength is second.strength and len(first.reasons) == len(second.reasons)


#: Reading order, and **not a weight** — the same refusal `Strength` makes.
_ORDER: dict[Strength, int] = {Strength.STRONG: 0, Strength.REASONABLE: 1, Strength.THIN: 2}
