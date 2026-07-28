"""Casbin-backed authorization.

Casbin is the single source of authorization truth (ADR-0010). Permissions
are never embedded in a JWT and never inferred ad hoc inside a route: a
handler asks this enforcer, and gets a yes or no.
"""

from enum import StrEnum
from pathlib import Path
from typing import Protocol
from uuid import UUID

import casbin

_POLICY_DIR = Path(__file__).parent / "policies"
MODEL_PATH = _POLICY_DIR / "model.conf"
POLICY_PATH = _POLICY_DIR / "policy.csv"


class Resource(StrEnum):
    """Resource types that appear as the ``obj`` term in a policy tuple.

    An enum rather than free strings so a typo is a type error at the call
    site instead of a silent authorization failure — a misspelled resource
    would otherwise match no policy and deny, which looks like a permissions
    bug and is tedious to trace.
    """

    WORKSPACE = "workspace"
    MEMBER = "member"


class Action(StrEnum):
    READ = "read"
    UPDATE = "update"
    ADD = "add"
    REMOVE = "remove"


class AuthorizationDeniedError(Exception):
    """The caller's role does not permit this action. Maps to HTTP 403.

    Only ever raised after membership has been verified, so the caller
    demonstrably knows the workspace exists and a 403 leaks nothing — unlike
    the non-member case, which must be a 404 (18-authentication.md).
    """

    def __init__(self, *, role: str, resource: Resource, action: Action) -> None:
        super().__init__(f"Role '{role}' may not {action} {resource}.")
        self.role = role
        self.resource = resource
        self.action = action


class Authorizer(Protocol):
    """Port consumed by the API dependency chain, so authorization can be
    substituted in tests without loading Casbin."""

    def is_allowed(
        self, *, role: str, workspace_id: UUID, resource: Resource, action: Action
    ) -> bool: ...


class CasbinAuthorizer:
    """Evaluates the model and policy files in ``policies/``.

    The enforcer is constructed once per process and is safe to share: policy
    is read-only at runtime. Policy changes ship as code review on
    ``policy.csv``, which is the point of choosing Casbin over a vendor's
    rules UI (ADR-0010).
    """

    def __init__(self, *, model_path: Path = MODEL_PATH, policy_path: Path = POLICY_PATH) -> None:
        self._enforcer = casbin.Enforcer(str(model_path), str(policy_path))

    def is_allowed(
        self, *, role: str, workspace_id: UUID, resource: Resource, action: Action
    ) -> bool:
        allowed = self._enforcer.enforce(role, str(workspace_id), str(resource), str(action))
        return bool(allowed)
