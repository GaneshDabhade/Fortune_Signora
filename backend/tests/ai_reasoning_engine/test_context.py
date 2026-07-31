"""The pipeline translation, unit-tested where the integration fixture cannot reach.

`_support`, `_temporal` and `_catalog_text` are pure functions over another
module's public types, so they are tested directly rather than only through the
real pipeline. **This is not a convenience.** Four mutations survived the
integration suite — counting signals instead of distinct events, dropping
`contested`, and removing two deduplications — because the seeded scenario
happens to have one event per signal, no contested score, and no two signal
types sharing a caveat. A property that a fixture cannot vary is a property the
fixture cannot test, and the coincidence would have been mistaken for coverage.

Each test below constructs the case the fixture cannot: an event cited by two
signals, a contested score, two types sharing a limitation.
"""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID, uuid4

import pytest

from modules.ai_reasoning_engine.infrastructure.context import (
    PipelineReasoningContext,
    _support,
    _temporal,
)
from modules.business_event_engine.public import (
    BusinessDomain,
    BusinessEvent,
    BusinessEventType,
)
from modules.buying_score_engine.public import (
    BuyingScoreExplanation,
    ScoreTrigger,
)
from modules.opportunity_engine.public import EvidenceState

NOW = datetime(2026, 6, 1, tzinfo=UTC)
WORKSPACE = uuid4()
ENTITY = uuid4()


def _event(*, providers: tuple[str, ...], event_id: UUID | None = None) -> BusinessEvent:
    observation = uuid4()
    return BusinessEvent(
        id=event_id or uuid4(),
        workspace_id=WORKSPACE,
        entity_id=ENTITY,
        type_key=BusinessEventType.HIRING_SURGE,
        domain=BusinessDomain.WORKFORCE,
        occurred_at=NOW,
        window_start=NOW,
        window_end=NOW,
        detected_at=NOW,
        summary="Grew",
        facts={"ratio": 0.4},
        evidence_observation_ids=(observation,),
        corroborating_providers=providers,
        taxonomy_version=1,
    )


class _Signal:
    """The one member of `SignalExplanation` that `_support` reads."""

    def __init__(self, events: tuple[BusinessEvent, ...]) -> None:
        self.business_events = events


class _Score:
    """The members of `BuyingScore` that `_support`/`_temporal` read."""

    def __init__(
        self,
        *,
        contested: bool = False,
        dissenting: tuple[UUID, ...] = (),
    ) -> None:
        self.id = uuid4()
        self.contested = contested
        self.dissenting_signal_ids = dissenting
        self.trigger = ScoreTrigger.SIGNAL_GENERATED
        self.basis_at = NOW
        self.computed_at = NOW
        self.delta = 0
        self.trend = None
        self.valid_until = None
        self.supersedes = None


class _Explanation:
    def __init__(self, score: _Score, signals: tuple[_Signal, ...]) -> None:
        self.score = score
        self.signals = signals


def _explanation(*args: object, **kwargs: object) -> BuyingScoreExplanation:
    """Structural stand-in. `_support` and `_temporal` read a handful of
    attributes and hold no reference to the type itself, which is what makes
    them testable without seeding six upstream modules."""
    return _Explanation(*args, **kwargs)  # type: ignore[arg-type,return-value]


class TestSupportCountsEventsNotSignals:
    """**`contributing_events` is a count of distinct business events.**

    Counting signals instead would double-count an event cited by two of them,
    and *"how much is behind this?"* is one of the eleven questions a customer
    asks. The seeded scenario has one event per signal, so the two counts
    coincide there and the distinction is invisible.
    """

    def test_an_event_cited_by_two_signals_is_counted_once(self) -> None:
        shared = _event(providers=("coresignal",))
        explanation = _explanation(_Score(), (_Signal((shared,)), _Signal((shared,))))

        basis = _support(explanation, EvidenceState.CURRENT)

        assert basis.contributing_events == 1, "the same event was counted twice"

    def test_distinct_events_are_counted_separately(self) -> None:
        """The positive control. Without it, a mutation returning a constant 1
        would satisfy the test above."""
        explanation = _explanation(
            _Score(),
            (
                _Signal((_event(providers=("coresignal",)),)),
                _Signal((_event(providers=("apollo",)),)),
            ),
        )

        assert _support(explanation, EvidenceState.CURRENT).contributing_events == 2


class TestCorroborationCountsDistinctProviders:
    """One provider repeating itself across ten events is **one source**."""

    def test_one_provider_across_many_events_is_not_corroboration(self) -> None:
        explanation = _explanation(
            _Score(),
            (
                _Signal((_event(providers=("coresignal",)),)),
                _Signal((_event(providers=("coresignal",)),)),
            ),
        )

        basis = _support(explanation, EvidenceState.CURRENT)

        assert basis.corroborating_providers == frozenset({"coresignal"})
        assert not basis.is_corroborated, "one provider repeating itself is one source"

    def test_two_independent_providers_corroborate(self) -> None:
        explanation = _explanation(
            _Score(), (_Signal((_event(providers=("coresignal", "apollo")),)),)
        )

        assert _support(explanation, EvidenceState.CURRENT).is_corroborated


class TestContentionSurvivesTheTranslation:
    """**Contradiction is preserved through six stages precisely so it is not
    netted away here.** The seeded scenario is not contested, so the adapter
    could have dropped the flag entirely and the integration suite would have
    stayed green while every customer was told nothing disagreed."""

    def test_contested_is_carried_with_its_dissenting_count(self) -> None:
        dissent = (uuid4(), uuid4())
        explanation = _explanation(
            _Score(contested=True, dissenting=dissent),
            (_Signal((_event(providers=("coresignal",)),)),),
        )

        basis = _support(explanation, EvidenceState.CURRENT)

        assert basis.contested is True
        assert basis.dissenting_signals == len(dissent)

    def test_contention_does_not_lower_the_level(self) -> None:
        """Ratified 2026-07-29: *the Buying Score Engine prioritizes; it never
        resolves*. A fought-over account warrants more attention, not average
        attention."""
        signals = (_Signal((_event(providers=("coresignal", "apollo")),)),)
        calm = _support(_explanation(_Score(), signals), EvidenceState.CURRENT)
        fought = _support(
            _explanation(_Score(contested=True, dissenting=(uuid4(),)), signals),
            EvidenceState.CURRENT,
        )

        assert fought.level is calm.level

    def test_an_uncontested_score_names_no_dissent(self) -> None:
        explanation = _explanation(_Score(), (_Signal((_event(providers=("coresignal",)),)),))
        basis = _support(explanation, EvidenceState.CURRENT)

        assert basis.contested is False
        assert basis.dissenting_signals == 0


class TestEvidenceStateIsReusedNeverRederived:
    @pytest.mark.parametrize("state", list(EvidenceState))
    def test_the_opportunity_engines_derivation_is_carried_through(
        self, state: EvidenceState
    ) -> None:
        """A second definition of *"is this still current"* would disagree with
        the first within a year."""
        explanation = _explanation(_Score(), (_Signal((_event(providers=("coresignal",)),)),))

        assert _support(explanation, state).evidence_state is state
        assert _temporal(explanation, state).evidence_state is state


class TestTemporalCopiesTheReadingFieldForField:
    def test_every_temporal_field_comes_from_the_score(self) -> None:
        """Nothing here is recomputed. `ScoreTrigger` exists precisely because
        a number that moved for an unexplainable reason is a number nobody
        trusts."""
        score = _Score()
        temporal = _temporal(_explanation(score, ()), EvidenceState.CURRENT)

        assert temporal.trigger is score.trigger
        assert temporal.basis_at == score.basis_at
        assert temporal.computed_at == score.computed_at
        assert temporal.delta == score.delta
        assert temporal.valid_until == score.valid_until
        assert temporal.supersedes == score.supersedes


class _Definition:
    def __init__(self, limitations: tuple[str, ...], validation: tuple[str, ...]) -> None:
        self.limitations = limitations
        self.suggested_validation = validation


class _Catalog:
    """A catalog where two types **share** a caveat.

    The shipped catalog's types happen to share none, so the deduplication in
    `_catalog_text` is unreachable through the seeded scenario — its removal
    survived mutation testing. The property is real and will matter as the
    catalog grows, so it is asserted against a catalog that can express it
    rather than deleted for being currently unobservable.
    """

    version = 7

    def __init__(self) -> None:
        self._definitions = {
            "hiring": _Definition(
                ("Hiring is not a budget decision.", "Shared caveat."),
                ("Check the careers page.", "Shared check."),
            ),
            "funding": _Definition(
                ("Shared caveat.", "Funding is not intent."),
                ("Shared check.", "Check the filing."),
            ),
        }

    def definition(self, key: str) -> _Definition:
        return self._definitions[key]


class _Signals:
    def catalog(self) -> _Catalog:
        return _Catalog()


def _context_source() -> PipelineReasoningContext:
    return PipelineReasoningContext(
        opportunities=None,  # type: ignore[arg-type]
        signals=_Signals(),  # type: ignore[arg-type]
        evidence=None,  # type: ignore[arg-type]
    )


class TestCatalogTextIsComposedForContributingTypesOnly:
    def test_a_caveat_shared_by_two_types_is_stated_once(self) -> None:
        """A customer reading the same limitation twice learns nothing the
        second time and trusts the package slightly less."""
        limitations, validation = _context_source()._catalog_text(
            ["hiring", "funding"]  # type: ignore[list-item]
        )

        assert limitations.count("Shared caveat.") == 1
        assert validation.count("Shared check.") == 1

    def test_the_catalogs_declared_order_is_preserved(self) -> None:
        """The reviewed artifact's order, not a set's iteration order — which
        would be a hidden input, and would reorder between runs."""
        limitations, _ = _context_source()._catalog_text(
            ["hiring", "funding"]  # type: ignore[list-item]
        )

        assert limitations == (
            "Hiring is not a budget decision.",
            "Shared caveat.",
            "Funding is not intent.",
        )

    def test_only_the_types_supplied_contribute(self) -> None:
        """A package listing the limitations of a signal that contributed
        nothing would be describing someone else's account."""
        limitations, _ = _context_source()._catalog_text(["hiring"])  # type: ignore[list-item]

        assert "Funding is not intent." not in limitations
