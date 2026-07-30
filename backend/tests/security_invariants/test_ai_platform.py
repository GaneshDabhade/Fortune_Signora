"""Invariants: the AI Platform is infrastructure, and stays infrastructure.

The AI Platform is the one module in Signora that answers no question about
a customer's accounts. It is the substrate M9 and M10 will be built on, and
its value comes from staying a substrate — which is a property that decays
one convenient import at a time.

Three guarantees, each of which would be violated quietly
(``docs/architecture/28-ai-platform.md``, ratified 2026-07-29; CLAUDE.md
§10, vendor neutrality ratified 2026-07-30):

**The substrate never depends on the pipeline.** ``domain/`` and
``application/`` know nothing of opportunities, scores, signals or events.
Reaching a business module happens in ``infrastructure/``, through that
module's ``public/`` contract, behind a Protocol the application layer
declares — the M5B ``SignalReader`` finding applied deliberately:

    If a fake cannot stand in for a dependency, the dependency was never
    really a boundary.

**No vendor SDK below the adapter line.** A model call buried in a use case
is invisible until the vendor changes, and by then every caller depends on
its shape.

**The contracts stay registered.** import-linter enforces all of the above
on every run, and its contracts live in a config file that a future change
could edit. This module asserts they are still there — deliberate overlap,
per CLAUDE.md §11, so that rewriting a feature cannot remove its guarantee.

These tests are deliberately structural. They read source and configuration;
they never call a model. A guarantee that needs a GPU to verify is not a
guarantee (28-ai-platform.md, "the two-tier guarantee").
"""

from __future__ import annotations

import ast
import tomllib
from pathlib import Path

import pytest

BACKEND_ROOT = Path(__file__).resolve().parents[2]
AI_PLATFORM_ROOT = BACKEND_ROOT / "modules" / "ai_platform"
PYPROJECT = BACKEND_ROOT / "pyproject.toml"

#: Every module that answers a question about a customer's accounts.
BUSINESS_MODULES = frozenset(
    {
        "provider_platform",
        "provider_normalization",
        "knowledge_graph",
        "observation_engine",
        "business_event_engine",
        "signal_engine",
        "buying_score_engine",
        "opportunity_engine",
        "workspace_tenancy",
    }
)

#: Model vendor SDKs and the transports they arrive on. None of these may
#: appear below ``infrastructure/``.
VENDOR_AND_TRANSPORT = frozenset(
    {"httpx", "anthropic", "openai", "ollama", "google", "boto3", "requests", "aiohttp"}
)

pytestmark = pytest.mark.security_invariant


def _sources(*layers: str) -> list[tuple[str, ast.Module]]:
    """Parsed sources for the named layers. Empty layers are legitimate —
    a guard installed before the code it guards is the right order."""
    found: list[tuple[str, ast.Module]] = []
    for layer in layers:
        for path in (AI_PLATFORM_ROOT / layer).rglob("*.py"):
            found.append((str(path.relative_to(BACKEND_ROOT)), ast.parse(path.read_text())))
    return found


def _imported_roots(tree: ast.Module) -> set[str]:
    """Top-level package names this module imports, from both import forms."""
    roots: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            roots.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module and node.level == 0:
            roots.add(node.module.split(".")[0])
    return roots


def _imported_module_names(tree: ast.Module) -> set[str]:
    """Fully dotted names of every ``modules.*`` import."""
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names.update(a.name for a in node.names if a.name.startswith("modules."))
        elif (
            isinstance(node, ast.ImportFrom) and node.module and node.module.startswith("modules.")
        ):
            names.add(node.module)
    return names


def _contract_names() -> set[str]:
    with PYPROJECT.open("rb") as handle:
        config = tomllib.load(handle)
    return {c["name"] for c in config["tool"]["importlinter"]["contracts"]}


class TestTheSubstrateNeverDependsOnThePipeline:
    """``domain/`` and ``application/`` contain no pipeline knowledge.

    This is the condition that keeps the AI Platform extractable and
    testable with fakes alone. Without it, the module that M9 and M10 stand
    on becomes a participant in the pipeline they consume — legal, acyclic,
    and a slow structural problem: by M11 the substrate cannot be reasoned
    about independently.
    """

    def test_domain_and_application_import_no_business_module(self) -> None:
        offences: list[str] = []
        for filename, tree in _sources("domain", "application"):
            for name in _imported_module_names(tree):
                owner = name.split(".")[1] if name.count(".") >= 1 else ""
                if owner in BUSINESS_MODULES:
                    offences.append(f"{filename} imports {name}")
        assert not offences, (
            "The AI Platform's domain and application layers must know nothing of the "
            "pipeline. Reach a business module from infrastructure/, through its public/ "
            "contract, behind a Protocol declared in application/ports.py.\n  "
            + "\n  ".join(offences)
        )

    def test_infrastructure_reaches_business_modules_only_through_public(self) -> None:
        offences: list[str] = []
        for filename, tree in _sources("infrastructure"):
            for name in _imported_module_names(tree):
                parts = name.split(".")
                if len(parts) >= 3 and parts[1] in BUSINESS_MODULES and parts[2] != "public":
                    offences.append(f"{filename} imports {name}")
        assert not offences, (
            "An adapter may satisfy a port from another module's public/ contract and "
            "nothing deeper. Importing a domain object, a use case, or a repository "
            "couples the substrate to an internal that is free to change.\n  "
            + "\n  ".join(offences)
        )


class TestNoVendorSdkBelowTheAdapterLine:
    """Model vendors are reached from ``infrastructure/adapters/`` only.

    CLAUDE.md §10. The AI Platform exists so that the rest of Signora never
    learns which vendor answered; a domain layer that imports ``anthropic``
    has already lost that.
    """

    def test_domain_and_application_import_no_vendor_sdk(self) -> None:
        offences: list[str] = []
        for filename, tree in _sources("domain", "application"):
            for root in sorted(_imported_roots(tree) & VENDOR_AND_TRANSPORT):
                offences.append(f"{filename} imports {root}")
        assert not offences, (
            "Vendor SDKs and HTTP transports belong in infrastructure/adapters/. "
            "Everything above the adapter speaks the port's vocabulary, which is what "
            "makes swapping Ollama for Claude a configuration change.\n  " + "\n  ".join(offences)
        )


class TestTheBoundaryContractsStayRegistered:
    """import-linter enforces the boundary; this asserts it is still asked to.

    A contract removed from ``pyproject.toml`` produces a green run, because
    a rule that is not configured cannot be broken. That failure mode is
    exactly why the overlap in CLAUDE.md §11 is deliberate.
    """

    REQUIRED = (
        "ai_platform: domain and application know nothing of the pipeline",
        "ai_platform infrastructure reaches business modules only through public/",
        "ai_platform: domain has no infrastructure/framework dependencies",
        "no business module depends on the AI Platform",
    )

    @pytest.mark.parametrize("contract", REQUIRED)
    def test_contract_is_configured(self, contract: str) -> None:
        assert contract in _contract_names(), (
            f"import-linter contract '{contract}' is missing from pyproject.toml. "
            "Deleting a contract makes the rule it expressed unenforceable while every "
            "run stays green."
        )

    def test_ai_platform_is_under_clean_architecture_enforcement(self) -> None:
        with PYPROJECT.open("rb") as handle:
            config = tomllib.load(handle)
        layering = next(
            c
            for c in config["tool"]["importlinter"]["contracts"]
            if c["name"] == "modules: Clean Architecture layering"
        )
        assert "modules.ai_platform" in layering["containers"], (
            "ai_platform must appear in the Clean Architecture layering contract's "
            "containers. The contract does not auto-discover modules, by design — so a "
            "module absent from this list is silently unenforced."
        )


class TestTheReleaseRuleHasExactlyOneException:
    """``Infer.measure`` skips the release rule. Only the harness may call it.

    The rule and the act that satisfies it cannot both come first: a prompt
    is usable with a model once it has passed evaluation against it, and
    evaluating it requires calling it. So the exception exists — named,
    narrow, and confined here rather than expressed as a
    ``skip_release_check`` argument that a request path would eventually be
    given.

    This is what makes it a guarantee rather than a comment. Without it, the
    method is one convenient import away from becoming the way a prompt gets
    used before it has earned anything, and the release rule would still
    *look* enforced.
    """

    ALLOWED = "evaluation"

    def test_only_the_harness_calls_measure(self) -> None:
        offences: list[str] = []
        for path in AI_PLATFORM_ROOT.rglob("*.py"):
            relative = path.relative_to(AI_PLATFORM_ROOT)
            if relative.parts[0] == self.ALLOWED or path.name == "infer.py":
                continue
            for node in ast.walk(ast.parse(path.read_text())):
                if (
                    isinstance(node, ast.Attribute)
                    and node.attr == "measure"
                    and isinstance(node.ctx, ast.Load)
                ):
                    offences.append(f"{path.relative_to(BACKEND_ROOT)}:{node.lineno}")

        assert not offences, (
            "Infer.measure bypasses the release rule and exists so that evaluation can "
            "produce the evidence a release is granted on. A caller outside evaluation/ "
            "using it is a prompt reaching a model it has not earned, while every test "
            "asserting the release rule still passes.\n  " + "\n  ".join(offences)
        )

    def test_the_request_path_still_enforces_the_rule(self) -> None:
        """The positive control. A refactor that removed the check from
        ``execute`` would satisfy the test above while deleting the rule."""
        source = (AI_PLATFORM_ROOT / "application" / "infer.py").read_text()
        execute = source.split("async def execute", 1)[1].split("async def measure", 1)[0]

        assert "require_model" in execute, (
            "Infer.execute no longer refuses a prompt that has not earned its model. "
            "That check is the release rule at the point of use (ADR-0028)."
        )


class TestOperationalHistoryOutlivesTheWorkItDescribes:
    """A failed inference's record survives the rollback that discards
    everything else (ADR-0029).

    **This guarantee was believed and untrue for a day**, which is the entire
    reason it is an invariant rather than a unit test. `Infer` wrote a row on
    every outcome — provably, with passing tests — while `tenant_scoped_session`
    rolled every failure record back. The ungrounded rate would have read 0%
    forever, confidently, and nothing in the suite would have said otherwise.

    Structural rather than behavioural, like everything else in this file: it
    reads the source, needs no database, and fails the moment the recorder
    starts sharing a caller's transaction again.
    """

    RECORDER = AI_PLATFORM_ROOT / "infrastructure" / "repository.py"

    def test_the_recorder_takes_a_session_factory_not_a_session(self) -> None:
        """A recorder handed a session has the caller's transaction, and
        therefore the caller's rollback."""
        tree = ast.parse(self.RECORDER.read_text())
        recorder = next(
            node
            for node in ast.walk(tree)
            if isinstance(node, ast.ClassDef) and node.name == "SqlInferenceRecorder"
        )
        init = next(
            node
            for node in recorder.body
            if isinstance(node, ast.FunctionDef) and node.name == "__init__"
        )
        annotations = {
            argument.arg: ast.unparse(argument.annotation)
            for argument in init.args.args
            if argument.annotation is not None
        }

        assert "async_sessionmaker" in annotations.get("session_factory", ""), (
            "SqlInferenceRecorder must own a session factory. Taking an AsyncSession joins "
            "the caller's transaction, so a grounding failure that propagates rolls the "
            "failure record back — and the ungrounded rate reads 0% forever (ADR-0029)."
        )

    def test_the_narration_repository_still_shares_the_callers_transaction(self) -> None:
        """The positive control, and the asymmetry that makes the rule mean
        something. A narration nobody committed was never shown to anyone, so
        it *should* roll back. If both took a factory, the distinction between
        operational history and business data would have been lost rather than
        drawn."""
        tree = ast.parse(self.RECORDER.read_text())
        repository = next(
            node
            for node in ast.walk(tree)
            if isinstance(node, ast.ClassDef) and node.name == "SqlNarrationRepository"
        )
        init = next(
            node
            for node in repository.body
            if isinstance(node, ast.FunctionDef) and node.name == "__init__"
        )
        annotations = {
            argument.arg: ast.unparse(argument.annotation)
            for argument in init.args.args
            if argument.annotation is not None
        }

        assert annotations.get("session") == "AsyncSession", (
            "SqlNarrationRepository must write on the caller's transaction. A narration "
            "that outlived a rolled-back unit of work would be an artifact no customer "
            "was ever shown (ADR-0029)."
        )

    def test_a_lost_record_is_reported_rather_than_swallowed(self) -> None:
        """The recorder deliberately does not fail its caller when it cannot
        write. That is only acceptable while the loss is loud — an ERROR line
        and a counter. A bare `except` that did neither would restore the
        silent-optimism failure by a different route."""
        source = self.RECORDER.read_text()

        assert "self._metrics.recording_failed()" in source
        assert "logger.error(" in source
        assert "operational history lost" in source
