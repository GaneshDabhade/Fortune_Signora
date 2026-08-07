"""A person at a target account, and nothing that judges them.

**The bounded context [ADR-0400](../../../../docs/architecture/adr/0400-person-as-an-entity.md)
ratified**, built at the scope [D-074](../../../../docs/DECISION_REGISTER.md)
approved: *"I approve moving the **People domain** implementation earlier in the
roadmap. **I am not approving the full People Intelligence feature set.**"*

> **People knows who somebody is and where they have worked. It never decides
> what any of that means about a deal.**

### Anonymous, and that is the design rather than a limitation

**No name. No email. No phone. No provider identifier.**
[C-221](../../../../docs/LANE_COORDINATION.md)
is not a constraint on this module — **it is its specification**: *"do not
expand the architecture around people… focus on role-based and
organization-level intelligence."*

**Six modules already run role changes through production and not one of them
knows a name.** A provider reports `ROLE_CHANGE` carrying
`RoleChangeValue(title, seniority, direction)`; `observation_engine` classifies
it; `business_event_engine` emits leadership appointed and departed;
`signal_engine` emits `new_decision_maker`. **What is missing is not a name —
it is a subject those events can point at**, and a subject needs no name to be
useful:

> *"A VP of Engineering joined Acme in March and left in September"* becomes
> **queryable**, where today it is two events that pass.

**Whether a provider could supply a name is ❓1 of the ADR and gates
[TASK-429](../../../../docs/BACKLOG.md), not this module.** If the answer turns
out to be no, nothing here changes.

### The temptation, named because the neighbouring module named its own

`commercial_profile/domain/committee.py` records that *"a person is one
plausible field away from becoming an influence model."* **`seniority_score`,
`is_key_contact`, `priority`, an ordered list read as a ranking** — each turns
an identity into a scoring input, **in the module least equipped to review it.**

**`test_boundary.py` reads this package as a syntax tree and refuses those
words**, exactly as the committee's does. Influence is `buying_score_engine`'s
and stays there.

### A `Person` is not a `Member`, and the separation is load-bearing

**A `Member` is a customer's employee using Signora. A `Person` is somebody at
a target account who has never heard of Signora.** Different lawful basis,
different lifecycle, different erasure story — and a test asserts the two are
not joinable.
"""

from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID


class PersonError(ValueError):
    """A person could not be described the way this module requires."""


@dataclass(frozen=True, slots=True)
class Person:
    """**An identity with nothing attached to it yet.**

    Deliberately almost empty, and the emptiness is the point: at this stage a
    person is *the thing an affiliation is about*, and every attribute anyone
    would want — a name, a title, an employer — either belongs to the
    affiliation or does not exist in this repository at all.

    **`workspace_id` is here because a person is tenant-owned.** Two customers
    tracking the same real human hold two unrelated `Person` rows, and that is
    correct rather than duplication: one customer's evidence must never become
    another's, and merging them would be the tenancy defect the whole platform
    is built to refuse.

    **There is no `current_employer` field, and there never will be.**
    [ADR-0400](../../../../docs/architecture/adr/0400-person-as-an-entity.md)
    stopped one from shipping: *"'Priya left Acme' is not a mutation of Priya —
    it is an interval closing."* A current-employer field would be **the one
    place in this repository where a state change overwrites its own
    evidence.**
    """

    id: UUID
    workspace_id: UUID

    def __post_init__(self) -> None:
        # A guard that can fire: a caller assembling a person from a row with a
        # missing tenant would otherwise produce an identity belonging to
        # nobody, which RLS cannot help with because the value never reaches it.
        if self.workspace_id is None:  # pragma: no cover - typing makes this rare
            raise PersonError("a person belongs to exactly one workspace.")


__all__ = ["Person", "PersonError"]
