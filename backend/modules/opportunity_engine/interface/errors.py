"""How this module's domain errors surface over HTTP.

Kept in the interface layer, because status codes are an HTTP concern: the
domain raises meaning, and this table assigns it a transport representation.
The composition root collects these mappings and registers them once
(19-api-conventions.md).

**The messages reach the caller verbatim.** The domain's refusals are written
to be read — *"'closed_won' cannot become 'engaged'. A won deal does not
reopen…"* — and the platform's handler passes `str(exc)` through. That is
deliberate here in a way it would not be for, say, an authentication failure:
a workflow refusal is a statement about the customer's own data, and telling
them exactly why is the whole point of a module that insists every state
records its reason.
"""

from fastapi import status

from modules.opportunity_engine.application.transition import (
    MembershipError,
    OpportunityNotFound,
)
from modules.opportunity_engine.domain.opportunity import OpportunityError
from signora_platform.api import ErrorMapping

ERROR_MAPPING: ErrorMapping = {
    # An opportunity the caller cannot see is indistinguishable from one that
    # was never created — the same rule the workspace itself follows.
    OpportunityNotFound: (status.HTTP_404_NOT_FOUND, "opportunity_not_found"),
    # The *assignee* is not a member. Not 403: the caller is permitted to do
    # this, and naming the wrong person is a fault in the request rather than
    # in their permissions. Attributing it to the caller would send an
    # engineer looking at the wrong account.
    MembershipError: (status.HTTP_422_UNPROCESSABLE_CONTENT, "owner_not_a_member"),
    # Everything the domain refuses: an illegal stage change, a state that
    # changes nothing, a decision with no reason. Registered last in the
    # source but never last in effect — handler lookup walks the exception's
    # MRO, so the two rows above still win for their own types.
    OpportunityError: (status.HTTP_422_UNPROCESSABLE_CONTENT, "transition_refused"),
}
