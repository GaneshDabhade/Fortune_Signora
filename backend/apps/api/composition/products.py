"""Composing the Commercial Profile's read and write surfaces.

**One level deep — the shallowest composition in the repository**, and that
is the boundary rather than an omission. The module records what a customer
declares: it reads no other module, calls no provider, and computes nothing,
so there is nothing to assemble but a session.

Its own file, like every other surface: a router inherits every import the
module it imports makes, and a shared composition would hand this one a
transitive dependency on the ten-stage pipeline it deliberately knows nothing
about.
"""

from typing import Annotated

from fastapi import Depends

from modules.action_batch.infrastructure.composition import (
    build_action_batch_proposer,
)
from modules.commercial_profile.application.assignment_use_cases import (
    AssignAccounts,
    ReverseAssignment,
)
from modules.commercial_profile.application.declare_committee import (
    DeclareBuyingCommittee,
)
from modules.commercial_profile.application.declare_competitors import DeclareCompetitors
from modules.commercial_profile.application.declare_focus import DeclareFocus
from modules.commercial_profile.application.declare_icp import DeclareIcp
from modules.commercial_profile.application.declare_target_accounts import (
    DeclareTargetAccounts,
)
from modules.commercial_profile.application.ports import (
    BuyingCommitteeRepository,
    CommercialFocusRepository,
    DeclaredCompetitorsRepository,
    IcpDeclarationRepository,
    ProductCatalogRepository,
    TargetAccountListRepository,
)
from modules.commercial_profile.application.publish import PublishProductCatalog
from modules.commercial_profile.application.segment_queries import SegmentQueries
from modules.commercial_profile.application.tag_use_cases import (
    ApplyTagUseCase,
    CreateTagUseCase,
    ProposeTagBatchUseCase,
    RenameTagUseCase,
    TagsForAccountsUseCase,
)
from modules.commercial_profile.infrastructure.assignment_repository import (
    SqlAccountAssignmentRepository,
)
from modules.commercial_profile.infrastructure.composition import (
    build_buying_committees,
    build_catalogs,
    build_competitors,
    build_declare_buying_committee,
    build_declare_competitors,
    build_declare_focus,
    build_declare_icp,
    build_declare_target_accounts,
    build_focuses,
    build_icp_declarations,
    build_publish_product_catalog,
    build_segment_queries,
    build_target_accounts,
)
from modules.commercial_profile.infrastructure.tag_repository import (
    SqlAccountTagRepository,
    SqlTagBatchStore,
)
from modules.workspace_tenancy.infrastructure.composition import build_query_service
from signora_platform.api import CurrentWorkspace
from signora_platform.event_bus import PostgresOutboxEventPublisher


def catalogs(context: CurrentWorkspace) -> ProductCatalogRepository:
    """The read side, typed as the **port** so the router reaches the one
    method it needs and no implementation detail."""
    return build_catalogs(context.session)


def publish_catalog(context: CurrentWorkspace) -> PublishProductCatalog:
    return build_publish_product_catalog(context.session)


def icp_declarations(context: CurrentWorkspace) -> IcpDeclarationRepository:
    return build_icp_declarations(context.session)


def declare_icp(context: CurrentWorkspace) -> DeclareIcp:
    return build_declare_icp(context.session)


def buying_committees(context: CurrentWorkspace) -> BuyingCommitteeRepository:
    return build_buying_committees(context.session)


def declare_buying_committee(context: CurrentWorkspace) -> DeclareBuyingCommittee:
    return build_declare_buying_committee(context.session)


def focuses(context: CurrentWorkspace) -> CommercialFocusRepository:
    return build_focuses(context.session)


def declare_focus(context: CurrentWorkspace) -> DeclareFocus:
    return build_declare_focus(context.session)


def target_accounts(context: CurrentWorkspace) -> TargetAccountListRepository:
    return build_target_accounts(context.session)


def declare_target_accounts(context: CurrentWorkspace) -> DeclareTargetAccounts:
    """The module's only announcing write.

    **The publisher writes to the outbox on the request's own session**, so the
    watch list and the event announcing it commit together or not at all. An
    event published before its cause committed is the failure the outbox exists
    to prevent (06-events.md).
    """
    return build_declare_target_accounts(context.session, publisher=PostgresOutboxEventPublisher())


def competitors(context: CurrentWorkspace) -> DeclaredCompetitorsRepository:
    return build_competitors(context.session)


def declare_competitors(context: CurrentWorkspace) -> DeclareCompetitors:
    return build_declare_competitors(context.session)


CatalogRead = Annotated[ProductCatalogRepository, Depends(catalogs)]
CatalogWrite = Annotated[PublishProductCatalog, Depends(publish_catalog)]
IcpRead = Annotated[IcpDeclarationRepository, Depends(icp_declarations)]
IcpWrite = Annotated[DeclareIcp, Depends(declare_icp)]
CommitteeRead = Annotated[BuyingCommitteeRepository, Depends(buying_committees)]
CommitteeWrite = Annotated[DeclareBuyingCommittee, Depends(declare_buying_committee)]
FocusRead = Annotated[CommercialFocusRepository, Depends(focuses)]
FocusWrite = Annotated[DeclareFocus, Depends(declare_focus)]
TargetAccountsRead = Annotated[TargetAccountListRepository, Depends(target_accounts)]
TargetAccountsWrite = Annotated[DeclareTargetAccounts, Depends(declare_target_accounts)]
CompetitorsRead = Annotated[DeclaredCompetitorsRepository, Depends(competitors)]
CompetitorsWrite = Annotated[DeclareCompetitors, Depends(declare_competitors)]

__all__ = [
    "CatalogRead",
    "CompetitorsRead",
    "CompetitorsWrite",
    "CatalogWrite",
    "CommitteeRead",
    "CommitteeWrite",
    "FocusRead",
    "FocusWrite",
    "TargetAccountsRead",
    "TargetAccountsWrite",
    "IcpRead",
    "IcpWrite",
    "buying_committees",
    "catalogs",
    "declare_buying_committee",
    "declare_focus",
    "declare_icp",
    "declare_target_accounts",
    "focuses",
    "target_accounts",
    "icp_declarations",
    "publish_catalog",
]


def segment_queries(context: CurrentWorkspace) -> SegmentQueries:
    return build_segment_queries(context.session)


SegmentRead = Annotated[SegmentQueries, Depends(segment_queries)]


def _tag_repository(context: CurrentWorkspace) -> SqlAccountTagRepository:
    return SqlAccountTagRepository(context.session)


def _assignment_repository(context: CurrentWorkspace) -> SqlAccountAssignmentRepository:
    return SqlAccountAssignmentRepository(context.session)


def assign_accounts(context: CurrentWorkspace) -> AssignAccounts:
    """⚡ **The membership port is injected here and nowhere else.**

    📁 §6: a Settings object — and a cross-module port — is constructed **only
    at the composition root**. `commercial_profile` names
    `WorkspaceQueryPort` in its signature and never learns which
    implementation it received, which is what keeps the approved synchronous
    read (`05-module-dependencies.md` line 60) a contract rather than a reach.
    """
    return AssignAccounts(
        repository=_assignment_repository(context),
        workspaces=build_query_service(context.session),
    )


def reverse_assignment(context: CurrentWorkspace) -> ReverseAssignment:
    # ⛔ **No membership port, deliberately.** A reversal restores who held the
    # account before, including somebody who has since left — see the use
    # case's own docstring for why rechecking would make *undo* mean two
    # things.
    return ReverseAssignment(repository=_assignment_repository(context))


def assignments_for_accounts(context: CurrentWorkspace) -> SqlAccountAssignmentRepository:
    return _assignment_repository(context)


def create_tag(context: CurrentWorkspace) -> CreateTagUseCase:
    return CreateTagUseCase(tags=_tag_repository(context))


def rename_tag(context: CurrentWorkspace) -> RenameTagUseCase:
    return RenameTagUseCase(tags=_tag_repository(context))


def apply_tag_to_accounts(context: CurrentWorkspace) -> ApplyTagUseCase:
    return ApplyTagUseCase(tags=_tag_repository(context))


def tags_for_accounts(context: CurrentWorkspace) -> TagsForAccountsUseCase:
    return TagsForAccountsUseCase(tags=_tag_repository(context))


def tag_vocabulary(context: CurrentWorkspace) -> SqlAccountTagRepository:
    return _tag_repository(context)


TagVocabularyRead = Annotated[SqlAccountTagRepository, Depends(tag_vocabulary)]
AssignmentsRead = Annotated[SqlAccountAssignmentRepository, Depends(assignments_for_accounts)]
AccountsAssign = Annotated[AssignAccounts, Depends(assign_accounts)]
AssignmentReverse = Annotated[ReverseAssignment, Depends(reverse_assignment)]
TagCreate = Annotated[CreateTagUseCase, Depends(create_tag)]
TagRename = Annotated[RenameTagUseCase, Depends(rename_tag)]
TagApply = Annotated[ApplyTagUseCase, Depends(apply_tag_to_accounts)]
TagsForAccounts = Annotated[TagsForAccountsUseCase, Depends(tags_for_accounts)]


def propose_tag_batch(context: CurrentWorkspace) -> ProposeTagBatchUseCase:
    """⚡ **One session, three collaborators** — which is what makes the batch
    and its payload atomic. 📁 [D-235](../../../docs/DECISION_REGISTER.md) ①."""
    return ProposeTagBatchUseCase(
        tags=_tag_repository(context),
        batches=SqlTagBatchStore(context.session),
        proposer=build_action_batch_proposer(context.session),
    )


TagBatchPropose = Annotated[ProposeTagBatchUseCase, Depends(propose_tag_batch)]
