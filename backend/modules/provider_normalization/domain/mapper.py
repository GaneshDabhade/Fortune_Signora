"""The Mapper port — the border between vendor languages and Signora's.

Every provider payload, today and years from now, enters the platform
through one of these. They are translation components, not parsing code.

**A mapper has exactly one responsibility: translate provider
representations into canonical Claims.** It must never resolve identities,
compare providers, infer missing information, reconcile conflicts, assign
confidence, or make business decisions. It translates faithfully and never
interprets.

**Unknown fields never disappear.** A mapper declares the fields it knows;
anything else in the payload becomes an explicit rejection carrying the
field path, the reason, the mapper version, and the provider. A vendor
adding or renaming a field is an operational event, and it must be
diagnosable without reading source code.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Iterator, Mapping
from datetime import date, datetime
from typing import Any, Final

from modules.provider_normalization.domain.claim import ClaimSource, SubjectHint
from modules.provider_normalization.domain.outcome import Rejection, RejectionReason
from modules.provider_normalization.domain.vocabulary import ClaimAttribute, ClaimValue

MAPPER_VERSION: Final = "1"


class MappedClaim:
    """One translation result, before it becomes a Claim.

    Separate from `Claim` so a mapper never constructs workspace-scoped
    domain objects — it translates shape, and the use case owns the
    tenancy and provenance context.
    """

    __slots__ = ("attribute", "value", "observed_at")

    def __init__(self, attribute: ClaimAttribute, value: ClaimValue, observed_at: datetime) -> None:
        self.attribute = attribute
        self.value = value
        self.observed_at = observed_at


class ProviderMapper(ABC):
    """Translates one provider's payloads into canonical claims."""

    provider: str
    version: str = MAPPER_VERSION

    #: Top-level payload keys this mapper understands. Anything else
    #: becomes an UNKNOWN_FIELD rejection — the signature of a vendor
    #: adding a field, which is how a shape change first shows itself.
    known_fields: frozenset[str] = frozenset()

    #: Keys deliberately not translated. Distinct from unknown, so "we
    #: chose not to map this" and "we could not map this" never look the
    #: same in a diagnosis.
    ignored_fields: frozenset[str] = frozenset()

    @abstractmethod
    def subject(self, payload: Mapping[str, Any]) -> SubjectHint:
        """Extract identity *hints*. Never resolves identity."""

    @abstractmethod
    def translate(
        self, payload: Mapping[str, Any], observed_at: datetime
    ) -> Iterator[MappedClaim | Rejection]:
        """Yield claims and rejections, interleaved.

        A generator rather than two lists: a payload that fails halfway
        should still surface everything it successfully translated.
        Discarding partial evidence because part of a payload was bad loses
        information that can never be recovered.
        """

    def unexpected_fields(self, payload: Mapping[str, Any]) -> Iterator[Rejection]:
        """Every top-level key the mapper neither knows nor ignores.

        Called by the use case, not by mappers, so no mapper can forget to
        do it — silent degradation is the failure mode this exists to
        prevent.
        """
        for key in payload:
            if key not in self.known_fields and key not in self.ignored_fields:
                yield Rejection(
                    reason=RejectionReason.UNKNOWN_FIELD,
                    detail=(
                        f"{self.provider} payload carried '{key}', which mapper "
                        f"v{self.version} does not know. A vendor added a field, or this "
                        "mapper is out of date."
                    ),
                )

    def source(self, raw_record_id: Any, payload_provenance: str) -> ClaimSource:
        return ClaimSource(
            provider=self.provider,
            raw_record_id=raw_record_id,
            mapper_version=self.version,
            payload_provenance=payload_provenance,
        )


def require(payload: Mapping[str, Any], path: str) -> tuple[Any, Rejection | None]:
    """Read a dotted path, returning a rejection if absent.

    Missing is reported as MISSING_REQUIRED_FIELD rather than UNKNOWN_FIELD
    because the two mean opposite things: a vendor *removing* or *renaming*
    a field breaks existing mappings and is urgent; adding one does not.
    """
    current: Any = payload
    for part in path.split("."):
        if not isinstance(current, Mapping) or part not in current:
            return None, Rejection(
                reason=RejectionReason.MISSING_REQUIRED_FIELD,
                detail=(
                    f"'{path}' absent — a vendor renamed or removed it, or the payload is partial"
                ),
            )
        current = current[part]
    return current, None


def parse_date(value: Any, path: str) -> tuple[date | None, Rejection | None]:
    if value is None:
        return None, None
    try:
        return date.fromisoformat(str(value)), None
    except ValueError:
        return None, Rejection(
            reason=RejectionReason.UNPARSEABLE_VALUE,
            detail=f"'{path}' is not an ISO date: {value!r}",
        )
