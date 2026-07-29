"""The Signal Engine's public contract.

**The first customer-specific layer in the pipeline.** Business events
describe objective business phenomena; signals describe *this workspace's*
commercial hypotheses about them — false for a company selling something
else, and unknowable from the evidence alone.

Consumers get hypotheses with their evidence and the interpretation that
produced them. There is deliberately no score, priority, likelihood, or
rank anywhere in this surface: how much something matters is the Buying
Score Engine's question.
"""

from modules.signal_engine.application.queries import SignalExplanation, SignalQueries
from modules.signal_engine.domain.catalog import (
    DetectionStrategy,
    Relevance,
    SignalCatalog,
    SignalType,
    SignalTypeDefinition,
)
from modules.signal_engine.domain.profile import (
    DEFAULT_PROFILE_VERSION,
    ProfileEntry,
    SignalProfile,
)
from modules.signal_engine.domain.signal import Signal

__all__ = [
    "DEFAULT_PROFILE_VERSION",
    "DetectionStrategy",
    "ProfileEntry",
    "Relevance",
    "Signal",
    "SignalCatalog",
    "SignalExplanation",
    "SignalProfile",
    "SignalQueries",
    "SignalType",
    "SignalTypeDefinition",
]
