"""Event handler: apply the batch somebody accepted.

Subscribes to `action_batch.application_requested`, which **this module
publishes to itself**. That is not a curiosity — it is the only durable way a
request handler may hand work to a worker (§9: *never publish directly to
Redis, bypassing the outbox*), and `ai_research_engine` established the shape.

**The batch is loaded, never trusted from the payload.** The envelope names a
`batch_id` and the handler reads the aggregate — so a replayed event cannot
apply a batch that has since been reversed. *Events carry identity; ports carry
payload.*

---

**Idempotency here is convergence, not a flag.** §9 requires consumers to be
idempotent on `event_id`, and the platform's ledger provides that. This handler
adds the second half: **a redelivery that slips past the ledger finds a batch
that is already applied, and the desired end state has been reached.** The
domain refuses the second application on its own — `applied_on` raises rather
than overwriting a timestamp — so the handler reads that refusal as *done*
rather than as a failure. **Nothing is written twice and nothing is reported as
broken.**

**Failure is split by whether retrying could help** (§15):

* **the batch is gone** — nothing to retry, and nothing to record a failure
  against. Logged and dropped;
* **the domain refuses** — and for a *dispatched* batch there is exactly one
  reachable reason: somebody applied it first. **That is convergence, not
  failure**, and it is logged;
* **anything else** — a database that is down, a refusal nothing here can
  explain. **Re-raised**, so ARQ retries and eventually dead-letters, which is
  the failure mode worth having.

---

**`fail_application` is not called from this handler, and that is deliberate.**
A first draft called it on any refusal, and building the test that would prove
it found the branch unreachable: a dispatched batch's state stays `APPROVED`, a
reversal needs an application first, and `failed_to_apply` itself refuses a
batch that was never dispatched. **A guard that cannot fail is documentation
pretending to be code** (§2), so it was removed rather than kept behind a
constructed fixture.

**The use case remains, and its caller is slice 6.** When the consuming domain
performs the work, *it* is what discovers the work could not be done — and it
records the failure so the screen stops saying *running*. **Recorded as a
limitation rather than left looking wired.**
"""

from __future__ import annotations

from collections.abc import Callable
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from modules.action_batch.application.batches import ActionBatchNotFound, ActionBatches
from modules.action_batch.domain.batch import ActionBatchError, ApplicationProgress
from signora_platform.db import tenant_scoped_session
from signora_platform.event_bus import EventEnvelope
from signora_platform.observability import get_logger

logger = get_logger(__name__)

CONSUMER_NAME = "action_batch.apply_accepted"
"""A permanent contract. Renaming it resets the idempotency ledger, and every
historical acceptance would be re-processed on replay — which here would mean
re-applying approvals a customer has already seen the outcome of."""

#: The identity rows are attributed to when the platform acts without a user.
#: The same constant `ai_research_engine`'s handler uses, for the same reason.
SYSTEM_USER_ID = UUID("00000000-0000-0000-0000-000000000001")

BatchesFactory = Callable[[AsyncSession], ActionBatches]


async def apply_accepted_batch(
    envelope: EventEnvelope,
    *,
    session_factory: async_sessionmaker[AsyncSession],
    batches: BatchesFactory,
) -> None:
    batch_id = UUID(str(envelope.payload["batch_id"]))
    workspace_id = envelope.workspace_id

    async with tenant_scoped_session(
        session_factory, workspace_id=workspace_id, user_id=SYSTEM_USER_ID
    ) as session:
        use_cases = batches(session)
        batch = await use_cases.current(workspace_id, batch_id)

        if batch is None:
            # **Nothing to retry and nothing to record against.** A batch that
            # does not exist in this workspace cannot be told it failed.
            logger.warning(
                "accepted batch no longer exists",
                extra={"batch_id": str(batch_id), "workspace_id": str(workspace_id)},
            )
            return

        if batch.progress is ApplicationProgress.APPLIED:
            # ⚡ **The redelivery path, and it is checked BEFORE applying rather
            # than caught after.** ⛔ The domain would refuse the second
            # application anyway; reading that refusal as *done* works, but
            # asking first says what is happening instead of inferring it from
            # an exception.
            logger.info(
                "accepted batch was already applied; redelivery converged",
                extra={"batch_id": str(batch_id)},
            )
            return

        try:
            applied = await use_cases.apply(workspace_id, batch_id)
        except ActionBatchNotFound:  # pragma: no cover — `current` just found it
            logger.warning("accepted batch vanished mid-apply", extra={"batch_id": str(batch_id)})
            return
        except ActionBatchError as refusal:
            # 🔴 **The ONLY refusal a dispatched batch can meet is that somebody
            # else applied it first**, and establishing that is what removed a
            # branch from this handler.
            #
            # ⛔ **A dispatched batch cannot legally become un-appliable**: its
            # state stays `APPROVED`, and a reversal needs an application first.
            # ⚡ **So the reachable case is a race** — two deliveries in flight,
            # one applying between this handler's read and `apply`'s own load.
            settled = await use_cases.current(workspace_id, batch_id)
            if settled is not None and settled.progress is ApplicationProgress.APPLIED:
                logger.info(
                    "accepted batch was applied concurrently; nothing to record",
                    extra={"batch_id": str(batch_id)},
                )
                return

            # ⚠️ **Anything else is genuinely unexpected, so it is LOUD** (§15).
            # ⛔ **`fail_application` is deliberately NOT called here.** **A
            # refusal this handler cannot explain is not a customer-facing
            # failure — it is a defect**, and recording it as *the work failed*
            # would put a reassuring state over an unexplained one. **Re-raising
            # dead-letters it with the domain's own sentence attached.**
            raise

    logger.info(
        "action batch applied by worker",
        extra={"batch_id": str(applied.id), "workspace_id": str(workspace_id)},
    )
