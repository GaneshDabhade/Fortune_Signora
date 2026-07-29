"""The Business Event Engine's public contract — Signora's business language.

This is the vocabulary the product, analytics, AI reasoning,
recommendations, customer interfaces, and future integrations all speak.
Downstream modules should reference **business event types** rather than
re-deriving meaning from observations.

What consumers get is **what happened in the customer's business**, never
what to do about it. There is deliberately no priority, score, urgency, or
rank anywhere in this surface: how important an account is, whether Sales
should engage, and how likely a purchase is are questions for the Signal
Engine and everything after it.
"""

from modules.business_event_engine.application.queries import (
    BusinessEventEvidence,
    BusinessEventQueries,
)
from modules.business_event_engine.domain.business_event import BusinessEvent
from modules.business_event_engine.domain.taxonomy import (
    BusinessDomain,
    BusinessEventType,
    Taxonomy,
    TypeDefinition,
)

__all__ = [
    "BusinessDomain",
    "BusinessEvent",
    "BusinessEventEvidence",
    "BusinessEventQueries",
    "BusinessEventType",
    "Taxonomy",
    "TypeDefinition",
]
