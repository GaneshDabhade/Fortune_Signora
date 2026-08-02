"""Which consumers this deployment runs. **The repository's first.**

Every `registry.subscribe` call before this one was in a test. The event bus,
the outbox, the relay, retry, dead-lettering and the idempotency ledger have all
been built, proven and unused — and the pipeline has been driven in-process
instead. M12.4 is the first capability a customer can *start*, so it is the
first that has to travel the path the architecture describes.

**Registration happens at import**, because two processes need it for two
different reasons: the worker needs the handler, and the **relay** needs only
the `(event_type → consumer, pool)` triple in order to know which queue an event
fans out to. Importing this module is part of starting either one, and it must
therefore open no connection and read no credential.

**Handlers resolve their dependencies at call time**, from a runtime the worker
installs at startup. A subscription registered at import cannot close over a
session factory that does not exist yet. `runtime()` raises rather than
defaulting: a worker dispatching research with no runtime installed is a
composition fault, and a fallback would make it a silent one.
"""

from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

import httpx
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from apps.worker.pools import AI_RESEARCH, READ_MODEL
from modules.ai_platform.infrastructure.composition import build_provider_registry
from modules.ai_platform.infrastructure.prompt_loader import load_prompt_registry
from modules.ai_platform.infrastructure.repository import SqlInferenceRecorder
from modules.ai_platform.infrastructure.settings import AISettings
from modules.ai_platform.public import Infer, InferencePolicy
from modules.ai_research_engine.domain.events import (
    RESEARCH_REQUESTED as RESEARCH_REQUESTED_EVENT,
)
from modules.ai_research_engine.application.run import FinishResearchRun
from modules.ai_research_engine.infrastructure.composition import (
    PROMPT_DIR,
    build_begin_research_run,
    build_finish_research_run,
)
from modules.ai_research_engine.interface.handlers import (
    CONSUMER_NAME as RESEARCH_CONSUMER,
)
from modules.ai_research_engine.interface.handlers import run_requested_research
from modules.timeline.domain.projection import PROJECTIONS
from modules.timeline.infrastructure.composition import build_project_event
from modules.timeline.interface.handlers import CONSUMER_NAME as TIMELINE_CONSUMER
from modules.timeline.interface.handlers import project_to_timeline
from modules.business_event_engine.infrastructure.composition import (
    build_queries as build_business_event_queries,
)
from modules.buying_score_engine.infrastructure.composition import (
    build_queries as build_buying_score_queries,
)
from modules.knowledge_graph.infrastructure.composition import (
    build_queries as build_graph_queries,
)
from modules.observation_engine.infrastructure.composition import (
    build_queries as build_observation_queries,
)
from modules.opportunity_engine.application.queries import OpportunityQueries
from modules.opportunity_engine.infrastructure.composition import (
    build_queries as build_opportunity_queries,
)
from modules.provider_normalization.infrastructure.claim_reader import SqlClaimReader
from modules.signal_engine.infrastructure.composition import (
    build_queries as build_signal_queries,
)
from signora_platform.db import tenant_scoped_session
from signora_platform.event_bus import (
    EventEnvelope,
    PostgresOutboxEventPublisher,
    registry,
)

#: Read from the domain module rather than written out, so a renamed event
#: cannot leave a subscription pointing at a string nothing publishes.
RESEARCH_REQUESTED: str = RESEARCH_REQUESTED_EVENT

#: The identity a projection is attributed to. Timeline's rows carry no actor —
#: nobody *did* a projection — but `app.user_id` must still be set, because
#: `tenant_scoped_session` establishes both keys and the platform requires it.
SYSTEM_USER_ID = UUID("00000000-0000-0000-0000-000000000001")


class RuntimeNotInstalled(RuntimeError):
    """A handler ran in a process that never installed a worker runtime."""


@dataclass(frozen=True)
class WorkerRuntime:
    """What a handler needs and cannot have at import time."""

    session_factory: async_sessionmaker[AsyncSession]
    http: httpx.AsyncClient
    ai: AISettings

    @property
    def model(self) -> str:
        """Which model this environment researches with.

        **Derived from which credentials exist** — the same fact
        `build_provider_registry` uses to decide which adapters are registered
        at all. One rule in one place, so a deployment cannot end up with an
        adapter for one vendor and a model name for another.

        A deployment holding an Anthropic key runs hosted (ADR-0028), and
        `research_planning@2`/`research_synthesis@2` hold releases only for
        `llama3.1:8b` today — **so a hosted run would be refused by the release
        rule.** That refusal is the rule working rather than a wiring defect;
        the prompts earn a release against the production model, or research
        does not run there.
        """
        return self.ai.anthropic_model if self.ai.anthropic_api_key else self.ai.ollama_model


_runtime: WorkerRuntime | None = None


def install(runtime_: WorkerRuntime) -> None:
    global _runtime
    _runtime = runtime_


def runtime() -> WorkerRuntime:
    if _runtime is None:
        raise RuntimeNotInstalled(
            "a subscription handler ran before the worker installed its runtime. "
            "Either import order or a missing `install()` at startup — never a "
            "default, because a handler quietly building its own connections would "
            "be a second composition root nobody reviewed."
        )
    return _runtime


def _infer(current: WorkerRuntime) -> Infer:
    """An `Infer` bound to the **AI Research Engine's own** prompt directory.

    `load_prompt_registry(directory)` is per-directory precisely so each module
    owns its prompts; binding one to a provider registry is the composition
    root's job, because this is the one place that may legitimately import two
    modules' infrastructure.

    The recorder takes the **session factory**, not a session: operational
    history commits on its own transaction, so a failed run still records that
    a model was called (ADR-0029).
    """
    return Infer(
        providers=build_provider_registry(current.ai, client=current.http),
        prompts=load_prompt_registry(PROMPT_DIR),
        recorder=SqlInferenceRecorder(current.session_factory),
        # Two attempts, matching the Playground's narration pass. A research
        # run is two model calls and about a minute; a third attempt on each
        # would treble the worst case for a failure class that is mostly
        # permanent (see `application/run.py`).
        policy=InferencePolicy(max_attempts=2),
    )


def _opportunities(session: AsyncSession, workspace_id: UUID) -> OpportunityQueries:
    """The six-deep read chain, assembled for one unit of work.

    The same chain `apps/api/composition/opportunities.py` builds, and the
    depth is the same finding recorded there — every edge one the dependency
    matrix already ratified. Research is the caller that actually needs the
    bottom of it: `explanation()` is what those five layers exist to satisfy.
    """
    graph = build_graph_queries(
        session, claims=SqlClaimReader(session, workspace_id=workspace_id)
    )
    observations = build_observation_queries(session, graph=graph)
    events = build_business_event_queries(session, observations=observations)
    signals = build_signal_queries(session, business_events=events)
    scores = build_buying_score_queries(session, signals=signals)
    return build_opportunity_queries(session, scores=scores)


async def _run_requested_research(envelope: EventEnvelope) -> None:
    current = runtime()

    def finish(session: AsyncSession) -> FinishResearchRun:
        return build_finish_research_run(
            session,
            infer=_infer(current),
            model=current.model,
            opportunities=_opportunities(session, envelope.workspace_id),
            publisher=PostgresOutboxEventPublisher(),
        )

    await run_requested_research(
        envelope,
        session_factory=current.session_factory,
        begin=build_begin_research_run,
        finish=finish,
    )


async def _project_to_timeline(envelope: EventEnvelope) -> None:
    """Timeline's projection, bound to a session at call time.

    **Idempotent without the dispatcher's ledger.** The entry id is derived
    from `event_id`, so a redelivery — or a dead letter replayed months later —
    derives the same id and `ON CONFLICT DO NOTHING` refuses it. That is what
    lets this consumer exist while [C-012] is still open: it needs no share of
    the dispatcher's transaction, because it cannot write twice.
    """
    current = runtime()
    async with tenant_scoped_session(
        current.session_factory,
        workspace_id=envelope.workspace_id,
        user_id=SYSTEM_USER_ID,
    ) as session:
        await project_to_timeline(envelope, project=build_project_event(session))
        await session.commit()


def register() -> None:
    """Register every subscription this deployment runs.

    Guarded rather than silent on a second call: `subscribe` raises on a
    duplicate, which is what stops one event being delivered twice to one
    consumer, and a re-import must not trip it.
    """
    if registry.find(consumer_name=RESEARCH_CONSUMER, event_type=RESEARCH_REQUESTED):
        return
    registry.subscribe(
        consumer_name=RESEARCH_CONSUMER,
        event_type=RESEARCH_REQUESTED,
        handler=_run_requested_research,
        # The lowest concurrency and longest timeout of any pool. Research is
        # agentic, multi-step and measured in minutes; sharing a pool with fast
        # internal work would let one run starve everything behind it.
        pool=AI_RESEARCH.name,
    )

    # **Nine event types, one handler, one subscription each.** The registry
    # keys on `(consumer, event_type)`, and the relay needs the triple in order
    # to know which queue an event fans out to — so a subscription per type is
    # not repetition, it is the routing table.
    #
    # Read from `PROJECTIONS` rather than listed here: the projection table is
    # the single authoritative statement of what Timeline consumes, and a
    # hand-written list beside it would be a second copy that drifts the first
    # time a rule is added.
    for event_type in PROJECTIONS:
        registry.subscribe(
            consumer_name=TIMELINE_CONSUMER,
            event_type=event_type,
            handler=_project_to_timeline,
            # `read_model` — declared in `pools.py` since M1.1 as *"Timeline,
            # Revenue Intelligence Platform — projection updates"*, and unused
            # until now. High concurrency and a short timeout, which is the
            # right shape for one `INSERT ... ON CONFLICT DO NOTHING`, and it
            # keeps a projection storm off the pool the pipeline runs in.
            pool=READ_MODEL.name,
        )


register()

__all__ = [
    "RESEARCH_REQUESTED",
    "RuntimeNotInstalled",
    "WorkerRuntime",
    "install",
    "register",
    "runtime",
]
