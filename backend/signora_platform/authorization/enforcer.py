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
    #: Registered by M12.1. A *use* of the platform rather than a change to
    #: it (§20a): a new member, no interface reshaped, no existing caller
    #: affected — the same category as registering a new event type.
    OPPORTUNITY = "opportunity"
    #: Registered by M12.2 — an account is what a customer calls the company
    #: an opportunity is about, and identities exist for accounts with no
    #: opportunity at all, so it is a distinct resource rather than a reuse.
    ACCOUNT = "account"
    #: Registered by M12.5. A *use* of the platform rather than a change to
    #: it (§20a) — a new member, no interface reshaped, no existing caller
    #: affected. Distinct from `WORKSPACE`: reading the catalog is something
    #: every member does daily, while changing what the company sells is an
    #: administrative act, and one resource could not express both.
    PRODUCT = "product"
    #: Registered by M12.5 slice 2, on the same terms as `PRODUCT` — a *use*
    #: of the platform rather than a change to it (§20a). Distinct from
    #: `PRODUCT` because the two are separate aggregates: a workspace can
    #: describe who buys a product without the right to change the catalog it
    #: names, and one resource could not express that.
    ICP = "icp"
    #: Registered by M12.4, on the same terms again. Distinct from `ACCOUNT`:
    #: reading an account is free and asking for research spends a model call,
    #: and one resource could not express both without making every reader a
    #: spender.
    RESEARCH = "research"
    #: Registered by M12.5 slice 3, on the same terms. Distinct from `ICP`
    #: because the two are separate aggregates a customer edits on different
    #: days — who a product is for, and who inside a company decides about it.
    BUYING_COMMITTEE = "buying_committee"
    #: Registered by M12.5 slice 4, on the same terms. Its own resource
    #: because what a company is pushing this quarter is a different
    #: administrative decision from what it sells or who buys it.
    COMMERCIAL_FOCUS = "commercial_focus"
    #: Registered by M12.5 slice 5, on the same terms. Its own resource
    #: because choosing which companies Signora spends money watching is the
    #: most consequential declaration a customer makes, and the one most
    #: likely to want a narrower grant than the rest of the profile later.
    TARGET_ACCOUNT = "target_account"
    #: Registered by M7, on the same terms as every member above — a *use* of
    #: the platform rather than a change to it (§20a). Its own resource rather
    #: than a reuse of `ACCOUNT`: reading what an account *is* and reading
    #: everything that has *happened* to it are different grants, and a feed is
    #: the surface most likely to want a narrower one later.
    TIMELINE = "timeline"
    #: Registered by M13, on the same terms as every member above — a *use* of
    #: the platform, not a change to it (§20a). Its own resource because a
    #: connection to a customer's *own* Salesforce is a different grant from
    #: anything Signora supplies: seeing which systems are connected is
    #: everyday, and connecting one spends a credential and is administrative.
    INTEGRATION = "integration"
    #: Registered by Epic D phase 1, on the same terms as every member above —
    #: a *use* of the platform, not a change to it (§20a). Its own resource
    #: rather than a reuse of `TARGET_ACCOUNT`: who a company watches and who
    #: it believes it is losing to are different admissions, and the second is
    #: the one a customer is most likely to want held more narrowly.
    COMPETITOR = "competitor"
    #: Registered by TASK-439, on the same terms as every member above — a
    #: *use* of the platform rather than a change to it (§20a), and the
    #: distinction [C-224](../../../docs/LANE_COORDINATION.md) ruled: **a
    #: `Resource` member is a declaration that a resource exists; who may act
    #: on it is granted only in `policy.csv`.** This member on its own confers
    #: nothing.
    #:
    #: Its own resource rather than a reuse of `ACCOUNT`: **triage is a write
    #: on a page every member reads.** Reading what Signora concluded is
    #: everyday; *deciding* that a conclusion was wrong is feedback the
    #: catalog learns from, and one resource could not express both without
    #: making every reader an author.
    SIGNAL = "signal"
    SAVED_VIEW = "saved_view"
    #: Registered by [TASK-469](../../../docs/BACKLOG.md) (Workflow 8), on the
    #: same terms as every member above — a *use* of the platform rather than
    #: a change to it (§20a), and the distinction
    #: [C-224](../../../docs/LANE_COORDINATION.md) ruled: **a `Resource`
    #: member declares that a resource exists; who may act on it is granted
    #: only in `policy.csv`.** This member on its own confers nothing.
    #:
    #: ⚡ **Its own resource rather than a reuse of `WORKSPACE`.** Onboarding
    #: records what *one person* confirmed on their way in, and a workspace
    #: grant would have made every owner able to read a colleague's run —
    #: which is a different admission from anything else in the workspace.
    #: ⛔ **The scoping to self is the endpoint's**, exactly as `LEAVE`'s is:
    #: the run is looked up by the caller's own verified identity, so another
    #: person's id never enters the request.
    ONBOARDING = "onboarding"
    #: Registered by [TASK-470](../../../docs/BACKLOG.md) (Workflow 9), on the
    #: same terms as every member above — a *use* of the platform rather than a
    #: change to it (§20a), and [C-224](../../../docs/LANE_COORDINATION.md)'s
    #: distinction: **declaring that a resource exists grants nothing.**
    #:
    #: ⚡ **Its own resource because a preference is one person's**, and every
    #: other resource here is the workspace's. ⛔ **The scoping to self is the
    #: endpoint's and the RLS policy's**, not the policy file's: the caller's
    #: own verified id is the only one that enters, so a grant cannot be
    #: widened into reading a colleague's preferences by editing `policy.csv`.
    PREFERENCES = "preferences"
    #: ⚡ **[TASK-465](../../../docs/BACKLOG.md), slice 5.** 📁 [§20a](../../../CLAUDE.md)
    #: ruled at [C-224](../../../docs/LANE_COORDINATION.md) that adding a member
    #: here is a **declarative registration and never an authorization grant** —
    #: *"a `Resource` entry without policy grants provides no runtime
    #: capability"* — so the grants live in `policy.csv` beside it.
    ACTION_BATCH = "action_batch"
    #: ⚡ **[TASK-466](../../../docs/BACKLOG.md), against
    #: [ADR-0411](../../../docs/architecture/adr/0411-customer-organized-account-metadata.md).**
    #: 📁 [§20a](../../../CLAUDE.md) ruled at
    #: [C-224](../../../docs/LANE_COORDINATION.md) that adding a member here is
    #: a **declarative registration and never an authorization grant** — the
    #: grants live in `policy.csv` beside it.
    #:
    #: ⚡ **Its own resource rather than a reuse of `ACCOUNT`.** ⛔ **Reading
    #: what an account IS and labelling it are different grants**, and the
    #: label is the one a customer is likely to want held more narrowly: a
    #: tag is somebody's private opinion of a company —
    #: *"Champion lost"*, *"Competitor"* — **written by a colleague and
    #: visible to everybody who can see the account.** ⚠️ **`ACCOUNT` read is
    #: granted to every member**, and folding the write in would have made
    #: every reader an author, which is the same mistake `SIGNAL` records
    #: avoiding one resource earlier.
    ACCOUNT_TAG = "account_tag"


class Action(StrEnum):
    READ = "read"
    UPDATE = "update"
    ADD = "add"
    REMOVE = "remove"
    #: Registered by ADR-0404 capability 4, closing C-207. A self-directed
    #: action, and distinct from `REMOVE` because the two differ in who the
    #: target is rather than in what happens: `remove` acts on somebody else
    #: and is an administrative power, `leave` acts on the caller and is not.
    #: Granting `member, member, remove` to express it would have made the
    #: policy file assert that a member may eject a colleague, which is false.
    #:
    #: **The scoping to self is the endpoint's, not the policy's.** Leaving
    #: takes no target, so identity never enters the request tuple —
    #: `model.conf` keeps `sub` as the caller's *role*, and membership stays in
    #: PostgreSQL under RLS rather than being mirrored into Casbin, where two
    #: sources of truth would eventually drift.
    #:
    #: **The sole-owner invariant is deliberately not here.** *"An owner may
    #: leave. A workspace may never become ownerless. Enforce the invariant in
    #: the application layer rather than the authorization engine"* — a
    #: workspace invariant hidden in the policy model is invisible to anyone
    #: reading the workspace. `Membership.LastOwnerCannotLeaveError` is where
    #: it lives.
    LEAVE = "leave"
    #: Registered by TASK-439. **Distinct from `UPDATE`, and the difference is
    #: what is being changed.** Updating an opportunity edits a record Signora
    #: keeps *for* the customer; resolving a signal is the customer telling
    #: Signora that a conclusion it reached was right, premature or wrong.
    #: **Nothing about the signal changes** — a resolution is a separate,
    #: immutable record beside it — so `update` would name a mutation that
    #: does not happen.
    RESOLVE = "resolve"


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
