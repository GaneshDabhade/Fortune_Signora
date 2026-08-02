"""Composing the connections surface.

One level deep: the module owns a business relationship and computes nothing
about synchronization, so there is nothing to assemble but a session.
"""

from typing import Annotated

from fastapi import Depends

from modules.integrations.application.queries import IntegrationQueries
from modules.integrations.infrastructure.composition import build_integration_queries
from signora_platform.api import CurrentWorkspace


def integration_queries(context: CurrentWorkspace) -> IntegrationQueries:
    return build_integration_queries(context.session)


IntegrationRead = Annotated[IntegrationQueries, Depends(integration_queries)]
