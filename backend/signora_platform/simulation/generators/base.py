"""Payload generators — rendering a scenario event into a provider shape.

**Every generator here emits a DEVELOPMENT FIXTURE, not an authentic
provider payload.** The Payload Provenance policy is unchanged: no fixture
may be presented as a real vendor response. These exist to unblock
architecture validation, and each carries a machine-readable designation
saying so — surfaced in ingestion logs, in health output, and in the
qualification register.

The design goal is that replacing a fixture with a real payload is a
**one-file change**. A generator owns exactly two things: the shape it
emits, and the mapping from scenario facts into that shape. Nothing else in
the system knows either, so when a legitimate artifact arrives the diff is
confined to one module and its golden test.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Mapping
from dataclasses import dataclass
from enum import StrEnum
from typing import Any, Final

from signora_platform.simulation.scenario import ScenarioEvent

#: Bumped whenever a generator's emitted shape changes. Recorded against
#: every run, because without it a downstream output change could come from
#: a model, a prompt, a dataset, *or* a quietly-updated payload shape.
GENERATOR_VERSION: Final = "0.1.0-fixture"


class PayloadProvenance(StrEnum):
    """Where a generator's shape came from.

    Not cosmetic. A payload built from a fixture and one built from a
    recorded vendor response must be distinguishable at a glance, or the
    fixture quietly becomes the contract — which is precisely the failure
    the provenance policy exists to prevent.
    """

    DEVELOPMENT_FIXTURE = "DEVELOPMENT_FIXTURE"
    """Representative structure, invented to unblock development. **Not the
    vendor's schema.** Must be replaced when a legitimate artifact arrives."""

    OFFICIAL_DOCUMENTATION = "OFFICIAL_DOCUMENTATION"
    VENDOR_SANDBOX = "VENDOR_SANDBOX"
    RECORDED_TEST_ACCOUNT = "RECORDED_TEST_ACCOUNT"
    SANITIZED_PRODUCTION = "SANITIZED_PRODUCTION"

    @property
    def is_authentic(self) -> bool:
        return self is not PayloadProvenance.DEVELOPMENT_FIXTURE


@dataclass(frozen=True, slots=True)
class GeneratedPayload:
    """One rendered payload plus the provenance of its shape."""

    provider: str
    external_id: str
    payload: Mapping[str, Any]
    provenance: PayloadProvenance

    def as_log_fields(self) -> dict[str, str]:
        return {
            "provider": self.provider,
            "payload_provenance": self.provenance.value,
            # Deliberately loud. If a fixture-derived payload ever reaches
            # somewhere it should not, the log says so without anyone
            # having to reconstruct which generator produced it.
            "fixture_warning": (
                "shape is a development fixture, not the vendor schema"
                if not self.provenance.is_authentic
                else ""
            ),
        }


class PayloadGenerator(ABC):
    """Renders scenario events into one provider's payload shape.

    Stateless and pure: a generator that remembers previous calls produces
    output depending on invocation order, which breaks replay.
    """

    provider: str
    provenance: PayloadProvenance = PayloadProvenance.DEVELOPMENT_FIXTURE

    #: Replaced with a real reference when the fixture is. Present in the
    #: qualification register and asserted by a test, so a generator cannot
    #: silently claim authenticity it does not have.
    source_reference: str = "none — development fixture pending a legitimate artifact"

    @abstractmethod
    def render(self, event: ScenarioEvent) -> Mapping[str, Any]:
        """Build the payload body for one event."""

    def generate(self, event: ScenarioEvent) -> GeneratedPayload:
        return GeneratedPayload(
            provider=self.provider,
            external_id=event.subject,
            payload=self.render(event),
            provenance=self.provenance,
        )


def _fixture_notice(provider: str) -> str:
    """The marker embedded in every fixture payload.

    Inside the body rather than only alongside it: a payload copied into a
    bug report, a test fixture, or a customer demo carries its own warning
    with it. It costs one field and removes the possibility of a fixture
    being mistaken for a real response somewhere down the line.

    This field disappears when the fixture is replaced — its absence is
    what a test asserts to confirm the replacement is complete.
    """
    return (
        f"DEVELOPMENT FIXTURE — this is NOT an authentic {provider} payload. "
        "Structure is representative only and must be replaced with a legitimate "
        "artifact (see docs/architecture/provider-qualification.md)."
    )
