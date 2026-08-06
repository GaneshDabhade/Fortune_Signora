"""The Signal Engine's domain and use case, tested against fakes.

The properties under test are the ones that define the module: the same
evidence reads differently in two workspaces, contradiction survives, a
composite enriches rather than replaces, and nothing anywhere is a score.
"""

from __future__ import annotations

from collections.abc import Sequence
from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

import pytest

from modules.business_event_engine.public import (
    BusinessDomain,
    BusinessEvent,
    BusinessEventType,
)
from modules.commercial_profile.public import (
    DeclaredCompetitorListView,
    DeclaredCompetitorView,
)
from modules.signal_engine.application.generate import (
    GenerateSignals,
    GenerateSignalsInput,
)
from modules.signal_engine.application.queries import SignalQueries
from modules.signal_engine.domain.catalog import Relevance, SignalType
from modules.signal_engine.domain.profile import ProfileEntry, SignalProfile
from modules.signal_engine.domain.signal import Signal, SignalError, signal_id
from modules.signal_engine.infrastructure.catalog_loader import load_catalog
from signora_platform.pagination import CursorPosition
from tests.knowledge_graph.fakes import RecordingPublisher

WORKSPACE = uuid4()
ENTITY = uuid4()
START = datetime(2026, 1, 1, tzinfo=UTC)
NOW = datetime(2026, 3, 1, tzinfo=UTC)


# --------------------------------------------------------------- fakes


class FakeSignalRepository:
    def __init__(self) -> None:
        self.rows: list[Signal] = []

    def _replaced(self) -> set[UUID]:
        return {s.supersedes for s in self.rows if s.supersedes is not None}

    async def current_for_entity(
        self, workspace_id: UUID, entity_id: UUID, *, signal_type: SignalType
    ) -> tuple[Signal, ...]:
        replaced = self._replaced()
        return tuple(
            s
            for s in self.rows
            if s.entity_id == entity_id and s.signal_type is signal_type and s.id not in replaced
        )

    async def record(self, signals: tuple[Signal, ...]) -> int:
        known = {s.id for s in self.rows}
        fresh = [s for s in signals if s.id not in known]
        self.rows.extend(fresh)
        return len(fresh)

    async def for_entity(
        self,
        workspace_id: UUID,
        entity_id: UUID,
        *,
        signal_type: SignalType | None = None,
        live_at: datetime | None = None,
    ) -> tuple[Signal, ...]:
        replaced = self._replaced()
        return tuple(
            s
            for s in self.rows
            if s.entity_id == entity_id
            and (signal_type is None or s.signal_type is signal_type)
            and (live_at is None or (s.relevant_until >= live_at and s.id not in replaced))
        )

    async def for_workspace(
        self,
        workspace_id: UUID,
        *,
        live_at: datetime,
        after: CursorPosition | None,
        limit: int,
    ) -> tuple[Signal, ...]:
        """The workspace queue, newest first — **B-132**.

        **TASK-439 widened `SignalRepository` and left this behind.** `pytest`
        stayed green because Python does not enforce a `Protocol` at runtime,
        so the fake was structurally wrong and behaviourally fine right up to
        the moment a caller reached for the method it did not have. `mypy
        --strict` is what noticed, and it belongs to certification rather than
        to `make validate` — which is why this reached QE.

        **It mirrors the real query rather than approximating it**: same two
        liveness rules, same newest-first order, same keyset semantics. A fake
        that answered a slightly different question would let a test pass
        against behaviour the database does not have.
        """
        replaced = self._replaced()
        live = sorted(
            (s for s in self.rows if s.relevant_until >= live_at and s.id not in replaced),
            key=lambda s: (s.occurred_at, s.id),
            reverse=True,
        )
        if after is not None:
            live = [s for s in live if (s.occurred_at, s.id) < (after.created_at, after.id)]
        return tuple(live[:limit])

    async def by_id(self, workspace_id: UUID, signal_id_: UUID) -> Signal | None:
        return next((s for s in self.rows if s.id == signal_id_), None)

    async def citing_events(
        self, workspace_id: UUID, business_event_ids: Sequence[UUID]
    ) -> tuple[Signal, ...]:
        wanted = set(business_event_ids)
        return tuple(s for s in self.rows if wanted & set(s.contributing_event_ids))


class FakeProfileRepository:
    def __init__(self, profile: SignalProfile | None = None) -> None:
        self.versions: dict[int, SignalProfile] = {}
        if profile is not None:
            self.versions[profile.version] = profile

    async def current(self, workspace_id: UUID) -> SignalProfile | None:
        return max(self.versions.values(), key=lambda p: p.version) if self.versions else None

    async def by_version(self, workspace_id: UUID, version: int) -> SignalProfile | None:
        return self.versions.get(version)

    async def save(self, profile: SignalProfile) -> None:
        self.versions[profile.version] = profile


class FakeBusinessEvents:
    def __init__(self, events: Sequence[BusinessEvent]) -> None:
        self._events = tuple(events)

    async def business_events(
        self, workspace_id: UUID, entity_id: UUID, **_: object
    ) -> tuple[BusinessEvent, ...]:
        return self._events


# --------------------------------------------------------------- builders


def _event(
    type_key: BusinessEventType,
    day: int,
    *,
    domain: BusinessDomain = BusinessDomain.WORKFORCE,
    summary: str = "Something happened",
    facts: dict[str, object] | None = None,
) -> BusinessEvent:
    when = START + timedelta(days=day)
    return BusinessEvent(
        id=uuid4(),
        workspace_id=WORKSPACE,
        entity_id=ENTITY,
        type_key=type_key,
        domain=domain,
        occurred_at=when,
        window_start=when,
        window_end=when,
        detected_at=when,
        summary=summary,
        facts=dict(facts or {}),
        evidence_observation_ids=(uuid4(),),
        corroborating_providers=("coresignal",),
        taxonomy_version=1,
    )


def _profile(version: int, *entries: ProfileEntry) -> SignalProfile:
    return SignalProfile(
        id=uuid4(),
        workspace_id=WORKSPACE,
        version=version,
        entries=entries,
        created_at=START,
        created_by=uuid4(),
    )


class FakeCompetitorReader:
    """A declaration this module reads but does not own (ADR-0403).

    `None` is the default because it is the state every existing test was
    written in — no workspace in this suite has ever declared a rival, and a
    fake returning an empty list instead would quietly assert that *"we
    compete with nobody"* and *"nobody has asked"* behave the same.
    """

    def __init__(self, declaration: DeclaredCompetitorListView | None = None) -> None:
        self._declaration = declaration

    async def current(self, workspace_id: UUID) -> DeclaredCompetitorListView | None:
        return self._declaration


def _engine(
    repository: FakeSignalRepository,
    events: Sequence[BusinessEvent],
    profile: SignalProfile | None = None,
    competitors: DeclaredCompetitorListView | None = None,
) -> tuple[GenerateSignals, RecordingPublisher, FakeProfileRepository]:
    publisher = RecordingPublisher()
    profiles = FakeProfileRepository(profile)
    return (
        GenerateSignals(
            repository=repository,
            profiles=profiles,
            competitors=FakeCompetitorReader(competitors),
            business_events=FakeBusinessEvents(events),  # type: ignore[arg-type]
            catalog=load_catalog(),
            publisher=publisher,
            session=None,  # type: ignore[arg-type]
            clock=lambda: NOW,
        ),
        publisher,
        profiles,
    )


async def _run(
    repository: FakeSignalRepository,
    events: Sequence[BusinessEvent],
    profile: SignalProfile | None = None,
    *,
    profile_version: int | None = None,
) -> RecordingPublisher:
    engine, publisher, _ = _engine(repository, events, profile)
    await engine.execute(
        GenerateSignalsInput(
            workspace_id=WORKSPACE, entity_id=ENTITY, profile_version=profile_version
        ),
        correlation_id=uuid4(),
    )
    return publisher


# --------------------------------------------------------------- tests


class TestInterpretationIsCustomerSpecific:
    """The defining characteristic of the module. Everything above it is
    globally true; this is the first thing that is not."""

    async def test_the_same_evidence_reads_differently_in_two_workspaces(self) -> None:
        events = [
            _event(BusinessEventType.TECHNOLOGY_RETIRED, 10, summary="Stopped using LegacyERP")
        ]

        interested = FakeSignalRepository()
        await _run(repository=interested, events=events)

        uninterested = FakeSignalRepository()
        await _run(
            uninterested,
            events,
            _profile(
                1,
                ProfileEntry(SignalType.DISPLACEMENT_OPPORTUNITY, Relevance.IGNORED),
            ),
        )

        assert [s.signal_type for s in interested.rows] == [SignalType.DISPLACEMENT_OPPORTUNITY]
        assert uninterested.rows == [], "IGNORED means the hypothesis is not held here at all"

    async def test_identical_profiles_produce_identical_readings(self) -> None:
        """Interpretation varies; evidence does not."""
        events = [_event(BusinessEventType.FUNDING_ROUND_CLOSED, 5, summary="Raised 24M USD")]

        first, second = FakeSignalRepository(), FakeSignalRepository()
        await _run(first, events)
        await _run(second, events)

        assert [s.id for s in first.rows] == [s.id for s in second.rows]

    async def test_relevance_is_recorded_on_the_signal_at_generation_time(self) -> None:
        """Denormalized so the signal stays self-describing when the profile
        later changes."""
        events = [_event(BusinessEventType.FUNDING_ROUND_CLOSED, 5)]
        repository = FakeSignalRepository()

        await _run(
            repository,
            events,
            _profile(1, ProfileEntry(SignalType.BUDGET_UNLOCKED, Relevance.PRIMARY)),
        )

        assert repository.rows[0].relevance is Relevance.PRIMARY
        assert repository.rows[0].profile_version == 1

    async def test_an_unconfigured_workspace_falls_back_to_catalog_defaults(self) -> None:
        """A workspace that has said nothing still gets signals, and the
        out-of-box reading is reviewable in the catalog rather than emergent
        from an empty table."""
        repository = FakeSignalRepository()

        await _run(repository, [_event(BusinessEventType.FUNDING_ROUND_CLOSED, 5)])

        assert repository.rows[0].profile_version == 0
        assert repository.rows[0].relevance is Relevance.SUPPORTING


class TestSignalsAreHypotheses:
    async def test_a_signal_asserts_nothing_of_its_own(self) -> None:
        """Every fact in a signal is a citation. The module holds no
        measurements and no claims about the world."""
        repository = FakeSignalRepository()
        event = _event(BusinessEventType.TECHNOLOGY_RETIRED, 10)

        await _run(repository, [event])

        signal = repository.rows[0]
        assert signal.contributing_event_ids == (event.id,)
        assert signal.contributing_event_types == (BusinessEventType.TECHNOLOGY_RETIRED,)

    async def test_contradictory_hypotheses_both_stand(self) -> None:
        """A contraction risk and an expansion opportunity can be live for
        one account at once. The Signal Engine must not pick."""
        repository = FakeSignalRepository()

        await _run(
            repository,
            [
                _event(BusinessEventType.HEADCOUNT_DECLINE, 10),
                _event(BusinessEventType.HIRING_SURGE, 20),
                _event(BusinessEventType.FUNDING_ROUND_CLOSED, 25),
            ],
        )

        types = {s.signal_type for s in repository.rows}
        assert SignalType.CONTRACTION_RISK in types
        assert SignalType.EXPANSION_OPPORTUNITY in types

    async def test_the_rationale_has_two_separately_challengeable_halves(self) -> None:
        """*"We don't care about that"* is a different objection from
        *"that didn't happen"*, and only one is Signora's mistake."""
        repository = FakeSignalRepository()

        await _run(
            repository,
            [_event(BusinessEventType.TECHNOLOGY_RETIRED, 10, summary="Stopped using LegacyERP")],
        )

        rationale = repository.rows[0].rationale
        assert "Your profile treats this as a" in rationale
        assert "Based on: Stopped using LegacyERP" in rationale

    async def test_a_hypothesis_has_a_shelf_life(self) -> None:
        repository = FakeSignalRepository()

        await _run(repository, [_event(BusinessEventType.BUYING_INTENT_SURGE, 10)])

        signal = repository.rows[0]
        assert signal.relevant_until > signal.occurred_at
        window = load_catalog().definition(SignalType.ACTIVE_EVALUATION).relevance_window_days
        assert signal.relevant_until == signal.occurred_at + timedelta(days=window)


class TestCompositesEnrichRatherThanReplace:
    def _modernizing(self) -> list[BusinessEvent]:
        return [
            _event(
                BusinessEventType.TECHNOLOGY_RETIRED,
                10,
                domain=BusinessDomain.TECHNOLOGY,
                summary="Stopped using LegacyERP",
            ),
            _event(
                BusinessEventType.TECHNOLOGY_ADOPTED,
                20,
                domain=BusinessDomain.TECHNOLOGY,
                summary="Started using CloudERP",
            ),
        ]

    async def test_the_constituent_signal_remains_independently_visible(self) -> None:
        repository = FakeSignalRepository()

        await _run(repository, self._modernizing())

        types = {s.signal_type for s in repository.rows}
        assert SignalType.MODERNIZATION_UNDERWAY in types
        assert SignalType.DISPLACEMENT_OPPORTUNITY in types, (
            "a composite must never suppress the hypothesis it builds on"
        )

    async def test_the_composite_names_what_it_enriches(self) -> None:
        repository = FakeSignalRepository()

        await _run(repository, self._modernizing())

        composite = next(
            s for s in repository.rows if s.signal_type is SignalType.MODERNIZATION_UNDERWAY
        )
        constituent = next(
            s for s in repository.rows if s.signal_type is SignalType.DISPLACEMENT_OPPORTUNITY
        )

        assert constituent.id in composite.constituent_signal_ids

    async def test_a_composite_needs_distinct_contributing_types(self) -> None:
        """Three hiring surges are one phenomenon reported repeatedly, not
        three independent grounds for believing a company is expanding."""
        repository = FakeSignalRepository()

        await _run(
            repository,
            [_event(BusinessEventType.HIRING_SURGE, day) for day in (5, 15, 25)],
        )

        assert not any(s.signal_type is SignalType.EXPANSION_OPPORTUNITY for s in repository.rows)

    async def test_evidence_outside_the_window_does_not_compose(self) -> None:
        repository = FakeSignalRepository()

        await _run(
            repository,
            [
                _event(BusinessEventType.HIRING_SURGE, 5),
                _event(BusinessEventType.FUNDING_ROUND_CLOSED, 900),
            ],
        )

        assert not any(s.signal_type is SignalType.EXPANSION_OPPORTUNITY for s in repository.rows)


class TestDurableHypotheses:
    async def test_re_running_over_the_same_evidence_generates_nothing(self) -> None:
        repository = FakeSignalRepository()
        events = [_event(BusinessEventType.FUNDING_ROUND_CLOSED, 5)]

        await _run(repository, events)
        publisher = await _run(repository, events)

        assert len(repository.rows) == 1
        assert publisher.events == []

    async def test_a_hypothesis_that_gains_evidence_supersedes(self) -> None:
        repository = FakeSignalRepository()
        hiring = _event(BusinessEventType.HIRING_SURGE, 5)
        funding = _event(BusinessEventType.FUNDING_ROUND_CLOSED, 15)

        await _run(repository, [hiring, funding])
        earlier = next(
            s for s in repository.rows if s.signal_type is SignalType.EXPANSION_OPPORTUNITY
        )

        revenue = _event(BusinessEventType.REVENUE_GROWTH, 25)
        publisher = await _run(repository, [hiring, funding, revenue])

        composites = [
            s for s in repository.rows if s.signal_type is SignalType.EXPANSION_OPPORTUNITY
        ]
        assert len(composites) == 2
        assert composites[-1].supersedes == earlier.id
        assert earlier in repository.rows, "the earlier hypothesis stays readable"
        assert "signal.superseded" in publisher.types()


class TestReplayModes:
    async def test_historical_replay_reproduces_what_the_customer_was_told(self) -> None:
        """Two modes, never conflated: this one answers *"reproduce what we
        told them"*."""
        repository = FakeSignalRepository()
        events = [_event(BusinessEventType.FUNDING_ROUND_CLOSED, 5)]
        original = _profile(1, ProfileEntry(SignalType.BUDGET_UNLOCKED, Relevance.PRIMARY))

        engine, _, profiles = _engine(repository, events, original)
        await profiles.save(
            _profile(2, ProfileEntry(SignalType.BUDGET_UNLOCKED, Relevance.CONTEXTUAL))
        )
        await engine.execute(
            GenerateSignalsInput(workspace_id=WORKSPACE, entity_id=ENTITY, profile_version=1),
            correlation_id=uuid4(),
        )

        assert repository.rows[0].relevance is Relevance.PRIMARY
        assert repository.rows[0].profile_version == 1

    async def test_current_replay_answers_what_we_would_say_now(self) -> None:
        repository = FakeSignalRepository()
        events = [_event(BusinessEventType.FUNDING_ROUND_CLOSED, 5)]

        await _run(
            repository,
            events,
            _profile(2, ProfileEntry(SignalType.BUDGET_UNLOCKED, Relevance.CONTEXTUAL)),
        )

        assert repository.rows[0].relevance is Relevance.CONTEXTUAL
        assert repository.rows[0].profile_version == 2


class TestTheDomainRefusesIncoherentSignals:
    def _signal(self, **overrides: object) -> Signal:
        event_ids = (uuid4(),)
        base: dict[str, object] = {
            "id": signal_id(
                workspace_id=WORKSPACE,
                entity_id=ENTITY,
                signal_type=SignalType.BUDGET_UNLOCKED,
                contributing_event_ids=event_ids,
            ),
            "workspace_id": WORKSPACE,
            "entity_id": ENTITY,
            "signal_type": SignalType.BUDGET_UNLOCKED,
            "relevance": Relevance.SUPPORTING,
            "occurred_at": START,
            "window_start": START,
            "window_end": START,
            "generated_at": NOW,
            "relevant_until": NOW,
            "rationale": "Because.",
            "contributing_event_ids": event_ids,
            "contributing_event_types": (BusinessEventType.FUNDING_ROUND_CLOSED,),
        }
        return Signal(**{**base, **overrides})  # type: ignore[arg-type]

    def test_a_signal_without_evidence_is_refused(self) -> None:
        with pytest.raises(SignalError, match="cites no business events"):
            self._signal(contributing_event_ids=())

    def test_a_signal_the_workspace_ignores_is_refused(self) -> None:
        """`IGNORED` means the hypothesis is not held here at all, not that
        it is held weakly."""
        with pytest.raises(SignalError, match="not held here at all"):
            self._signal(relevance=Relevance.IGNORED)

    def test_a_signal_without_a_rationale_is_refused(self) -> None:
        with pytest.raises(SignalError, match="neither understand nor"):
            self._signal(rationale="  ")

    def test_a_shelf_life_before_the_event_is_refused(self) -> None:
        with pytest.raises(SignalError, match="stop being relevant before"):
            self._signal(relevant_until=START - timedelta(days=1))


class TestTheReadSurface:
    async def _queries(
        self,
        repository: FakeSignalRepository,
        events: Sequence[BusinessEvent],
        profile: SignalProfile | None = None,
    ) -> SignalQueries:
        return SignalQueries(
            repository=repository,
            profiles=FakeProfileRepository(profile),
            business_events=FakeBusinessEvents(events),  # type: ignore[arg-type]
            catalog=load_catalog(),
        )

    async def test_an_explanation_answers_all_four_questions(self) -> None:
        repository = FakeSignalRepository()
        events = [
            _event(BusinessEventType.TECHNOLOGY_RETIRED, 10, summary="Stopped using LegacyERP")
        ]
        await _run(repository, events)
        queries = await self._queries(repository, events)

        explanation = await queries.explanation(WORKSPACE, repository.rows[0].id)

        assert explanation is not None
        assert explanation.signal.rationale
        assert explanation.business_events[0].summary == "Stopped using LegacyERP"
        assert explanation.profile_version == 0
        assert explanation.signal.relevant_until > explanation.signal.occurred_at
        assert explanation.definition.hypothesis

    async def test_an_expired_hypothesis_is_not_live(self) -> None:
        repository = FakeSignalRepository()
        events = [_event(BusinessEventType.BUYING_INTENT_SURGE, 10)]
        await _run(repository, events)
        queries = await self._queries(repository, events)

        live = await queries.signals(WORKSPACE, ENTITY, now=NOW + timedelta(days=3650))

        assert live == ()

    async def test_a_type_the_workspace_stopped_holding_is_not_live(self) -> None:
        """The third way a hypothesis stops being current, and the only one
        that is a profile question rather than a signal one."""
        repository = FakeSignalRepository()
        events = [_event(BusinessEventType.FUNDING_ROUND_CLOSED, 5)]
        await _run(repository, events)

        queries = await self._queries(
            repository,
            events,
            _profile(1, ProfileEntry(SignalType.BUDGET_UNLOCKED, Relevance.IGNORED)),
        )
        live = await queries.signals(WORKSPACE, ENTITY, now=NOW)

        assert live == ()

    def test_a_signal_answers_only_the_shelf_life_question_itself(self) -> None:
        """`supersedes` points **backwards**, at the signal this one
        replaces — so whether anything replaced *this* one is a fact about
        other rows, and a lone signal cannot report it.

        The earlier `is_live_at` conflated the two and returned True for any
        signal that replaced nothing, skipping the shelf-life check
        entirely. It was unused, which is the only reason it never bit.
        """
        from modules.signal_engine.domain.signal import relevant_until

        superseding = _signal_replacing_something()

        assert superseding.is_within_shelf_life(superseding.occurred_at) is True
        assert superseding.is_within_shelf_life(superseding.relevant_until) is True
        assert (
            superseding.is_within_shelf_life(relevant_until(superseding.relevant_until, 1)) is False
        ), "shelf life must be checked whether or not this signal replaces another"

    async def test_the_catalog_is_reachable_through_the_read_surface(self) -> None:
        queries = await self._queries(FakeSignalRepository(), [])

        assert len(queries.catalog().types) == len(SignalType)


def _signal_replacing_something() -> Signal:
    """A signal that supersedes an earlier one — the case the old method
    got wrong in the opposite direction."""
    event_ids = (uuid4(),)
    return Signal(
        id=signal_id(
            workspace_id=WORKSPACE,
            entity_id=ENTITY,
            signal_type=SignalType.BUDGET_UNLOCKED,
            contributing_event_ids=event_ids,
        ),
        workspace_id=WORKSPACE,
        entity_id=ENTITY,
        signal_type=SignalType.BUDGET_UNLOCKED,
        relevance=Relevance.SUPPORTING,
        occurred_at=START,
        window_start=START,
        window_end=START,
        generated_at=NOW,
        relevant_until=START + timedelta(days=30),
        rationale="Because.",
        contributing_event_ids=event_ids,
        contributing_event_types=(BusinessEventType.FUNDING_ROUND_CLOSED,),
        supersedes=uuid4(),
    )


def _input() -> GenerateSignalsInput:
    return GenerateSignalsInput(workspace_id=WORKSPACE, entity_id=ENTITY)


def _adopted(day: int, technology: str) -> BusinessEvent:
    return _event(
        BusinessEventType.TECHNOLOGY_ADOPTED,
        day,
        domain=BusinessDomain.TECHNOLOGY,
        summary=f"Started using {technology}",
        facts={"technology": technology, "category": "crm"},
    )


def _declared(*names: str) -> DeclaredCompetitorListView:
    return DeclaredCompetitorListView(
        workspace_id=WORKSPACE,
        competitors=tuple(DeclaredCompetitorView(id=uuid4(), name=name) for name in names),
    )


def _entries(repository: FakeSignalRepository) -> list[SignalType]:
    return [row.signal_type for row in repository.rows]


class TestCompetitorEntry:
    """The third detection strategy: evidence that is not grounds on its own.

    *A company started using CloudCRM* is a fact about them. Whether it is a
    risk depends on a sentence the customer typed, which is why this is the
    first signal type whose grounds live outside the evidence.
    """

    async def test_an_adopted_rival_is_grounds(self) -> None:
        repository = FakeSignalRepository()
        engine, _, _ = _engine(
            repository, [_adopted(1, "CloudCRM")], competitors=_declared("CloudCRM")
        )

        await engine.execute(_input(), correlation_id=uuid4())

        assert SignalType.COMPETITOR_ENTRY in _entries(repository)

    async def test_an_adoption_nobody_declared_is_not(self) -> None:
        """The same event, and the customer said nothing about it."""
        repository = FakeSignalRepository()
        engine, _, _ = _engine(
            repository, [_adopted(1, "CloudCRM")], competitors=_declared("Salesforce")
        )

        await engine.execute(_input(), correlation_id=uuid4())

        assert SignalType.COMPETITOR_ENTRY not in _entries(repository)

    async def test_a_workspace_that_declared_nobody_grounds_nothing(self) -> None:
        repository = FakeSignalRepository()
        engine, _, _ = _engine(repository, [_adopted(1, "CloudCRM")], competitors=_declared())

        await engine.execute(_input(), correlation_id=uuid4())

        assert SignalType.COMPETITOR_ENTRY not in _entries(repository)

    async def test_a_workspace_that_was_never_asked_grounds_nothing(self) -> None:
        """`None` and an empty list reach the rule the same way.

        They are different facts to the surface that asks and the same
        instruction to the rule that grounds — see `_resolve_competitors`.
        """
        repository = FakeSignalRepository()
        engine, _, _ = _engine(repository, [_adopted(1, "CloudCRM")], competitors=None)

        await engine.execute(_input(), correlation_id=uuid4())

        assert SignalType.COMPETITOR_ENTRY not in _entries(repository)

    async def test_the_match_ignores_case_and_surrounding_space(self) -> None:
        repository = FakeSignalRepository()
        engine, _, _ = _engine(
            repository, [_adopted(1, "CloudCRM")], competitors=_declared("  cloudcrm ")
        )

        await engine.execute(_input(), correlation_id=uuid4())

        assert SignalType.COMPETITOR_ENTRY in _entries(repository)

    async def test_it_resolves_nothing_beyond_that(self) -> None:
        """**No second resolver.** *Salesforce* and *salesforce.com* are one
        thing to the Knowledge Graph and two here, deliberately — a cleverer
        comparison in this module would quietly disagree with the one that
        owns resolution. The catalog records the consequence as a limitation.
        """
        repository = FakeSignalRepository()
        engine, _, _ = _engine(
            repository, [_adopted(1, "Salesforce")], competitors=_declared("salesforce.com")
        )

        await engine.execute(_input(), correlation_id=uuid4())

        assert SignalType.COMPETITOR_ENTRY not in _entries(repository)

    async def test_two_rivals_arriving_are_two_signals(self) -> None:
        """Merging them would hide the second, as `_single` says of its own."""
        repository = FakeSignalRepository()
        engine, _, _ = _engine(
            repository,
            [_adopted(1, "CloudCRM"), _adopted(2, "HubSpot")],
            competitors=_declared("CloudCRM", "HubSpot"),
        )

        await engine.execute(_input(), correlation_id=uuid4())

        assert _entries(repository).count(SignalType.COMPETITOR_ENTRY) == 2

    async def test_a_declaration_grounds_nothing_without_an_adoption(self) -> None:
        repository = FakeSignalRepository()
        engine, _, _ = _engine(
            repository,
            [_event(BusinessEventType.HEADCOUNT_DECLINE, 1)],
            competitors=_declared("CloudCRM"),
        )

        await engine.execute(_input(), correlation_id=uuid4())

        assert SignalType.COMPETITOR_ENTRY not in _entries(repository)
