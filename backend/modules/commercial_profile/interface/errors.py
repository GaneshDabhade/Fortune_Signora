"""How this module's domain errors surface over HTTP.

The domain raises meaning; this table assigns it a transport representation.
Messages reach the caller verbatim, because a refusal here is a statement
about the customer's own declaration and they are entitled to the reason.
"""

from fastapi import status

from modules.commercial_profile.application.declare_icp import (
    IcpVersionConflictError,
    UnknownProductError,
)
from modules.commercial_profile.application.publish import CatalogVersionConflictError
from modules.commercial_profile.domain.declaration import CommercialProfileError
from modules.commercial_profile.domain.icp import IcpError
from signora_platform.api import ErrorMapping

ERROR_MAPPING: ErrorMapping = {
    # **409, not 422.** The request is well-formed and the caller is
    # permitted; what changed is the world. A colleague saved first, and the
    # only useful response is to say so and let this caller reload rather
    # than overwrite work they have not seen.
    CatalogVersionConflictError: (status.HTTP_409_CONFLICT, "catalog_version_conflict"),
    # The same reasoning, and a **distinct code** rather than a shared one:
    # the two refusals send the reader to different pages, and a client that
    # cannot tell them apart can only say "something changed".
    IcpVersionConflictError: (status.HTTP_409_CONFLICT, "icp_version_conflict"),
    # Its own code because it is the only refusal here a caller fixes
    # somewhere else — in the catalog, not on the page they are looking at.
    UnknownProductError: (status.HTTP_422_UNPROCESSABLE_CONTENT, "icp_unknown_product"),
    # Everything the ideal customer refuses: a description with no criteria, a
    # size range whose floor is above its ceiling, the same industry twice.
    IcpError: (status.HTTP_422_UNPROCESSABLE_CONTENT, "icp_refused"),
    # Everything the domain refuses: an unnamed product, two products sharing
    # a name, an ideal customer with no criteria, a size range whose floor is
    # above its ceiling. Registered after the rows above and never shadowing
    # them — handler lookup walks the exception's MRO, so a derived type still
    # wins for its own instances.
    CommercialProfileError: (
        status.HTTP_422_UNPROCESSABLE_CONTENT,
        "catalog_refused",
    ),
}
