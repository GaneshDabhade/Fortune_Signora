"""The Opportunity Engine's public contract.

**Signora's first workflow module.** Every module upstream derives
information from evidence and can be regenerated from it; this one records
human commitment, which nothing reproduces.

*Permanent architectural principle, ratified 2026-07-29:*

> **Intelligence suggests. Humans commit.**
>
> A buying score may **create** an opportunity. **Only a human may progress
> one beyond the machine-authored boundary.** Commercial intelligence
> informs workflow; it never owns it.

What consumers get is what Sales should actively **track** — never what
Sales should *do*. There is deliberately no recommendation, next action,
message, or reasoning in this surface, and no stored copy of any derived
intelligence: an opportunity cites the score that caused it to exist and
reads everything else live.

An opportunity **outlives the score that created it**. The score explains
why it was opened; it does not control whether it stays open, and no code
path in this module closes anything without a person.
"""

from modules.opportunity_engine.application.queries import (
    OpportunityExplanation,
    OpportunityQueries,
    TrackedOpportunity,
    evidence_state,
)
from modules.opportunity_engine.domain.opportunity import (
    MACHINE_AUTHORED,
    OPEN_STAGES,
    TERMINAL_STAGES,
    EvidenceState,
    Opportunity,
    OpportunityState,
    Qualification,
    Stage,
    allowed_from,
)
from modules.opportunity_engine.domain.policy import (
    DEFAULT_POLICY_VERSION,
    OpportunityPolicy,
    WorkspaceOpportunityPolicy,
)

__all__ = [
    "DEFAULT_POLICY_VERSION",
    "MACHINE_AUTHORED",
    "OPEN_STAGES",
    "TERMINAL_STAGES",
    "EvidenceState",
    "Opportunity",
    "OpportunityExplanation",
    "OpportunityPolicy",
    "OpportunityQueries",
    "OpportunityState",
    "Qualification",
    "Stage",
    "TrackedOpportunity",
    "WorkspaceOpportunityPolicy",
    "allowed_from",
    "evidence_state",
]
