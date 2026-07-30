"""The closed evidence set: closure, isolation, typing, provenance, determinism.

The six properties grounding is built on. Each is tested for what it
*refuses*, not only for what it permits — a closed universe that can be
persuaded to open is not a closed universe.
"""

from __future__ import annotations

from dataclasses import FrozenInstanceError
from datetime import UTC, date, datetime
from decimal import Decimal
from uuid import UUID, uuid4

import pytest

from modules.ai_platform.domain.evidence import (
    EvidenceError,
    EvidenceFact,
    EvidenceRef,
    EvidenceSet,
    EvidenceSetBuilder,
    WorkspaceMismatchError,
)

ASSEMBLED = datetime(2026, 7, 30, 12, 0, tzinfo=UTC)


def a_fact(
    workspace_id: UUID,
    *,
    kind: str = "business_event",
    id: UUID | None = None,
    summary: str = "Raised 24M USD in a Series B round",
    **attributes: object,
) -> EvidenceFact:
    return EvidenceFact(
        ref=EvidenceRef(kind=kind, id=id or uuid4()),
        workspace_id=workspace_id,
        summary=summary,
        attributes=tuple(attributes.items()),  # type: ignore[arg-type]
    )


class TestTheUniverseIsClosed:
    def test_a_built_set_cannot_be_mutated(self) -> None:
        workspace = uuid4()
        evidence = EvidenceSet(
            workspace_id=workspace, facts=(a_fact(workspace),), assembled_at=ASSEMBLED
        )
        with pytest.raises(FrozenInstanceError):
            evidence.facts = ()  # type: ignore[misc]

    def test_adding_to_the_builder_afterwards_does_not_change_the_built_set(self) -> None:
        """The set is a universe, not a view onto a mutable collection."""
        workspace = uuid4()
        builder = EvidenceSetBuilder(workspace)
        builder.add(kind="signal", id=uuid4(), summary="Hiring surge may indicate expansion")
        evidence = builder.build(assembled_at=ASSEMBLED)
        before = evidence.digest

        builder.add(kind="signal", id=uuid4(), summary="A second hypothesis")

        assert len(evidence) == 1
        assert evidence.digest == before

    def test_an_empty_set_is_refused(self) -> None:
        """A model given nothing to reference can only produce something
        ungrounded. Failing here names the real cause."""
        with pytest.raises(EvidenceError, match="no facts"):
            EvidenceSet(workspace_id=uuid4(), facts=(), assembled_at=ASSEMBLED)

    def test_a_repeated_reference_is_refused(self) -> None:
        workspace = uuid4()
        ref_id = uuid4()
        with pytest.raises(EvidenceError, match="repeats a reference"):
            EvidenceSet(
                workspace_id=workspace,
                facts=(a_fact(workspace, id=ref_id), a_fact(workspace, id=ref_id)),
                assembled_at=ASSEMBLED,
            )


class TestWorkspaceIsolationIsAConstructionProperty:
    """Not a validation step somebody might forget to call."""

    def test_the_builder_refuses_a_fact_from_another_workspace(self) -> None:
        builder = EvidenceSetBuilder(uuid4())
        with pytest.raises(WorkspaceMismatchError, match="never combined across workspaces"):
            builder.include(a_fact(uuid4()))

    def test_the_builder_stamps_every_fact_it_creates(self) -> None:
        """Via `add`, a foreign workspace is not merely refused — there is
        no argument through which one could be supplied."""
        workspace = uuid4()
        builder = EvidenceSetBuilder(workspace)
        builder.add(kind="claim", id=uuid4(), summary="Apollo reports headcount 240")
        evidence = builder.build(assembled_at=ASSEMBLED)
        assert all(f.workspace_id == workspace for f in evidence)

    def test_the_set_re_verifies_even_though_the_builder_already_refused(self) -> None:
        """Defence in depth, the same discipline as RLS plus an explicit
        workspace filter: the authoritative control is not the only one."""
        workspace = uuid4()
        with pytest.raises(WorkspaceMismatchError, match="cross-tenant leak"):
            EvidenceSet(
                workspace_id=workspace,
                facts=(a_fact(workspace), a_fact(uuid4())),
                assembled_at=ASSEMBLED,
            )

    def test_the_mismatch_names_the_offending_fact(self) -> None:
        workspace = uuid4()
        intruder = a_fact(uuid4(), kind="signal")
        with pytest.raises(WorkspaceMismatchError) as caught:
            EvidenceSet(
                workspace_id=workspace,
                facts=(a_fact(workspace), intruder),
                assembled_at=ASSEMBLED,
            )
        assert intruder.ref.token in str(caught.value)


class TestEvidenceStaysTyped:
    def test_typed_values_survive_construction(self) -> None:
        """Not stringified on the way in. The grounding quantity check reads
        numbers as numbers, so it is arithmetic rather than a regex."""
        workspace = uuid4()
        builder = EvidenceSetBuilder(workspace)
        builder.add(
            kind="business_event",
            id=uuid4(),
            summary="Raised 24M USD in a Series B round",
            attributes={
                "amount": Decimal("24000000"),
                "headcount": 240,
                "confirmed": True,
                "occurred_on": date(2026, 6, 1),
            },
        )
        attributes = dict(builder.build(assembled_at=ASSEMBLED).facts[0].attributes)

        assert attributes["amount"] == Decimal("24000000")
        assert attributes["headcount"] == 240
        assert attributes["confirmed"] is True
        assert attributes["occurred_on"] == date(2026, 6, 1)

    def test_a_repeated_attribute_name_is_refused(self) -> None:
        workspace = uuid4()
        with pytest.raises(EvidenceError, match="repeats an attribute"):
            EvidenceFact(
                ref=EvidenceRef(kind="signal", id=uuid4()),
                workspace_id=workspace,
                summary="ambiguous",
                attributes=(("headcount", 240), ("headcount", 250)),
            )

    def test_a_fact_without_a_summary_is_refused(self) -> None:
        with pytest.raises(EvidenceError, match="no summary"):
            EvidenceFact(
                ref=EvidenceRef(kind="signal", id=uuid4()),
                workspace_id=uuid4(),
                summary="   ",
            )


class TestProvenanceResolves:
    def test_a_ref_round_trips_through_its_citation_token(self) -> None:
        ref = EvidenceRef(kind="business_event", id=uuid4())
        assert EvidenceRef.parse(ref.token) == ref

    def test_a_fact_resolves_from_its_ref(self) -> None:
        workspace = uuid4()
        fact = a_fact(workspace)
        evidence = EvidenceSet(workspace_id=workspace, facts=(fact,), assembled_at=ASSEMBLED)
        assert evidence.resolve(fact.ref) == fact
        assert evidence.contains(fact.ref)

    def test_a_ref_outside_the_universe_resolves_to_nothing(self) -> None:
        """The definition of an ungrounded statement, and what T115 is
        built on."""
        workspace = uuid4()
        evidence = EvidenceSet(
            workspace_id=workspace, facts=(a_fact(workspace),), assembled_at=ASSEMBLED
        )
        outside = EvidenceRef(kind="business_event", id=uuid4())
        assert evidence.resolve(outside) is None
        assert not evidence.contains(outside)

    def test_two_kinds_sharing_an_identifier_do_not_collide(self) -> None:
        workspace = uuid4()
        shared = uuid4()
        evidence = EvidenceSet(
            workspace_id=workspace,
            facts=(
                a_fact(workspace, kind="signal", id=shared, summary="a hypothesis"),
                a_fact(workspace, kind="business_event", id=shared, summary="an event"),
            ),
            assembled_at=ASSEMBLED,
        )
        assert evidence.resolve(EvidenceRef("signal", shared)) is not None
        assert len(evidence) == 2

    @pytest.mark.parametrize("token", ["", "no-separator", "signal:not-a-uuid", ":" + str(uuid4())])
    def test_an_unparseable_citation_raises_rather_than_returning_none(self, token: str) -> None:
        """An absence and a malformed citation are different failures, and
        collapsing them would report a hallucinated reference as a missing
        fact."""
        with pytest.raises(EvidenceError):
            EvidenceRef.parse(token)

    def test_a_kind_containing_the_separator_is_refused(self) -> None:
        with pytest.raises(EvidenceError, match="token separator"):
            EvidenceRef(kind="business:event", id=uuid4())

    def test_a_kindless_ref_is_refused(self) -> None:
        with pytest.raises(EvidenceError, match="no kind"):
            EvidenceRef(kind=" ", id=uuid4())


class TestConstructionIsDeterministic:
    """Replay, prompt regression, and future Business Capability
    Verification all depend on this."""

    def test_assembly_order_does_not_change_the_digest(self) -> None:
        workspace = uuid4()
        first, second = uuid4(), uuid4()

        forwards = EvidenceSetBuilder(workspace)
        forwards.add(kind="signal", id=first, summary="one")
        forwards.add(kind="signal", id=second, summary="two")

        backwards = EvidenceSetBuilder(workspace)
        backwards.add(kind="signal", id=second, summary="two")
        backwards.add(kind="signal", id=first, summary="one")

        assert (
            forwards.build(assembled_at=ASSEMBLED).digest
            == backwards.build(assembled_at=ASSEMBLED).digest
        )

    def test_facts_are_held_in_canonical_order_regardless_of_insertion(self) -> None:
        """Order is not information about evidence. Letting insertion order
        survive would make the rendered prompt depend on how the caller
        looped — a hidden input, which statelessness forbids."""
        workspace = uuid4()
        builder = EvidenceSetBuilder(workspace)
        builder.add(kind="signal", id=uuid4(), summary="s")
        builder.add(kind="business_event", id=uuid4(), summary="e")
        builder.add(kind="claim", id=uuid4(), summary="c")

        kinds = [f.ref.kind for f in builder.build(assembled_at=ASSEMBLED)]
        assert kinds == sorted(kinds)

    def test_attribute_order_does_not_change_the_digest(self) -> None:
        workspace = uuid4()
        shared = uuid4()
        one = EvidenceSet(
            workspace_id=workspace,
            facts=(a_fact(workspace, id=shared, headcount=240, amount=1),),
            assembled_at=ASSEMBLED,
        )
        other = EvidenceSet(
            workspace_id=workspace,
            facts=(a_fact(workspace, id=shared, amount=1, headcount=240),),
            assembled_at=ASSEMBLED,
        )
        assert one.digest == other.digest

    def test_assembled_at_does_not_change_the_digest(self) -> None:
        """It records when evidence was gathered, not what it contains.
        Including it would give identical evidence a new identity on every
        assembly, and replay comparison would never match."""
        workspace = uuid4()
        shared = uuid4()
        early = EvidenceSet(
            workspace_id=workspace, facts=(a_fact(workspace, id=shared),), assembled_at=ASSEMBLED
        )
        late = EvidenceSet(
            workspace_id=workspace,
            facts=(a_fact(workspace, id=shared),),
            assembled_at=datetime(2027, 1, 1, tzinfo=UTC),
        )
        assert early.digest == late.digest

    def test_different_evidence_produces_a_different_digest(self) -> None:
        workspace = uuid4()
        one = EvidenceSet(
            workspace_id=workspace,
            facts=(a_fact(workspace, id=UUID(int=1), summary="headcount 240"),),
            assembled_at=ASSEMBLED,
        )
        other = EvidenceSet(
            workspace_id=workspace,
            facts=(a_fact(workspace, id=UUID(int=1), summary="headcount 250"),),
            assembled_at=ASSEMBLED,
        )
        assert one.digest != other.digest

    def test_the_same_facts_in_a_different_workspace_digest_differently(self) -> None:
        shared = uuid4()
        one, other = uuid4(), uuid4()
        assert (
            EvidenceSet(
                workspace_id=one, facts=(a_fact(one, id=shared),), assembled_at=ASSEMBLED
            ).digest
            != EvidenceSet(
                workspace_id=other, facts=(a_fact(other, id=shared),), assembled_at=ASSEMBLED
            ).digest
        )

    @pytest.mark.parametrize(
        ("left", "right"),
        [
            pytest.param(True, 1, id="bool-vs-int (bool subclasses int)"),
            pytest.param(True, "true", id="bool-vs-its-own-text"),
            pytest.param(1, "1", id="int-vs-its-own-text"),
            pytest.param(Decimal("1"), 1, id="decimal-vs-int"),
            pytest.param(Decimal("1.0"), "1.0", id="decimal-vs-its-own-text"),
            pytest.param(
                datetime(2026, 6, 1, tzinfo=UTC),
                "2026-06-01T00:00:00+00:00",
                id="datetime-vs-its-own-text",
            ),
            pytest.param(
                datetime(2026, 6, 1, tzinfo=UTC),
                date(2026, 6, 1),
                id="datetime-vs-date (datetime subclasses date)",
            ),
            pytest.param(date(2026, 6, 1), "2026-06-01", id="date-vs-its-own-text"),
        ],
    )
    def test_values_of_different_types_never_digest_alike(
        self, left: object, right: object
    ) -> None:
        """The canonical form is type-tagged, and the tag is load-bearing.

        Untagged, every one of these pairs collapses onto identical text and
        two different facts become indistinguishable — so a digest could no
        longer answer *did these two inferences see the same evidence?*

        Two pairs here are subclass relationships — ``bool``/``int`` and
        ``datetime``/``date``. They are distinguished by their own text as
        well as by their tag; the tag is what the *next* test pins.
        """
        workspace = uuid4()
        shared = uuid4()
        digests = {
            EvidenceSet(
                workspace_id=workspace,
                facts=(a_fact(workspace, id=shared, value=value),),
                assembled_at=ASSEMBLED,
            ).digest
            for value in (left, right)
        }
        assert len(digests) == 2

    def test_the_digest_is_stable_across_runs(self) -> None:
        """Not Python's hash(), which is salted per process. A digest that
        changes between runs would make every recorded inference
        unreproducible."""
        workspace = UUID(int=7)
        evidence = EvidenceSet(
            workspace_id=workspace,
            facts=(
                EvidenceFact(
                    ref=EvidenceRef(kind="signal", id=UUID(int=1)),
                    workspace_id=workspace,
                    summary="Hiring surge may indicate expansion",
                    attributes=(("headcount", 240),),
                ),
            ),
            assembled_at=ASSEMBLED,
        )
        # Pinned from the implementation and verified identical across three
        # processes with differing PYTHONHASHSEED. If this value changes, the
        # canonical form changed — which invalidates every recorded
        # evidence_digest, so it is a migration, not a refactor.
        assert evidence.digest == (
            "b3bcc3f23ca6791c94827469fa8e24c3d08c735c920f4d8d9a7e327081c98744"
        )


class TestEvidenceSaysNothingAboutLanguage:
    def test_no_rendering_lives_in_the_evidence_domain(self) -> None:
        """Evidence is truth; prompts are language. A fact that knows how it
        will be phrased makes a wording change a change to the evidence
        model."""
        for owner in (EvidenceSet, EvidenceFact, EvidenceRef):
            surface = {name for name in dir(owner) if not name.startswith("_")}
            offenders = {
                name
                for name in surface
                if any(word in name for word in ("render", "prompt", "template", "text", "format"))
            }
            assert not offenders, f"{owner.__name__} has grown a rendering concern: {offenders}"


class TestTheCanonicalFormLabelsEveryType:
    """The tag each type receives, pinned directly.

    Cross-type *collisions* are covered above. This covers the weaker but
    real property that a value is labelled as what it is: reversing a
    subclass check would tag a bool as an integer, which collides with
    nothing and is still wrong, because a canonical form nobody can read
    back is one nobody can debug.
    """

    @pytest.mark.parametrize(
        ("value", "expected"),
        [
            pytest.param(True, "value=b:true", id="bool-before-int"),
            pytest.param(False, "value=b:false", id="bool-false"),
            pytest.param(240, "value=i:240", id="int"),
            pytest.param(Decimal("24000000"), "value=n:24000000", id="decimal"),
            pytest.param(
                datetime(2026, 6, 1, tzinfo=UTC),
                "value=t:2026-06-01T00:00:00+00:00",
                id="datetime-before-date",
            ),
            pytest.param(date(2026, 6, 1), "value=d:2026-06-01", id="date"),
            pytest.param("Series B", "value=s:Series B", id="str"),
        ],
    )
    def test_a_value_is_tagged_as_what_it_is(self, value: object, expected: str) -> None:
        fact = a_fact(uuid4(), value=value)
        assert expected in fact.canonical_form()
