"""What other modules may say about a person — and it is never their name.

**[TASK-457](../../../../docs/BACKLOG.md).** The types `people` publishes, so
that a consumer can name a subject without reaching into this module's domain.

> **People knows who somebody is and where they have worked. It never decides
> what any of that means about a deal.**

### Anonymous, and that is the specification rather than a limitation

**No name. No email. No phone. No provider identifier.**
[C-221](../../../../docs/LANE_COORDINATION.md) is not a constraint on this
module — it *is* its specification: *"do not expand the architecture around
people… focus on role-based and organization-level intelligence."*

**What a consumer gets is a subject, and a subject needs no name to be
useful:** *"a VP of Engineering joined Acme in March and left in September"*
becomes something an event can point at, where today it is two events that
pass.

### ⛔ What this contract deliberately does not publish

**A name, or any direct identifier.** C-221. Whether a provider could even
supply one is ❓1 of
[ADR-0400](../../../../docs/architecture/adr/0400-person-as-an-entity.md) and
gates [TASK-429](../../../../docs/BACKLOG.md) — **not this row**.

**Anything that reads these types.** The row's own bound: *"the types `people`
publishes… and nothing that reads them."* ⛔ **No reader port**, because no
consumer has been written yet and a port shaped for an imagined caller is the
speculative abstraction §6 forbids.

**Any judgement.** No score, no rank, no priority, no `is_key_contact`.
**`test_boundary.py` reads this package as a syntax tree and refuses those
words** — extended to cover `public/` by this row, because a judgement
published on a contract is one every consumer inherits. Influence is
`buying_score_engine`'s and stays there.

### Why an interval rather than a current employer

**The load-bearing choice of ADR-0400**: *"Priya left Acme" is not a mutation
of Priya — it is an interval closing.* A `current_employer` field would destroy
the history the product is built on, so **what is published is the interval**,
and *open* means **no departure has been observed** rather than *"they are
still there"*. **The two are different claims and only the first is one this
module can make.**
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from uuid import UUID


@dataclass(frozen=True, slots=True)
class PersonView:
    """Somebody at a target account, as every other module may know them.

    **Two fields, and there will never be a third that identifies them.** This
    is a subject to hang a role and an interval on — not a profile.
    """

    id: UUID
    workspace_id: UUID


@dataclass(frozen=True, slots=True)
class AffiliationView:
    """Where somebody has worked, and for how long.

    **The unit consumers actually want.** A signal saying *"a decision maker
    departed"* needs a subject, a company, a role and a period — and none of
    those is a name.
    """

    id: UUID
    workspace_id: UUID
    person_id: UUID
    #: The company as the Knowledge Graph knows it — **the same `entity_id`
    #: every other module cites**, so this joins to an account without
    #: `people` owning a second notion of what a company is.
    company_id: UUID
    #: Verbatim from the provider. ⛔ **Not normalised and not mapped to a
    #: committee seat** — *"which seat does 'Head of Clinical Informatics'
    #: fill?"* is [C-018](../../../../docs/LANE_COORDINATION.md)'s question
    #: with a different noun, and it belongs to whoever owns that mapping.
    title: str
    #: The provider's own seniority band, carried rather than re-derived
    #: because it is what the business-event rules already filter on.
    seniority: str
    started_on: date
    #: `None` means **no departure has been observed**, which is *not* the
    #: same claim as *"they still work there"*.
    ended_on: date | None = None

    @property
    def is_open(self) -> bool:
        """**No departure has been observed.** Deliberately not *"they still
        work there"* — see the module docstring."""
        return self.ended_on is None


__all__ = ["AffiliationView", "PersonView"]
