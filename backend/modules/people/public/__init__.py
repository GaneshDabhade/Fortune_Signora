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

> ⚡ **The reader arrived on 2026-08-07, and the reason it was withheld is the
> reason it now exists.** This said *"no reader port, because no consumer has
> been written yet and a port shaped for an imagined caller is the speculative
> abstraction §6 forbids."* **[TASK-458](../../../../docs/BACKLOG.md) is the
> event that ends that** — `signal_engine` is claimed, and it stated what it
> needs rather than leaving the shape to guesswork
> ([C-237](../../../../docs/LANE_COORDINATION.md)). **The port is no longer
> imagined; it is specified by its first caller**, which is the trigger the
> paragraph named.

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
from typing import Protocol
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


class AffiliationReader(Protocol):
    """Where another module asks who has held a role at a company.

    **Specified by its first caller**, [TASK-458](../../../../docs/BACKLOG.md):
    *"what a signal cannot say today is **which seat**."* `signal_engine` raises
    `new_decision_maker` and `decision_maker_departed` and can name neither the
    subject nor the period — this is the read that lets it.

    ⛔ **Read-only, and there is no write here at any point.** Affiliations are
    opened and closed by `people`'s own use case from reported role changes; a
    port that let a consumer write one would let a judging module author the
    history it is meant to read.
    """

    async def at_company(
        self, workspace_id: UUID, company_id: UUID
    ) -> tuple[AffiliationView, ...]:
        """Everyone recorded in a role at this company, **open and closed.**

        ⚠️ **Closed intervals are included deliberately.** *"Who left, and
        when"* is the question `decision_maker_departed` exists to answer, and
        a read that returned only current holders could not answer it at all.

        ⛔ **Scoped to one company on purpose.** The same title is held at every
        company in a workspace, and a workspace-wide read would invite a
        consumer to match on title alone — which is the mistake
        `match_departure` refuses one layer down.
        """
        ...

    async def for_person(
        self, workspace_id: UUID, person_id: UUID
    ) -> tuple[AffiliationView, ...]:
        """Everywhere this person has been recorded, **oldest first.**

        ⚠️ **Today this returns one affiliation in almost every case**, and that
        is a property of the platform rather than of the port: **`people` mints
        a new subject per arrival** because it holds no identifier to match one
        against ([C-221](../../../../docs/LANE_COORDINATION.md)). **Joining a
        person across companies needs a provider identifier** — ❓1 of
        [ADR-0400](../../../../docs/architecture/adr/0400-person-as-an-entity.md),
        gated on [TASK-429](../../../../docs/BACKLOG.md). **Stated so a consumer
        does not read a single-element result as a data gap.**
        """
        ...


__all__ = ["AffiliationReader", "AffiliationView", "PersonView"]
