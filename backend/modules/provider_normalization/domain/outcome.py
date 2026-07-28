"""The result of normalizing one raw record.

**Not a bare list of claims.** A record yielding zero claims must be
distinguishable from one never processed, and a field the mapper could not
translate must be a diagnosable event rather than a silent null.

A vendor shape change is an operational incident. It arrives as a rising
rejection rate, and that is only visible if rejections are recorded as
data rather than logged and forgotten.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from uuid import UUID

from modules.provider_normalization.domain.claim import Claim


class RejectionReason(StrEnum):
    UNKNOWN_FIELD = "unknown_field"
    """The payload carried something the mapper does not recognise — the
    signature of a vendor adding a field."""

    MISSING_REQUIRED_FIELD = "missing_required_field"
    """The mapper expected something absent — the signature of a vendor
    renaming or removing one. The more urgent of the two."""

    UNPARSEABLE_VALUE = "unparseable_value"
    UNRESOLVABLE_SUBJECT = "unresolvable_subject"
    UNSUPPORTED_CAPABILITY = "unsupported_capability"


@dataclass(frozen=True, slots=True)
class Rejection:
    reason: RejectionReason
    #: The field or path that failed. Named precisely, because "mapping
    #: failed" costs an engineer an hour that "employee_count absent" does
    #: not.
    detail: str


@dataclass(frozen=True, slots=True)
class NormalizationOutcome:
    raw_record_id: UUID
    provider: str
    mapper_version: str
    claims: tuple[Claim, ...] = ()
    rejections: tuple[Rejection, ...] = ()
    #: Fields present in the payload that the mapper deliberately ignores —
    #: distinct from a rejection. Recorded so "we chose not to map this" and
    #: "we could not map this" never look the same in a diagnosis.
    ignored_fields: tuple[str, ...] = field(default=())

    @property
    def is_total_failure(self) -> bool:
        """Nothing was translated. Distinct from a record that legitimately
        carried no mappable content."""
        return not self.claims and bool(self.rejections)

    @property
    def has_missing_fields(self) -> bool:
        """The leading indicator of a vendor shape change."""
        return any(r.reason is RejectionReason.MISSING_REQUIRED_FIELD for r in self.rejections)
