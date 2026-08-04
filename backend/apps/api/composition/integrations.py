"""Composing the connections surface.

One level deep: the module owns a business relationship and computes nothing
about synchronization, so there is nothing to assemble but a session.
"""

from typing import Annotated

from fastapi import Depends

from functools import lru_cache

from modules.integrations.application.connect import ConnectSystem
from modules.integrations.application.disconnect import DisconnectSystem
from modules.integrations.application.probe import ProbeConnection
from modules.integrations.application.queries import IntegrationQueries
from modules.integrations.infrastructure.composition import (
    build_connect_system,
    build_disconnect_system,
    build_integration_queries,
    build_probe_connection,
)
from modules.integrations.infrastructure.settings import IntegrationSettings
from signora_platform.api import CurrentWorkspace


def integration_queries(context: CurrentWorkspace) -> IntegrationQueries:
    return build_integration_queries(context.session)


IntegrationRead = Annotated[IntegrationQueries, Depends(integration_queries)]


@lru_cache(maxsize=1)
def _settings() -> IntegrationSettings:
    """Constructed once, at the composition root, and injected — never read
    from the environment inside the module (§6, §20b)."""
    return IntegrationSettings()


def disconnect_system(context: CurrentWorkspace) -> DisconnectSystem:
    return build_disconnect_system(context.session, _settings(), context.workspace_id)


IntegrationDisconnect = Annotated[DisconnectSystem, Depends(disconnect_system)]


def connect_system(context: CurrentWorkspace) -> ConnectSystem:
    return build_connect_system(context.session, _settings())


IntegrationConnect = Annotated[ConnectSystem, Depends(connect_system)]


def probe_connection(context: CurrentWorkspace) -> ProbeConnection:
    return build_probe_connection(context.session, _settings())


IntegrationProbe = Annotated[ProbeConnection, Depends(probe_connection)]
