"""The one line this module has to hold: **it identifies; it does not judge.**

[ADR-0400](../../../docs/architecture/adr/0400-person-as-an-entity.md) asks for
this test by name — *"a structural test refuses the words, as `test_boundary.py`
already does for the committee"* — and says why it is needed here more than
anywhere:

> **A person is one plausible field away from becoming an influence model.**

`seniority_score`, `is_key_contact`, `priority`, an ordered list read as a
ranking: each turns an identity into a scoring input, **in the module least
equipped to review it.** Influence is `buying_score_engine`'s.

**Modelled on `tests/commercial_profile/test_boundary.py` and deliberately not
shared with it.** Two bounded contexts asserting one rule through one helper
would make either free to weaken it for the other, and the word lists are not
the same: this one adds `seniority` and `key_contact`, which mean nothing next
to an ICP and everything next to a person.
"""

from __future__ import annotations

import ast
import importlib
import inspect
import pkgutil

import modules.people.domain as domain

#: Words that turn an identity into a scoring input.
#:
#: **`seniority` is deliberately absent, and it is the interesting exclusion.**
#: `Affiliation.seniority` carries the provider's own band verbatim, because
#: `business_event_engine` already filters on it — banning the word would force
#: a synonym and put a second vocabulary in the module that owns none. **What
#: is banned is `seniority_score`**, which `_SCORING` catches through `score`.
FORBIDDEN = (
    "score",
    "priority",
    "rank",
    "propensity",
    "fit",
    "weight",
    "influence",
    "importance",
    "key_contact",
)


def _identifiers(source: str) -> set[str]:
    """Every name the code *uses*, read as a syntax tree.

    **Not text.** This module's prose argues at length about influence models
    and scoring, which is the rule being explained rather than broken — and a
    check that cannot tell code from a comment gets weakened until it means
    nothing.
    """
    tree = ast.parse(source)
    return (
        {
            node.id if isinstance(node, ast.Name) else node.attr
            for node in ast.walk(tree)
            if isinstance(node, (ast.Name, ast.Attribute))
        }
        | {
            node.name
            for node in ast.walk(tree)
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))
        }
        | {
            node.target.id
            for node in ast.walk(tree)
            if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name)
        }
    )


def _domain_modules() -> list[str]:
    found = [info.name for info in pkgutil.iter_modules(domain.__path__) if not info.ispkg]
    assert found, "the scan found no domain modules — it would pass vacuously"
    return found


class TestPeopleIdentifiesAndJudgesNothing:
    def test_no_domain_module_names_a_judgement(self) -> None:
        offenders = {
            f"{name}.{identifier}"
            for name in _domain_modules()
            for identifier in _identifiers(
                inspect.getsource(importlib.import_module(f"{domain.__name__}.{name}"))
            )
            for term in FORBIDDEN
            if term in identifier.casefold()
        }

        assert offenders == set(), (
            f"{sorted(offenders)} name a judgement about a person. This module records "
            "who somebody is and where they have worked; what any of it means about a "
            "deal belongs to the modules that already decide that."
        )

    def test_the_scan_would_notice_one(self) -> None:
        """A guard that cannot fail is documentation pretending to be code."""
        assert {
            identifier
            for identifier in _identifiers("def seniority_score(x: int) -> int: ...")
            for term in FORBIDDEN
            if term in identifier.casefold()
        } == {"seniority_score"}

    def test_it_would_notice_the_field_the_adr_names(self) -> None:
        """`is_key_contact` is the ADR's own example, and `score` does not catch it."""
        assert {
            identifier
            for identifier in _identifiers("class P:\n    is_key_contact: bool")
            for term in FORBIDDEN
            if term in identifier.casefold()
        } == {"is_key_contact"}

    def test_the_provider_seniority_band_is_still_allowed(self) -> None:
        """**The exclusion, asserted so nobody tightens it by accident.**

        `Affiliation.seniority` is the provider's word and the business-event
        rules already filter on it. A scan that banned it would force a synonym
        here and create the second vocabulary this module refuses to own.
        """
        assert {
            identifier
            for identifier in _identifiers("class A:\n    seniority: str")
            for term in FORBIDDEN
            if term in identifier.casefold()
        } == set()
