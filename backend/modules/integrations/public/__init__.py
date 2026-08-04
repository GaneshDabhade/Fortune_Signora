"""What other modules may read from Integrations.

**Provider Platform depends on Integrations; Integrations depends on nothing.**
That direction is the ownership ruling of 2026-08-02 made physical: a Connected
Account is a business relationship that exists before, during and after any
synchronization, so the module that *synchronizes* consumes it rather than
owning it.

Deliberately narrow. A consumer needs to know a connection exists, whether it is
usable, and how to obtain an execution context — never how a credential was
acquired, stored or refreshed.

**The source port joined it on 2026-08-04**, when [ADR-0300](../../../../docs/architecture/adr/0300-inbound-customer-systems.md)
Option A was approved by the product owner. It is published here **because a port belongs to the module that
owns the language it represents** (`CLAUDE.md` §6) and its driver lives in
another module — Provider Platform runs it, and this module does not know that.
**Nothing about credential acquisition, storage or renewal joined it**: the
contract still says what a consumer may *do*, never how the material behind it
came to exist.
"""

from modules.integrations.application.resolve import ConnectionUnusable
from modules.integrations.domain.catalog import Capability
from modules.integrations.domain.connection import ConnectedAccount, ConnectionState
from modules.integrations.domain.execution import ExecutionContext
from modules.integrations.domain.grant import Credential
from modules.integrations.domain.source import (
    IntegrationCapabilityUnsupportedError,
    IntegrationFetchRequest,
    IntegrationPage,
    IntegrationPayloadInvalidError,
    IntegrationRecord,
    IntegrationSourceAdapter,
    IntegrationSourceDescriptor,
    IntegrationSourceError,
    IntegrationSourcePermanentError,
    IntegrationSourceRateLimitedError,
    IntegrationSourceTransientError,
)

__all__ = [
    "Capability",
    "ConnectedAccount",
    "ConnectionState",
    "ConnectionUnusable",
    "Credential",
    "ExecutionContext",
    "IntegrationCapabilityUnsupportedError",
    "IntegrationFetchRequest",
    "IntegrationPage",
    "IntegrationPayloadInvalidError",
    "IntegrationRecord",
    "IntegrationSourceAdapter",
    "IntegrationSourceDescriptor",
    "IntegrationSourceError",
    "IntegrationSourcePermanentError",
    "IntegrationSourceRateLimitedError",
    "IntegrationSourceTransientError",
]
