"""Composing the Provider Platform's A7 read surface.

Nothing deep: the question is answered entirely inside this module's own
tables, so this file reaches no other module at all.
"""

from typing import Annotated

from fastapi import Depends

from modules.provider_platform.application.report_coverage import ReportCoverage
from modules.provider_platform.infrastructure.repository import CoverageReadRepository
from signora_platform.api import CurrentWorkspace


def report_coverage(context: CurrentWorkspace) -> ReportCoverage:
    """Assembled for one request, from the **workspace-scoped** context — so
    RLS is already established and the workspace identifier is one the caller
    was verified to be a member of, never one they supplied."""
    return ReportCoverage(watermarks=CoverageReadRepository(context.session))


CoverageRead = Annotated[ReportCoverage, Depends(report_coverage)]

__all__ = ["CoverageRead", "report_coverage"]
