"""How this module's domain errors surface over HTTP.

The domain raises meaning; this table assigns it a transport representation.
Messages reach the caller verbatim, because a refusal here is a statement
about the customer's own declaration and they are entitled to the reason.
"""

from fastapi import status

from modules.commercial_profile.application.declare_committee import (
    CommitteeVersionConflictError,
)
from modules.commercial_profile.application.declare_competitors import (
    CompetitorsVersionConflictError,
)
from modules.commercial_profile.application.declare_focus import FocusVersionConflictError
from modules.commercial_profile.application.declare_icp import IcpVersionConflictError
from modules.commercial_profile.application.declare_target_accounts import (
    TargetAccountsVersionConflictError,
)
from modules.commercial_profile.application.declaring import (
    CommitteeUnknownProductError,
    FocusUnknownProductError,
    IcpUnknownProductError,
)
from modules.commercial_profile.application.publish import CatalogVersionConflictError
from modules.commercial_profile.application.assignment_use_cases import (
    NotAWorkspaceMemberError,
)
from modules.commercial_profile.domain.account_assignment import AssignmentError
from modules.commercial_profile.domain.account_tag import AccountTagError
from modules.commercial_profile.domain.committee import BuyingCommitteeError
from modules.commercial_profile.domain.competitors import CompetitorsError
from modules.commercial_profile.domain.declaration import CommercialProfileError
from modules.commercial_profile.domain.focus import CommercialFocusError
from modules.commercial_profile.domain.icp import IcpError
from modules.commercial_profile.domain.target_accounts import TargetAccountError
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
    IcpUnknownProductError: (
        status.HTTP_422_UNPROCESSABLE_CONTENT,
        "icp_unknown_product",
    ),
    CommitteeVersionConflictError: (
        status.HTTP_409_CONFLICT,
        "committee_version_conflict",
    ),
    # **One condition, three codes by slice 4**, and deliberately not one
    # neutral `unknown_product`: renaming a shipped code is outside this
    # lane's budget, and each code names the page the reader fixes it on.
    # The consolidation is raised for the product owner rather than taken.
    CommitteeUnknownProductError: (
        status.HTTP_422_UNPROCESSABLE_CONTENT,
        "committee_unknown_product",
    ),
    FocusVersionConflictError: (status.HTTP_409_CONFLICT, "focus_version_conflict"),
    TargetAccountsVersionConflictError: (
        status.HTTP_409_CONFLICT,
        "target_accounts_version_conflict",
    ),
    CompetitorsVersionConflictError: (
        status.HTTP_409_CONFLICT,
        "competitors_version_conflict",
    ),
    # Everything the competitor list refuses: a blank name, a name past the
    # limit, the same entry twice, two rivals sharing a name.
    CompetitorsError: (status.HTTP_422_UNPROCESSABLE_CONTENT, "competitors_refused"),
    FocusUnknownProductError: (
        status.HTTP_422_UNPROCESSABLE_CONTENT,
        "focus_unknown_product",
    ),
    # Everything the ideal customer refuses: a description with no criteria, a
    # size range whose floor is above its ceiling, the same industry twice.
    IcpError: (status.HTTP_422_UNPROCESSABLE_CONTENT, "icp_refused"),
    # Everything the committee refuses: an empty one, two roles sharing a
    # title, a role with no title.
    BuyingCommitteeError: (status.HTTP_422_UNPROCESSABLE_CONTENT, "committee_refused"),
    # A duplicated product in the focus, or an objective past its limit.
    CommercialFocusError: (status.HTTP_422_UNPROCESSABLE_CONTENT, "focus_refused"),
    # An unnamed company, two entries sharing a name, the same entry twice.
    # **No `*_unknown_product` here** — a watch list cites no product, so the
    # condition C-003 tracks does not reach a fourth code after all.
    TargetAccountError: (
        status.HTTP_422_UNPROCESSABLE_CONTENT,
        "target_accounts_refused",
    ),
    # Everything the domain refuses: an unnamed product, two products sharing
    # a name, an ideal customer with no criteria, a size range whose floor is
    # above its ceiling. Registered after the rows above and never shadowing
    # them — handler lookup walks the exception's MRO, so a derived type still
    # wins for its own instances.
    # **Listed before the base class it inherits, as a reading convention.**
    # `AccountTagError` extends `CommercialProfileError`, and without its own
    # row a customer who typed a duplicate label would be told
    # `catalog_refused` — a code naming a document they were not editing.
    #
    # ⚠️ **Corrected 2026-08-14: the ORDER is not what prevents that, and this
    # comment previously implied it was.** Handler lookup walks the exception's
    # MRO, exactly as the note above says, **so the derived row wins wherever
    # it sits.** 🔴 **Measured rather than reasoned**: moving this row after
    # `CommercialProfileError` leaves all 18 tag API tests green.
    #
    # ⛔ **The false claim mattered.** It was reported to QE as a load-bearing
    # choice to check during TASK-466's validation, and a comment that sends a
    # reviewer to verify a mechanism that does not exist is the [§2](../../../../CLAUDE.md)
    # defect — *"the comment beside it is then a false claim that survives
    # review."* **What actually protects the code is the row's existence, and
    # a test that pins the code.**
    # **Before `AssignmentError`, by the same reading convention** — and, like
    # that row, **not because the order decides anything.** ⚡ *"This person is
    # not on your team"* and *"this selection named no accounts"* are answered
    # by different people (📁 §10's truthful-attribution rule), and a shared
    # code would send a customer to look at their selection when the problem is
    # their colleague. **The distinct row is what prevents that; `test_api_
    # account_assignments.py` pins the code so the row cannot quietly go.**
    AssignmentError: (
        status.HTTP_422_UNPROCESSABLE_CONTENT,
        "account_assignment_refused",
    ),
    NotAWorkspaceMemberError: (
        status.HTTP_422_UNPROCESSABLE_CONTENT,
        "not_a_workspace_member",
    ),
    AccountTagError: (
        status.HTTP_422_UNPROCESSABLE_CONTENT,
        "account_tag_refused",
    ),
    CommercialProfileError: (
        status.HTTP_422_UNPROCESSABLE_CONTENT,
        "catalog_refused",
    ),
}
