"""M9's evaluation command refuses to invent a result.

The same guarantee M8's harness carries, asserted separately because this is a
**different composition root** — M9 owns its own, since M8's cannot import
`ReasonedOutput` without breaking the reverse-dependency contract.

The unreachable address is injected rather than inherited. M8 learned that the
hard way: those tests once passed only because no runtime happened to be
running, and broke the hour one was installed.
"""

from __future__ import annotations

from typing import Any

import pytest

from modules.ai_reasoning_engine.evaluation.__main__ import _reachable, main

#: Port 1 on the loopback: privileged, unbound, refused immediately.
NOWHERE = "http://127.0.0.1:1"


@pytest.fixture(autouse=True)
def _no_runtime(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SIGNORA_OLLAMA_BASE_URL", NOWHERE)


class TestItRefusesToMeasureWithoutAModel:
    async def test_it_exits_non_zero_and_says_why(self, capsys: Any) -> None:
        """A run that failed for some other reason would also exit non-zero,
        so the message is asserted alongside the code."""
        exit_code = await main([])

        assert exit_code == 2
        printed = capsys.readouterr().err
        assert "No model runtime" in printed
        assert NOWHERE in printed, "the refusal must name the address it tried"

    async def test_the_refusal_names_the_rootless_runtime_this_machine_uses(
        self, capsys: Any
    ) -> None:
        """`sudo` is unavailable here, so the official installer is not the
        instruction an engineer can follow."""
        await main([])
        assert "ollama serve" in capsys.readouterr().err

    async def test_an_unreachable_runtime_is_detected(self) -> None:
        import httpx

        async with httpx.AsyncClient() as client:
            assert await _reachable(client, NOWHERE) is False

    async def test_a_reachable_runtime_is_not_refused(self) -> None:
        """The positive control. A check that always reported "unreachable"
        would satisfy every test above and never run an evaluation."""
        import httpx

        async def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(200, json={"models": []})

        async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
            assert await _reachable(client, "http://any-host") is True
