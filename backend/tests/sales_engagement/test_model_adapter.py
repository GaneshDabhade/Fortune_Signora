"""The one file in this module that touches a model.

**Written for [B-109](../../../docs/BUGS.md)**, which found it at 0% — the
adapter carrying every synthesis to a provider had never been executed by a
test, so *"it names no vendor"* and *"it does not repair"* rested on reading it.

These assert the four properties the module docstring claims for itself, each
of which would be violated by ordinary-looking code: **it resolves by model and
never by vendor** (`CLAUDE.md` §10), **it states sampling policy exactly once**,
**it hands the reply across untouched**, and **it asks for the domain's schema
rather than a copy of it**.

No model is called. A scripted double is correct here and a real one would be
wrong: this verifies deterministic engineering behaviour, and *"a quality
measurement taken against a fake measures the fake"* (§10).
"""

from __future__ import annotations

import json
from typing import Any
from uuid import UUID, uuid4

import pytest

from modules.ai_platform.public import InferenceRequest
from modules.sales_engagement.domain.draft import SCHEMA
from modules.sales_engagement.infrastructure.model import (
    MAX_OUTPUT_TOKENS,
    TEMPERATURE,
    TIMEOUT_SECONDS,
    ProviderSynthesisModel,
)

WORKSPACE = UUID("11111111-1111-4111-8111-111111111111")
CORRELATION = UUID("22222222-2222-4222-8222-222222222222")
REPLY = '{"summary": "They are replacing an ERP."}'


class FakeResult:
    def __init__(self, content: str) -> None:
        self.content = content


class FakeAdapter:
    def __init__(self, content: str = REPLY) -> None:
        self._content = content
        self.requests: list[InferenceRequest] = []

    async def complete(self, request: InferenceRequest) -> FakeResult:
        self.requests.append(request)
        return FakeResult(self._content)


class FakeRegistry:
    """Answers `for_model` and **offers no way to ask for a vendor** — which is
    the platform's own registry shape, kept here so a test could not simulate
    the branch the architecture forbids."""

    def __init__(self, adapter: FakeAdapter | None = None) -> None:
        self.adapter = adapter or FakeAdapter()
        self.asked_for: list[str] = []

    def for_model(self, model: str) -> FakeAdapter:
        self.asked_for.append(model)
        return self.adapter


async def _complete(
    registry: FakeRegistry, *, model: str = "claude-sonnet-4-5", prompt: str = "Explain."
) -> Any:
    adapter = ProviderSynthesisModel(registry)  # type: ignore[arg-type]
    return await adapter.complete(
        prompt=prompt, model=model, workspace_id=WORKSPACE, correlation_id=CORRELATION
    )


class TestItResolvesByModel:
    async def test_it_asks_the_registry_for_the_model_it_was_given(self) -> None:
        registry = FakeRegistry()

        await _complete(registry, model="llama3.1:8b")

        assert registry.asked_for == ["llama3.1:8b"]

    async def test_the_same_call_serves_any_model_the_environment_registers(self) -> None:
        """Vendor selection is configuration, never business logic (§10). This
        file has no branch that could distinguish one."""
        registry = FakeRegistry()

        await _complete(registry, model="claude-sonnet-4-5")
        await _complete(registry, model="granite3.3:2b")

        assert registry.asked_for == ["claude-sonnet-4-5", "granite3.3:2b"]

    def test_it_names_no_vendor_in_executable_code(self) -> None:
        """The Security Invariants parse the evaluation framework for this;
        the adapter is where a vendor name would actually be *useful*, which
        is why it is worth asserting here too."""
        import inspect

        from modules.sales_engagement.infrastructure import model as module

        source = inspect.getsource(module)
        executable = "\n".join(
            line for line in source.splitlines() if not line.lstrip().startswith("#")
        )
        body = executable.split('"""')[-1]
        for vendor in ("anthropic", "openai", "ollama", "gemini", "bedrock", "azure"):
            assert vendor not in body.lower(), f"{vendor} named in executable code"


class TestTheRequestItBuilds:
    async def test_it_carries_the_prompt_and_model_unchanged(self) -> None:
        registry = FakeRegistry()

        await _complete(registry, prompt="Summarise this account.", model="m")

        request = registry.adapter.requests[0]
        assert (request.prompt, request.model) == ("Summarise this account.", "m")

    async def test_the_workspace_and_correlation_travel_with_it(self) -> None:
        """Context assembled for a synthesis is workspace-scoped, and a call
        nobody can correlate is a call nobody can debug (§10, §16)."""
        registry = FakeRegistry()

        await _complete(registry)

        request = registry.adapter.requests[0]
        assert (request.workspace_id, request.correlation_id) == (WORKSPACE, CORRELATION)

    async def test_sampling_policy_is_the_one_stated_here(self) -> None:
        """**Behaviour exists exactly once** (§2). If these ever disagree with
        the constants, the policy has acquired a second home."""
        registry = FakeRegistry()

        await _complete(registry)

        request = registry.adapter.requests[0]
        assert request.temperature == TEMPERATURE
        assert request.max_output_tokens == MAX_OUTPUT_TOKENS
        assert request.timeout_seconds == TIMEOUT_SECONDS

    async def test_it_asks_for_the_domain_schema_rather_than_a_copy(self) -> None:
        """A second schema would be a second definition of what a draft is,
        free to drift from the type that validates one."""
        registry = FakeRegistry()

        await _complete(registry)

        assert registry.adapter.requests[0].output_schema == json.loads(SCHEMA)


class TestWhatItRefusesToDo:
    @pytest.mark.parametrize(
        "content",
        ["", "not json at all", '{"summary": ', '{"unexpected": true}'],
        ids=["empty", "prose", "truncated", "wrong-shape"],
    )
    async def test_it_hands_a_malformed_reply_across_untouched(self, content: str) -> None:
        """**It does not validate, ground, or repair.**

        An adapter that quietly fixed a malformed draft would be repairing the
        exact defect the evaluation exists to measure — and the failure rate
        would stop being measurable, which is the one number this platform most
        needs about itself (ADR-0031).
        """
        registry = FakeRegistry(FakeAdapter(content))

        reply = await _complete(registry)

        assert reply.text == content

    async def test_it_raises_nothing_of_its_own_on_a_refusal(self) -> None:
        """A refusal is content, not an exception. It is carried up to where
        it can be recorded as a result rather than lost as an error."""
        registry = FakeRegistry(FakeAdapter("I cannot help with that."))

        reply = await _complete(registry)

        assert reply.text == "I cannot help with that."


class TestTheInferenceId:
    async def test_every_reply_carries_one(self) -> None:
        registry = FakeRegistry()

        reply = await _complete(registry)

        assert isinstance(reply.inference_id, UUID)

    async def test_two_replies_are_told_apart(self) -> None:
        """Generated here today, and this becomes the `ai_inference` row's id
        when C-214 lands — nothing above the port changes either way, because
        `Synthesis` never interprets it."""
        registry = FakeRegistry()

        first = await _complete(registry)
        second = await _complete(registry)

        assert first.inference_id != second.inference_id
        assert uuid4() not in {first.inference_id, second.inference_id}
