"""The one line this module has to hold: **it records; it does not compute.**

Asserted structurally over the whole domain package rather than over one file.
Slice 1 scanned `catalog.py` alone, which was true and narrow — the guard
would not have noticed a judgement arriving in the second aggregate, and the
second aggregate is where one is far more likely to arrive: an ideal customer
is one short step from a fit score, and the step is a plausible-looking method
somebody adds because the data is right there.
"""

from __future__ import annotations

import ast
import importlib
import inspect
import pkgutil

import modules.commercial_profile.domain as domain

#: Words that name a judgement about the world. Every one of them belongs to a
#: module downstream of this one, which already owns that judgement and is
#: already reviewed for it.
FORBIDDEN = ("score", "priority", "rank", "propensity", "fit", "weight")


def _identifiers(source: str) -> set[str]:
    """Every name the code *uses*, read as a syntax tree.

    Deliberately not text. This module's prose says *"nothing here is derived,
    matched, scored or resolved"*, which is the rule rather than a violation of
    it — and a check that cannot tell code from a comment gets weakened until
    it means nothing. The M4 and M5B invariants read ASTs for the same reason.
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


class TestTheHeadOfThePipelineComputesNothing:
    def test_no_domain_module_names_a_judgement(self) -> None:
        """**The boundary, asserted rather than documented.**

        This module records what a customer declared. The moment it carries a
        number about the world it has started deciding, and every such
        judgement is already owned — and reviewed — downstream.
        """
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
            f"{sorted(offenders)} name a judgement in the head of the pipeline. It "
            "records declarations; every judgement belongs downstream."
        )

    def test_the_scan_would_notice_one(self) -> None:
        """A guard that cannot fail is documentation pretending to be code."""
        assert {
            identifier
            for identifier in _identifiers("def icp_fit_score(x: int) -> int: ...")
            for term in FORBIDDEN
            if term in identifier.casefold()
        } == {"icp_fit_score"}
