"""The rule registry — one rule per business event type.

Declared here rather than discovered, so a rule that exists but is never
registered is a visible omission rather than a silent one. The pairing
with the taxonomy is asserted at load time: a declared type with no rule
is a promise the product cannot keep, and a rule with no declaration is a
business threshold nobody reviewed.
"""

from modules.business_event_engine.domain.rules.base import Detection, DetectionRule, window_of
from modules.business_event_engine.domain.rules.point import POINT_RULES
from modules.business_event_engine.domain.rules.window import WINDOW_RULES

RULES: tuple[DetectionRule, ...] = POINT_RULES + WINDOW_RULES

__all__ = ["RULES", "Detection", "DetectionRule", "window_of"]
