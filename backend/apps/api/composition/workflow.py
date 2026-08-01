"""Composing the Opportunity Engine's **write** surface.

Separate from `composition/opportunities.py`, and not for tidiness: the read
surface is six modules deep because an attention row needs a live score, and
none of that is reachable — or wanted — from a path that records a human
decision. **Progressing an opportunity needs the workflow tables and a
membership check, and nothing else at all.**

That asymmetry is the module's design showing through the composition root. An
opportunity holds no derived intelligence, so changing one consults none: a
falling score cannot revoke a seller's commitment, and a composition that
handed this path a score reader would be the first step toward one that could.
"""

from typing import Annotated

from fastapi import Depends

from modules.opportunity_engine.application.transition import TransitionOpportunity
from modules.opportunity_engine.infrastructure.composition import (
    build_transition_opportunity,
)
from modules.workspace_tenancy.infrastructure.composition import build_query_service
from signora_platform.api import CurrentWorkspace
from signora_platform.event_bus import PostgresOutboxEventPublisher


def transition_opportunity(context: CurrentWorkspace) -> TransitionOpportunity:
    """The workflow write path, assembled for one request.

    The publisher writes to the outbox **on the request's own session**, so
    the state row and the event announcing it commit together or not at all.
    An event published before its cause committed is the failure the outbox
    exists to prevent (06-events.md).
    """
    return build_transition_opportunity(
        context.session,
        # Membership is Workspace & Tenancy's fact, read through the one
        # approved synchronous cross-module interface. This module keeps no
        # copy of who belongs where.
        workspaces=build_query_service(context.session),
        publisher=PostgresOutboxEventPublisher(),
    )


OpportunityWorkflow = Annotated[TransitionOpportunity, Depends(transition_opportunity)]

__all__ = ["OpportunityWorkflow", "transition_opportunity"]
