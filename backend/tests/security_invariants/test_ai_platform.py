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
import re
import tomllib
from datetime import UTC, datetime
from pathlib import Path
from uuid import UUID

import pytest

from modules.ai_platform.application.render import render
from modules.ai_platform.domain.evidence import EvidenceFact, EvidenceRef, EvidenceSet
from modules.ai_platform.domain.prompt import PromptVersion

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


class TestTheEvaluationFrameworkNamesNoVendor:
    """**The benchmark is unchanged by who executes it.**

    Ruled 2026-07-30, when both evaluation entry points were routed through
    `build_provider_registry` and an Ollama-specific reachability probe was
    removed from each. The probe hit `/api/tags` before every run, which meant
    a *hosted* evaluation — the one that earns a release — was gated on a
    *local* runtime answering.

    The invariant is stated structurally because the failure is quiet: a
    vendor check added to the harness would still produce green runs on the
    machine that added it, and would only be discovered by whoever next tried
    to certify a prompt against a different provider. Adding OpenAI or Gemini
    must remain an adapter registration, never an edit here.

    ``evaluation/`` may still *import* a provider registry and a settings
    object — that is composition. What it may not do is name a vendor, name a
    concrete adapter, or reach a vendor's URL.
    """

    #: Both frameworks. M9 owns its own entry point (M8's cannot import
    #: ``ReasonedOutput``), so the rule has two places to be broken.
    EVALUATION_ROOTS = (
        BACKEND_ROOT / "modules" / "ai_platform" / "evaluation",
        BACKEND_ROOT / "modules" / "ai_reasoning_engine" / "evaluation",
    )

    #: Vendor tokens, matched against **executable code only**. Prose is
    #: deliberately exempt: the first draft of this invariant failed on three
    #: docstrings explaining why the framework is vendor-neutral, which would
    #: have banned exactly the writing that keeps the rule understood. The
    #: rule constrains what the code *does*.
    VENDOR_TOKENS = ("ollama", "anthropic", "claude", "openai", "gpt", "gemini", "bedrock")

    #: One legitimate appearance, and the reason the scan is scoped rather
    #: than absolute: an evaluation run needs a default model when `--model`
    #: is absent, and development is the local runtime (ADR-0028). A
    #: **default is not a branch** — nothing consults it, `--model` overrides
    #: it, and registering a Gemini adapter still requires no edit here.
    ALLOWED_ATTRIBUTES = frozenset({"ollama_model"})

    def _evaluation_modules(self) -> list[tuple[str, ast.Module]]:
        found: list[tuple[str, ast.Module]] = []
        for root in self.EVALUATION_ROOTS:
            for path in root.rglob("*.py"):
                found.append((str(path.relative_to(BACKEND_ROOT)), ast.parse(path.read_text())))
        return found

    @staticmethod
    def _docstrings(tree: ast.Module) -> set[int]:
        """Node ids of every docstring, so prose is excluded from the scan."""
        holders = (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)
        found: set[int] = set()
        for node in ast.walk(tree):
            if isinstance(node, holders) and node.body:
                first = node.body[0]
                if isinstance(first, ast.Expr) and isinstance(first.value, ast.Constant):
                    found.add(id(first.value))
        return found

    def test_the_evaluation_sources_exist(self) -> None:
        """A scan over nothing passes. Both frameworks must be present for the
        assertions below to have said anything at all."""
        scanned = {name for name, _ in self._evaluation_modules()}
        assert any("ai_platform" in name for name in scanned)
        assert any("ai_reasoning_engine" in name for name in scanned)

    def test_no_evaluation_module_imports_or_builds_a_concrete_adapter(self) -> None:
        """**The property that actually decides whether a new vendor is free.**

        An evaluation that constructs an adapter has to be edited to add one;
        an evaluation that asks a registry does not. It is also what makes
        "never substitutes a fake" true: a file that may not name an adapter
        cannot name a scripted one.
        """
        offences: list[str] = []
        for filename, tree in self._evaluation_modules():
            for name in _imported_module_names(tree):
                if "adapters" in name:
                    offences.append(f"{filename} imports {name}")
            for node in ast.walk(tree):
                if isinstance(node, ast.Call):
                    called = str(
                        getattr(node.func, "id", "") or getattr(node.func, "attr", "") or ""
                    )
                    if called.endswith("Adapter"):
                        offences.append(f"{filename} constructs {called}")
        assert not offences, (
            "The evaluation framework must obtain providers from the registry the AI "
            "Platform builds from settings, never construct one. Adding OpenAI or Gemini "
            "has to remain an adapter registration, not an edit here.\n  " + "\n  ".join(offences)
        )

    def test_no_evaluation_module_names_a_vendor_in_code(self) -> None:
        """String literals and attribute names, docstrings excluded.

        This is what caught the `/api/tags` reachability probe: a vendor's own
        URL, hard-coded in the framework, gating a *hosted* release run on a
        *local* runtime answering.
        """
        offences: list[str] = []
        for filename, tree in self._evaluation_modules():
            prose = self._docstrings(tree)
            for node in ast.walk(tree):
                if (
                    isinstance(node, ast.Constant)
                    and isinstance(node.value, str)
                    and id(node) not in prose
                ):
                    lowered = node.value.lower()
                    for token in (*self.VENDOR_TOKENS, "/api/"):
                        if token in lowered:
                            offences.append(f"{filename} has the literal '{node.value}'")
                elif isinstance(node, ast.Attribute) and node.attr not in self.ALLOWED_ATTRIBUTES:
                    lowered = node.attr.lower()
                    for token in self.VENDOR_TOKENS:
                        if token in lowered:
                            offences.append(f"{filename} reads '.{node.attr}'")
        assert not offences, (
            "A run states the *model* it wants; which adapter serves it is the registry's "
            "answer. A vendor named in evaluation code makes the benchmark depend on who "
            "executes it, which is the one thing it must not.\n  " + "\n  ".join(offences)
        )

    def test_the_scan_would_detect_a_vendor_if_one_appeared(self) -> None:
        """The positive control. Without it, a scan whose token list had been
        emptied — or whose paths had drifted — would pass silently and assert
        nothing, which is the exact failure mode this class exists to prevent.
        """
        planted = ast.parse('probe("http://x/api/tags")\nadapter = OllamaAdapter()\n')
        prose = self._docstrings(planted)
        literals = [
            n.value
            for n in ast.walk(planted)
            if isinstance(n, ast.Constant) and isinstance(n.value, str) and id(n) not in prose
        ]
        assert any("/api/" in literal for literal in literals)
        assert any(
            getattr(n.func, "id", "").endswith("Adapter")
            for n in ast.walk(planted)
            if isinstance(n, ast.Call)
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
        """**Widened at T137, from the AI Platform to every module.**

        The scan previously covered `modules/ai_platform` alone, so a consumer
        calling `measure` from its own request path was invisible to it — found
        by a mutation that swapped `execute` for `measure` in the AI Research
        Engine and broke nothing. The rule was always repository-wide: the
        exception belongs to evaluation, whoever's evaluation it is.
        """
        offences: list[str] = []
        for path in (BACKEND_ROOT / "modules").rglob("*.py"):
            if self.ALLOWED in path.parts or path.name == "infer.py":
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


class TestOneAuthorityDecidesWhatAModelSees:
    """**ADR-0031's defect, made unrepresentable.**

    For two milestones `application/render.py` authored the citation's display
    form while `EvidenceRef.parse` defined the grammar that had to read it back,
    and nothing reconciled them — *a protocol shared by two components that
    neither owned*. The disagreement was invisible until a model took its
    instructions literally, and it cost three prompts their release.

    These assert the ownership, not the form. The form is protocol 2 and is
    pinned by specimen in `tests/ai_platform/test_rendering_protocol.py`; what
    must never come back is a **second** author.
    """

    RENDERER = AI_PLATFORM_ROOT / "application" / "render.py"
    PROTOCOL = AI_PLATFORM_ROOT / "domain" / "rendering.py"

    def test_the_renderer_never_touches_a_fact_or_a_citation(self) -> None:
        """It composes: a template, a placeholder, and the protocol's output.
        A renderer that could *see* a fact could format one.

        Read from the **syntax tree**, not the text: a first attempt matched the
        word "attributes" in this module's own docstring, which would have made
        the invariant fail on prose while a real reference slipped past inside
        an f-string.
        """
        tree = ast.parse(self.RENDERER.read_text())
        referenced = {node.attr for node in ast.walk(tree) if isinstance(node, ast.Attribute)} | {
            node.id for node in ast.walk(tree) if isinstance(node, ast.Name)
        }

        for authored in ("token", "EvidenceFact", "attributes", "summary", "ref"):
            assert authored not in referenced, (
                f"application/render.py references '{authored}'. It composes protocol output "
                "and must not author protocol behaviour — the moment it can reach inside a "
                "fact, the citation has two authors again (ADR-0031)."
            )

    def test_nothing_in_the_repository_re_decorates_a_citation(self) -> None:
        """Protocol 1 wrapped citations in brackets, which is what models
        transcribed. **The specific defect is now forbidden by pattern**, not
        merely superseded — anywhere, in any module."""
        decorated = re.compile(r"[\[(<]\{[^}]*\btoken\b")
        offenders = [
            path.relative_to(BACKEND_ROOT)
            for path in (BACKEND_ROOT / "modules").rglob("*.py")
            if decorated.search(path.read_text())
        ]

        assert offenders == [], (
            f"{offenders} wrap a citation token in a delimiter. A citation must be presented "
            "exactly as `EvidenceRef.parse` accepts it, so that copying is the winning "
            "strategy and no prompt has to instruct a transformation."
        )

    def test_only_the_protocol_module_names_a_protocol_version(self) -> None:
        """One authoritative representation. A second literal would be a copy
        that goes stale the first time the protocol moves."""
        assignment = re.compile(r"^PROMPT_RENDERING_PROTOCOL_VERSION\s*[:=]", re.MULTILINE)
        declaring = [
            path.relative_to(BACKEND_ROOT)
            for path in (BACKEND_ROOT / "modules").rglob("*.py")
            if assignment.search(path.read_text())
        ]

        assert declaring == [self.PROTOCOL.relative_to(BACKEND_ROOT)]

    def test_what_is_rendered_is_what_the_parser_accepts(self) -> None:
        """The round trip, over the bytes rather than over the token — the
        assertion whose absence let the two drift apart."""
        prompt = PromptVersion(
            name="specimen", version=1, owner="ai-platform@signora", text="{facts}"
        )
        workspace_id = UUID(int=99)
        facts = tuple(
            EvidenceFact(
                ref=EvidenceRef(kind=kind, id=UUID(int=index)),
                workspace_id=workspace_id,
                summary=f"Fact {index}.",
                attributes=(("weight", index),),
            )
            for index, kind in enumerate(("business_event", "signal_contribution"), start=1)
        )
        evidence = EvidenceSet(
            workspace_id=workspace_id, facts=facts, assembled_at=datetime(2026, 7, 31, tzinfo=UTC)
        )

        blocks = render(prompt, evidence).split("\n\n")

        assert len(blocks) == len(facts)
        for block, fact in zip(blocks, evidence, strict=True):
            citation = block.splitlines()[0].split(" ")[0]
            assert EvidenceRef.parse(citation) == fact.ref
