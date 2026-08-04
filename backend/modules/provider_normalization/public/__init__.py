"""Provider Normalization's public contract.

Other modules and the composition root import from here. Nothing imports
`domain/`, `application/`, or `infrastructure/` directly (CLAUDE.md §5).

The canonical vocabulary is re-exported deliberately: it is Signora's
controlled language, and every downstream module reasons in its terms.
Extending it requires an RFC; consuming it does not.
"""

from modules.provider_normalization.domain.vocabulary import (
    VOCABULARY_VERSION,
    AcquisitionValue,
    ClaimAttribute,
    ClaimDomain,
    FundingValue,
    IntentSurgeValue,
    RevenueBand,
    RoleChangeValue,
    RoleDirection,
    TechnologyValue,
    TrendDirection,
)
from modules.provider_normalization.public.claims import (
    ClaimReader,
    ClaimView,
    NameMatch,
    SubjectRef,
    TechnologyRef,
)

__all__ = [
    "VOCABULARY_VERSION",
    "AcquisitionValue",
    "ClaimAttribute",
    "ClaimDomain",
    "ClaimReader",
    "ClaimView",
    "FundingValue",
    "IntentSurgeValue",
    "NameMatch",
    "RevenueBand",
    "RoleChangeValue",
    "RoleDirection",
    "SubjectRef",
    "TechnologyRef",
    "TechnologyValue",
    "TrendDirection",
]
