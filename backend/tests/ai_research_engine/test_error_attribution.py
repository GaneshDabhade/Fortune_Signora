"""Whose fault the customer is told it was. **The regression test for `B-103`.**

One exception class carried two meanings. A negative sequence — which nothing
a customer can send is capable of producing — surfaced as
`422 research_request_refused`, *your request was refused*. A seller was told
their request was rejected; support went to look at their data; the bug was in
ours.

`CLAUDE.md` §10: *"an incorrect attribution is worse than none, because it
misdirects the investigation."* **This one misdirected it at the customer.**

**The split is in the type, so the transport cannot re-merge it.** The row's
own warning is that without a test *"the next class added re-merges them"* —
so what is asserted here is that every unreachable state raises the invariant
type and that the mapping resolves it away from `4xx`, rather than that three
particular messages produce three particular codes.

**Module-scoped, not repository-wide, and deliberately.** `B-103` names the
same defect in `opportunity_engine`, which is another lane's module — a
repository-wide invariant asserted from here would fail their build for a row
they have not taken, and *"finding a defect outside your assignment is not
permission to fix it"* (§20e). The pattern is worth generalising once both
halves are closed.
"""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

import pytest
from fastapi import status

from modules.ai_research_engine.domain.request import (
    ResearchRequestError,
    ResearchRequestInvariantError,
    ResearchRequestState,
    ResearchStatus,
    next_state,
    opening_state,
)
from modules.ai_research_engine.interface.errors import ERROR_MAPPING
from tests.ai_research_engine.test_request import _request

NOW = datetime(2026, 8, 1, 9, 0, tzinfo=UTC)


def _resolve(exception: BaseException) -> tuple[int, str]:
    """What the customer would actually be told.

    **Starlette's own lookup, reproduced**: `_lookup_exception_handler` walks
    `type(exc).__mro__` and takes the first registered class. Asserting against
    `ERROR_MAPPING[type(exc)]` instead would pass for an exception nothing is
    registered for, which is exactly the case that matters here — the whole
    defect was a subclass falling through to its base's row.
    """
    for candidate in type(exception).__mro__:
        if candidate in ERROR_MAPPING:
            return ERROR_MAPPING[candidate]
    raise AssertionError(f"{type(exception).__name__} reaches no mapping at all")


def _settled() -> ResearchRequestState:
    """A request that has finished. **Through `RUNNING`, because the domain
    refuses the shortcut** — `REQUESTED` may only become `running` or `failed`,
    which the first draft of this file got wrong and the transition table
    caught."""
    running = next_state(opening_state(_request()), ResearchStatus.RUNNING, occurred_at=NOW)
    return next_state(running, ResearchStatus.NOTHING_TO_RESEARCH, occurred_at=NOW)


class TestAStateSignoraCouldNotHaveBuiltIsOurFault:
    """Nothing a customer sends reaches this constructor — states are built by
    the use case and the worker. Each of these means Signora constructed
    something it should not have been able to construct."""

    def test_a_negative_sequence_is_ours(self) -> None:
        with pytest.raises(ResearchRequestInvariantError):
            ResearchRequestState(
                request_id=uuid4(),
                workspace_id=uuid4(),
                sequence=-1,
                status=ResearchStatus.REQUESTED,
                occurred_at=NOW,
            )

    def test_a_completed_request_with_no_artifact_is_ours(self) -> None:
        with pytest.raises(ResearchRequestInvariantError):
            ResearchRequestState(
                request_id=uuid4(),
                workspace_id=uuid4(),
                sequence=1,
                status=ResearchStatus.COMPLETED,
                occurred_at=NOW,
            )

    def test_a_failure_with_no_reason_is_ours(self) -> None:
        with pytest.raises(ResearchRequestInvariantError):
            ResearchRequestState(
                request_id=uuid4(),
                workspace_id=uuid4(),
                sequence=1,
                status=ResearchStatus.FAILED,
                occurred_at=NOW,
            )

    @pytest.mark.parametrize(
        ("sequence", "state_status", "task_id", "detail"),
        [
            (-1, ResearchStatus.REQUESTED, None, None),
            (1, ResearchStatus.COMPLETED, None, None),
            (1, ResearchStatus.FAILED, None, None),
        ],
    )
    def test_none_of_them_reaches_the_customer_as_their_mistake(
        self,
        sequence: int,
        state_status: ResearchStatus,
        task_id: None,
        detail: None,
    ) -> None:
        """**The defect itself.** Each of these answered `422` — *your request
        was refused* — for a state the customer had no way to cause."""
        with pytest.raises(ResearchRequestError) as raised:
            ResearchRequestState(
                request_id=uuid4(),
                workspace_id=uuid4(),
                sequence=sequence,
                status=state_status,
                occurred_at=NOW,
                task_id=task_id,
                detail=detail,
            )

        code, _ = _resolve(raised.value)
        assert code >= status.HTTP_500_INTERNAL_SERVER_ERROR, (
            "a state nobody could have asked for must never be attributed to the person "
            "who asked for something else"
        )


class TestWhatTheCustomerActuallyDidStaysTheirs:
    """**The half that must not move.** `B-103` says so in as many words: *"do
    not widen the existing mapping — a refusal must stay 422, because those
    messages are written to be read and that is the point of the module."*"""

    def test_asking_a_settled_request_to_move_again_is_still_refused(self) -> None:
        settled = _settled()

        with pytest.raises(ResearchRequestError) as raised:
            next_state(settled, ResearchStatus.RUNNING, occurred_at=NOW)

        assert not isinstance(raised.value, ResearchRequestInvariantError)
        assert _resolve(raised.value) == (
            status.HTTP_422_UNPROCESSABLE_CONTENT,
            "research_request_refused",
        )

    def test_the_refusal_still_explains_itself(self) -> None:
        """The message is customer copy and stays so. A 500's message is not a
        substitute for it — it is the absence of one."""
        settled = _settled()

        with pytest.raises(ResearchRequestError, match="may become: nothing"):
            next_state(settled, ResearchStatus.RUNNING, occurred_at=NOW)


class TestTheSplitCannotQuietlyCollapse:
    def test_the_invariant_is_still_a_kind_of_refusal_to_every_caller(self) -> None:
        """**A subclass, not a sibling.** Every `except ResearchRequestError`
        in the module keeps working — both really are *"this state is not
        permitted"*. Only what a customer is told differs."""
        assert issubclass(ResearchRequestInvariantError, ResearchRequestError)

    def test_the_two_meanings_have_two_rows(self) -> None:
        """**The guard that would fail if somebody deleted the mapping row.**
        Without its own row the subclass falls through the MRO to its base and
        is `422` again — silently, and exactly as it was before `B-103`."""
        assert ResearchRequestInvariantError in ERROR_MAPPING
        assert ERROR_MAPPING[ResearchRequestInvariantError][0] >= 500
        assert ERROR_MAPPING[ResearchRequestError] == (
            status.HTTP_422_UNPROCESSABLE_CONTENT,
            "research_request_refused",
        )

    def test_the_two_codes_are_different_words(self) -> None:
        """The code is what a client branches on. Two meanings sharing one code
        would leave the split invisible to everything downstream."""
        assert (
            ERROR_MAPPING[ResearchRequestInvariantError][1]
            != (ERROR_MAPPING[ResearchRequestError][1])
        )
