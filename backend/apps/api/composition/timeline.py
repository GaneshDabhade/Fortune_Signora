"""Composing Timeline's read surface.

**One level deep, and that is the boundary rather than an omission.** Timeline
projects; it reads no other module, calls no provider and computes nothing, so
there is nothing to assemble but a session.

Its own file, like every other surface: a router inherits every import the
module it imports makes, and a shared composition would hand a projection a
transitive dependency on the pipeline it deliberately knows nothing about.
"""

from typing import Annotated

from fastapi import Depends

from modules.timeline.application.queries import TimelineQueries
from modules.timeline.infrastructure.composition import build_timeline_queries
from signora_platform.api import CurrentWorkspace


def timeline_queries(context: CurrentWorkspace) -> TimelineQueries:
    return build_timeline_queries(context.session)


TimelineRead = Annotated[TimelineQueries, Depends(timeline_queries)]
