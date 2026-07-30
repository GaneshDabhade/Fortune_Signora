"""The operational record of an evaluation run, readable by the run itself.

An `InferenceRecorder` — the same port the production recorder satisfies —
that keeps its records in memory instead of a table, and lets the harness
read back what happened on each call.

**Why the harness needs this at all.** `Infer` writes a record on every
outcome and returns it only on success; a grounding failure raises, taking
the returned record with it. So a run's retry count was previously visible
only in the vendor's own server log — which meant a run that timed out and
retried was indistinguishable, in Signora's own report, from a clean one.
Under *observability is a product capability* (CLAUDE.md §2) that is a
defect: the operational history has to answer the question without
reconstruction, and "read the Ollama log" is reconstruction.

**Lookup is by `correlation_id`, never by position.** The harness knows the
id it sent for each case, so nothing depends on records arriving in the order
cases were submitted — an assumption that would hold today and break the
first time the harness evaluated cases concurrently.

**Deliberately not the production table.** An evaluation is a measurement of
a prompt run from a developer's terminal; writing its rows into
`ai_inference` would put synthetic calls in the same table the *production*
ungrounded rate is read from, and the two must stay distinguishable.
"""

from __future__ import annotations

from uuid import UUID

from modules.ai_platform.domain.record import InferenceRecord


class RunLog:
    """Collects the inference records one evaluation run produced."""

    def __init__(self) -> None:
        self._records: dict[UUID, InferenceRecord] = {}

    async def record(self, record: InferenceRecord) -> None:
        self._records[record.correlation_id] = record

    def retries_for(self, correlation_id: UUID) -> int:
        """How many times the call for this case was retried.

        Zero when no record exists rather than raising: a case can fail
        *before* any call is made — an unreleased prompt, an unregistered
        model — and a report that crashed while describing that failure would
        replace a usable diagnosis with a stack trace.
        """
        found = self._records.get(correlation_id)
        return found.usage.retries if found else 0

    def __len__(self) -> int:
        return len(self._records)
