"""What other modules may read from Integrations.

**Provider Platform depends on Integrations; Integrations depends on nothing.**
That direction is the ownership ruling of 2026-08-02 made physical: a Connected
Account is a business relationship that exists before, during and after any
synchronization, so the module that *synchronizes* consumes it rather than
owning it.

Deliberately narrow. A consumer needs to know a connection exists, whether it is
usable, and how to obtain an execution context — never how a credential was
acquired, stored or refreshed.
"""

from modules.integrations.application.resolve import (
    ConnectionUnusable,
    ExecutionContext,
)
from modules.integrations.domain.connection import ConnectedAccount, ConnectionState
from modules.integrations.domain.grant import Credential

__all__ = [
    "ConnectedAccount",
    "ConnectionState",
    "ConnectionUnusable",
    "Credential",
    "ExecutionContext",
]
