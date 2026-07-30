"""The one root every AI Platform failure descends from.

Extracted here rather than left in ``provider.py`` because it stopped being
true there. That module declared ``AIPlatformError`` *"the base for
everything this module raises"* while ``EvidenceError`` descended from
``ValueError`` alone — so a caller catching the documented base would have
missed the module's most serious failure, a cross-workspace evidence set.

A base class that does not actually cover the module is worse than none:
callers write the broad ``except`` the docstring promises, it silently fails
to catch, and the gap surfaces as an unhandled exception in production
rather than as a review comment.
"""

from __future__ import annotations


class AIPlatformError(Exception):
    """Base for everything the AI Platform raises.

    Descendants are split by **what was actually reached** — a rule that
    matters because an incorrect attribution misdirects an investigation
    more effectively than no attribution does (CLAUDE.md §6):

    - ``InferenceRequestError`` · ``ModelNotRegisteredError`` — no vendor was
      involved, so none is named.
    - ``AIRegistrationError`` — composition-time, names the adapter.
    - ``AIProviderError`` and below — a vendor call failed, always names the
      vendor.
    - ``EvidenceError`` — an evidence set could not be a closed universe.
    - ``GroundingError`` — output did not correspond to the evidence.
    """
