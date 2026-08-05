"""How this module's domain errors surface over HTTP.

Kept in the interface layer, because status codes are an HTTP concern: the
domain raises meaning, and this table assigns it a transport representation.
The composition root collects these mappings and registers them once
(19-api-conventions.md).
"""

from fastapi import status

from modules.ai_research_engine.application.queries import ResearchArtifactMissing
from modules.ai_research_engine.application.request import NoOpportunityToResearch
from modules.ai_research_engine.domain.request import (
    ResearchRequestError,
    ResearchRequestInvariantError,
)
from signora_platform.api import ErrorMapping

ERROR_MAPPING: ErrorMapping = {
    # An account Signora has not qualified is indistinguishable from one the
    # caller cannot see — the same rule the workspace itself follows, applied
    # to a resource inside it.
    NoOpportunityToResearch: (status.HTTP_404_NOT_FOUND, "nothing_to_research"),
    # A completed request naming an artifact that is not stored. **500, not
    # 404**: the customer asked correctly and the platform lost something, and
    # answering "not found" would attribute our fault to their request.
    ResearchArtifactMissing: (status.HTTP_500_INTERNAL_SERVER_ERROR, "research_artifact_missing"),
    # A state the platform should never have been able to construct. **500,
    # like `ResearchArtifactMissing` above and for the same reason**: the
    # customer did nothing wrong, and telling them their request was refused
    # sends support to look at their data for a bug in ours (`B-103`).
    #
    # **This row is what splits the two meanings**, not the exception's
    # position in the file. `ResearchRequestInvariantError` subclasses
    # `ResearchRequestError`, and handler lookup walks the MRO, so the more
    # specific type finds this row before reaching the one below.
    ResearchRequestInvariantError: (
        status.HTTP_500_INTERNAL_SERVER_ERROR,
        "research_request_invalid",
    ),
    # Everything the domain refuses **because of something the customer did** —
    # asking a settled request to change again. Registered last in the source
    # but never last in effect: handler lookup walks the exception's MRO, so
    # the rows above still win for their own types.
    ResearchRequestError: (status.HTTP_422_UNPROCESSABLE_CONTENT, "research_request_refused"),
}
