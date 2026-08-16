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
from typing import Final
from uuid import UUID

import httpx
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from apps.worker.pools import AI_RESEARCH, DEFAULT, INTELLIGENCE, READ_MODEL
from modules.action_batch.domain.events import (
    APPLICATION_REQUESTED as ACTION_BATCH_APPLICATION_REQUESTED,
)

# **Two `build_provider_registry` functions exist and they are different
# things.** `ai_platform`'s resolves a *model* to a vendor adapter;
# `provider_platform`'s resolves a *data provider* to its adapter. ADR-0404
# tripped over the collision and TASK-419's row warns about it by name, so
# both are imported under explicit aliases here rather than one shadowing the
# other by import order.
from modules.action_batch.domain.events import (
    APPLIED as ACTION_BATCH_APPLIED,
)
from modules.action_batch.domain.events import (
    REVERSED as ACTION_BATCH_REVERSED,
)
from modules.action_batch.infrastructure.composition import build_action_batches
from modules.action_batch.interface.handlers import (
    CONSUMER_NAME as ACTION_BATCH_CONSUMER,
)
from modules.action_batch.interface.handlers import apply_accepted_batch
from modules.ai_platform.infrastructure.composition import (
    build_provider_registry as build_ai_provider_registry,
)
from modules.ai_platform.infrastructure.prompt_loader import load_prompt_registry
from modules.ai_platform.infrastructure.repository import SqlInferenceRecorder
from modules.ai_platform.infrastructure.settings import AISettings
from modules.ai_platform.public import Infer, InferencePolicy
from modules.ai_research_engine.application.run import FinishResearchRun
from modules.ai_research_engine.domain.events import (
    RESEARCH_REQUESTED as RESEARCH_REQUESTED_EVENT,
)
from modules.ai_research_engine.infrastructure.composition import (
    PROMPT_DIR,
    build_begin_research_run,
    build_finish_research_run,
)
from modules.ai_research_engine.interface.handlers import (
    CONSUMER_NAME as RESEARCH_CONSUMER,
)
from modules.ai_research_engine.interface.handlers import run_requested_research
from modules.workspace_tenancy.domain.notification import NOTIFICATION_REQUESTED
from modules.workspace_tenancy.infrastructure.composition import build_notifier
from modules.workspace_tenancy.interface.handlers import (
    CONSUMER_NAME as NOTIFICATION_CONSUMER,
)
from modules.workspace_tenancy.interface.handlers import deliver_requested_notification
from modules.business_event_engine.infrastructure.composition import (
    build_queries as build_business_event_queries,
)
from modules.business_event_engine.public import BusinessEventQueries
from modules.buying_score_engine.infrastructure.composition import (
    build_compute_buying_score,
)
from modules.buying_score_engine.infrastructure.composition import (
    build_queries as build_buying_score_queries,
)
from modules.buying_score_engine.interface.handlers import (
    CONSUMER_NAME as SCORE_CONSUMER,
)
from modules.buying_score_engine.interface.handlers import compute_from_signal
from modules.commercial_profile.infrastructure.competitor_reader import (
    SqlDeclaredCompetitorReader,
)
from modules.commercial_profile.infrastructure.composition import (
    build_apply_assignment_batch,
    build_apply_segment_batch,
    build_apply_tag_batch,
    build_reverse_assignment_batch,
    build_reverse_segment_batch,
    build_reverse_tag_batch,
)
from modules.commercial_profile.interface.tag_batch_handlers import (
    APPLY_CONSUMER_NAME as TAG_BATCH_APPLY_CONSUMER,
)
from modules.commercial_profile.interface.tag_batch_handlers import (
    ASSIGNMENT_APPLY_CONSUMER_NAME as ASSIGNMENT_BATCH_APPLY_CONSUMER,
)
from modules.commercial_profile.interface.tag_batch_handlers import (
    ASSIGNMENT_REVERSE_CONSUMER_NAME as ASSIGNMENT_BATCH_REVERSE_CONSUMER,
)
from modules.commercial_profile.interface.tag_batch_handlers import (
    REVERSE_CONSUMER_NAME as TAG_BATCH_REVERSE_CONSUMER,
)
from modules.commercial_profile.interface.tag_batch_handlers import (
    SEGMENT_APPLY_CONSUMER_NAME as SEGMENT_BATCH_APPLY_CONSUMER,
)
from modules.commercial_profile.interface.tag_batch_handlers import (
    SEGMENT_REVERSE_CONSUMER_NAME as SEGMENT_BATCH_REVERSE_CONSUMER,
)
from modules.commercial_profile.interface.tag_batch_handlers import (
    apply_assignment_batch,
    apply_segment_batch,
    apply_tag_batch,
    reverse_assignment_batch,
    reverse_segment_batch,
    reverse_tag_batch,
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
from modules.people.infrastructure.composition import build_affiliation_reader
from modules.provider_normalization.infrastructure.claim_reader import SqlClaimReader
from modules.provider_platform.domain.provider import ProviderRegistry
from modules.signal_engine.infrastructure.composition import build_generate_signals
from modules.signal_engine.infrastructure.composition import (
    build_queries as build_signal_queries,
)
from modules.signal_engine.interface.handlers import CONSUMER_NAME as SIGNAL_CONSUMER
from modules.signal_engine.interface.handlers import generate_from_business_event
from modules.timeline.domain.projection import PROJECTIONS
from modules.timeline.infrastructure.composition import build_project_event
from modules.timeline.interface.handlers import CONSUMER_NAME as TIMELINE_CONSUMER
from modules.timeline.interface.handlers import project_to_timeline
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

#: What Signal Engine consumes, named here as strings.
#:
#: ⚠️ **Not imported from `business_event_engine.domain.events`, because there
#: is nothing there to import.** Both wire names exist only as defaults on
#: `slots=True` dataclasses, and reading `BusinessEventDetected.event_type`
#: yields a descriptor repr rather than the string — the trap
#: `ai_research_engine` hit and then fixed by declaring `Final` constants
#: beside its events. **That module has not, so this composition root spells
#: them out and says why.** Reported rather than fixed: the constants belong
#: in the module that owns the vocabulary, and it is not this lane's.
SIGNAL_INPUTS: Final = ("business_event.detected", "business_event.superseded")

#: What Buying Score Engine consumes. **Both, and its own docstring says why**:
#: *"a strengthened hypothesis arrives as a new signal plus a supersession, and
#: a consumer that handled only the first would keep weighing the replaced
#: reading alongside the one that replaced it — counting the same grounds
#: twice."* Spelled out here for `SIGNAL_INPUTS`' reason, one module over.
SCORE_INPUTS: Final = ("signal.generated", "signal.superseded")


class RuntimeNotInstalled(RuntimeError):
    """A handler ran in a process that never installed a worker runtime."""


@dataclass(frozen=True)
class WorkerRuntime:
    """What a handler needs and cannot have at import time."""

    session_factory: async_sessionmaker[AsyncSession]
    http: httpx.AsyncClient
    ai: AISettings
    #: The **data** provider adapters this deployment serves —
    #: [ADR-0404](../../../docs/architecture/adr/0404-platform-composition.md)
    #: capability 3, and the half `apps/` owes.
    #:
    #: **Named `provider_registry` rather than `providers`**, because `ai` above
    #: already carries the AI provider registry and the two are different
    #: things. ADR-0404 tripped over exactly that collision.
    #:
    #: **No default.** A handler reaching a provider is the capability this
    #: field exists for; a default would let a worker start with an empty
    #: registry and surface as *"no adapter registered"* at call time, which is
    #: a composition fault reported as a data problem. `runtime()` already
    #: refuses to invent a runtime for the same reason.
    provider_registry: ProviderRegistry

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
        providers=build_ai_provider_registry(current.ai, client=current.http),
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
    graph = build_graph_queries(session, claims=SqlClaimReader(session, workspace_id=workspace_id))
    observations = build_observation_queries(session, graph=graph)
    events = build_business_event_queries(session, observations=observations)
    signals = build_signal_queries(session, business_events=events)
    scores = build_buying_score_queries(session, signals=signals)
    return build_opportunity_queries(session, scores=scores)


async def _apply_accepted_batch(envelope: EventEnvelope) -> None:
    current = runtime()

    await apply_accepted_batch(
        envelope,
        session_factory=current.session_factory,
        batches=build_action_batches,
    )


async def _apply_tag_batch(envelope: EventEnvelope) -> None:
    current = runtime()

    await apply_tag_batch(
        envelope,
        session_factory=current.session_factory,
        apply=build_apply_tag_batch,
    )


async def _reverse_tag_batch(envelope: EventEnvelope) -> None:
    current = runtime()

    await reverse_tag_batch(
        envelope,
        session_factory=current.session_factory,
        reverse=build_reverse_tag_batch,
    )


async def _apply_assignment_batch(envelope: EventEnvelope) -> None:
    current = runtime()

    await apply_assignment_batch(
        envelope,
        session_factory=current.session_factory,
        apply=build_apply_assignment_batch,
    )


async def _apply_segment_batch(envelope: EventEnvelope) -> None:
    current = runtime()

    await apply_segment_batch(
        envelope,
        session_factory=current.session_factory,
        apply=build_apply_segment_batch,
    )


async def _reverse_segment_batch(envelope: EventEnvelope) -> None:
    current = runtime()

    await reverse_segment_batch(
        envelope,
        session_factory=current.session_factory,
        reverse=build_reverse_segment_batch,
    )


async def _reverse_assignment_batch(envelope: EventEnvelope) -> None:
    current = runtime()

    await reverse_assignment_batch(
        envelope,
        session_factory=current.session_factory,
        reverse=build_reverse_assignment_batch,
    )


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


async def _deliver_requested_notification(envelope: EventEnvelope) -> None:
    """Deliver what a producer asked to be delivered — [TASK-495](../../../docs/BACKLOG.md).

    ⚡ **The registry is built per session** because the in-app channel writes
    through a session-bound repository — 📁 the same shape every other handler
    here takes, and the reason `build_notifier` is a factory rather than a
    module-level singleton.
    """
    current = runtime()

    await deliver_requested_notification(
        envelope,
        session_factory=current.session_factory,
        notify=build_notifier,
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


def _business_events(session: AsyncSession, workspace_id: UUID) -> BusinessEventQueries:
    """The read chain two pipeline stages need — **built once here**.

    **The same two-levels-deep chain `apps/api/composition/triage.py` builds**:
    business events need observations, which need the graph. **Every edge is
    one the dependency matrix already ratified; none is new.**

    ⚠️ **The claim reader is workspace-scoped from the caller**, never from a
    default. The API takes it from the verified request context; a handler's
    equivalent is the event's own `workspace_id`, which `tenant_scoped_session`
    has just established as the RLS key.

    **One function rather than one per consumer** — Signal Engine needs this
    chain to form hypotheses and Buying Score needs it to read them back, and
    two copies would drift the first time an edge changes (§2).
    """
    graph = build_graph_queries(session, claims=SqlClaimReader(session, workspace_id=workspace_id))
    observations = build_observation_queries(session, graph=graph)
    return build_business_event_queries(session, observations=observations)


async def _compute_buying_score(envelope: EventEnvelope) -> None:
    """Re-read an account's attention when its hypotheses move (TASK-901 slice 3).

    **Signals are read back through the Signal Engine's published port rather
    than reconstructed from the envelope**, which is the module's own rule:
    *"events carry identity; ports carry payload, and a score built from an
    event body would be a score built from whatever the envelope happened to
    include."* That is why this composes the read chain rather than passing the
    payload along.
    """
    current = runtime()
    async with tenant_scoped_session(
        current.session_factory,
        workspace_id=envelope.workspace_id,
        user_id=SYSTEM_USER_ID,
    ) as session:
        signals = build_signal_queries(
            session, business_events=_business_events(session, envelope.workspace_id)
        )
        await compute_from_signal(
            envelope,
            compute=build_compute_buying_score(
                session, signals=signals, publisher=PostgresOutboxEventPublisher()
            ),
        )
        await session.commit()


async def _generate_signals(envelope: EventEnvelope) -> None:
    """Form hypotheses when a business event is detected (TASK-901 slice 2).

    **The same two-levels-deep chain `apps/api/composition/triage.py` builds**
    — signals need business events, which need observations, which need the
    graph — and it is built here for the same reason it is built there: **the
    composition root is the one place that may legitimately import more than
    one module's infrastructure** (ADR-0403).

    ⚠️ **The claim reader is workspace-scoped from the envelope**, never from
    a default. The API takes it from the verified request context; a handler's
    equivalent is the event's own `workspace_id`, which the relay carries and
    `tenant_scoped_session` has just established as the RLS key.
    """
    current = runtime()
    async with tenant_scoped_session(
        current.session_factory,
        workspace_id=envelope.workspace_id,
        user_id=SYSTEM_USER_ID,
    ) as session:
        events = _business_events(session, envelope.workspace_id)
        await generate_from_business_event(
            envelope,
            generate=build_generate_signals(
                session,
                business_events=events,
                competitors=SqlDeclaredCompetitorReader(session),
                affiliations=build_affiliation_reader(session),
                publisher=PostgresOutboxEventPublisher(),
            ),
        )
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

    # **Somebody is told that something happened** — [TASK-495](../../../docs/BACKLOG.md),
    # on [ADR-0017](../../../docs/architecture/adr/0017-notifications.md).
    #
    # 🔴 **This is what makes the trigger interface asynchronous, and that is
    # the architectural point rather than a performance one.** 📁
    # [05](../../../docs/architecture/05-module-dependencies.md) approves only
    # READ-ONLY synchronous edges into `workspace_tenancy`, so a producer
    # calling a notify port directly would be a synchronous write into another
    # module — ⛔ **an architecture change no lane may make.** ✅ **Publishing
    # conforms to that module's published language, which 05 already ratifies.**
    #
    # ⛔ **`default`, and named rather than assumed.** ⚡ **Delivering in-app is
    # one INSERT** — no model call, no provider, no vendor — **and inventing a
    # `notification` pool for one fast consumer is capacity nobody has measured
    # a need for** (§14). ⚠️ **When a channel that leaves the process arrives,
    # that is the moment to ask again**: an email adapter waiting on a vendor
    # has a latency profile this one does not.
    registry.subscribe(
        consumer_name=NOTIFICATION_CONSUMER,
        event_type=NOTIFICATION_REQUESTED,
        handler=_deliver_requested_notification,
        pool=DEFAULT.name,
    )

    # **The Action Batch applies what somebody accepted** —
    # [TASK-465](../../../docs/BACKLOG.md), slice 5.
    #
    # ⚡ **This module publishes to itself, and that is the point**: §14 says a
    # handler answers once a request is durably accepted, and §9 says the only
    # durable way to hand work onward is the outbox. **`ai_research_engine`
    # established the shape and this follows it** rather than adding a second
    # mechanism.
    #
    # ⛔ **`default`, and named rather than assumed.** 📁 The pool's own
    # description is *"consumers that have not yet been assigned a specific
    # pool"*, and that is the honest answer: applying a batch is fast internal
    # work with no model call and no provider, so it belongs to none of the
    # named pools — **and inventing an `action_batch` pool for one consumer
    # would be capacity nobody has measured a need for** (§14).
    registry.subscribe(
        consumer_name=ACTION_BATCH_CONSUMER,
        event_type=ACTION_BATCH_APPLICATION_REQUESTED,
        handler=_apply_accepted_batch,
        pool=DEFAULT.name,
    )

    # **The consuming domain performs the work** — [TASK-466](../../../docs/BACKLOG.md),
    # and `action_batch`'s own handler names this slice: *"the use case
    # remains, and its caller is slice 6."*
    #
    # ⚡ **This is the composition root knowing both names, which is its job.**
    # ⛔ **`commercial_profile` imports nothing from `action_batch`** — its
    # handlers take a generic `EventEnvelope` and read `payload["batch_id"]`,
    # so the producing module's types never cross the boundary (§5).
    #
    # ⛔ **`default`, on the same reasoning as the subscription above**:
    # tagging a page of accounts is fast internal work with no model call and
    # no provider, and inventing a pool for one consumer would be capacity
    # nobody has measured a need for (§14).
    if not registry.find(
        consumer_name=TAG_BATCH_APPLY_CONSUMER, event_type=ACTION_BATCH_APPLIED
    ):
        registry.subscribe(
            consumer_name=TAG_BATCH_APPLY_CONSUMER,
            event_type=ACTION_BATCH_APPLIED,
            handler=_apply_tag_batch,
            pool=DEFAULT.name,
        )
    if not registry.find(
        consumer_name=TAG_BATCH_REVERSE_CONSUMER, event_type=ACTION_BATCH_REVERSED
    ):
        registry.subscribe(
            consumer_name=TAG_BATCH_REVERSE_CONSUMER,
            event_type=ACTION_BATCH_REVERSED,
            handler=_reverse_tag_batch,
            pool=DEFAULT.name,
        )

    # **ADR-0411's second capability on the same two events** — TASK-1479
    # slice ⓶. ⚡ **Separate consumers from the tag pair**, because one consumer
    # handling both would make a tag batch and an owner batch share an
    # idempotency key, and a replayed event would be swallowed by whichever ran
    # first.
    if not registry.find(
        consumer_name=ASSIGNMENT_BATCH_APPLY_CONSUMER, event_type=ACTION_BATCH_APPLIED
    ):
        registry.subscribe(
            consumer_name=ASSIGNMENT_BATCH_APPLY_CONSUMER,
            event_type=ACTION_BATCH_APPLIED,
            handler=_apply_assignment_batch,
            pool=DEFAULT.name,
        )
    if not registry.find(
        consumer_name=ASSIGNMENT_BATCH_REVERSE_CONSUMER, event_type=ACTION_BATCH_REVERSED
    ):
        registry.subscribe(
            consumer_name=ASSIGNMENT_BATCH_REVERSE_CONSUMER,
            event_type=ACTION_BATCH_REVERSED,
            handler=_reverse_assignment_batch,
            pool=DEFAULT.name,
        )

    # **ADR-0411's THIRD capability on the same two events** — TASK-1479 slice
    # ⓶b. ⚡ **A third consumer pair, on the same reasoning the second one
    # states**: one consumer handling several capabilities would make a tag
    # batch, an owner batch and a segment batch share an idempotency key, and a
    # replayed event would be swallowed by whichever ran first.
    #
    # ⛔ **Each handler returns early on a batch that is not its own** — the
    # `applied` event is a shared lifecycle and every consumer sees every one
    # of them, so "not mine" is a normal outcome and never an error.
    if not registry.find(
        consumer_name=SEGMENT_BATCH_APPLY_CONSUMER, event_type=ACTION_BATCH_APPLIED
    ):
        registry.subscribe(
            consumer_name=SEGMENT_BATCH_APPLY_CONSUMER,
            event_type=ACTION_BATCH_APPLIED,
            handler=_apply_segment_batch,
            pool=DEFAULT.name,
        )
    if not registry.find(
        consumer_name=SEGMENT_BATCH_REVERSE_CONSUMER, event_type=ACTION_BATCH_REVERSED
    ):
        registry.subscribe(
            consumer_name=SEGMENT_BATCH_REVERSE_CONSUMER,
            event_type=ACTION_BATCH_REVERSED,
            handler=_reverse_segment_batch,
            pool=DEFAULT.name,
        )

    # **Signal generation, TASK-901 slice 2 — the second module to consume
    # what it declares.** Two event types because the module's own handler
    # documents two: a business event detected, and one superseded. **One
    # subscription each**, for the reason the Timeline block below states —
    # the registry keys on `(consumer, event_type)` and the relay needs the
    # triple to route.
    #
    # `intelligence` is the pool `pools.py` declared for exactly this since
    # M1.1 — *"Business Event, Signal, Buying Score, Opportunity Engines"* —
    # and it has never had a subscriber.
    for signal_event in SIGNAL_INPUTS:
        registry.subscribe(
            consumer_name=SIGNAL_CONSUMER,
            event_type=signal_event,
            handler=_generate_signals,
            pool=INTELLIGENCE.name,
        )

    # **Buying Score, TASK-901 slice 3.** The stage directly downstream of the
    # one above, on the same pool, for the same reason.
    for score_event in SCORE_INPUTS:
        registry.subscribe(
            consumer_name=SCORE_CONSUMER,
            event_type=score_event,
            handler=_compute_buying_score,
            pool=INTELLIGENCE.name,
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
