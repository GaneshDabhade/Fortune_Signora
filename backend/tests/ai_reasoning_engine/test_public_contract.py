"""Six verbs and no others, and a surface that cannot change the answer.

**[TASK-453](../../../docs/BACKLOG.md)**, ruled by
[D-112](../../../docs/DECISION_REGISTER.md) at
[C-419](../../../docs/LANE_COORDINATION.md): *"the engine owns the language.
Screens consume that language."*

⚠️ **This file exists because the contract did not.** `public/__init__.py` was
`__all__ = []` while the row read `CLAIMED` since 2026-08-06, and
[445](../../../docs/architecture/445-ai-copilot-traceability-audit.md) had
already recorded the gap as *"🔴 missing entirely."* **`people/public/` reached
`main` empty the same way** ([C-235](../../../docs/LANE_COORDINATION.md)) —
**a contract with no test is how an empty one survives a release check.**
"""

from __future__ import annotations

import ast
import importlib
import inspect
import json
import pkgutil
from dataclasses import FrozenInstanceError
from enum import StrEnum

import pytest

from modules.ai_reasoning_engine.public import ReasoningVerb, Surface

THE_SIX = {"explain", "summarize", "predict", "recommend", "generate", "reason"}

#: Declaration order, which is the order a consumer receives them in.
_DECLARED = ["explain", "summarize", "predict", "recommend", "generate", "reason"]


def _declared_order(value: str) -> int:
    return _DECLARED.index(value)


class TestTheVerbSetIsClosed:
    """**Closed is the property the design asserts** — *"six verbs and no
    others"* — and before this it was closed in a document and nowhere in the
    code."""

    def test_there_are_exactly_the_six_the_design_names(self) -> None:
        assert {v.value for v in ReasoningVerb} == THE_SIX

    def test_a_seventh_cannot_be_added_from_outside_this_module(self) -> None:
        """⚡ **The closure is structural, not conventional.** Python refuses to
        subclass an enum that has members, so a screen or another module
        cannot extend the taxonomy — which is exactly what putting it in the
        frontend would have allowed."""
        with pytest.raises(TypeError):

            class Seventh(ReasoningVerb):  # type: ignore[misc]
                CRITIQUE = "critique"

    def test_an_unknown_verb_is_refused_rather_than_coerced(self) -> None:
        with pytest.raises(ValueError):
            ReasoningVerb("critique")

    def test_it_is_a_string_enum_so_it_crosses_the_wire_as_its_own_name(self) -> None:
        """A consumer serializes `explain`, not `ReasoningVerb.EXPLAIN` and not
        `0` — **the taxonomy has to survive JSON to be one contract**, and
        seventeen surfaces speaking different dialects of it would be the
        duplication D-112 forbids."""
        assert issubclass(ReasoningVerb, StrEnum)
        assert json.dumps(list(ReasoningVerb)) == json.dumps(sorted(THE_SIX, key=_declared_order))
        assert f"{ReasoningVerb.EXPLAIN}" == "explain"


class TestAVerbIsNotAScale:
    """**The same refusals `SupportLevel` carries**, and for the same reason:
    a type that can be ordered is a type somebody will rank."""

    @pytest.mark.parametrize("op", ["__lt__", "__le__", "__gt__", "__ge__"])
    def test_verbs_have_no_order(self, op: str) -> None:
        with pytest.raises(TypeError, match="no order"):
            getattr(ReasoningVerb.EXPLAIN, op)(ReasoningVerb.PREDICT)

    @pytest.mark.parametrize("cast", [int, float])
    def test_a_verb_is_not_a_number(self, cast: type) -> None:
        with pytest.raises(TypeError, match="not a number"):
            cast(ReasoningVerb.EXPLAIN)

    def test_equality_still_works_because_a_consumer_must_dispatch(self) -> None:
        """**Refusing order must not refuse identity.** A caller has to be able
        to ask *which verb was this*; what it must not do is ask *which verb is
        greater*. **Exercised through a lookup**, which is how a consumer will
        actually dispatch on it."""
        handlers = {verb: verb.value.upper() for verb in ReasoningVerb}

        assert handlers[ReasoningVerb.EXPLAIN] == "EXPLAIN"
        assert len(handlers) == len(THE_SIX)
        assert len({verb.value for verb in ReasoningVerb}) == len(THE_SIX)


class TestASurfaceIsProvenanceAndNeverAnInput:
    """> **The answer must not differ because of where it was asked.**

    That sentence is what *"17 surfaces, one contract"* means."""

    def test_it_carries_nothing_to_branch_on(self) -> None:
        """⛔ **No category, no capability, no tier.** A field to branch on is a
        branch somebody will write, and seventeen branches is seventeen
        contracts sharing a route."""
        published = {f for f in Surface.__dataclass_fields__}

        assert published == {"key"}
        forbidden = {"kind", "category", "tier", "capability", "allows", "is_copilot"}
        assert not {a for a in dir(Surface) if not a.startswith("_")} & forbidden

    def test_it_is_frozen_so_two_consumers_cannot_disagree(self) -> None:
        surface = Surface("account.360")

        with pytest.raises(FrozenInstanceError):
            surface.key = "copilot"  # type: ignore[misc]

    @pytest.mark.parametrize(
        "key", ["copilot", "account.360", "opportunity.next_actions", "a", "a1.b2_c3"]
    )
    def test_a_well_formed_key_is_accepted(self, key: str) -> None:
        assert Surface(key).key == key

    @pytest.mark.parametrize(
        "key",
        [
            "",
            "Account360",
            "account-360",
            "account..360",
            ".leading",
            "trailing.",
            "1starts_with_digit",
            "has space",
            "a" * 65,
        ],
    )
    def test_a_malformed_key_is_refused(self, key: str) -> None:
        """⚠️ **The form is constrained precisely because the membership is
        not.** One operational record holding `account-360`, `account_360` and
        `Account360` can be counted by nothing — which defeats the only reason
        the surface is carried at all."""
        with pytest.raises(ValueError):
            Surface(key)

    def test_an_unattributed_inference_is_refused(self) -> None:
        with pytest.raises(ValueError, match="must say where it is"):
            Surface("")

    def test_the_set_is_deliberately_open_and_that_is_recorded(self) -> None:
        """⚠️ **`ReasoningVerb` is closed and `Surface` is not**, and the reason
        is evidence rather than taste: **the six verbs are named in the design
        and the seventeen surfaces are not.** Enumerating them here would
        invent architecture (§21), and the invented names would become the ones
        every screen had to use.

        **Pinned as a test so a later lane closing the set does so
        deliberately** — narrowing to a registry is additive and breaks no
        consumer, but it is a decision, not a tidy-up.
        """
        assert not issubclass(Surface, StrEnum)
        assert Surface("something.nobody.listed").key == "something.nobody.listed"


class TestTheEngineNeverDecidesOnASurface:
    """⚡ **Vendor neutrality's shape, one module over.** *"Recorded as
    provenance on every inference and never consulted for a decision"* (§10) —
    and asserted the way that rule is asserted, by reading the source rather
    than by trusting the docstring.

    **A guard that cannot fail is documentation pretending to be code** (§2).
    This one fails the moment somebody writes `if surface == …`.
    """

    @staticmethod
    def _sources() -> list[tuple[str, ast.Module]]:
        import modules.ai_reasoning_engine.application as application
        import modules.ai_reasoning_engine.domain as domain
        import modules.ai_reasoning_engine.public as public

        trees = []
        for package in (domain, application, public):
            for module in pkgutil.walk_packages(
                package.__path__, prefix=f"{package.__name__}."
            ):
                loaded = importlib.import_module(module.name)
                trees.append((module.name, ast.parse(inspect.getsource(loaded))))
            trees.append((package.__name__, ast.parse(inspect.getsource(package))))
        return trees

    @staticmethod
    def _offences(tree: ast.Module) -> list[int]:
        """Comparisons mentioning a surface, **excluding `Surface`'s own body.**

        ⚠️ **The exclusion is narrow and it is the point.** A type constraining
        its *own* key at construction is not a decision about which surface it
        is — `__post_init__` rejects `Account360` whoever sends it. **What is
        forbidden is everything else**: a comparison anywhere outside that
        class means behaviour turned on where the question came from.
        """
        pruned = ast.Module(
            body=[
                node
                for node in tree.body
                if not (isinstance(node, ast.ClassDef) and node.name == "Surface")
            ],
            type_ignores=[],
        )
        return [
            node.lineno
            for node in ast.walk(pruned)
            if isinstance(node, ast.Compare) and "surface" in ast.dump(node).lower()
        ]

    def test_no_decision_path_compares_against_a_surface(self) -> None:
        offences = [
            f"{name}:{line}" for name, tree in self._sources() for line in self._offences(tree)
        ]

        assert not offences, (
            "these compare against a surface: "
            + ", ".join(offences)
            + ". A surface is provenance; branching on it makes 17 contracts out of one."
        )

    def test_the_scan_catches_a_violation_when_there_is_one(self) -> None:
        """⛔ **Proving the guard can fail**, because one that cannot is
        documentation pretending to be code (§2). **Run against a synthetic
        module that does the forbidden thing**, the scan must report it — and
        the same snippet placed inside `Surface` must not, or the exclusion
        above would be hiding real violations rather than construction."""
        violating = ast.parse(
            "def answer(surface, question):\n"
            "    if surface == 'copilot':\n"
            "        return 'a different answer'\n"
        )
        assert self._offences(violating)

        constructing = ast.parse(
            "class Surface:\n"
            "    def __post_init__(self):\n"
            "        if self.surface_key > 'z':\n"
            "            raise ValueError\n"
        )
        assert not self._offences(constructing)

    def test_the_scan_actually_reaches_the_published_contract(self) -> None:
        """⚠️ **The check above passes trivially if it scans nothing.** `people`
        learned this the expensive way — its boundary scan covered `domain/`
        and not `public/`, so a judgement published on the contract would have
        been invisible to it."""
        scanned = {name for name, _ in self._sources()}

        assert any("public" in name for name in scanned)
        assert any("domain" in name for name in scanned)


def test_the_contract_publishes_exactly_these_two_things() -> None:
    """⛔ **Scope, held by a test.** TASK-453 delivers the verb set and a
    surface identifier. **A Decision Package type, a request shape or a route
    does not belong here** — those are Epic G's, and Epic G is blocked on the
    hosted credential ([C-334](../../../docs/LANE_COORDINATION.md))."""
    import modules.ai_reasoning_engine.public as contract

    assert contract.__all__ == ["ReasoningVerb", "Surface"]
