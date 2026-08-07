"""An action is approved before it is effective, and reversible after.

**The contract, and nothing else** — slice 1 of six
([455 §5](../../../../docs/architecture/455-context-definitions-r02-r03.md)),
ratified by [ADR-0405](../../../../docs/architecture/adr/0405-an-action-is-approved-before-it-is-effective.md)
and assigned to Lane B by [D-127](../../../../docs/DECISION_REGISTER.md).

> ## **This context coordinates lifecycle. Business domains own business behaviour.**

| **This context owns** | **The consuming domain owns** |
|---|---|
| The action as the canonical unit of work · approval · withdrawal · approval state · the reversible window · execution metadata · **this contract** | **Interpreting** the action · **performing** the operation · **validating** business rules · **executing** the change · **implementing the inverse** |

⛔ **It is not responsible for business semantics**, and that sentence is the
whole boundary. It is [ADR-0402](../../../../docs/architecture/adr/0402-a-rule-is-data.md)'s
shape reused: **the module that owns an operation is the only thing that knows
how to perform or undo it.**

### Why the contract ships alone

**[P-E](../../../../docs/DOMAIN_DISCOVERY_REGISTER.md), ratified at
[D-121](../../../../docs/DECISION_REGISTER.md).** Seven consumers are waiting,
and **publishing first is what stops seven approval models being invented while
this is built.** ADR-0405 states the same thing as architecture rather than as
review practice:

> **Any future workflow requiring approval, deferred execution, reversible
> execution, withdrawal, human confirmation or staged execution must first
> evaluate whether it should *consume* this capability before introducing
> another approval model.**

**A consumer can compile, type-check and write its tests against this before a
single row is persisted** — and `lint-imports` proves the coupling never forms
while `mypy --strict` proves the contract is honoured.

### ⚠️ `action_batch` is the identity of the context, not the product's word

**No customer-facing name is ratified.** [D-127](../../../../docs/DECISION_REGISTER.md)
forbids a placeholder becoming production terminology because implementation
started first, and ADR-0405 leaves the name deliberately open: *"a name is
[ADR-0034](../../../../docs/architecture/adr/0034-ubiquitous-language.md)'s test
— would a salesperson use this word unprompted? — and it is worth one
deliberate pass rather than a placeholder that ships."*

**So nothing here names the concept in customer language**, and a consumer
rendering it must take its wording from the ratified name when there is one.

### What is deliberately absent

**No table, no endpoint, no events.** Events are slice 4 and neither is
designed — **[P-C](../../../../docs/DOMAIN_DISCOVERY_REGISTER.md): an event
exists when a consumer appears.**

> ⚠️ **Updated by slice 2.** `ApprovalState` was **defined here** while there
> was no domain to hold it. **It now lives in
> [`domain/batch.py`](../domain/batch.py) and is re-exported from here** —
> §6, *a port belongs to the module that owns the language it represents… it
> lives in that module's `domain/` and is published through its `public/`*,
> and the shape `knowledge_graph/public/attributes.py` and
> `commercial_profile/public/` both already use.
>
> ⚡ **The published API is unchanged**: same names, same `__all__`, same
> import path for every consumer. **What changed is which layer defines them**,
> and it changed because the alternative was `domain/` importing from
> `public/` — a dependency pointing outward, which every later slice would
> have inherited.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Protocol
from uuid import UUID

from modules.action_batch.domain.batch import ApprovalState, has_settled


@dataclass(frozen=True, slots=True)
class ActionBatchView:
    """One named unit of work, and where it stands.

    **`item_count` and not the items.** A consumer needs to know how large the
    thing it is describing is; **what each item *means* belongs to the domain
    that proposed it**, and publishing the items here would put business
    semantics in the context whose whole boundary is that it holds none.
    """

    id: UUID
    workspace_id: UUID
    #: What the customer called it. **Their words**, so a history reads as a
    #: record of decisions rather than a list of identifiers.
    name: str
    state: ApprovalState
    #: How many things it covers. **A count, never the payload.**
    item_count: int
    proposed_at: datetime
    proposed_by: UUID
    #: When it became effective. `None` until then — and **`APPROVED` with no
    #: `applied_at` is a real state**, not an inconsistency: approval and
    #: application are two moments, and slice 5 makes the gap between them
    #: visible.
    applied_at: datetime | None = None
    #: How long a reversal remains possible after it applied.
    reversible_for: timedelta | None = None

    def is_settled(self, *, now: datetime) -> bool:
        """Whether the reversible window has elapsed.

        > **A predicate, never a stored state** — ADR-0405 §2.

        **`now` is a parameter with no default.** A stored `is_settled` column
        would be two representations of one fact (§2), and a scheduler to flip
        it is machinery [P-B](../../../../docs/DOMAIN_DISCOVERY_REGISTER.md)
        exists to refuse. **The precedent is `Snoozed.until` in
        `signal_engine`**, which [447](../../../../docs/architecture/447-signal-center-traceability-audit.md)
        named *"the pattern R-03 should copy."*

        **An action that never applied is not settled** — it has no window to
        have elapsed — and neither is one with no window declared, which means
        reversal was never offered rather than that it has expired.

        ⚡ **Slice 2: this delegates rather than restates.** The rule is
        `domain.batch.has_settled`, and the aggregate that *enforces* the
        window on reversal calls the same function. **Two implementations of
        one window would eventually disagree about whether a customer may
        still undo something** (§2, *behaviour exists exactly once*).
        """
        return has_settled(self.applied_at, self.reversible_for, now=now)


class ActionBatchReader(Protocol):
    """Where a consuming module asks about the actions it proposed.

    ⛔ **Read-only, and deliberately.** Proposing, approving and reversing are
    slice 4's application layer; **a port that could write before the domain
    exists would let a consumer commit to a lifecycle nobody has built.**

    ⚠️ **Nothing implements this yet, and that is the slice.**
    """

    async def by_id(self, workspace_id: UUID, batch_id: UUID) -> ActionBatchView | None:
        """One action, or `None` when this workspace has no such action.

        **`None` rather than an exception**, on the terms every reader in this
        repository uses: absence is an answer a caller acts on, not a failure.
        """
        ...

    async def proposed_by(
        self, workspace_id: UUID, actor_id: UUID
    ) -> tuple[ActionBatchView, ...]:
        """Everything this person proposed, **newest first**.

        **The read a *"what did I just do?"* surface needs**, and the reason it
        is scoped to one actor rather than paginated over everybody: a person
        recalling their own action is looking at a short list, and a
        workspace-wide feed is a different question with different
        authorization.
        """
        ...


__all__ = ["ActionBatchReader", "ActionBatchView", "ApprovalState"]
