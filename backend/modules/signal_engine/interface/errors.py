"""How this module's domain errors surface over HTTP.

Kept in the interface layer, because status codes are an HTTP concern: the
domain raises meaning, and this table assigns it a transport representation.
The composition root collects these mappings and registers them once
(19-api-conventions.md).

**The module's first mapping, because this is its first write.** Everything
before it was a read, and a read that finds nothing answers with an empty list
rather than an error.

**Two meanings, two rows, and the split is the point** (`B-103`). A resolution
the customer got wrong — a dismissal with no reason, a snooze already elapsed —
is `422`, and the message is written to be read by them. A `Resolution` the
platform should not have been able to construct is not the customer's fault and
must never be reported as though it were; `ResolutionError` covers both, so the
one that reaches a customer is deliberately the refusal.
"""

from fastapi import status

from modules.signal_engine.application.resolve import SignalNotFoundError
from modules.signal_engine.domain.resolution import ResolutionError, UnreadableOutcomeError
from signora_platform.api import ErrorMapping

ERROR_MAPPING: ErrorMapping = {
    # **404, and it does not say which of the two it is.** A signal that does
    # not exist and one belonging to another workspace answer identically —
    # distinguishing them would tell somebody who cannot see a workspace
    # whether it holds a particular signal.
    SignalNotFoundError: (status.HTTP_404_NOT_FOUND, "signal_not_found"),
    # A decision the customer described in a way the product cannot record: a
    # dismissal with no reason, a snooze that has already elapsed. **The
    # message is customer copy** — it says which part was wrong and why the
    # product insists on it.
    # A stored decision this build cannot interpret. **500, because the
    # customer did nothing wrong** — the same split `B-103` established in
    # `ai_research_engine`, applied here before it could ship as a defect.
    UnreadableOutcomeError: (
        status.HTTP_500_INTERNAL_SERVER_ERROR,
        "resolution_unreadable",
    ),
    ResolutionError: (status.HTTP_422_UNPROCESSABLE_CONTENT, "resolution_refused"),
}

__all__ = ["ERROR_MAPPING"]
