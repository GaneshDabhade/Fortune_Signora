"""Projecting one event onto one account's feed."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any
from uuid import UUID

from modules.timeline.application.ports import EntryStore
from modules.timeline.domain.entry import TimelineEntry
from modules.timeline.domain.projection import ENTITY_KEY, ProjectionRule, rule_for


class UnprojectableEvent(Exception):
    """A mapped event whose payload does not carry what its rule requires.

    **A refusal, not a fallback.** The alternative — projecting an entry with a
    missing entity or a missing reference — puts a row on a customer's feed that
    points nowhere, and the module deliberately holds no meaning of its own to
    fall back on. Failing here surfaces an upstream contract change as an error
    on the projection rather than as an unresolvable row a seller finds later.
    """


@dataclass(frozen=True, slots=True)
class ProjectEventInput:
    event_id: UUID
    event_type: str
    workspace_id: UUID
    occurred_at: datetime
    payload: dict[str, Any]


class ProjectEvent:
    """Records what an upstream module said, in time order, and nothing more."""

    def __init__(self, entries: EntryStore) -> None:
        self._entries = entries

    async def execute(self, request: ProjectEventInput) -> bool:
        """Project `request` if Timeline has a rule for it.

        Returns whether an entry was newly written — `False` covers both *"not
        an event this module projects"* and *"already projected"*, and neither
        is an error. A caller that needs to tell them apart is asking a question
        about the bus rather than about the feed.
        """
        rule = rule_for(request.event_type)
        if rule is None:
            return False

        entry = TimelineEntry.project(
            workspace_id=request.workspace_id,
            entity_id=_uuid(request.payload, ENTITY_KEY, request.event_type),
            kind=rule.kind,
            occurred_at=_when(request, rule),
            event_id=request.event_id,
            source_module=rule.source_module,
            source_ref=_uuid(request.payload, rule.source_ref_key, request.event_type),
            detail={
                key: request.payload[key]
                for key in rule.detail_keys
                # Absent rather than null: an optional field the upstream did
                # not send should not appear as a key holding nothing, because
                # the edge renders what is present.
                if request.payload.get(key) is not None
            },
        )
        return await self._entries.append(entry)


def _when(request: ProjectEventInput, rule: ProjectionRule) -> datetime:
    """When the thing happened, which is not always when the event did."""
    if rule.time_key is None:
        return request.occurred_at
    raw = request.payload.get(rule.time_key)
    if raw is None:
        return request.occurred_at
    if isinstance(raw, datetime):
        return raw
    return datetime.fromisoformat(str(raw))


def _uuid(payload: dict[str, Any], key: str, event_type: str) -> UUID:
    raw = payload.get(key)
    if raw is None:
        raise UnprojectableEvent(f"{event_type} carries no {key}")
    if isinstance(raw, UUID):
        return raw
    try:
        return UUID(str(raw))
    except ValueError as exc:
        raise UnprojectableEvent(f"{event_type} has a malformed {key}") from exc
