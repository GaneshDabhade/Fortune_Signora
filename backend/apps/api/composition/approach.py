"""Composing Sales Engagement's approach read surface.

**The first composition root this module has ever had.** Its `public/` has
published 39 names since SE-01 and nothing could reach any of them, because the
three ports `AssembleApproach` declares had no implementations — which is what
A-ii builds.

**Three dependencies and no model.** Assembling an approach is deterministic:
it ranks a declared committee against recorded evidence and infers which
product the account is about. The narration that turns it into prose is a
separate use case with a separate composition root, and keeping them apart is
what stops a read path acquiring a provider (§7).

**Its own file, like every other read surface** — a router inherits every
import the module it imports makes, so a shared composition would hand this one
a transitive dependency on modules it never touches.
"""

from typing import Annotated

from fastapi import Depends

from modules.business_event_engine.infrastructure.composition import (
    build_queries as build_business_event_queries,
)
from modules.commercial_profile.infrastructure.composition import (
    build_buying_committee_reader,
    build_product_catalog_reader,
)
from modules.knowledge_graph.infrastructure.composition import (
    build_queries as build_graph_queries,
)
from modules.observation_engine.infrastructure.composition import (
    build_queries as build_observation_queries,
)
from modules.provider_normalization.infrastructure.claim_reader import SqlClaimReader
from modules.sales_engagement.application.approach import AssembleApproach
from modules.sales_engagement.infrastructure.readers import (
    BusinessEventEvidenceReader,
    CommercialProfileCommittee,
    CommercialProfilePortfolio,
)
from signora_platform.api import CurrentWorkspace


def assemble_approach(context: CurrentWorkspace) -> AssembleApproach:
    """The approach use case, assembled for one request.

    **Every adapter is constructed here and injected**, so nothing in
    `sales_engagement` learns that a committee is stored, that evidence is
    queried two levels down, or that any of it is backed by SQL. The module
    programs against its own three Protocols and could not reach past them —
    the import contract refuses it.
    """
    session = context.session
    graph = build_graph_queries(
        session, claims=SqlClaimReader(session, workspace_id=context.workspace_id)
    )
    observations = build_observation_queries(session, graph=graph)
    events = build_business_event_queries(session, observations=observations)

    return AssembleApproach(
        committees=CommercialProfileCommittee(build_buying_committee_reader(session)),
        evidence=BusinessEventEvidenceReader(events),
        portfolio=CommercialProfilePortfolio(build_product_catalog_reader(session)),
    )


ApproachRead = Annotated[AssembleApproach, Depends(assemble_approach)]

__all__ = ["ApproachRead", "assemble_approach"]
