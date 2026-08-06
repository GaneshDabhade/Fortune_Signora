"""Answering *"is Signora still watching these companies?"* — **A7**.

A read, so it is a query object rather than a command: nothing here decides
anything, writes anything, or publishes anything. It exists so the interface
layer depends on a port and a pure domain function rather than on SQLAlchemy.
"""

from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from modules.provider_platform.application.ports import CoverageRepository
from modules.provider_platform.domain.coverage import SubjectCoverage, coverage


@dataclass(frozen=True, slots=True)
class ReportCoverage:
    watermarks: CoverageRepository

    async def execute(
        self, workspace_id: UUID, subjects: tuple[str, ...]
    ) -> tuple[SubjectCoverage, ...]:
        """One entry per subject, in the order asked.

        **The set handed to the repository is deduplicated; the order given to
        the domain is not.** The query has no reason to read one subject twice,
        and the caller's order is the customer's own — the same reasoning
        `subjects_needing_sync` applies, and the only order in this module with
        any meaning.
        """
        if not subjects:
            return ()
        rows = await self.watermarks.watermarks_for(workspace_id, frozenset(subjects))
        return coverage(subjects, rows)


__all__ = ["ReportCoverage"]
