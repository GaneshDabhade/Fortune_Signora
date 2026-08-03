"""Sales Engagement's published contract.

**This module owns commercial reasoning and commercial synthesis, and no fact
at all** ([ADR-0200](../../../../docs/architecture/adr/0200-sales-engagement.md)).
Every value it publishes is derived at read time from facts other modules own;
drop everything it stores and every conclusion is reproduced.

**Reasoning is exported; synthesis is not, and will not be.** Prose is a
rendering of the values below, and a consumer that wanted the prose without the
values would have no way to check it — which is the one thing this design
exists to prevent.

**Nothing reads this module today.** It is exported for the API layer, which
composes it onto the account brief; no pipeline module may consume it, because
a derived conclusion is not a fact and a module that stored one would have
created the second representation this architecture refuses.
"""

from modules.sales_engagement.application.approach import (
    Approach,
    ApproachInput,
    AssembleApproach,
)
from modules.sales_engagement.application.ports import (
    CommitteeReader,
    EvidenceReader,
    PortfolioReader,
)
from modules.sales_engagement.domain.brief import (
    ApproachBrief,
    Pass,
    assemble,
)
from modules.sales_engagement.domain.fit import (
    FitDimension,
    FitReason,
    ProductFit,
    ProductRef,
    fit,
    likely,
)
from modules.sales_engagement.domain.reasoning import (
    STALE_AFTER_DAYS,
    ApproachReasoning,
    CommitteeRoleRef,
    Evidence,
    NextAction,
    RankedRole,
    ReasoningError,
    Recommendation,
    Risk,
    RiskKind,
    Strength,
    Unknown,
    contradictions,
    rank_roles,
    reason,
    recommend,
    risks,
    unknowns,
    vacancy,
)
from modules.sales_engagement.domain.synthesis import (
    Passage,
    Synthesis,
    SynthesisRefusedError,
    SynthesisSource,
    validate,
)

__all__ = [
    "STALE_AFTER_DAYS",
    "Approach",
    "ApproachBrief",
    "ApproachInput",
    "ApproachReasoning",
    "AssembleApproach",
    "CommitteeReader",
    "CommitteeRoleRef",
    "Evidence",
    "EvidenceReader",
    "FitDimension",
    "FitReason",
    "PortfolioReader",
    "ProductFit",
    "ProductRef",
    "NextAction",
    "Pass",
    "Passage",
    "RankedRole",
    "ReasoningError",
    "Recommendation",
    "Risk",
    "RiskKind",
    "Strength",
    "Synthesis",
    "SynthesisRefusedError",
    "SynthesisSource",
    "Unknown",
    "assemble",
    "contradictions",
    "fit",
    "rank_roles",
    "reason",
    "likely",
    "recommend",
    "risks",
    "unknowns",
    "validate",
    "vacancy",
]
