"""The Commercial Context Protocol — what a model is shown, and what that admits.

**The protocol is an experimental input, so it is pinned like one.** A change to
what a model reads without a version bump makes every recorded evaluation
describe text that is no longer produced — the hidden input `rendering.py` exists
because the repository shipped once already.
"""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID, uuid4

import pytest

from modules.sales_engagement.domain.context import (
    COMMERCIAL_CONTEXT_PROTOCOL_VERSION,
    CommercialContext,
)
from modules.sales_engagement.domain.fit import FitDimension, FitReason, ProductFit, ProductRef
from modules.sales_engagement.domain.synthesis import (
    Passage,
    SynthesisRefusedError,
    SynthesisSource,
    validate,
)
from modules.sales_engagement.public import CommitteeRoleRef, Evidence, Strength, reason

NOW = datetime(2026, 8, 3, tzinfo=UTC)
ACCOUNT = UUID("22222222-2222-4222-8222-222222222222")
EVENT = UUID("5e000000-0000-4000-8000-000000000001")
CHAMPION = CommitteeRoleRef(title="VP Engineering", part="champion")
BUYER = CommitteeRoleRef(title="CFO", part="economic_buyer")

APPOINTMENT = Evidence(
    event_id=EVENT,
    type_key="leadership_appointed",
    summary="Appointed a new VP of Engineering",
    occurred_at=datetime(2026, 7, 14, tzinfo=UTC),
    corroborating_providers=2,
    names_title="VP of Engineering",
)


def context(
    *, fits: tuple[ProductFit, ...] = (), product: ProductRef | None = None
) -> CommercialContext:
    return CommercialContext(
        source=SynthesisSource(
            reasoning=reason(
                account_id=ACCOUNT,
                committee=(CHAMPION, BUYER),
                evidence=(APPOINTMENT,),
                now=NOW,
            ),
            fits=fits,
            product=product,
        )
    )


class TestTheProtocolShowsWhatTheGraphDecided:
    def test_it_shows_the_recommendation_first(self) -> None:
        """Everything below the recommendation is *why*, and a strategist reads
        the answer before the argument."""
        rendered = context().render()

        assert rendered.startswith("── recommendation ──")

    def test_every_citable_thing_appears_as_a_copyable_cite_line(self) -> None:
        """**Protocol 2's lesson, borrowed intact.** Every observed grounding
        failure across three prompts and four models was an error in how much to
        strip; a form requiring no transformation has no mechanism for one."""
        rendered = context().render()

        for token in ("recommendation", "VP Engineering", str(EVENT)):
            assert f"cite: {token}" in rendered

    def test_an_unranked_role_carries_its_reason(self) -> None:
        """*"Nothing names your CFO"* is the useful half of an empty result, and
        a protocol that dropped unranked roles would hide the sentence this
        module exists to produce."""
        rendered = context().render()

        assert "title: CFO" in rendered
        assert "why not:" in rendered

    def test_a_section_with_nothing_to_say_is_absent(self) -> None:
        """A heading with nothing under it looks the same for every Target
        Account — the defect R1-06 named on the workflow line."""
        rendered = context().render()

        assert "product fit" not in rendered
        assert "likely product" not in rendered

    def test_the_context_ends_with_every_legal_citation(self) -> None:
        """**A model that has to infer the citable set will infer it wrongly.**
        Protocol 1 refused six of ten real cases on headings the model took for
        tokens; a complete list removes the guess rather than instructing
        against it."""
        rendered = context().render()
        listed = rendered.split("── citable ──\n")[1].strip().splitlines()

        assert {one.strip().casefold() for one in listed} == context().citable()

    def test_a_heading_cannot_be_mistaken_for_a_citation(self) -> None:
        """The observed failure, pinned. A heading is delimited and lower case,
        and no citable token takes that form."""
        rendered = context().render()

        for heading in ("recommendation", "buying committee roles"):
            assert f"── {heading} ──" in rendered
        assert "BUYING COMMITTEE ROLES" not in rendered

    def test_a_section_with_something_to_say_is_present(self) -> None:
        product = ProductRef(id=uuid4(), name="Revenue Cloud")
        rendered = context(
            product=product,
            fits=(
                ProductFit(
                    product=product,
                    strength=Strength.STRONG,
                    reasons=(FitReason(dimension=FitDimension.COMMITTEE_OVERLAP, detail="x"),),
                ),
            ),
        ).render()

        assert "── likely product ──" in rendered
        assert "── product fit ──" in rendered


class TestTheClosedSetIsComputedFromWhatWasShown:
    """**The property that makes this more than a formatter.**

    A renderer showing a model a figure the validator had never heard of would
    cause a *false refusal* — the model faithfully copies what it was given and
    is punished for it.
    """

    def test_a_date_the_protocol_showed_is_quotable(self) -> None:
        one = context()
        assert "2026" in one.numbers()
        assert "14" in one.numbers()

    def test_a_corroboration_count_the_protocol_showed_is_quotable(self) -> None:
        assert "2" in context().numbers()

    def test_a_figure_nothing_showed_is_not_quotable(self) -> None:
        assert "73" not in context().numbers()

    def test_digits_inside_a_citation_are_not_quotable(self) -> None:
        """**Otherwise the numeral check would be decorative.** A UUID contains
        digits, and folding them in would let *"3 providers"* pass because some
        event id happened to contain a `3`."""
        one = context()
        # The event id contains 5, e and zeros; `5e000000` must not license "5".
        assert "5" not in one.numbers()
        assert "000000" not in one.numbers()

    def test_a_draft_quoting_a_shown_date_is_accepted(self) -> None:
        """The end-to-end form of the property above, through the real fence."""
        result = validate(
            (Passage(text="The appointment landed in 2026.", cites=("VP Engineering",)),),
            context(),
            inference_id=uuid4(),
        )

        assert len(result.passages) == 1

    def test_a_draft_quoting_a_date_the_narrower_set_lacks_would_have_been_refused(self) -> None:
        """**The false refusal this layer removes, demonstrated.** The same
        passage fails against `SynthesisSource` alone and passes against the
        context — which is the whole reason `validate` takes a `ClosedSet`."""
        passage = (Passage(text="The appointment landed in 2026.", cites=("VP Engineering",)),)

        with pytest.raises(SynthesisRefusedError, match="2026"):
            validate(passage, context().source, inference_id=uuid4())

    def test_an_invented_figure_is_still_refused(self) -> None:
        """Widening the set must not disarm the check it widened."""
        with pytest.raises(SynthesisRefusedError, match="73"):
            validate(
                (Passage(text="Confidence is 73 percent.", cites=("recommendation",)),),
                context(),
                inference_id=uuid4(),
            )

    def test_an_invented_name_is_still_refused(self) -> None:
        with pytest.raises(SynthesisRefusedError, match="databricks"):
            validate(
                (Passage(text="They are leaving Databricks.", cites=("recommendation",)),),
                context(),
                inference_id=uuid4(),
            )

    def test_a_month_name_the_protocol_showed_is_quotable(self) -> None:
        """**Protocol 1 refused two real cases for a word it had itself
        withheld.** A model asked for prose writes *July*; showing only
        `2026-07-20` gave it the date and not the English name of the date."""
        assert "july" in context().vocabulary()

    def test_a_draft_naming_the_month_it_was_shown_is_accepted(self) -> None:
        result = validate(
            (Passage(text="The appointment landed in July.", cites=("VP Engineering",)),),
            context(),
            inference_id=uuid4(),
        )

        assert len(result.passages) == 1

    def test_the_possessive_of_a_shown_name_is_accepted(self) -> None:
        """**The possessive of a permitted name is not a new name.** Found by
        the second pass's evaluation: the graph offered *Revenue Cloud*, the
        model wrote *Revenue Cloud's*, and the fence read `cloud's` as an
        invented product. Same class as the month-name false refusal — a word
        the model was given, in a grammatical form the checker had not
        anticipated."""
        result = validate(
            (Passage(text="It is VP Engineering's decision.", cites=("VP Engineering",)),),
            context(),
            inference_id=uuid4(),
        )

        assert len(result.passages) == 1

    def test_the_possessive_of_an_invented_name_is_still_refused(self) -> None:
        """Reducing the possessive must not disarm the check it unblocked."""
        with pytest.raises(SynthesisRefusedError, match="databricks"):
            validate(
                (Passage(text="We saw Databricks's move.", cites=("recommendation",)),),
                context(),
                inference_id=uuid4(),
            )

    def test_a_month_the_protocol_did_not_show_is_still_refused(self) -> None:
        """Widening to the month shown must not admit every month."""
        with pytest.raises(SynthesisRefusedError, match="november"):
            validate(
                (Passage(text="This started in November.", cites=("VP Engineering",)),),
                context(),
                inference_id=uuid4(),
            )

    def test_what_may_be_cited_is_the_graphs_question_not_the_protocols(self) -> None:
        """This layer decides how a citation is *displayed*; the graph decides
        what exists to be cited. A second opinion here would be the two
        assemblies SE-09a exists to prevent."""
        one = context()

        assert one.citable() == one.source.citable()


class TestTheProtocolIsPinned:
    SPECIMEN = """── recommendation ──
  cite: recommendation
  action: approach
  role: VP Engineering
  reason: Appointed a new VP of Engineering — 20 days ago, and more than one provider saw it.

── buying committee roles ──
  title: VP Engineering
  cite: VP Engineering
  part: champion
  strength: strong
  evidence: Appointed a new VP of Engineering
  cite: 5e000000-0000-4000-8000-000000000001
  occurred: 2026-07-14 (July 2026)
  corroborating providers: 2
  title: CFO
  cite: CFO
  part: economic_buyer
  strength: not ranked
  why not: Nothing Signora has observed at this account names this role.

── what signora does not know ──
  subject: CFO
  cite: CFO
  question: Who is your CFO, and are they involved yet?

── citable ──
  recommendation
  VP Engineering
  5e000000-0000-4000-8000-000000000001
  CFO"""

    #: Labels whose *value* is the reasoning graph's prose, not the protocol's.
    #: Pinned by label and position; their wording belongs to `reasoning.py` and
    #: is that module's to change without bumping this protocol.
    _PROSE = ("reason", "why not", "question", "evidence")

    def test_the_rendered_shape_matches_the_specimen(self) -> None:
        """**A bare version integer with no referent would be worse than
        nothing** — nobody could tell whether a change required a bump. This is
        what `COMMERCIAL_CONTEXT_PROTOCOL_VERSION` identifies, and changing what
        a model is shown without bumping it fails here.

        **Labels and order are pinned exactly; prose values are pinned by label
        only.** The protocol owns the form — which sections, in what order, with
        which labels, and how a citation is presented. It does not own the
        graph's sentences, and asserting those here would make every wording
        change in `reasoning.py` look like a protocol change.
        """
        specimen = self.SPECIMEN.splitlines()
        actual = context().render().splitlines()

        assert len(actual) == len(specimen)
        for expected, got in zip(specimen, actual, strict=True):
            label = expected.strip().split(":", 1)[0]
            if expected.startswith("  ") and label in self._PROSE:
                assert got.startswith(f"  {label}: "), f"expected a {label} line, got {got!r}"
                continue
            assert got == expected

    def test_the_protocol_version_is_recorded(self) -> None:
        assert COMMERCIAL_CONTEXT_PROTOCOL_VERSION == 2
