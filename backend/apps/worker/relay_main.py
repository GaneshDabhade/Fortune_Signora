"""Outbox relay entry point.

Runs as its own process, separate from the ARQ workers, because its failure
and scaling characteristics differ: the relay is a single lightweight
database consumer, while workers are many and CPU/IO-bound. Separating them
also makes the rollback story clean — scaling the relay to zero halts
dispatch while events continue accumulating durably in the outbox, and they
drain when it returns.

Run with:  ``python -m apps.worker.relay_main``
"""

import asyncio
import contextlib
import signal
from typing import Any

from arq import create_pool
from arq.connections import RedisSettings

from signora_platform.db import create_relay_engine, create_session_factory
from signora_platform.event_bus import ArqQueuePublisher, OutboxRelay, registry
from signora_platform.observability import (
    configure_error_tracking,
    configure_logging,
    configure_metrics,
    configure_tracing,
    get_logger,
    instrument_sqlalchemy,
)
from signora_platform.settings import get_settings

logger = get_logger(__name__)


async def run() -> None:
    settings = get_settings()
    configure_logging(level=settings.log_level)
    configure_tracing(settings)
    configure_error_tracking(settings)
    metrics = configure_metrics(settings)

    if settings.relay_database_url is None:
        # Not fatal — a single-role local setup is legitimate — but never
        # silent: running the relay as the application role restores the
        # cross-workspace read path migration 0006 closed.
        logger.warning(
            "relay running under the application identity",
            extra={"reason": "SIGNORA_RELAY_DATABASE_URL not configured"},
        )

    engine = create_relay_engine(settings)
    instrument_sqlalchemy(engine)
    session_factory = create_session_factory(engine)
    redis = await create_pool(RedisSettings.from_dsn(str(settings.redis_url)))

    relay = OutboxRelay(
        session_factory=session_factory,
        queue_publisher=ArqQueuePublisher(redis),
        registry=registry,
        metrics=metrics,
    )

    task = asyncio.create_task(relay.run_forever())
    _install_signal_handlers(task)

    try:
        await task
    except asyncio.CancelledError:
        # Expected on SIGTERM. In-flight batches complete because each
        # batch runs inside a transaction that either commits or rolls
        # back atomically — a cancelled relay never leaves an event
        # half-relayed.
        pass
    finally:
        await redis.aclose()
        await engine.dispose()
        logger.info("relay shut down cleanly")


def _install_signal_handlers(task: asyncio.Task[Any]) -> None:
    loop = asyncio.get_running_loop()
    for sig in (signal.SIGTERM, signal.SIGINT):
        with contextlib.suppress(NotImplementedError):
            loop.add_signal_handler(sig, task.cancel)


if __name__ == "__main__":
    asyncio.run(run())
