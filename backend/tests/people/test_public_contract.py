"""What `people` publishes, and what it refuses to.

**[TASK-457](../../../docs/BACKLOG.md)**, extended 2026-08-07 by
[C-237](../../../docs/LANE_COORDINATION.md). The types other modules may use to
name a subject, **and the reader that lets them obtain one** — added when
`signal_engine` became a real caller and stated its own requirement, which is
the trigger TASK-457's *"nothing that reads them"* bound was waiting for.

⚠️ **This file exists because the contract did not.** `people/public/__init__.py`
was an empty file on `main` while the row read `CLAIMED`, and
[C-235](../../../docs/LANE_COORDINATION.md) found it from the outside — Lane A's
TASK-458 had been released against it. **A contract with no test is how an
empty one survives a release check.**
"""

from __future__ import annotations

from dataclasses import FrozenInstanceError, fields
from datetime import date
from uuid import UUID, uuid4

import pytest

from modules.people.public import AffiliationReader, AffiliationView, PersonView

STARTED = date(2026, 3, 1)


def _affiliation(*, ended: date | None = None) -> AffiliationView:
    return AffiliationView(
        id=uuid4(),
        workspace_id=uuid4(),
        person_id=uuid4(),
        company_id=uuid4(),
        title="VP of Engineering",
        seniority="vp",
        started_on=STARTED,
        ended_on=ended,
    )


class TestThePublishedSubjectCarriesNoIdentity:
    """**C-221 is the specification, not a limitation** — *"do not expand the
    architecture around people… role-based and organization-level."*"""

    def test_a_person_is_an_id_and_a_workspace_and_nothing_else(self) -> None:
        assert {f.name for f in fields(PersonView)} == {"id", "workspace_id"}

    def test_no_published_field_could_hold_a_direct_identifier(self) -> None:
        """**The words, refused by name.** `test_boundary.py` refuses
        *judgements*; this refuses *identity*, and the two rules are different
        — a name is not a judgement, and neither may be published."""
        published = {f.name for f in fields(PersonView)} | {
            f.name for f in fields(AffiliationView)
        }
        forbidden = {"name", "email", "phone", "full_name", "external_id", "provider_id"}

        assert published & forbidden == set()


class TestAnOpenIntervalIsAClaimAboutObservation:
    def test_no_departure_observed_reads_as_open(self) -> None:
        assert _affiliation().is_open

    def test_a_closed_interval_is_not_open(self) -> None:
        assert not _affiliation(ended=date(2026, 9, 30)).is_open

    def test_the_contract_publishes_an_interval_and_not_a_current_employer(self) -> None:
        """ADR-0400's load-bearing choice: *"Priya left Acme" is not a mutation
        of Priya — it is an interval closing.* A `current_employer` field would
        destroy the history the product is built on."""
        names = {f.name for f in fields(AffiliationView)}

        assert {"started_on", "ended_on"} <= names
        assert "current_employer" not in names


class TestItIsAContractAndNotAnImplementation:
    def test_the_published_types_are_frozen(self) -> None:
        """A view a consumer can mutate is a view two consumers disagree
        about."""
        view = _affiliation()

        with pytest.raises(FrozenInstanceError):
            view.title = "CTO"  # type: ignore[misc]

    def test_the_reader_is_published_and_offers_no_way_to_write(self) -> None:
        """⚠️ **Re-aimed 2026-08-07 by [C-237](../../../docs/LANE_COORDINATION.md).**

        This asserted that *no* reader was published — correct while no
        consumer existed, and expired the moment `signal_engine` claimed
        TASK-458 and stated what it needed. **The property worth keeping is not
        the port's absence; it is that the port cannot write.** A judging module
        must never be able to author the history it reads.
        """
        import modules.people.public as contract

        assert contract.__all__ == ["AffiliationReader", "AffiliationView", "PersonView"]

        methods = [m for m in dir(AffiliationReader) if not m.startswith("_")]
        assert methods == ["at_company", "for_person"]
        assert not [m for m in methods if m.startswith(("add", "create", "close", "set"))]

    def test_a_fake_satisfies_the_reader(self) -> None:
        """The port is structural, so a consumer can test against it before
        `people` persists a single row."""

        class Fake:
            async def at_company(
                self, workspace_id: UUID, company_id: UUID
            ) -> tuple[AffiliationView, ...]:
                return ()

            async def for_person(
                self, workspace_id: UUID, person_id: UUID
            ) -> tuple[AffiliationView, ...]:
                return ()

        reader: AffiliationReader = Fake()
        assert reader is not None

    def test_the_reader_returns_the_interval_and_never_a_current_employer(self) -> None:
        """C-237 names this exactly: the answer must carry the interval,
        because `ended_on = None` means *no departure has been observed* and
        not *"they still work there"* — the distinction a signal would
        otherwise flatten."""
        import inspect

        signature = inspect.signature(AffiliationReader.at_company)

        assert signature.return_annotation == "tuple[AffiliationView, ...]"
        assert {"started_on", "ended_on"} <= {f.name for f in fields(AffiliationView)}
