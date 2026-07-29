"""Load and validate the default opportunity policy artifact.

File I/O is infrastructure; the policy is domain language. It is read once
and validated, so a malformed policy **fails at startup rather than at the
first qualification** — an account nobody was told about is invisible, and
"no opportunities" looks exactly like "nothing qualified".

The artifact lives in the repository because the *shape* of the policy is
Signora's design. A customer's own thresholds live in the database because
*"when do we start tracking"* is a commercial judgement about their
business. The deciding criterion is ownership, not technology
(docs/architecture/27-opportunity-engine.md).
"""

from __future__ import annotations

from functools import cache
from pathlib import Path

from pydantic import ValidationError

from modules.opportunity_engine.domain.policy import (
    CURRENT_POLICY_VERSION,
    OpportunityPolicy,
    PolicyError,
)

POLICY_DIR = Path(__file__).resolve().parent.parent / "policy"


@cache
def load_policy(version: int = CURRENT_POLICY_VERSION) -> OpportunityPolicy:
    path = POLICY_DIR / f"opportunity_policy@{version}.json"
    if not path.exists():
        raise PolicyError(
            f"opportunity policy v{version} not found at {path}. A version recorded on "
            "historical opportunities must remain loadable, or those opportunities become "
            "unexplainable."
        )

    try:
        policy = OpportunityPolicy.model_validate_json(path.read_text())
    except ValidationError as exc:
        raise PolicyError(
            f"opportunity policy v{version} is malformed: {exc}. Failing at startup rather than "
            "at the first qualification — an account nobody was told about is invisible."
        ) from exc

    if policy.version != version:
        raise PolicyError(
            f"{path.name} declares version {policy.version}. The filename and the declared "
            "version must agree, or an opportunity's recorded version names the wrong rule."
        )
    return policy
