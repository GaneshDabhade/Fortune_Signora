"""The AI Platform's own operational metrics.

Module-owned, not added to `PipelineMetrics`. A module owns everything
required to realize its behaviour, and the platform composes modules rather
than becoming the owner of their internals (CLAUDE.md §2, ratified
2026-07-30) — the same reasoning that put `AISettings` here rather than in
`signora_platform/settings.py`.

Exactly one instrument, because exactly one decision depends on it.

**`signora.ai.recording_failures` is the alarm on the alarm.** The AI
Platform's most important number is the ungrounded rate, read from
`ai_inference`. `SqlInferenceRecorder` deliberately does not fail a caller
when it cannot write that table (ADR-0029) — a narration produced correctly
must not be discarded because a log row could not be saved. But a swallowed
write is a row that silently never existed, and enough of them make the
ungrounded rate optimistic for a second time by a second mechanism.

So this counter exists to make the swallow visible. **A non-zero value means
the platform's self-measurement is incomplete, and every quality number read
from `ai_inference` during that window understates reality.** It warrants an
alert, not a dashboard tile nobody looks at.
"""

from __future__ import annotations

from typing import Final, Protocol

from opentelemetry import metrics

_METER_NAME: Final = "signora.ai_platform"

RECORDING_FAILURES: Final = "signora.ai.recording_failures"


class RecordingReporter(Protocol):
    """What the recorder needs from monitoring, and nothing more.

    A Protocol rather than the concrete class, so a test can assert the
    counter was incremented without standing up a meter provider — the same
    reason every other boundary in this module is a port.
    """

    def recording_failed(self) -> None: ...


class RecordingMetrics:
    """Instruments for durable operational recording.

    Constructed with whatever meter provider is installed. Absent an
    exporter the instrument still exists and is still recorded to — only
    export is missing — so instrumented code behaves identically in every
    environment, exactly as ``PipelineMetrics`` does.
    """

    def __init__(self, meter: metrics.Meter | None = None) -> None:
        resolved = meter or metrics.get_meter(_METER_NAME)
        self._recording_failures = resolved.create_counter(
            RECORDING_FAILURES,
            unit="1",
            description=(
                "Inference records that could not be persisted. Non-zero means the "
                "ungrounded rate and every other figure read from ai_inference "
                "understates reality for that window."
            ),
        )

    def recording_failed(self) -> None:
        self._recording_failures.add(1)
