"""Unit tests for the Casbin policy.

These assert the *policy* itself, not just the plumbing — a policy change
that silently widens permissions should fail here.
"""

from uuid import uuid4

import pytest

from signora_platform.authorization import (
    Action,
    AuthorizationDeniedError,
    CasbinAuthorizer,
    Resource,
)


@pytest.fixture(scope="module")
def authorizer() -> CasbinAuthorizer:
    return CasbinAuthorizer()


class TestOwnerPermissions:
    @pytest.mark.parametrize(
        ("resource", "action"),
        [
            (Resource.WORKSPACE, Action.READ),
            (Resource.WORKSPACE, Action.UPDATE),
            (Resource.MEMBER, Action.READ),
            (Resource.MEMBER, Action.ADD),
            (Resource.MEMBER, Action.REMOVE),
        ],
    )
    def test_owner_is_allowed(
        self, authorizer: CasbinAuthorizer, resource: Resource, action: Action
    ) -> None:
        assert authorizer.is_allowed(
            role="owner", workspace_id=uuid4(), resource=resource, action=action
        )


class TestMemberPermissions:
    @pytest.mark.parametrize(
        ("resource", "action"),
        [(Resource.WORKSPACE, Action.READ), (Resource.MEMBER, Action.READ)],
    )
    def test_member_may_read(
        self, authorizer: CasbinAuthorizer, resource: Resource, action: Action
    ) -> None:
        assert authorizer.is_allowed(
            role="member", workspace_id=uuid4(), resource=resource, action=action
        )

    @pytest.mark.parametrize(
        ("resource", "action"),
        [
            (Resource.WORKSPACE, Action.UPDATE),
            (Resource.MEMBER, Action.ADD),
            (Resource.MEMBER, Action.REMOVE),
        ],
    )
    def test_member_may_not_mutate(
        self, authorizer: CasbinAuthorizer, resource: Resource, action: Action
    ) -> None:
        assert not authorizer.is_allowed(
            role="member", workspace_id=uuid4(), resource=resource, action=action
        )


def test_unknown_role_is_denied_everything(authorizer: CasbinAuthorizer) -> None:
    """Fails closed: a role with no policy rows gets nothing, rather than
    falling through to a permissive default."""
    assert not authorizer.is_allowed(
        role="viewer", workspace_id=uuid4(), resource=Resource.WORKSPACE, action=Action.READ
    )


def test_policy_applies_in_every_workspace(authorizer: CasbinAuthorizer) -> None:
    """Policies use "*" as the domain, so a role carries the same permissions
    in whichever workspace the caller was verified against."""
    first, second = uuid4(), uuid4()

    assert authorizer.is_allowed(
        role="owner", workspace_id=first, resource=Resource.MEMBER, action=Action.ADD
    )
    assert authorizer.is_allowed(
        role="owner", workspace_id=second, resource=Resource.MEMBER, action=Action.ADD
    )


def test_denial_error_carries_the_context_needed_to_debug_it() -> None:
    error = AuthorizationDeniedError(role="member", resource=Resource.MEMBER, action=Action.ADD)

    assert error.role == "member"
    assert error.resource is Resource.MEMBER
    assert error.action is Action.ADD
