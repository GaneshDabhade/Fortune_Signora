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
    AccountPage,
    ListedAccount,
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
from modules.knowledge_graph.domain.attributes import (
    ResolvedAttribute,
    ValueAgreement,
)
from modules.knowledge_graph.domain.naming import NameAgreement, SelectedName, select_name
from modules.knowledge_graph.public.attributes import (
    AccountAttributes,
    AccountAttributesReader,
)

__all__ = [
    "ListedAccount",
    "AccountPage",
    "AccountAttributes",
    "AccountAttributesReader",
    "AccountIdentity",
    "ClaimSet",
    "Entity",
    "EntityEvidence",
    "EntityKind",
    "GraphQueries",
    "IdentityBinding",
    "IdentityState",
    "MatchStrength",
    "NameAgreement",
    "Relationship",
    "ResolutionDecision",
    "ResolutionOutcome",
    "ResolutionReason",
    "ResolutionRule",
    "ResolvedAttribute",
    "SelectedName",
    "USES_TECHNOLOGY",
    "ValueAgreement",
    "select_name",
]
