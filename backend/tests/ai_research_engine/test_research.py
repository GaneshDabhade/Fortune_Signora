"""The AI Research Engine's domain types, and the contract rules they carry.

Every test here names the Knowledge Contract rule it protects, because these
types exist to make those rules hold — a test that only checked field
assignment would pass while the rule it was written for had been deleted.

No database, no model, no infrastructure. These are pure domain assertions.
"""

from __future__ import annotations

from dataclasses import fields
from datetime import UTC, datetime
from decimal import Decimal
from uuid import UUID, uuid4

import pytest
from modules.ai_platform.public import AIVendor, EvidenceRef, GroundedStatement
from modules.ai_research_engine.domain.knowledge import EpistemicOrigin
from modules.ai_research_engine.domain.research import (
    FINDING_KIND,
    RESEARCH_FINDING_NAMESPACE,
    ResearchError,
    ResearchFinding,
    ResearchSynthesis,
    ResearchTask,
    research_finding_id,
)

WORKSPACE = UUID("11111111-1111-4111-8111-111111111111")
SUBJECT = EvidenceRef(kind="entity", id=UUID("22222222-2222-4222-8222-222222222222"))
CITED = (
    EvidenceRef(kind="claim", id=UUID("33333333-3333-4333-8333-333333333333")),
    EvidenceRef(kind="claim", id=UUID("44444444-4444-4444-8444-444444444444")),
)
NOW = datetime(2026, 7, 31, 12, 0, tzinfo=UTC)


def _finding(**overrides: object) -> ResearchFinding:
    fields: dict[str, object] = {
        "id": uuid4(),
        "workspace_id": WORKSPACE,
        "task_id": uuid4(),
        "subject": SUBJECT,
        "derivation": "headcount_disagreement",
        "derivation_version": 1,
        "attributes": (("providers", 2), ("spread", Decimal("0.4"))),
        "cited": CITED,
        "created_at": NOW,
    }
    fields.update(overrides)
    return ResearchFinding(**fields)  # type: ignore[arg-type]


def _synthesis(**overrides: object) -> ResearchSynthesis:
    fields: dict[str, object] = {
        "id": uuid4(),
        "workspace_id": WORKSPACE,
        "task_id": uuid4(),
        "statements": (GroundedStatement(text="Two providers disagree.", evidence=("x:1",)),),
        "finding_ids": (uuid4(),),
        "prompt_name": "research_synthesis",
        "prompt_version": 1,
        "prompt_fingerprint": "f" * 64,
        "model": "granite3.3:2b",
        "vendor": AIVendor.OLLAMA,
        "evidence_digest": "d" * 64,
        "inference_id": uuid4(),
        "created_at": NOW,
    }
    fields.update(overrides)
    return ResearchSynthesis(**fields)  # type: ignore[arg-type]


class TestEpistemicOrigin:
    """Rules 4 and 5, and the 2026-07-31 Internal Research ruling."""

    def test_only_the_two_origins_this_module_can_produce_exist(self) -> None:
        """The ruling made mechanical. ATTESTED is not withheld by policy — it
        is **unconstructable**, so external findings cannot arrive by editing a
        field. Adding external retrieval must add the member, in a diff."""
        assert {origin.value for origin in EpistemicOrigin} == {"derived", "inferred"}

    @pytest.mark.parametrize(
        ("cls", "expected"),
        [
            (ResearchFinding, EpistemicOrigin.DERIVED),
            (ResearchSynthesis, EpistemicOrigin.INFERRED),
        ],
    )
    def test_origin_cannot_vary_between_instances(
        self, cls: type, expected: EpistemicOrigin
    ) -> None:
        """Rule 5 — origin is immutable for the object's lifetime. Declared on
        the type rather than per instance, so two objects of one kind can never
        disagree about how a reader must check them, and no caller can supply
        one."""
        assert cls.origin is expected  # type: ignore[attr-defined]
        assert "origin" not in {field.name for field in fields(cls)}


class TestCitabilityIsAddressability:
    """Rule 12 — INFERRED knowledge is never citable, by any consumer."""

    def test_a_finding_addresses_itself(self) -> None:
        finding = _finding()
        assert finding.ref == EvidenceRef(kind=FINDING_KIND, id=finding.id)
        assert finding.ref.token == f"{FINDING_KIND}:{finding.id}"

    def test_a_synthesis_has_no_address_at_all(self) -> None:
        """**This is the enforcement, not a convention.** A synthesis is not
        refused a citation — it has nothing to be cited by, so no consumer can
        make one model's output another model's evidence even by trying."""
        synthesis = _synthesis()
        assert not hasattr(synthesis, "ref")
        assert not hasattr(synthesis, "token")
        assert not any(
            isinstance(getattr(synthesis, field), EvidenceRef)
            for field in synthesis.__dataclass_fields__
        )


class TestIdentityConstantsArePinned:
    """**Both constants are pinned to their literal value, deliberately.**

    Found by mutation: every other identity test computes both sides with the
    same constant, so changing it moves every id at once and nothing fails. The
    two values below are wire format — one keys every finding ever derived, the
    other prefixes every citation that addresses one — and a silent change to
    either re-identifies history while every test stays green.

    **The same mutation survives in the Signal Engine and three other modules**,
    whose namespaces are pinned by a docstring saying *"never change it"* and by
    nothing else. Reported rather than fixed here: repairing four modules is not
    this task's scope, and the decision belongs to whoever owns them.
    """

    def test_the_finding_namespace_has_not_moved(self) -> None:
        assert RESEARCH_FINDING_NAMESPACE == UUID("3a02938f-4da2-4c51-8040-894b7520cee1"), (
            "The namespace changed. Every finding in every workspace now has a different "
            "identity, and the next research run inserts a duplicate of the entire table."
        )

    def test_the_citation_kind_has_not_moved(self) -> None:
        assert FINDING_KIND == "research_finding", (
            "The citation kind changed. Every stored citation addressing a finding now names "
            "a kind nothing resolves, so grounding reports UNRESOLVED_CITATION on packages "
            "that were valid when they were written."
        )


class TestFindingIdentity:
    """Rule 1 — content-derived, because a finding is reproducible."""

    def test_the_same_derivation_over_the_same_rows_is_the_same_finding(self) -> None:
        """Re-running research must insert nothing. This is what lets research
        be replayed and regression-tested without duplicating its history."""
        first = research_finding_id(
            workspace_id=WORKSPACE,
            subject=SUBJECT,
            derivation="headcount_disagreement",
            derivation_version=1,
            cited=CITED,
        )
        second = research_finding_id(
            workspace_id=WORKSPACE,
            subject=SUBJECT,
            derivation="headcount_disagreement",
            derivation_version=1,
            cited=CITED,
        )
        assert first == second

    def test_citation_order_does_not_change_identity(self) -> None:
        """Insertion order is a hidden input. Two callers assembling the same
        rows in different order must produce one finding."""
        forward = research_finding_id(
            workspace_id=WORKSPACE,
            subject=SUBJECT,
            derivation="d",
            derivation_version=1,
            cited=CITED,
        )
        reversed_ = research_finding_id(
            workspace_id=WORKSPACE,
            subject=SUBJECT,
            derivation="d",
            derivation_version=1,
            cited=tuple(reversed(CITED)),
        )
        assert forward == reversed_

    @pytest.mark.parametrize(
        ("field", "value"),
        [
            ("workspace_id", uuid4()),
            ("subject", EvidenceRef(kind="entity", id=uuid4())),
            ("derivation", "different_comparison"),
            ("derivation_version", 2),
            ("cited", CITED[:1]),
        ],
    )
    def test_every_input_independently_changes_identity(self, field: str, value: object) -> None:
        """Each field is load-bearing. A field that could change without
        changing identity would let new content collide with an old id and
        insert nothing."""
        base: dict[str, object] = {
            "workspace_id": WORKSPACE,
            "subject": SUBJECT,
            "derivation": "d",
            "derivation_version": 1,
            "cited": CITED,
        }
        changed = {**base, field: value}
        assert research_finding_id(**base) != research_finding_id(**changed)  # type: ignore[arg-type]

    def test_the_derivation_version_is_part_of_identity(self) -> None:
        """**The deliberate contrast with `Signal`**, which excludes its profile
        version. A signal's type *is* its claim, so a profile change that keeps
        the type keeps the signal. A derivation change can compute a different
        value from identical rows, so a finding that ignored it would overwrite
        nothing and silently keep the old answer."""
        one = research_finding_id(
            workspace_id=WORKSPACE, subject=SUBJECT, derivation="d", derivation_version=1, cited=CITED
        )
        two = research_finding_id(
            workspace_id=WORKSPACE, subject=SUBJECT, derivation="d", derivation_version=2, cited=CITED
        )
        assert one != two

    @pytest.mark.parametrize(
        "hostile",
        [
            "d|claim:33333333-3333-4333-8333-333333333333",
            "d@1|claim:33333333-3333-4333-8333-333333333333",
            "|",
            "@1",
            "d@1",
        ],
    )
    def test_a_derivation_containing_the_separator_still_cannot_collide(self, hostile: str) -> None:
        """**Why the removed guard was decorative.** A version renders as digits
        and every citation token ends in a UUID, so the boundary between the
        derivation and the citation list falls in exactly one place. These are
        the strings a guard would have rejected; none of them can be confused
        with an ordinary finding."""
        hostile_id = research_finding_id(
            workspace_id=WORKSPACE,
            subject=SUBJECT,
            derivation=hostile,
            derivation_version=1,
            cited=CITED,
        )
        ordinary_id = research_finding_id(
            workspace_id=WORKSPACE,
            subject=SUBJECT,
            derivation="d",
            derivation_version=1,
            cited=CITED,
        )
        assert hostile_id != ordinary_id


class TestFindingRefusesWhatCannotBeDefended:
    def test_a_finding_that_cites_nothing_is_refused(self) -> None:
        with pytest.raises(ResearchError, match="cites nothing"):
            _finding(cited=())

    def test_a_finding_that_states_nothing_is_refused(self) -> None:
        with pytest.raises(ResearchError, match="states nothing"):
            _finding(attributes=())

    def test_an_unnamed_derivation_is_refused(self) -> None:
        with pytest.raises(ResearchError, match="names no derivation"):
            _finding(derivation="   ")

    def test_a_zero_derivation_version_is_refused(self) -> None:
        with pytest.raises(ResearchError, match="Versions start at 1"):
            _finding(derivation_version=0)

    def test_a_repeated_attribute_name_is_refused(self) -> None:
        with pytest.raises(ResearchError, match="repeats an attribute name"):
            _finding(attributes=(("providers", 2), ("providers", 3)))

    def test_attributes_are_held_in_canonical_order(self) -> None:
        """Two callers building the same finding must produce the same bytes,
        so a stored finding and a recomputed one compare equal."""
        finding = _finding(attributes=(("z", 1), ("a", 2)))
        assert finding.attributes == (("a", 2), ("z", 1))

    def test_a_finding_cannot_be_edited(self) -> None:
        """Immutability is the default for anything that records a fact."""
        finding = _finding()
        with pytest.raises(AttributeError):
            finding.derivation = "something_else"  # type: ignore[misc]


class TestSynthesisRefusesWhatCannotBeDefended:
    def test_a_synthesis_saying_nothing_is_refused(self) -> None:
        with pytest.raises(ResearchError, match="says nothing"):
            _synthesis(statements=())

    def test_a_synthesis_resting_on_no_findings_is_refused(self) -> None:
        with pytest.raises(ResearchError, match="rests on no findings"):
            _synthesis(finding_ids=())

    def test_a_finding_counted_twice_is_refused(self) -> None:
        """Rule 21 in miniature — one source appearing to agree with itself."""
        repeated = uuid4()
        with pytest.raises(ResearchError, match="names a finding twice"):
            _synthesis(finding_ids=(repeated, repeated))

    def test_a_synthesis_cannot_be_edited(self) -> None:
        synthesis = _synthesis()
        with pytest.raises(AttributeError):
            synthesis.model = "something_else"  # type: ignore[misc]

    def test_it_references_its_findings_rather_than_absorbing_them(self) -> None:
        """Rule 7 — a composite preserves the origin of its parts. Holding ids
        rather than findings is what keeps each finding separately addressable,
        and therefore separately checkable, beneath an INFERRED whole."""
        synthesis = _synthesis()
        assert all(isinstance(finding_id, UUID) for finding_id in synthesis.finding_ids)
        assert not any(
            isinstance(getattr(synthesis, field), ResearchFinding)
            for field in synthesis.__dataclass_fields__
        )


class TestResearchTask:
    def test_a_task_carries_no_epistemic_origin(self) -> None:
        """It asserts nothing about a customer's world — it records that Signora
        looked. Classifying machinery would make the ladder meaningless."""
        assert not hasattr(ResearchTask, "origin")

    def test_a_task_cannot_be_edited(self) -> None:
        task = ResearchTask(
            id=uuid4(),
            workspace_id=WORKSPACE,
            correlation_id=uuid4(),
            subject=SUBJECT,
            opportunity_id=uuid4(),
            requested_at=NOW,
        )
        with pytest.raises(AttributeError):
            task.workspace_id = uuid4()  # type: ignore[misc]
