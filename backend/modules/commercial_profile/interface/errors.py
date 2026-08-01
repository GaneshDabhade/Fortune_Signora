"""How this module's domain errors surface over HTTP.

The domain raises meaning; this table assigns it a transport representation.
Messages reach the caller verbatim, because a refusal here is a statement
about the customer's own declaration and they are entitled to the reason.
"""

from fastapi import status

from modules.commercial_profile.application.publish import CatalogVersionConflictError
from modules.commercial_profile.domain.catalog import CommercialProfileError
from signora_platform.api import ErrorMapping

ERROR_MAPPING: ErrorMapping = {
    # **409, not 422.** The request is well-formed and the caller is
    # permitted; what changed is the world. A colleague saved first, and the
    # only useful response is to say so and let this caller reload rather
    # than overwrite work they have not seen.
    CatalogVersionConflictError: (status.HTTP_409_CONFLICT, "catalog_version_conflict"),
    # Everything the domain refuses: an unnamed product, two products sharing
    # a name, the same product listed twice. Registered after the row above
    # and never shadowing it — handler lookup walks the exception's MRO, so
    # the derived type still wins for its own instances.
    CommercialProfileError: (
        status.HTTP_422_UNPROCESSABLE_CONTENT,
        "catalog_refused",
    ),
}
