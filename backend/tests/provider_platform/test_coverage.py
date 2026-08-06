"""*"Is Signora still watching this company?"* — **A7's render slice.**

**The half A4 could not answer.** A4 says how old the newest evidence is; it
cannot say whether anybody has looked since. **An account nobody has found
anything about and an account nobody has checked produce identical A4 lines**,
and those demand opposite actions — one is a reason to stop working the
account, the other a reason to distrust the page.

These assert the four states stay four. Collapsing any pair would let the
product state something it cannot support, which is the risk
[51 §A7](../../../docs/architecture/51-implementation-specifications.md) names
in its own words: *"only ship the word checked once it is true."*
"""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from modules.provider_platform.application.report_coverage import ReportCoverage
from modules.provider_platform.domain.coverage import SubjectCoverage, coverage
from modules.provider_platform.domain.provider import ProviderCapability, ProviderName
from modules.provider_platform.domain.sync import SyncWatermark

WORKSPACE = uuid4()
MONDAY = datetime(2026, 8, 3, 9, 0, tzinfo=UTC)
FRIDAY = datetime(2026, 8, 7, 9, 0, tzinfo=UTC)


def watermark(
    subject: str,
    *,
    provider: ProviderName = ProviderName.APOLLO,
    capability: ProviderCapability = ProviderCapability.COMPANY_ENRICHMENT,
    position: datetime | None = None,
    attempted_at: datetime | None = None,
) -> SyncWatermark:
    return SyncWatermark(
        workspace_id=WORKSPACE,
        provider=provider,
        capability=capability,
        subject=subject,
        position=position,
        attempted_at=attempted_at,
    )


class FakeCoverageRepository:
    """Live rows, keyed the way the real one queries them.

    It returns **only** the subjects asked for, because the real repository
    filters in SQL — a fake that returned everything would let a caller
    accidentally depend on rows the database would never have sent.
    """

    def __init__(self, *rows: SyncWatermark) -> None:
        self.rows = list(rows)
        self.asked: list[frozenset[str]] = []

    async def watermarks_for(
        self, workspace_id: object, subjects: frozenset[str]
    ) -> tuple[SyncWatermark, ...]:
        self.asked.append(subjects)
        return tuple(row for row in self.rows if row.subject in subjects)


class TestTheFourStatesStayFour:
    def test_a_company_nobody_has_ever_checked(self) -> None:
        """**No watermark row at all.** The honest answer, and the one a
        seller most needs, because it means the pipeline has not run rather
        than that the account is quiet."""
        (found,) = coverage(["Northwind Health"], [])

        assert found == SubjectCoverage(
            subject="Northwind Health", last_attempt=None, stored_anything=False
        )

    def test_a_company_checked_today_with_nothing_new(self) -> None:
        """**Acceptance ①, and the case the whole slice exists for.** A
        watermark with an attempt and no position records a completed read
        that stored nothing — indistinguishable from *never checked* until
        this field existed."""
        (found,) = coverage(
            ["Northwind Health"], [watermark("Northwind Health", attempted_at=FRIDAY)]
        )

        assert found.last_attempt == FRIDAY
        assert found.stored_anything is False

    def test_a_company_checked_and_found(self) -> None:
        (found,) = coverage(
            ["Northwind Health"],
            [watermark("Northwind Health", position=MONDAY, attempted_at=FRIDAY)],
        )

        assert found.last_attempt == FRIDAY
        assert found.stored_anything is True

    def test_a_company_read_before_the_attempt_was_recorded(self) -> None:
        """**The fourth state, and the reason `last_attempt` is nullable
        independently.** Rows written before `attempted_at` existed carry a
        position and no time. Those subjects *were* read and nothing recorded
        when — so the product says it does not know, rather than backfilling a
        date it invented or calling them unchecked, which would be false."""
        (found,) = coverage(["Northwind Health"], [watermark("Northwind Health", position=MONDAY)])

        assert found.last_attempt is None
        assert found.stored_anything is True

    def test_never_checked_and_checked_empty_are_distinguishable(self) -> None:
        """**Acceptance ②, asserted as the comparison rather than as two
        separate facts.** The defect this slice removes is precisely that
        these two were one state."""
        never, empty = coverage(["Never", "Empty"], [watermark("Empty", attempted_at=FRIDAY)])

        assert never != empty
        assert (never.last_attempt, never.stored_anything) == (None, False)
        assert (empty.last_attempt, empty.stored_anything) == (FRIDAY, False)


class TestOneAnswerAcrossEveryProvider:
    def test_the_latest_attempt_wins(self) -> None:
        """A subject has one watermark per `(provider, capability)`, and the
        question a seller asks is *when did anybody last look* — not *when did
        Apollo's company enrichment last look*."""
        (found,) = coverage(
            ["Northwind Health"],
            [
                watermark("Northwind Health", attempted_at=MONDAY),
                watermark(
                    "Northwind Health",
                    provider=ProviderName.BOMBORA,
                    attempted_at=FRIDAY,
                ),
            ],
        )

        assert found.last_attempt == FRIDAY

    def test_evidence_from_any_provider_counts(self) -> None:
        (found,) = coverage(
            ["Northwind Health"],
            [
                watermark("Northwind Health", attempted_at=FRIDAY),
                watermark(
                    "Northwind Health",
                    provider=ProviderName.BOMBORA,
                    position=MONDAY,
                    attempted_at=MONDAY,
                ),
            ],
        )

        assert found.stored_anything is True

    def test_a_row_with_no_attempt_does_not_erase_one_that_has_it(self) -> None:
        """**The guard that would be easy to write wrongly.** Taking a `max`
        over a list containing `None` raises; taking the *last* row's value
        would let an older provider's silence overwrite a newer one's answer."""
        (found,) = coverage(
            ["Northwind Health"],
            [
                watermark("Northwind Health", attempted_at=FRIDAY),
                watermark("Northwind Health", provider=ProviderName.BOMBORA),
            ],
        )

        assert found.last_attempt == FRIDAY


class TestEverySubjectAskedAboutGetsAnAnswer:
    def test_a_subject_with_no_row_is_present_rather_than_missing(self) -> None:
        """**Absence stated, never omitted.** A caller reading a missing key
        renders a blank, and a blank reads as a screen that forgot to render
        something rather than as an answer."""
        found = coverage(["Known", "Unknown"], [watermark("Known", attempted_at=FRIDAY)])

        assert [entry.subject for entry in found] == ["Known", "Unknown"]

    def test_the_customers_own_order_is_kept(self) -> None:
        """The only order in this module with any meaning — nothing here knows
        which of a customer's companies matters more, and inventing a priority
        would be a commercial judgement nobody asked for."""
        found = coverage(["Zeta", "Alpha", "Mu"], [])

        assert [entry.subject for entry in found] == ["Zeta", "Alpha", "Mu"]

    def test_a_company_named_twice_is_one_company(self) -> None:
        """Matching `subjects_needing_sync`, which collapses for the same
        reason: two entries naming one company are one thing to report on,
        however many times it was typed."""
        found = coverage(["Acme", "Acme"], [])

        assert len(found) == 1

    def test_a_watermark_for_a_subject_nobody_asked_about_is_ignored(self) -> None:
        found = coverage(["Asked"], [watermark("Not asked", attempted_at=FRIDAY)])

        assert [entry.subject for entry in found] == ["Asked"]


class TestTheQuery:
    async def test_it_reports_what_the_domain_computes(self) -> None:
        repository = FakeCoverageRepository(watermark("Acme", attempted_at=FRIDAY))

        found = await ReportCoverage(watermarks=repository).execute(WORKSPACE, ("Acme",))

        assert found == (
            SubjectCoverage(subject="Acme", last_attempt=FRIDAY, stored_anything=False),
        )

    async def test_it_asks_for_each_company_once(self) -> None:
        """A duplicate in the request is not a reason to read the same row
        twice — the deduplication is the repository's set, and the order the
        customer typed survives it because the domain re-reads the original."""
        repository = FakeCoverageRepository()

        await ReportCoverage(watermarks=repository).execute(WORKSPACE, ("Acme", "Acme"))

        assert repository.asked == [frozenset({"Acme"})]

    async def test_asking_about_nothing_reads_nothing(self) -> None:
        """**Not merely an empty result — no query at all.** A `subject IN ()`
        is a round trip that can only return nothing, and the endpoint already
        refuses an empty list, so this is the guard behind that one rather
        than a duplicate of it."""
        repository = FakeCoverageRepository(watermark("Acme", attempted_at=FRIDAY))

        found = await ReportCoverage(watermarks=repository).execute(WORKSPACE, ())

        assert found == ()
        assert repository.asked == []
