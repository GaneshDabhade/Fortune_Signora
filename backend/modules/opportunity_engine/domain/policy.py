"""The opportunity policy — when an account becomes worth tracking.

**The fourth layer of the platform's configuration ownership split.** The
signal catalog is Signora's (*what hypotheses mean*); the signal profile is
the customer's (*which we care about*); the scoring model is the customer's
(*how much attention each earns*); this is the customer's too — *at what
point do we start tracking?*

It is deliberately **not** folded into the scoring model, on exactly the
reasoning that kept the scoring model out of the signal profile. Every
buying score records the scoring model version that produced it, so folding
qualification in would mean changing a threshold mints a new *scoring*
version and churns the recorded explanation of every historical score — for
a reason that has nothing to do with scoring.

> **The emerging pattern:** each module owns its own customer-authored
> policy, versioned immutably alongside its output. Four modules, four
> policies, no shared configuration table — which is also what keeps any of
> them extractable.

**Qualification is a suggestion, never a commitment.** Crossing this
threshold opens an opportunity at `TRACKING` and nothing more. *Intelligence
suggests; humans commit* (ratified 2026-07-29).
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Final
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from modules.buying_score_engine.public import MAX_SCORE as SCORE_CEILING
from modules.buying_score_engine.public import BuyingScore

CURRENT_POLICY_VERSION: Final = 1
"""The artifact version this build ships. Recorded on every opportunity,
because *why does this exist* has two halves and this is one of them."""

DEFAULT_POLICY_VERSION: Final = 0
"""The version recorded when a workspace has configured nothing.

An absent policy falls back to the shipped artifact rather than qualifying
nothing, so out-of-box behaviour is reviewable in a pull request instead of
emerging from an empty table — and no seeding write is needed, which keeps
the module free of any dependency on workspace creation.
"""


class PolicyError(Exception):
    """The policy artifact is malformed.

    Raised at load time rather than at first qualification: a policy that is
    wrong should stop a deployment, not silently stop opening opportunities.
    An account nobody was told about is invisible.
    """


class OpportunityPolicy(BaseModel):
    """A complete, versioned statement of what qualifies for tracking."""

    model_config = ConfigDict(frozen=True, extra="forbid", populate_by_name=True)

    version: int
    minimum_score: int = Field(ge=0, le=SCORE_CEILING)
    """The attention at which an account becomes worth a person's time. A
    declared, reviewable constant in data — never a literal in qualification
    code, where the inherited syntax-tree invariants would forbid it."""

    contested_qualifies: bool
    """Whether opposing live readings still qualify. **True by default.** A
    fought-over account is exactly what a seller should look at, and the
    Buying Score Engine already scores it high rather than averaging it
    away — declining to act on that would partly undo its central
    decision."""

    automatic_creation: bool
    """Whether Signora opens opportunities unprompted. Creation is automatic
    and closure never is: a suggestion costs a glance to dismiss, while
    closing something a human is working on destroys their work."""

    note: str = Field(default="", alias="_comment")

    def qualifies(self, score: BuyingScore) -> bool:
        """Whether this reading is grounds for suggesting the account.

        Reads the score as given. It does not recompute, re-weight, or
        second-guess it — *why* the number is what it is was settled one
        module upstream, and the ledger already explains it.
        """
        if score.value < self.minimum_score:
            return False
        return self.contested_qualifies or not score.contested


@dataclass(frozen=True, slots=True)
class WorkspaceOpportunityPolicy:
    """A workspace's own qualification settings.

    **Immutable and versioned**, superseded rather than edited, for the
    reason that governs every configuration artifact here: every opportunity
    records the policy version that qualified it, and an edited policy would
    make every historical opportunity unexplainable — *"why was I shown
    this?"* would have no answer, because the reason changed underneath it.
    """

    id: UUID
    workspace_id: UUID
    version: int
    policy: OpportunityPolicy
    created_at: datetime
    #: Auditability. A qualification change is a commercial decision, and a
    #: customer should be able to see who made it and when.
    created_by: UUID
    supersedes: UUID | None = None


def resolve_policy(
    artifact: OpportunityPolicy, stored: WorkspaceOpportunityPolicy | None
) -> tuple[OpportunityPolicy, int]:
    """The policy in force, and the version to record against it.

    Falling back to the shipped artifact rather than failing: a workspace
    that has configured nothing should still be shown what deserves
    tracking, at Signora's declared defaults.
    """
    if stored is None:
        return artifact, DEFAULT_POLICY_VERSION
    return stored.policy, stored.version
