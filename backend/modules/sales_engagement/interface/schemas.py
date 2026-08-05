"""HTTP response schemas for the approach read path.

**Facts travel; sentences are the frontend's** — the precedent the Decision
Package schema set, and ADR-0034's rule that presentation lives at the frontend
edge. `strength`, `why_not`, `kind` and `action` are returned as the values the
domain computed, never as the prose a screen builds from them.

**A ranked role and its support are inseparable.** The whole value of this
surface is *why* a role ranked where it did, and a wire format able to carry
the ranking without the evidence would make the ranking an opinion. Same rule
as the citations on a reasoned statement, one module over.

**`why_not` is a first-class field, not an error.** An unranked role carries
the sentence *"no evidence names your CFO"*, which the domain calls "the whole
value of an unranked one" — a ranked list structurally cannot say it, and a
schema that dropped it would turn a useful absence into a silent one.

**What is deliberately absent.** No `id`, no `correlation_id`: they are how an
engineer traces a request, not how a seller decides anything. And no synthesis
— the prose that explains an approach is a separate use case with a separate
model call, and folding it in here would put a provider on a read path (§7).
"""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from modules.sales_engagement.application.approach import Approach
from modules.sales_engagement.domain.fit import ProductFit
from modules.sales_engagement.domain.reasoning import Evidence, RankedRole


class EvidenceResponse(BaseModel):
    """One recorded fact the ranking rests on. **A citation, never a copy.**"""

    model_config = ConfigDict(frozen=True)

    event_id: UUID = Field(
        description=(
            "The Business Event Engine's identifier. Follow it to the observations and "
            "providers behind it — this module reproduces none of them."
        )
    )
    type_key: str = Field(description="What kind of thing happened, in Signora's business language.")
    summary: str = Field(description="The sentence a customer reads, rendered by the rule that detected it.")
    occurred_at: datetime = Field(
        description="When it happened in the customer's business, never when Signora noticed."
    )
    corroborating_providers: int = Field(
        description="How many providers' series independently supported it. A count of agreement, never a weight."
    )

    @classmethod
    def from_domain(cls, evidence: Evidence) -> "EvidenceResponse":
        return cls(
            event_id=evidence.event_id,
            type_key=evidence.type_key,
            summary=evidence.summary,
            occurred_at=evidence.occurred_at,
            corroborating_providers=evidence.corroborating_providers,
        )


class RankedRoleResponse(BaseModel):
    """One seat on the buying committee, and why it ranked where it did."""

    model_config = ConfigDict(frozen=True)

    title: str = Field(description="The customer's own words for the role.")
    part: str = Field(
        description=(
            "The part they play in a purchase, as Commercial Profile declared it. A value "
            "this response does not recognise is a part that module has added."
        )
    )
    strength: str | None = Field(
        default=None,
        description="How well the evidence supports approaching them. Absent when nothing does.",
    )
    support: tuple[EvidenceResponse, ...] = Field(
        default=(), description="The evidence that ranked them. Empty exactly when unranked."
    )
    why_not: str | None = Field(
        default=None,
        description=(
            "Why this role did not rank. The whole value of an unranked role — a list that "
            "silently omitted them would be less useful, not cleaner."
        ),
    )

    @classmethod
    def from_domain(cls, ranked: RankedRole) -> "RankedRoleResponse":
        return cls(
            title=ranked.role.title,
            part=ranked.role.part,
            strength=None if ranked.strength is None else ranked.strength.value,
            support=tuple(EvidenceResponse.from_domain(item) for item in ranked.support),
            why_not=ranked.why_not,
        )


class FitReasonResponse(BaseModel):
    """Why a product fits, in a form a seller can disagree with specifically.

    **Structural rather than prose**, which is the domain's own reasoning: a
    paragraph saying the same thing is one a seller can only accept or reject
    whole.
    """

    model_config = ConfigDict(frozen=True)

    dimension: str
    detail: str


class ProductFitResponse(BaseModel):
    """How well one product fits this account, and why."""

    model_config = ConfigDict(frozen=True)

    product_id: UUID
    product_name: str
    strength: str
    reasons: tuple["FitReasonResponse", ...] = Field(
        description="Why that product. A fit that stated no reason would be a verdict."
    )

    @classmethod
    def from_domain(cls, fit: ProductFit) -> "ProductFitResponse":
        return cls(
            product_id=fit.product.id,
            product_name=fit.product.name,
            strength=fit.strength.value,
            reasons=tuple(
                FitReasonResponse(dimension=reason.dimension.value, detail=reason.detail)
                for reason in fit.reasons
            ),
        )


class UnknownResponse(BaseModel):
    """Something the platform cannot answer, and the question that would."""

    model_config = ConfigDict(frozen=True)

    subject: str
    question: str


class RiskResponse(BaseModel):
    """Something that argues against approaching this account now."""

    model_config = ConfigDict(frozen=True)

    kind: str
    detail: str


class RecommendationResponse(BaseModel):
    """What to do with the next fifteen minutes, and why."""

    model_config = ConfigDict(frozen=True)

    action: str = Field(description="Approach, verify, or wait.")
    reason: str
    role_title: str | None = Field(
        default=None, description="Who to approach, where the recommendation names one."
    )


class ApproachResponse(BaseModel):
    """How to approach one account, and everything that argues about it.

    **`fits` is empty when the seller said which product**, and that is the
    domain's decision rather than a missing field: showing a ranking beside
    somebody's own answer invites them to re-litigate a decision they made.
    """

    model_config = ConfigDict(frozen=True)

    account_id: UUID
    recommendation: RecommendationResponse
    roles: tuple[RankedRoleResponse, ...]
    unknowns: tuple[UnknownResponse, ...]
    risks: tuple[RiskResponse, ...]
    product_id: UUID | None = Field(
        default=None,
        description=(
            "Which product this approach is about, where one could be inferred. Absent when "
            "the seller already said, when two products tie, and when nothing fits."
        ),
    )
    product_name: str | None = None
    fits: tuple[ProductFitResponse, ...] = Field(
        default=(), description="How each product ranked, when the product had to be inferred."
    )

    @classmethod
    def from_domain(cls, approach: Approach) -> "ApproachResponse":
        reasoning = approach.reasoning
        recommendation = reasoning.recommendation
        return cls(
            account_id=reasoning.account_id,
            recommendation=RecommendationResponse(
                action=recommendation.action.value,
                reason=recommendation.reason,
                role_title=None if recommendation.role is None else recommendation.role.title,
            ),
            roles=tuple(RankedRoleResponse.from_domain(role) for role in reasoning.roles),
            unknowns=tuple(
                UnknownResponse(subject=unknown.subject, question=unknown.question)
                for unknown in reasoning.unknowns
            ),
            risks=tuple(
                RiskResponse(kind=risk.kind.value, detail=risk.detail) for risk in reasoning.risks
            ),
            product_id=None if approach.product is None else approach.product.id,
            product_name=None if approach.product is None else approach.product.name,
            fits=tuple(ProductFitResponse.from_domain(fit) for fit in approach.fits),
        )


__all__ = [
    "ApproachResponse",
    "EvidenceResponse",
    "FitReasonResponse",
    "ProductFitResponse",
    "RankedRoleResponse",
    "RecommendationResponse",
    "RiskResponse",
    "UnknownResponse",
]
