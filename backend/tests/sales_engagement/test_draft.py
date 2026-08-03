"""Reading a model's reply — the shape boundary, and only the shape.

**Two failures that must stay two.** A model that cannot hold the schema needs
different work from a model that embellishes, and an evaluation that reported one
number for both would be unreadable.
"""

from __future__ import annotations

import json

import pytest

from modules.sales_engagement.domain.draft import SCHEMA, DraftMalformedError, parse


class TestTheShapeIsTheOnlyQuestionHere:
    def test_a_well_formed_reply_becomes_passages(self) -> None:
        draft = parse('{"passages": [{"text": "Approach them.", "cites": ["recommendation"]}]}')

        assert len(draft) == 1
        assert draft[0].text == "Approach them."
        assert draft[0].cites == ("recommendation",)

    def test_a_fenced_reply_is_tolerated(self) -> None:
        """**Exactly one tolerance**, and it is a presentation artifact rather
        than a failure to follow the schema. Tolerating more would be the
        platform quietly repairing output whose defects it is measuring."""
        draft = parse(
            '```json\n{"passages": [{"text": "Approach them.", "cites": ["recommendation"]}]}\n```'
        )

        assert draft[0].text == "Approach them."

    def test_prose_instead_of_json_is_malformed(self) -> None:
        with pytest.raises(DraftMalformedError, match="not the declared shape"):
            parse("Here is your summary! They look like a great fit.")

    def test_an_empty_reply_is_not_a_refusal(self) -> None:
        """A refusal is a draft that failed the fence. This never reached it,
        and conflating the two would misattribute a silent model."""
        with pytest.raises(DraftMalformedError, match="returned nothing"):
            parse("   ")

    def test_a_passage_with_no_citation_is_refused_at_the_shape_boundary(self) -> None:
        """**Caught here so the fence's message stays about content.** Free
        floating prose is an assertion, and this module publishes none."""
        with pytest.raises(DraftMalformedError):
            parse('{"passages": [{"text": "Approach them.", "cites": []}]}')

    def test_no_passages_at_all_is_refused(self) -> None:
        with pytest.raises(DraftMalformedError):
            parse('{"passages": []}')

    def test_an_unexpected_field_is_refused(self) -> None:
        """`extra="forbid"`: a model inventing a field is a model that did not
        read the schema, and accepting it would hide that."""
        with pytest.raises(DraftMalformedError):
            parse('{"passages": [{"text": "x", "cites": ["recommendation"], "confidence": 0.9}]}')


class TestTheSchemaIsDerivedNotTranscribed:
    def test_the_schema_shown_to_a_model_comes_from_the_validating_type(self) -> None:
        """**Truth has one authoritative representation** (`CLAUDE.md` §2). A
        hand-copied schema beside the parser is the second one, and the two
        disagree the first time either changes."""
        schema = json.loads(SCHEMA)

        assert "passages" in schema["properties"]
        assert schema["required"] == ["passages"]
