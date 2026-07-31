"""The Knowledge Graph's public contract.

Downstream modules import from here and nowhere deeper. What they get is
**identity and evidence, never a resolved value**: an entity, the provider
identities bound to it, the decisions that explain why, the edges between
entities, and claim *sets*.

`MatchStrength` is exported as the semantic category it is. It must never
be converted to a number or used in a weighted calculation; the type itself
refuses both.
"""

from modules.knowledge_graph.application.queries import (
    AccountIdentity,
    ClaimSet,
    EntityEvidence,
    GraphQueries,
)
from modules.knowledge_graph.domain.identity import (
    USES_TECHNOLOGY,
    Entity,
    EntityKind,
    IdentityBinding,
    IdentityState,
    MatchStrength,
    Relationship,
    ResolutionDecision,
    ResolutionOutcome,
    ResolutionReason,
    ResolutionRule,
)
from modules.knowledge_graph.domain.naming import NameAgreement, SelectedName, select_name

__all__ = [
    "USES_TECHNOLOGY",
    "AccountIdentity",
    "ClaimSet",
    "Entity",
    "EntityEvidence",
    "EntityKind",
    "GraphQueries",
    "IdentityBinding",
    "NameAgreement",
    "IdentityState",
    "MatchStrength",
    "Relationship",
    "ResolutionDecision",
    "ResolutionOutcome",
    "ResolutionReason",
    "ResolutionRule",
    "SelectedName",
    "select_name",
]
