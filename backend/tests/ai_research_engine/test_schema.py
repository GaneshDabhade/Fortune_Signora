"""The at-rest guarantees of migration `0018`.

The migration claims that the domain's refusals hold *"at rest, so a row
arriving by any other path cannot claim to be a derivation."* **That claim is
prose until something proves it**, and unproven prose asserting a guarantee is
the defect shape this repository treats most seriously.

So these tests write rows the domain would refuse, by raw SQL, under the
application role — the path a future repository bug, a migration, or a
maintenance script would take. Every one must be rejected by the database
itself.

**Deliberately not re-testing what the tenancy suite already proves.** RLS,
forced RLS, the policy set, the absent `UPDATE` grant and cross-workspace
refusal are asserted for all three tables by `test_tenancy_policy.py`, driven
by their registration in `tenancy_policy.py`. Repeating them here would be a
second representation of one guarantee.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from typing import Any
from uuid import UUID, uuid4

import pytest
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from signora_platform.db.session import tenant_scoped_session

pytestmark = pytest.mark.asyncio

WORKSPACE = UUID("aaaaaaaa-1111-4111-8111-aaaaaaaaaaaa")
USER = UUID("bbbbbbbb-2222-4222-8222-bbbbbbbbbbbb")
NOW = datetime(2026, 7, 31, 12, 0, tzinfo=UTC)

_TASK = text(
    """
    INSERT INTO research_task (
        id, workspace_id, correlation_id, subject_kind, subject_id,
        opportunity_id, requested_at, created_by, updated_by
    ) VALUES (
        :id, :workspace_id, :correlation_id, :subject_kind, :subject_id,
        :opportunity_id, :requested_at, :actor, :actor
    )
    """
)

_FINDING = text(
    """
    INSERT INTO research_finding (
        id, workspace_id, task_id, subject_kind, subject_id, derivation,
        derivation_version, attributes, cited, payload_version,
        created_by, updated_by
    ) VALUES (
        :id, :workspace_id, :task_id, :subject_kind, :subject_id, :derivation,
        :derivation_version, CAST(:attributes AS jsonb), :cited, :payload_version,
        :actor, :actor
    )
    """
)

_SYNTHESIS = text(
    """
    INSERT INTO research_synthesis (
        id, workspace_id, task_id, statements, finding_ids, prompt_name,
        prompt_version, prompt_fingerprint, model, vendor, evidence_digest,
        inference_id, payload_version, created_by, updated_by
    ) VALUES (
        :id, :workspace_id, :task_id, CAST(:statements AS jsonb), :finding_ids,
        :prompt_name, :prompt_version, :prompt_fingerprint, :model, :vendor,
        :evidence_digest, :inference_id, :payload_version, :actor, :actor
    )
    """
)


def _task_row(**overrides: Any) -> dict[str, Any]:
    row: dict[str, Any] = {
        "id": uuid4(),
        "workspace_id": WORKSPACE,
        "correlation_id": uuid4(),
        "subject_kind": "entity",
        "subject_id": uuid4(),
        "opportunity_id": uuid4(),
        "requested_at": NOW,
        "actor": USER,
    }
    return row | overrides


def _finding_row(**overrides: Any) -> dict[str, Any]:
    row: dict[str, Any] = {
        "id": uuid4(),
        "workspace_id": WORKSPACE,
        "task_id": uuid4(),
        "subject_kind": "entity",
        "subject_id": uuid4(),
        "derivation": "headcount_disagreement",
        "derivation_version": 1,
        "attributes": json.dumps([{"name": "providers", "type": "int", "value": 2}]),
        "cited": [f"claim:{uuid4()}"],
        "payload_version": 1,
        "actor": USER,
    }
    return row | overrides


def _synthesis_row(**overrides: Any) -> dict[str, Any]:
    row: dict[str, Any] = {
        "id": uuid4(),
        "workspace_id": WORKSPACE,
        "task_id": uuid4(),
        "statements": json.dumps([{"text": "Two providers disagree.", "evidence": ["x:1"]}]),
        "finding_ids": [uuid4()],
        "prompt_name": "research_synthesis",
        "prompt_version": 1,
        "prompt_fingerprint": "f" * 64,
        "model": "granite3.3:2b",
        "vendor": "ollama",
        "evidence_digest": "d" * 64,
        "inference_id": uuid4(),
        "payload_version": 1,
        "actor": USER,
    }
    return row | overrides


async def _write(
    factory: async_sessionmaker[AsyncSession], statement: Any, row: dict[str, Any]
) -> None:
    async with tenant_scoped_session(factory, workspace_id=WORKSPACE, user_id=USER) as session:
        await session.execute(statement, row)


class TestTheTablesAcceptWhatTheDomainWouldBuild:
    """The positive control. Every refusal below must be a refusal *of
    something specific*, not of any insert at all."""

    async def test_a_task_is_accepted(
        self, session_factory: async_sessionmaker[AsyncSession]
    ) -> None:
        await _write(session_factory, _TASK, _task_row())

    async def test_a_finding_is_accepted(
        self, session_factory: async_sessionmaker[AsyncSession]
    ) -> None:
        await _write(session_factory, _FINDING, _finding_row())

    async def test_a_synthesis_is_accepted(
        self, session_factory: async_sessionmaker[AsyncSession]
    ) -> None:
        await _write(session_factory, _SYNTHESIS, _synthesis_row())


class TestAFindingCannotClaimToBeDerived:
    async def test_it_cannot_cite_nothing(
        self, session_factory: async_sessionmaker[AsyncSession]
    ) -> None:
        """Grounding refuses an uncited statement in flight. An uncited
        derivation is the same defect at rest."""
        with pytest.raises(IntegrityError, match="ck_research_finding_cites_evidence"):
            await _write(session_factory, _FINDING, _finding_row(cited=[]))

    async def test_it_cannot_state_nothing(
        self, session_factory: async_sessionmaker[AsyncSession]
    ) -> None:
        with pytest.raises(IntegrityError, match="ck_research_finding_states_something"):
            await _write(session_factory, _FINDING, _finding_row(attributes=json.dumps([])))

    async def test_attributes_must_be_an_array(
        self, session_factory: async_sessionmaker[AsyncSession]
    ) -> None:
        """A JSON object would store the same attributes unordered, and the
        canonical order a finding is built with would be lost on the way in."""
        with pytest.raises(IntegrityError, match="ck_research_finding_states_something"):
            await _write(
                session_factory, _FINDING, _finding_row(attributes=json.dumps({"providers": 2}))
            )

    async def test_it_cannot_hide_which_code_derived_it(
        self, session_factory: async_sessionmaker[AsyncSession]
    ) -> None:
        with pytest.raises(IntegrityError, match="ck_research_finding_names_its_derivation"):
            await _write(session_factory, _FINDING, _finding_row(derivation="   "))

    async def test_its_derivation_version_starts_at_one(
        self, session_factory: async_sessionmaker[AsyncSession]
    ) -> None:
        """Identity keys on this. A zero would make the first revision
        indistinguishable from an unversioned finding."""
        with pytest.raises(
            IntegrityError, match="ck_research_finding_derivation_version_positive"
        ):
            await _write(session_factory, _FINDING, _finding_row(derivation_version=0))


class TestASynthesisCannotBeEmptyOrUnfounded:
    async def test_it_cannot_say_nothing(
        self, session_factory: async_sessionmaker[AsyncSession]
    ) -> None:
        """An empty synthesis is a failed inference recorded as a successful
        one, and the operational history would then disagree with itself."""
        with pytest.raises(IntegrityError, match="ck_research_synthesis_says_something"):
            await _write(session_factory, _SYNTHESIS, _synthesis_row(statements=json.dumps([])))

    async def test_it_cannot_rest_on_no_findings(
        self, session_factory: async_sessionmaker[AsyncSession]
    ) -> None:
        """A narration over nothing is a model writing unprompted."""
        with pytest.raises(IntegrityError, match="ck_research_synthesis_rests_on_findings"):
            await _write(session_factory, _SYNTHESIS, _synthesis_row(finding_ids=[]))


class TestATaskNamesWhatItResearched:
    async def test_its_subject_must_be_addressed(
        self, session_factory: async_sessionmaker[AsyncSession]
    ) -> None:
        with pytest.raises(IntegrityError, match="ck_research_task_subject_is_addressed"):
            await _write(session_factory, _TASK, _task_row(subject_kind=" "))


class TestIdentityIsEnforcedByThePrimaryKey:
    async def test_re_deriving_the_same_finding_inserts_nothing_twice(
        self, session_factory: async_sessionmaker[AsyncSession]
    ) -> None:
        """**What makes replay safe.** A finding's id is derived from its
        content, so a later run that recomputes the same comparison over the
        same rows produces the same key — and the database, not the caller,
        is what stops a duplicate.

        The row is written with a *different* `task_id` the second time, which
        is the real case: `task_id` records the run that first derived it and
        is deliberately absent from identity.
        """
        derived_id = uuid4()
        await _write(session_factory, _FINDING, _finding_row(id=derived_id))

        with pytest.raises(IntegrityError, match="research_finding_pkey"):
            await _write(session_factory, _FINDING, _finding_row(id=derived_id))
