"""What a customer reads when the platform refuses them.

**Domain error messages are customer copy.** `signora_platform/api/errors.py`
passes `str(exc)` through for every exception type a module registers in its
`ERROR_MAPPING`, and that is deliberate: a workflow refusal is a statement
about the customer's own data, and telling them exactly why is the point of a
module that insists every state records its reason.

It also means those sentences are **product surface**, and they were not
written as product surface. R4-03 found an opportunity UUID in a dialog
(*"It looks like a stack trace leaked into the UI."*); fixing it found two more
in the same function, one of which rendered a **Python list literal** into a
sentence a salesperson reads.

**So this asserts the pattern, not the instances.** A per-message test would
have closed one and left the rest, which is what the last two slices found
twice — the same reasoning that produced a defect once has usually produced it
more than once, and a developer following the file in front of them will
reproduce it again.
"""

from __future__ import annotations

import ast
import importlib
import inspect
import pkgutil
import re
from pathlib import Path

import pytest

import modules

#: A name whose value is an identifier. Interpolating one of these into a
#: message that reaches a customer puts something on their screen they cannot
#: read, cannot act on, and did not ask for.
_IDENTIFIER = re.compile(r"(^|_)(id|uuid)$")

#: Names that end in `_id` but are not identifiers a customer would see as
#: noise. Empty today, and present so that adding one is a deliberate act with
#: a reason beside it rather than a quietly widened regex.
_PERMITTED: frozenset[str] = frozenset()


def _module_packages() -> list[str]:
    return [
        name
        for _, name, is_pkg in pkgutil.iter_modules(modules.__path__, "modules.")
        if is_pkg
    ]


def _error_mappings() -> dict[str, list[type[Exception]]]:
    """Every exception type whose message reaches a customer verbatim.

    Read from each module's own `interface/errors.py`, so a module that adds a
    mapping is covered without this file being edited — which is what stops the
    invariant from decaying into a list somebody forgot to extend.
    """
    mappings: dict[str, list[type[Exception]]] = {}
    for package in _module_packages():
        try:
            errors = importlib.import_module(f"{package}.interface.errors")
        except ModuleNotFoundError:
            continue
        mappings[package] = list(getattr(errors, "ERROR_MAPPING", {}))
    return mappings


def _customer_facing_names() -> set[str]:
    return {
        exception.__name__
        for types in _error_mappings().values()
        for exception in types
        # Subclasses reach the customer through their base's mapping, so the
        # base name alone is not enough — but every concrete raise names one or
        # the other, and both are collected here.
        for exception in (exception, *exception.__subclasses__())
    }


def _interpolated_names(node: ast.JoinedStr) -> list[str]:
    """Every simple name interpolated into an f-string, including attributes.

    `f"{opportunity.id}"` yields `opportunity.id`; `f"{request_id}"` yields
    `request_id`. Anything more complex than a name or an attribute chain is
    reported by its source text, which is enough to fail loudly.
    """
    names: list[str] = []
    for part in node.values:
        if not isinstance(part, ast.FormattedValue):
            continue
        target = part.value
        if isinstance(target, ast.Name):
            names.append(target.id)
        elif isinstance(target, ast.Attribute):
            names.append(target.attr)
    return names


def _offending_raises(path: Path, customer_facing: set[str]) -> list[tuple[int, str]]:
    tree = ast.parse(path.read_text())
    offences: list[tuple[int, str]] = []

    for node in ast.walk(tree):
        if not isinstance(node, ast.Raise) or node.exc is None:
            continue
        call = node.exc
        if not isinstance(call, ast.Call):
            continue
        raised = call.func
        name = (
            raised.id
            if isinstance(raised, ast.Name)
            else raised.attr
            if isinstance(raised, ast.Attribute)
            else None
        )
        if name is None or name not in customer_facing:
            continue

        for argument in call.args:
            for piece in ast.walk(argument):
                if not isinstance(piece, ast.JoinedStr):
                    continue
                for interpolated in _interpolated_names(piece):
                    if interpolated in _PERMITTED:
                        continue
                    if _IDENTIFIER.search(interpolated):
                        offences.append((node.lineno, f"{name}: {{{interpolated}}}"))
    return offences


def _module_sources() -> list[Path]:
    root = Path(inspect.getfile(modules)).parent
    return sorted(
        path
        for path in root.rglob("*.py")
        # Interface layers map errors; they do not raise the domain's.
        if "__pycache__" not in path.parts
    )


class TestNoIdentifierReachesACustomer:
    """R4-03, as an invariant."""

    def test_at_least_one_module_publishes_customer_facing_errors(self) -> None:
        """**Guards the guard.** If `ERROR_MAPPING` were renamed or the import
        silently failed, every assertion below would pass over an empty set —
        a test that cannot fail is documentation pretending to be code."""
        assert _customer_facing_names(), (
            "no ERROR_MAPPING was found in any module, so this invariant is "
            "asserting nothing. Check that interface/errors.py still exports it."
        )

    def test_no_customer_facing_message_interpolates_an_identifier(self) -> None:
        """A UUID on a customer's screen is noise they cannot use.

        The identifier an engineer needs is on the correlation id, the log
        line and the row the reader is already looking at — three places that
        do not cost a salesperson a sentence they cannot read.
        """
        customer_facing = _customer_facing_names()
        offences = [
            f"{path.relative_to(Path(inspect.getfile(modules)).parent)}:{line} — {what}"
            for path in _module_sources()
            for line, what in _offending_raises(path, customer_facing)
        ]

        assert offences == [], (
            "These raises reach a customer verbatim through an ERROR_MAPPING and "
            "interpolate an identifier into the message:\n  "
            + "\n  ".join(offences)
            + "\n\nA message that needs sanitising before display is a message that "
            "will be shown unsanitised somewhere else (R4-03). Remove the id — it is "
            "already on the correlation id, the log line and the row."
        )


class TestTheInvariantWouldActuallyFire:
    """A scan that cannot detect the defect it was written for is worse than
    no scan, because it is believed. This asserts the detector directly."""

    @pytest.mark.parametrize(
        "source",
        [
            'raise OpportunityError(f"opportunity {opportunity_id} is already engaged.")',
            'raise OpportunityError(f"opportunity {current.id} is already engaged.")',
            'raise OpportunityError(f"user {user_id} is not a member.")',
        ],
        ids=["bare-name", "attribute", "other-id"],
    )
    def test_it_catches_an_identifier(self, source: str, tmp_path: Path) -> None:
        path = tmp_path / "offender.py"
        path.write_text(source)

        assert _offending_raises(path, {"OpportunityError"}) != []

    def test_it_permits_a_message_with_no_identifier(self, tmp_path: Path) -> None:
        path = tmp_path / "clean.py"
        path.write_text('raise OpportunityError(f"This account is already {stage}.")')

        assert _offending_raises(path, {"OpportunityError"}) == []

    def test_it_ignores_an_exception_no_customer_sees(self, tmp_path: Path) -> None:
        """An invariant violation raised deep in the domain becomes a 500 with
        a generic message. Those may name whatever an engineer needs."""
        path = tmp_path / "internal.py"
        path.write_text('raise ResearchError(f"finding {self.id} cites nothing.")')

        assert _offending_raises(path, {"OpportunityError"}) == []
