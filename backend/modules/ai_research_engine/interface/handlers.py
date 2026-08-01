"""Event handler: run the research somebody asked for.

Subscribes to `ai_research.requested`. **This is the only automatic path into a
model call in this module**, and what makes it automatic is a person having
clicked — nothing schedules research, nothing infers that an account is worth
researching, and there is deliberately no handler on `buying_score.updated`
that would.

That absence is the principle rather than an unfinished feature. Research costs
two model calls and about a minute; a platform that decided on its own when to
spend that would be making a commercial judgement nobody asked it to make, and
the first anyone would know is the bill. *Intelligence suggests; humans commit*
applies to spending as much as to workflow.

**The request is read, never trusted from the payload.** The envelope names a
request id and the handler loads the row — so a replayed event cannot start a
run against an account the request no longer points at. *Events carry identity;
ports carry payload*, and this is what that rule buys.

---

**This handler opens its own sessions, and that is a finding rather than a
preference.** `EventHandler` is `Callable[[EventEnvelope], Awaitable[None]]`:
the dispatcher opens a tenant-scoped session to claim idempotency and **does not
pass it on**, so a consumer has no way to join the transaction that is already
open for it. Widening that signature is a `signora_platform/` change and this
module does not get to make one (§20a), so the handler opens what it needs and
the consequence is recorded here rather than smoothed over:

* the idempotency claim and the work commit **separately**. If the claim's
  transaction were lost after the work committed, redelivery would find a
  settled request, the domain would refuse to advance it, and the event would
  dead-letter — **loudly, and without a second model call**, which is the
  failure mode worth having;
* two sessions are opened on purpose anyway. `RUNNING` has to be visible while
  the run is happening, and a status written inside the same transaction as the
  minute it describes becomes visible only once that minute is over.

**Raised for the platform's owner:** `ai_research_engine` is the repository's
**first production event consumer** — every prior `registry.subscribe` call is
in a test — so this is the first time the gap could be hit.
"""

from __future__ import annotations

from collections.abc import Callable
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from modules.ai_research_engine.application.run import BeginResearchRun, FinishResearchRun
from signora_platform.db import tenant_scoped_session
from signora_platform.event_bus import EventEnvelope
from signora_platform.observability import get_logger

logger = get_logger(__name__)

CONSUMER_NAME = "ai_research_engine.run_requested"
"""A permanent contract. Renaming it resets the idempotency ledger and every
historical event would be re-processed on replay — which here would mean
re-spending every model call anybody has ever asked for."""

#: The identity rows are attributed to when the platform acts without a user.
#: The same constant the repository uses, for the same reason.
SYSTEM_USER_ID = UUID("00000000-0000-0000-0000-000000000001")

BeginFactory = Callable[[AsyncSession], BeginResearchRun]
FinishFactory = Callable[[AsyncSession], FinishResearchRun]


async def run_requested_research(
    envelope: EventEnvelope,
    *,
    session_factory: async_sessionmaker[AsyncSession],
    begin: BeginFactory,
    finish: FinishFactory,
) -> None:
    request_id = UUID(str(envelope.payload["request_id"]))

    async with tenant_scoped_session(
        session_factory, workspace_id=envelope.workspace_id, user_id=SYSTEM_USER_ID
    ) as session:
        request, running = await begin(session).execute(envelope.workspace_id, request_id)

    async with tenant_scoped_session(
        session_factory, workspace_id=envelope.workspace_id, user_id=SYSTEM_USER_ID
    ) as session:
        await finish(session).execute(
            request, running, correlation_id=envelope.correlation_id
        )
